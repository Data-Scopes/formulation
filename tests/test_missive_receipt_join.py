"""STEPL1: cue both-hits + seeds → labelled table; exclude aanstelling ids."""

from __future__ import annotations

import pandas as pd
import pytest

from formulation.missive_receipt import (
    LABEL_MISSIVE,
    LABEL_OVERIG,
    SOURCE_CUE_BOTH,
    SOURCE_HAND_SEED,
    build_labelled_table,
    cue_both_positives,
    match_hand_seeds,
    normalize_text,
    open_close_mask,
)


def _flat(rows: list[dict]) -> pd.DataFrame:
    return pd.DataFrame(rows)


def test_normalize_text_collapses_case_and_space() -> None:
    assert normalize_text("  ONtfangen  een   Missive  ") == "ontfangen een missive"


def test_open_close_mask_requires_both() -> None:
    text = pd.Series(
        [
            "Ontfangen een missive van X. WAAR op geen resolutie is gevallen.",
            "Ontfangen een missive van Y. is goedgevonden te committeren.",
            "Other text. geen resolutie vereischende.",
            "Ontfangen een brief van Z geen resolutie vereyschende.",
        ]
    )
    mask = open_close_mask(text)
    assert mask.tolist() == [True, False, False, True]


def test_cue_both_excludes_aanstelling_ids() -> None:
    flat = _flat(
        [
            {
                "id": "session-1-num-1-resolution-1",
                "date": "1780-01-01",
                "year": 1780,
                "resolutions_text": (
                    "Ontfangen een missive van A. WAAR op geen resolutie is gevallen."
                ),
            },
            {
                "id": "session-1-num-1-resolution-2",
                "date": "1780-01-02",
                "year": 1780,
                "resolutions_text": (
                    "Ontfangen een missive van B. WAAR op geen resolutie is gevallen."
                ),
            },
            {
                "id": "session-1-num-1-resolution-3",
                "date": "1779-01-01",
                "year": 1779,
                "resolutions_text": (
                    "Ontfangen een missive van C. WAAR op geen resolutie is gevallen."
                ),
            },
        ]
    )
    hits = cue_both_positives(
        flat,
        year_min=1780,
        year_max=1780,
        exclude_ids=["session-1-num-1-resolution-1"],
    )
    assert list(hits["id"]) == ["session-1-num-1-resolution-2"]
    assert (hits["positive_source"] == SOURCE_CUE_BOTH).all()


def test_match_hand_seeds_exact_and_unmatched() -> None:
    text = "Ontfangen een missive van Seed. WAAR op geen resolutie is gevallen."
    flat = _flat(
        [
            {
                "id": "session-9-num-1-resolution-1",
                "date": "1780-06-01",
                "year": 1780,
                "resolutions_text": text,
            }
        ]
    )
    seeds = [
        {"text": text, "note": "match", "source": "hand"},
        {"text": "totally absent seed text", "note": "miss", "source": "hand"},
    ]
    hits, unmatched = match_hand_seeds(flat, seeds, exclude_ids=[])
    assert list(hits["id"]) == ["session-9-num-1-resolution-1"]
    assert hits.iloc[0]["positive_source"] == SOURCE_HAND_SEED
    assert len(unmatched) == 1
    assert unmatched[0]["text"] == "totally absent seed text"


def test_build_labelled_table_10x_overig_and_exclusion() -> None:
    both = "Ontfangen een missive van X. WAAR op geen resolutie is gevallen."
    other = "Gewoon andere resolutie zonder cues."
    rows = []
    for i in range(1, 6):
        rows.append(
            {
                "id": f"session-1-num-1-resolution-{i}",
                "date": f"1780-01-{i:02d}",
                "year": 1780,
                "type": "",
                "weekday": "",
                "paragraph_texts": "",
                "resolutions_text": both if i <= 2 else other,
            }
        )
    # Extra overig pool
    for i in range(6, 40):
        rows.append(
            {
                "id": f"session-1-num-1-resolution-{i}",
                "date": f"1780-02-{(i % 28) + 1:02d}",
                "year": 1780,
                "type": "",
                "weekday": "",
                "paragraph_texts": "",
                "resolutions_text": other,
            }
        )
    flat = _flat(rows)
    seeds = [{"text": "unmatched hand seed only", "note": "x", "source": "hand"}]
    labelled = build_labelled_table(
        flat,
        seeds,
        exclude_ids=["session-1-num-1-resolution-1"],
        year_min=1780,
        year_max=1780,
        overig_per_positive=10,
        random_state=42,
        include_unmatched_seeds=True,
    )
    pos = labelled.loc[labelled["label"].eq(LABEL_MISSIVE)]
    neg = labelled.loc[labelled["label"].eq(LABEL_OVERIG)]
    # cue hit resolution-2 + unmatched hand_seed:0
    assert "session-1-num-1-resolution-1" not in set(pos["id"].astype(str))
    assert "session-1-num-1-resolution-2" in set(pos["id"].astype(str))
    assert any(str(i).startswith("hand_seed:") for i in pos["id"])
    assert len(neg) == 10 * len(pos)
    assert set(neg["id"]).isdisjoint(set(pos["id"]))


def test_build_labelled_table_rejects_bad_year_window() -> None:
    flat = _flat(
        [
            {
                "id": "session-1-num-1-resolution-1",
                "date": "1780-01-01",
                "year": 1780,
                "resolutions_text": "x",
            }
        ]
    )
    with pytest.raises(ValueError, match="year_min"):
        build_labelled_table(flat, [], year_min=1790, year_max=1780, exclude_ids=[])
