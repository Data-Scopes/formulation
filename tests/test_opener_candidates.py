"""Unit tests for STEPT1y opener_candidates queue + driver (no parquet / ES)."""

from __future__ import annotations

import copy

import pytest

from formulation.opener_candidates import (
    AUDIT_EVIDENCE,
    OpenerCandidatesError,
    active_candidates,
    load_fixture_candidates,
    merge_candidates,
    name_candidate,
    phase_measure,
    phase_propose_promote,
    phase_wire,
    set_a_verdict,
    set_promote_verdict,
    validate_rows,
)


def test_fixture_seed_has_six_blueprints_and_two_pockets() -> None:
    rows = load_fixture_candidates()
    validate_rows(rows)
    by_status: dict[str, list[str]] = {}
    for row in rows:
        by_status.setdefault(row["status"], []).append(row["candidate_id"])
    assert set(by_status["blueprint"]) == set(AUDIT_EVIDENCE)
    assert len(by_status["blueprint"]) == 6
    assert set(by_status["pocket"]) == {"voordracht", "conclusie_handen"}
    for cid in by_status["pocket"]:
        row = next(r for r in rows if r["candidate_id"] == cid)
        assert row["canonic"] in (None, "")
        assert row["n_empty_support"] in (80, 41)


def test_measure_refuses_pocket() -> None:
    rows = load_fixture_candidates()
    with pytest.raises(OpenerCandidatesError, match="pocket"):
        phase_measure(rows, "voordracht")


def test_measure_refuses_unknown_adapter() -> None:
    rows = load_fixture_candidates()
    named = name_candidate(
        rows,
        "voordracht",
        canonic="DE Heer praesideerende heeft voorgedragen",
        es_proposition_type="voordracht",
    )
    with pytest.raises(OpenerCandidatesError, match="no measure adapter"):
        phase_measure(named, "voordracht")


def test_measure_audit_writeback_on_blueprint() -> None:
    rows = load_fixture_candidates()
    out = phase_measure(rows, "rapport_gehoord", fixture_only=True)
    row = next(r for r in out if r["candidate_id"] == "rapport_gehoord")
    assert row["status"] == "blueprint"
    assert row["recall"] == 0.895
    assert row["fp_rate"] == 0.006
    assert row["operating_cut"] == 7.5
    assert row["measured_at"]
    # driver must not invent verdicts
    assert row["a_verdict"] == "accept"  # pre-seeded audit; unchanged
    assert row["promote_verdict"] == "accept"


def test_measure_named_to_measured_does_not_set_verdict() -> None:
    rows = load_fixture_candidates()
    # clone rapport as a named row for transition test
    base = next(r for r in rows if r["candidate_id"] == "rapport_gehoord")
    trial = copy.deepcopy(base)
    trial["candidate_id"] = "rapport_gehoord_trial"
    trial["status"] = "named"
    trial["a_verdict"] = None
    trial["promote_verdict"] = None
    trial["measured_at"] = None
    rows2 = rows + [trial]
    # adapter keyed by id — trial has no adapter
    with pytest.raises(OpenerCandidatesError, match="no measure adapter"):
        phase_measure(rows2, "rapport_gehoord_trial")

    # use real id but force named status on a copy of the queue
    rows3 = copy.deepcopy(rows)
    row = next(r for r in rows3 if r["candidate_id"] == "rapport_gehoord")
    row["status"] = "named"
    row["a_verdict"] = None
    row["promote_verdict"] = None
    out = phase_measure(rows3, "rapport_gehoord")
    row_out = next(r for r in out if r["candidate_id"] == "rapport_gehoord")
    assert row_out["status"] == "measured"
    assert row_out["a_verdict"] in (None, "")
    assert row_out["recall"] == 0.895


def test_wire_refuses_without_a_accept() -> None:
    rows = load_fixture_candidates()
    rows = copy.deepcopy(rows)
    row = next(r for r in rows if r["candidate_id"] == "rapport_gehoord")
    row["status"] = "measured"
    row["a_verdict"] = None
    with pytest.raises(OpenerCandidatesError, match="wire requires"):
        phase_wire(rows, "rapport_gehoord")


def test_human_a_then_wire() -> None:
    rows = load_fixture_candidates()
    rows = copy.deepcopy(rows)
    row = next(r for r in rows if r["candidate_id"] == "rapport_gehoord")
    row["status"] = "measured"
    row["a_verdict"] = None
    row["promote_verdict"] = None
    rows = set_a_verdict(rows, "rapport_gehoord", "accept")
    assert next(r for r in rows if r["candidate_id"] == "rapport_gehoord")["status"] == (
        "accepted_a"
    )
    out = phase_wire(rows, "rapport_gehoord")
    row_out = next(r for r in out if r["candidate_id"] == "rapport_gehoord")
    assert row_out["status"] == "wired"
    assert row_out["n_present"] == 63
    assert row_out["empty_delta"] == -0.015
    assert row_out["wired_at"]


def test_propose_promote_refuses_apply_without_verdict() -> None:
    rows = load_fixture_candidates()
    rows = copy.deepcopy(rows)
    row = next(r for r in rows if r["candidate_id"] == "rapport_gehoord")
    row["status"] = "wired"
    row["promote_verdict"] = None
    with pytest.raises(OpenerCandidatesError, match="promote_verdict=accept"):
        phase_propose_promote(rows, "rapport_gehoord", apply_promote=True)


def test_propose_promote_default_does_not_advance_status() -> None:
    rows = load_fixture_candidates()
    rows = copy.deepcopy(rows)
    row = next(r for r in rows if r["candidate_id"] == "rapport_gehoord")
    row["status"] = "wired"
    row["promote_verdict"] = None
    out = phase_propose_promote(rows, "rapport_gehoord", apply_promote=False)
    row_out = next(r for r in out if r["candidate_id"] == "rapport_gehoord")
    assert row_out["status"] == "wired"
    assert row_out["proposed_promote_at"]
    assert row_out["promote_verdict"] in (None, "")


def test_propose_promote_apply_with_human_accept() -> None:
    rows = load_fixture_candidates()
    rows = copy.deepcopy(rows)
    row = next(r for r in rows if r["candidate_id"] == "rapport_gehoord")
    row["status"] = "wired"
    row["promote_verdict"] = None
    rows = set_promote_verdict(rows, "rapport_gehoord", "accept")
    out = phase_propose_promote(rows, "rapport_gehoord", apply_promote=True)
    row_out = next(r for r in out if r["candidate_id"] == "rapport_gehoord")
    assert row_out["status"] == "blueprint"


def test_driver_never_sets_verdicts_on_measure_wire() -> None:
    rows = load_fixture_candidates()
    rows = copy.deepcopy(rows)
    row = next(r for r in rows if r["candidate_id"] == "advies_geleesen")
    row["status"] = "named"
    row["a_verdict"] = None
    row["promote_verdict"] = None
    measured = phase_measure(rows, "advies_geleesen")
    m = next(r for r in measured if r["candidate_id"] == "advies_geleesen")
    assert m["a_verdict"] in (None, "")
    assert m["promote_verdict"] in (None, "")


def test_merge_pockets_accumulates_surfaces() -> None:
    rows = load_fixture_candidates()
    out = merge_candidates(
        rows,
        into_id="voordracht",
        from_ids=["conclusie_handen"],
        canonic="heeft voorgedragen",
    )
    survivor = next(r for r in out if r["candidate_id"] == "voordracht")
    absorbed = next(r for r in out if r["candidate_id"] == "conclusie_handen")
    assert survivor["status"] == "named"
    assert survivor["canonic"] == "heeft voorgedragen"
    assert "conclusie_handen" in survivor["merged_from"]
    assert survivor["n_empty_support"] == 80 + 41
    assert absorbed["status"] == "merged"
    assert absorbed["merged_into"] == "voordracht"
    active_ids = {r["candidate_id"] for r in active_candidates(out)}
    assert "voordracht" in active_ids
    assert "conclusie_handen" not in active_ids


def test_merge_refuses_blueprint() -> None:
    rows = load_fixture_candidates()
    with pytest.raises(OpenerCandidatesError, match="blueprint"):
        merge_candidates(
            rows, into_id="rapport_gehoord", from_ids=["voordracht"]
        )
    with pytest.raises(OpenerCandidatesError, match="blueprint"):
        merge_candidates(
            rows, into_id="voordracht", from_ids=["rapport_gehoord"]
        )


def test_measure_refuses_merged_away() -> None:
    rows = load_fixture_candidates()
    out = merge_candidates(
        rows, into_id="voordracht", from_ids=["conclusie_handen"]
    )
    with pytest.raises(OpenerCandidatesError, match="merged into"):
        phase_measure(out, "conclusie_handen")
