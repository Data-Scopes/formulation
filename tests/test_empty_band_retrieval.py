"""Unit smoke for STEPT1j2 empty-band R1/L1 retrieval probe (no parquet)."""

from __future__ import annotations

from formulation.aanstelling_harvest import BUCKET_GREY, BUCKET_HIGH, BUCKET_LOW
from formulation.empty_band_retrieval import (
    fixture_retrieval_frame,
    summarize_empty_retrieval,
)


def test_fixture_summarize_separates_l1_high_missive() -> None:
    frame = fixture_retrieval_frame()
    metrics = summarize_empty_retrieval(frame, year=1780)
    assert metrics["step"] == "STEPT1j2"
    assert metrics["n_empty"] == 6
    assert metrics["l1"]["n_high"] == 2
    assert metrics["r1"]["n_low"] >= 4
    high_types = {r["proposition_type"] for r in metrics["l1_high_type_mix"]}
    assert "missive" in high_types


def test_fixture_by_type_has_rekest_and_missive() -> None:
    frame = fixture_retrieval_frame()
    metrics = summarize_empty_retrieval(frame, year=1780)
    l1_types = {r["proposition_type"] for r in metrics["l1_by_proposition_type"]}
    assert "rekest" in l1_types
    assert "missive" in l1_types
    missive = next(
        r for r in metrics["l1_by_proposition_type"] if r["proposition_type"] == "missive"
    )
    assert missive["frac_high"] > 0.5


def test_fixture_buckets_use_r1_cuts() -> None:
    frame = fixture_retrieval_frame()
    assert set(frame["bucket_l1"]) <= {BUCKET_HIGH, BUCKET_GREY, BUCKET_LOW}
