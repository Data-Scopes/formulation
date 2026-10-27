"""Unit smoke for STEPT1r part A requeste low-band profile (no parquet / no ES)."""

from __future__ import annotations

from formulation.requeste_low_band_profile import (
    band_of,
    build_low_band_profile,
    fixture_bands,
)


def test_band_of_thresholds() -> None:
    assert band_of(4.5) == "low"
    assert band_of(4.6) == "low"
    assert band_of(6.0) == "mid"
    assert band_of(9.0) == "high"
    assert band_of(None) is None


def test_fixture_profile_shapes() -> None:
    clean, full = fixture_bands()
    metrics = build_low_band_profile(clean, full)

    clean_bands = {b["band"]: b for b in metrics["clean_gold_sample"]["bands"]}
    assert clean_bands["low"]["n"] == 2
    assert clean_bands["high"]["n"] == 1

    full_summary = metrics["full_predicted_population"]
    assert full_summary["n"] == 3
    assert full_summary["lexical_flag_rate_by_band"]["gedelibereert_start"]["low"] == 0.0
    assert full_summary["lexical_flag_rate_by_band"]["gedelibereert_start"]["high"] == 1.0
    assert "part_b_pending" in metrics
    assert metrics["naming_gate"]["auto_mint"] is False
    assert "split_short_form_subtype_after_human_name" in metrics["naming_gate"]["call_options"]
