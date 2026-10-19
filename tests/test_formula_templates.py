"""Smoke tests for formula_templates registry stub."""

from __future__ import annotations

import pytest

from formulation.boundary.tfidf_windows import (
    DEFAULT_THRESHOLD,
    OPENING_TEMPLATE_18C,
    TEMPLATE_ID_OPENING,
)
from formulation.formula_templates import (
    LOGICAL_NAME,
    get_template,
    load_templates,
    templates_by_role,
    validate_template,
)


def test_manifest_load_and_unique_ids():
    rows = load_templates()
    assert len(rows) >= 8
    ids = [r["template_id"] for r in rows]
    assert len(ids) == len(set(ids))
    assert "unknown_residual" in ids
    assert LOGICAL_NAME == "formula_templates"


def test_opening_requeste_matches_steps1b_constants():
    opening = get_template(TEMPLATE_ID_OPENING)
    assert opening["role"] == "framing"
    assert opening["tokens"] == list(OPENING_TEMPLATE_18C)
    assert opening["threshold"] == pytest.approx(DEFAULT_THRESHOLD)
    assert opening["threshold_frozen"] is True
    assert opening["nlp_start_marker"] is False
    assert opening["outcome_signal"] is False


def test_appointment_siblings_use_institution_discriminator():
    verg = get_template("appointment_vergadering")
    rek = get_template("appointment_rekenkamer")
    assert verg["discriminators"] == ["institution"]
    assert rek["discriminators"] == ["institution"]
    assert "rekenkamer" in rek["institution_targets"]
    assert "staten_generael_vergadering" in verg["institution_targets"]


def test_goedgevonden_is_not_outcome_signal():
    row = get_template("goedgevonden_decision_opener")
    assert row["outcome_signal"] is False
    assert row["role"] == "doc_flag"


def test_roles_partition():
    framing = templates_by_role("framing")
    residual = templates_by_role("residual")
    assert any(r["template_id"] == TEMPLATE_ID_OPENING for r in framing)
    assert any(r["template_id"] == "unknown_residual" for r in residual)


def test_validate_rejects_institution_without_targets():
    bad = dict(get_template("appointment_rekenkamer"))
    bad["institution_targets"] = []
    with pytest.raises(ValueError, match="institution_targets"):
        validate_template(bad)
