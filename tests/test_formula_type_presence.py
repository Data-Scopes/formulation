"""Unit smoke for STEPT1b presence scoring (no parquet)."""

from __future__ import annotations

from formulation.advies_formula_type import FORMULA_TYPE_ID as ADVIES_ID
from formulation.appointment_formula_type import FORMULA_TYPE_ID as APPOINTMENT_ID
from formulation.appointment_formula_type import apply_popularity, popularity_weight
from formulation.formula_type_presence import (
    fixture_presence_frames,
    fixture_presence_models,
    score_presence_frame,
    summarize_presence,
)
from formulation.rapport_formula_type import FORMULA_TYPE_ID as RAPPORT_ID
from formulation.requeste_formula_type import FORMULA_TYPE_ID as REQUESTE_ID
from formulation.requeste_op_de_formula_type import (
    FORMULA_TYPE_ID as REQUESTE_OP_DE_ID,
)


def test_fixture_presence_scores_and_weights():
    frame = fixture_presence_frames()
    models = fixture_presence_models()
    scores = score_presence_frame(frame, models)
    assert set(scores["formula_type_id"]) >= {
        APPOINTMENT_ID,
        ADVIES_ID,
        REQUESTE_ID,
        REQUESTE_OP_DE_ID,
        RAPPORT_ID,
        "ontfangen_start",
    }
    assert "score_weighted" in scores.columns
    assert "present" in scores.columns
    # Same raw score gets higher weight when rarer.
    appt = scores.loc[scores["formula_type_id"] == APPOINTMENT_ID]
    rate = float(appt["corpus_rate"].iloc[0])
    w = popularity_weight(rate)
    assert abs(float(appt["popularity_weight"].iloc[0]) - w) < 1e-3
    assert abs(
        float(appt["score_weighted"].iloc[0])
        - apply_popularity(float(appt["score"].iloc[0]), rate)
    ) < 1e-2


def test_fixture_bags_summary():
    frame = fixture_presence_frames()
    models = fixture_presence_models()
    scores = score_presence_frame(frame, models)
    metrics = summarize_presence(
        scores, year=1780, models=models, random_state=0, limit=None
    )
    assert metrics["n_resolutions"] == 7
    assert metrics["appointment_accepted"] is True
    assert metrics["advies_accepted"] is True
    assert metrics["requeste_accepted"] is True
    assert metrics["requeste_op_de_accepted"] is True
    assert metrics["rapport_accepted"] is True
    assert metrics["openings_provisional"] is True
    bags = metrics["bags"]
    assert bags["frac_zero"] is not None
    assert "size_histogram" in bags
    type_ids = {t["formula_type_id"] for t in metrics["types"]}
    assert APPOINTMENT_ID in type_ids
    assert ADVIES_ID in type_ids
    assert REQUESTE_ID in type_ids
    assert REQUESTE_OP_DE_ID in type_ids
    assert RAPPORT_ID in type_ids
    # Appointment / advies / requeste / rapport fixture positives under cut=2.0.
    appt_type = next(t for t in metrics["types"] if t["formula_type_id"] == APPOINTMENT_ID)
    assert appt_type["n_present"] >= 1
    adv_type = next(t for t in metrics["types"] if t["formula_type_id"] == ADVIES_ID)
    assert adv_type["n_present"] >= 1
    req_type = next(t for t in metrics["types"] if t["formula_type_id"] == REQUESTE_ID)
    assert req_type["n_present"] >= 1
    req_op = next(t for t in metrics["types"] if t["formula_type_id"] == REQUESTE_OP_DE_ID)
    assert req_op["n_present"] >= 1
    rap = next(t for t in metrics["types"] if t["formula_type_id"] == RAPPORT_ID)
    assert rap["n_present"] >= 1
