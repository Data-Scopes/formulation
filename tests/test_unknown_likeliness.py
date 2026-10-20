"""Unit smoke for STEPT1h unknown-likeliness (no parquet)."""

from __future__ import annotations

from formulation.unknown_likeliness import (
    COVER_AXES,
    fixture_unknown_frame,
    score_unknown,
    summarize_unknown_likeliness,
)


def test_fixture_scores_and_high_unknown_band() -> None:
    frame = fixture_unknown_frame()
    metrics = summarize_unknown_likeliness(frame, year=1780)

    assert metrics["step"] == "STEPT1h"
    assert metrics["cover_axes"] == list(COVER_AXES)
    assert metrics["n_universe"] == 5
    # Two rows with no cover
    assert metrics["n_high_unknown"] == 2
    assert metrics["frac_high_unknown"] == 0.4
    assert "subtypes" not in metrics

    # Covered rows: scores < 1
    covered = frame.loc[~frame["high_unknown"]]
    assert (covered["unknown_score"] < 1.0).all()
    # R1+appointment → 2/4 cover → score 0.5
    r1 = frame.loc[frame["id"].str.endswith("resolution-2")].iloc[0]
    assert r1["n_cover_hits"] == 2
    assert r1["unknown_score"] == 0.5


def test_score_unknown_requires_axes() -> None:
    import pandas as pd
    import pytest

    with pytest.raises(ValueError, match="Missing cover axes"):
        score_unknown(pd.DataFrame({"id": ["a"]}))


def test_cover_axis_fracts_in_metrics() -> None:
    frame = fixture_unknown_frame()
    metrics = summarize_unknown_likeliness(frame, year=1780)
    assert metrics["cover"]["cover_l1"]["n"] == 1
    assert metrics["cover"]["cover_r1"]["n"] == 1
    assert metrics["cover"]["cover_appointment"]["n"] == 1
    assert metrics["cover"]["cover_advies"]["n"] == 1
    assert "1.00" in metrics["unknown_score_hist"]
