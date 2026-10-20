"""Smoke tests for formula_templates registry stub."""

from __future__ import annotations

import pytest

from formulation.boundary.tfidf_windows import (
    DEFAULT_THRESHOLD,
    OPENING_TEMPLATE_18C,
    TEMPLATE_ID_OPENING,
    default_framing_threshold,
    default_opening_template,
)
from formulation.formula_templates import (
    DEFAULT_FRAMING_ID,
    LOGICAL_NAME,
    get_template,
    load_templates,
    resolve_framing_template,
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


def test_opening_requeste_drives_boundary_defaults():
    opening = get_template(TEMPLATE_ID_OPENING)
    resolved = resolve_framing_template(DEFAULT_FRAMING_ID)
    tid, tokens = default_opening_template()
    assert opening["role"] == "framing"
    assert opening["threshold_frozen"] is True
    assert opening["nlp_start_marker"] is False
    assert opening["outcome_signal"] is False
    assert tid == TEMPLATE_ID_OPENING == DEFAULT_FRAMING_ID
    assert tokens == list(OPENING_TEMPLATE_18C) == resolved["tokens"]
    assert default_framing_threshold() == pytest.approx(DEFAULT_THRESHOLD)
    assert resolved["threshold"] == pytest.approx(0.40)


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


def test_resolve_framing_rejects_empty_tokens():
    rows = load_templates()
    bad = [dict(r) for r in rows]
    for row in bad:
        if row["template_id"] == DEFAULT_FRAMING_ID:
            row["tokens"] = []
            break
    with pytest.raises(ValueError, match="tokens empty"):
        resolve_framing_template(rows=bad)
