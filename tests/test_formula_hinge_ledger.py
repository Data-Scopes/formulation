"""Unit tests for STEPT1ah hinge archetype seed."""

from __future__ import annotations

from formulation.formula_hinge_ledger import (
    BLUEPRINT_IDS,
    DECISION_POLARITY_POCKET_IDS,
    DECISION_SCAFFOLD_IDS,
    default_seed_rows,
    ledger_metrics,
    load_fixture_rows,
    validate_ledger,
)


def test_default_seed_valid_and_in_band() -> None:
    rows = default_seed_rows()
    assert validate_ledger(rows) == []
    assert 15 <= len(rows) <= 25


def test_fixture_matches_default() -> None:
    fix = load_fixture_rows()
    assert validate_ledger(fix) == []
    assert {r["hinge_id"] for r in fix} == {r["hinge_id"] for r in default_seed_rows()}


def test_no_gedelibereert_and_scaffolds_present() -> None:
    ids = {r["hinge_id"] for r in default_seed_rows()}
    assert not any("gedelibereert" in i for i in ids)
    assert DECISION_SCAFFOLD_IDS <= ids


def test_six_blueprints_linked() -> None:
    linked = {
        r["blueprint_id"]
        for r in default_seed_rows()
        if r["status"] == "from_blueprint"
    }
    assert linked == BLUEPRINT_IDS


def test_pockets_unnamed() -> None:
    pockets = [r for r in default_seed_rows() if r["status"] == "pocket"]
    ids = {r["hinge_id"] for r in pockets}
    assert {"voordracht", "conclusie_handen"} <= ids
    assert DECISION_POLARITY_POCKET_IDS <= ids
    assert all(r["canonic"] is None for r in pockets)


def test_metrics_shape() -> None:
    m = ledger_metrics(default_seed_rows())
    assert m["step"] == "STEPT1ah"
    assert m["n_hinges"] == len(default_seed_rows())
    assert "scaffolding" in m["by_layer"]
    assert "from_blueprint" in m["by_status"]
