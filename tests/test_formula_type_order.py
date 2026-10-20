"""Unit smoke for STEPT1d order / composition (no parquet)."""

from __future__ import annotations

from formulation.appointment_formula_type import FORMULA_TYPE_ID as APPOINTMENT_ID
from formulation.formula_type_order import (
    composition_rows,
    expected_order_holds,
    fixture_order_frames,
    fixture_order_models,
    score_order_frame,
    summarize_order,
)


def test_expected_order_holds():
    assert expected_order_holds(
        ["ontfangen_start", APPOINTMENT_ID],
        "ontfangen_start",
        APPOINTMENT_ID,
    ) is True
    assert expected_order_holds(
        [APPOINTMENT_ID, "ontfangen_start"],
        "ontfangen_start",
        APPOINTMENT_ID,
    ) is False
    assert expected_order_holds(
        ["ontfangen_start"],
        "ontfangen_start",
        APPOINTMENT_ID,
    ) is None


def test_fixture_order_sequences():
    frame = fixture_order_frames()
    models = fixture_order_models()
    scores, compositions = score_order_frame(frame, models)
    assert "ordered_types" in compositions.columns
    assert "bag_types" in compositions.columns

    fwd = compositions.loc[compositions["id"] == "fix-order-1"].iloc[0]
    assert fwd["n_present"] >= 2
    types = list(fwd["ordered_types"])
    assert "ontfangen_start" in types
    assert APPOINTMENT_ID in types
    assert types.index("ontfangen_start") < types.index(APPOINTMENT_ID)
    assert fwd["matches_any_expected_order"] is True

    rev = compositions.loc[compositions["id"] == "fix-order-rev"].iloc[0]
    assert rev["n_present"] >= 2
    rtypes = list(rev["ordered_types"])
    assert rtypes.index(APPOINTMENT_ID) < rtypes.index("ontfangen_start")
    assert rev["matches_any_expected_order"] is False

    # Long scores still available for span checks.
    assert "start_idx" in scores.columns
    assert len(composition_rows(scores)) == len(compositions)


def test_fixture_order_summary():
    frame = fixture_order_frames()
    models = fixture_order_models()
    _scores, compositions = score_order_frame(frame, models)
    metrics = summarize_order(
        compositions, year=1780, models=models, random_state=0, limit=None
    )
    assert metrics["step"] == "STEPT1d"
    assert "expected_orders" in metrics
    seq = metrics["sequences"]
    assert "top_ordered" in seq
    assert "order_vs_bag" in seq
    ont_appt = next(
        e
        for e in metrics["expected_orders"]
        if e["earlier"] == "ontfangen_start" and e["later"] == APPOINTMENT_ID
    )
    assert ont_appt["n_both_present"] >= 1
    assert ont_appt["frac_expected_order"] is not None
