"""Unit smoke for STEPT1c position / zone scoring (no parquet)."""

from __future__ import annotations

from formulation.advies_formula_type import FORMULA_TYPE_ID as ADVIES_ID
from formulation.appointment_formula_type import FORMULA_TYPE_ID as APPOINTMENT_ID
from formulation.formula_type_position import (
    fixture_position_frames,
    fixture_position_models,
    score_position_frame,
    summarize_position,
    zone_from_span,
)


def test_zone_from_span_tertiles():
    assert zone_from_span(0, 2, 30) == "opening"
    assert zone_from_span(14, 16, 30) == "body"
    assert zone_from_span(28, 30, 30) == "close"
    assert zone_from_span(0, 0, 0) == "unknown"


def test_fixture_position_zones():
    frame = fixture_position_frames()
    models = fixture_position_models()
    scores = score_position_frame(frame, models)
    assert "zone" in scores.columns
    assert "mid_norm" in scores.columns
    assert "start_idx" in scores.columns

    ont = scores.loc[
        (scores["formula_type_id"] == "ontfangen_start") & scores["present"]
    ]
    assert len(ont) >= 1
    assert set(ont["zone"].dropna()) <= {"opening", "body", "close"}
    assert (ont["zone"] == "opening").all()

    adv = scores.loc[
        (scores["formula_type_id"] == ADVIES_ID) & scores["present"]
    ]
    assert len(adv) >= 1
    assert (adv["zone"] == "opening").all()

    appt = scores.loc[
        (scores["formula_type_id"] == APPOINTMENT_ID) & scores["present"]
    ]
    assert len(appt) >= 1
    assert (appt["zone"] != "opening").all()


def test_fixture_position_summary():
    frame = fixture_position_frames()
    models = fixture_position_models()
    scores = score_position_frame(frame, models)
    metrics = summarize_position(
        scores, year=1780, models=models, random_state=0, limit=None
    )
    assert metrics["step"] == "STEPT1c"
    assert metrics["advies_accepted"] is True
    assert "zone_cuts" in metrics
    bags = metrics["bags"]
    assert "top_zone_patterns" in bags
    appt_type = next(
        t for t in metrics["types"] if t["formula_type_id"] == APPOINTMENT_ID
    )
    assert appt_type["expected_zone"] == "close"
    assert appt_type["zone"]["n"] >= 1
    adv_type = next(t for t in metrics["types"] if t["formula_type_id"] == ADVIES_ID)
    assert adv_type["expected_zone"] == "opening"
    assert adv_type["zone"]["n"] >= 1
