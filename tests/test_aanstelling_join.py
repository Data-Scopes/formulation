"""STEPR1: gold URNs join to resolutions_text; overig is a sample, not invented text."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import pytest

from formulation.aanstelling import (
    LABEL_AANSTELLING,
    LABEL_OVERIG,
    RECOVERY_KEEP_NAIVE,
    RECOVERY_NAIVE,
    assign_recovered_ids,
    build_labelled_table,
    extract_urns,
    gold_urn_rows,
    naive_id_from_urn,
    urn_date,
)

FIXTURE = Path(__file__).parent / "fixtures" / "aanstelling_gold_relocations.jsonl"


def _relocations() -> list[dict]:
    return [json.loads(line) for line in FIXTURE.read_text(encoding="utf-8").splitlines() if line.strip()]


def test_extract_urns_raw_semicolon_and_url() -> None:
    raw = "urn:republic:inv-3852-date-1789-08-31-session-239-resolution-1"
    assert extract_urns(raw) == [raw]

    trailing = raw + ";"
    assert extract_urns(trailing) == [raw]

    two = (
        "urn:republic:inv-3789-date-1734-06-24-session-154-resolution-5; "
        "urn:republic:inv-3805-date-1750-01-09-session-8-resolution-6"
    )
    assert extract_urns(two) == [
        "urn:republic:inv-3789-date-1734-06-24-session-154-resolution-5",
        "urn:republic:inv-3805-date-1750-01-09-session-8-resolution-6",
    ]

    glued = (
        "urn:republic:inv-3783-date-1728-10-18-session-272-resolution-7;"
        "urn:republic:inv-3814-date-1759-08-09-session-212-resolution-3"
    )
    assert len(extract_urns(glued)) == 2

    url = (
        "https://app.goetgevonden.nl/detail/urn:republic:inv-456-date-1704-10-01-"
        "session-227-resolution-5?query[dateFrom]=1700-08-04&fragmentSize=500"
    )
    assert extract_urns(url) == [
        "urn:republic:inv-456-date-1704-10-01-session-227-resolution-5"
    ]
    assert extract_urns("") == []
    assert extract_urns(None) == []


def test_naive_id_from_urn() -> None:
    urn = "urn:republic:inv-3312-date-1685-09-23-session-82-resolution-2"
    assert naive_id_from_urn(urn) == "session-3312-num-82-resolution-2"
    assert urn_date(urn) == "1685-09-23"


def test_unparseable_republic_cell_raises() -> None:
    gold = pd.DataFrame({"resolutie_refs": ["urn:republic:not-a-resolution"]})
    with pytest.raises(ValueError, match="no well-formed"):
        gold_urn_rows(gold)


def test_relocations_override_naive_id() -> None:
    urn = "urn:republic:inv-3781-date-1726-05-01-session-98-resolution-4"
    gold = pd.DataFrame(
        {
            "resolutie_refs": [urn],
            "delegate_id": ["1"],
            "fullname": ["X"],
        }
    )
    assigned = assign_recovered_ids(gold_urn_rows(gold), _relocations())
    assert assigned["naive_id"].iloc[0] == "session-3781-num-98-resolution-4"
    assert assigned["recovered_id"].iloc[0] == "session-3781-num-116-resolution-4"
    assert assigned["join_recovery"].iloc[0] == "same_inv_date_resolution"


def test_keep_naive_1685_stays_on_naive_id() -> None:
    urn = "urn:republic:inv-3312-date-1685-09-23-session-82-resolution-2"
    gold = pd.DataFrame({"resolutie_refs": [urn], "delegate_id": ["1"], "fullname": ["X"]})
    assigned = assign_recovered_ids(gold_urn_rows(gold), _relocations())
    assert assigned["recovered_id"].iloc[0] == assigned["naive_id"].iloc[0]
    assert assigned["join_recovery"].iloc[0] == RECOVERY_KEEP_NAIVE


def _toy_flat() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "id": [
                "session-3789-num-154-resolution-5",
                "session-3781-num-116-resolution-4",
                "session-3312-num-82-resolution-2",
                "session-3900-num-1-resolution-1",
                "session-3900-num-2-resolution-1",
                "session-3900-num-3-resolution-1",
            ],
            "type": ["resolution"] * 6,
            "date": [
                "1734-06-24",
                "1726-05-01",
                "1685-09-25",
                "1734-01-01",
                "1734-01-02",
                "1734-01-03",
            ],
            "year": [1734, 1726, 1685, 1734, 1734, 1734],
            "weekday": ["a"] * 6,
            "paragraph_texts": ['["p"]'] * 6,
            "resolutions_text": [
                "aanstelling text one",
                "aanstelling text two",
                "aanstelling text 1685",
                "overig a",
                "overig b",
                "overig c",
            ],
        }
    )


def test_labelled_table_joins_text_and_samples_overig() -> None:
    gold = pd.DataFrame(
        {
            "resolutie_refs": [
                "urn:republic:inv-3789-date-1734-06-24-session-154-resolution-5",
                "urn:republic:inv-3781-date-1726-05-01-session-98-resolution-4",
                "urn:republic:inv-3312-date-1685-09-23-session-82-resolution-2",
            ],
            "delegate_id": ["10", "11", None],
            "cons_id_str": ["10", "11", "republic_add_17"],
            "fullname": ["A", "B", "C"],
        }
    )
    labelled = build_labelled_table(
        _toy_flat(),
        gold,
        _relocations(),
        overig_per_positive=1,
        random_state=0,
    )
    pos = labelled.loc[labelled["label"].eq(LABEL_AANSTELLING)]
    neg = labelled.loc[labelled["label"].eq(LABEL_OVERIG)]
    assert len(pos) == 3
    assert len(neg) == 3
    assert set(pos["resolutions_text"]) == {
        "aanstelling text one",
        "aanstelling text two",
        "aanstelling text 1685",
    }
    assert "paragraph_texts" in labelled.columns
    assert pos["join_recovery"].tolist().count("same_inv_date_resolution") == 1
    assert (pos["join_recovery"] == RECOVERY_KEEP_NAIVE).sum() == 1
    assert (pos["join_recovery"] == RECOVERY_NAIVE).sum() == 1
    assert set(neg["id"]).isdisjoint(set(pos["id"]))
    assert (neg["resolutions_text"].str.startswith("overig")).all()
    add = pos.loc[pos["id"].eq("session-3312-num-82-resolution-2"), "delegate_ids"].iloc[0]
    assert add == "republic_add_17"


def test_two_delegates_same_urn_one_resolution_row() -> None:
    urn = "urn:republic:inv-3789-date-1734-06-24-session-154-resolution-5"
    gold = pd.DataFrame(
        {
            "resolutie_refs": [urn, urn],
            "delegate_id": ["10", "20"],
            "fullname": ["A", "B"],
        }
    )
    labelled = build_labelled_table(
        _toy_flat(),
        gold,
        [],
        overig_per_positive=1,
        random_state=0,
    )
    pos = labelled.loc[labelled["label"].eq(LABEL_AANSTELLING)]
    assert len(pos) == 1
    assert pos["delegate_ids"].iloc[0] == "10; 20"


def test_missing_recovered_id_does_not_invent_text() -> None:
    gold = pd.DataFrame(
        {
            "resolutie_refs": ["urn:republic:inv-9999-date-1734-06-24-session-1-resolution-1"],
            "delegate_id": ["1"],
            "fullname": ["X"],
        }
    )
    with pytest.raises(ValueError, match="do not invent text"):
        build_labelled_table(_toy_flat(), gold, [], overig_per_positive=1, random_state=0)


def test_naive_date_mismatch_without_relocation_raises() -> None:
    flat = _toy_flat()
    flat = flat.assign(date=flat["date"].where(flat["id"] != "session-3789-num-154-resolution-5", "1734-01-01"))
    gold = pd.DataFrame(
        {
            "resolutie_refs": ["urn:republic:inv-3789-date-1734-06-24-session-154-resolution-5"],
            "delegate_id": ["1"],
            "fullname": ["X"],
        }
    )
    with pytest.raises(ValueError, match="parquet date"):
        build_labelled_table(flat, gold, [], overig_per_positive=1, random_state=0)
