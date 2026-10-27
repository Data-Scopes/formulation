"""Unit tests for STEPT1aj near+mid hinge-witness skim."""

from __future__ import annotations

import pytest

from formulation.formula_hinge_witness_skim import (
    HUMAN_KEEP_VALUES,
    SKIM_COLUMNS,
    filter_near_mid,
    fixture_adjudication_for_skim,
    ingest_skim_xlsx,
    parse_filled_keep,
    skim_metrics,
    skim_rows,
    write_skim_xlsx,
)


def test_filter_near_mid_excludes_far() -> None:
    rows = [
        {"band": "near", "witness_id": "a"},
        {"band": "mid", "witness_id": "b"},
        {"band": "far", "witness_id": "c"},
    ]
    out = filter_near_mid(rows)
    assert {r["witness_id"] for r in out} == {"a", "b"}


def test_skim_rows_blank_and_columns() -> None:
    adj = fixture_adjudication_for_skim()
    rows = skim_rows(adj)
    assert rows
    assert all(r["band"] in {"near", "mid"} for r in rows)
    assert all(r["human_keep"] == "" for r in rows)
    assert all(r["human_note"] == "" for r in rows)
    assert set(SKIM_COLUMNS) <= set(rows[0].keys())
    # near before mid
    bands = [r["band"] for r in rows]
    if "near" in bands and "mid" in bands:
        assert bands.index("near") < bands.index("mid") or bands.count("near") == len(
            bands
        )


def test_skim_metrics_sum() -> None:
    adj = fixture_adjudication_for_skim()
    skim = skim_rows(adj)
    m = skim_metrics(adj, skim)
    assert m["step"] == "STEPT1aj"
    assert m["n_skim"] == len(skim)
    assert sum(m["by_band_skim"].values()) == len(skim)
    assert m["by_band_adjudication"]["far"] + m["n_skim"] == m["n_adjudication"]


def test_write_and_ingest_roundtrip(tmp_path) -> None:
    adj = fixture_adjudication_for_skim()
    path = write_skim_xlsx(tmp_path / "skim.xlsx", adj, metrics={"n": 1})
    assert path.exists()

    # blank emit → ingest yields zero judged
    judged, summary = ingest_skim_xlsx(path)
    assert judged == []
    assert summary["n_judged"] == 0

    # fill two rows
    import pandas as pd

    book = pd.read_excel(path, sheet_name="near_mid")
    assert len(book) >= 1
    book["human_keep"] = book["human_keep"].astype(object)
    book["human_note"] = book["human_note"].astype(object)
    book.loc[0, "human_keep"] = "variant"
    book.loc[0, "human_note"] = "ok"
    if len(book) > 1:
        book.loc[1, "human_keep"] = "composition"
        book.loc[1, "human_note"] = "goedgevonden + refer"
    with pd.ExcelWriter(path, engine="openpyxl") as writer:
        book.to_excel(writer, sheet_name="near_mid", index=False)
        pd.DataFrame([{"field": "human_keep"}]).to_excel(
            writer, sheet_name="guide", index=False
        )

    judged, summary = ingest_skim_xlsx(path)
    assert summary["n_judged"] >= 1
    assert judged[0]["human_keep"] == "variant"
    assert set(summary["by_human_keep"]) == HUMAN_KEEP_VALUES


def test_parse_filled_keep_rejects_unknown() -> None:
    assert parse_filled_keep("") is None
    assert parse_filled_keep("Variant") == "variant"
    with pytest.raises(ValueError, match="Unrecognised"):
        parse_filled_keep("mint")
