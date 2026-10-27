"""Unit tests for STEPT1ai hinge witness adjudication."""

from __future__ import annotations

from formulation.formula_hinge_ledger import default_seed_rows
from formulation.formula_hinge_witness import (
    ADJUDICATION_COLUMNS,
    BANDS,
    MID_CUT,
    NEAR_CUT,
    adjudicate_witnesses,
    adjudication_metrics,
    band_for_sim,
    hinge_targets,
    load_witness_fixture,
    witnesses_from_families,
)


def test_hinge_targets_exclude_pockets() -> None:
    hinges = default_seed_rows()
    targets = hinge_targets(hinges)
    ids = {t["hinge_id"] for t in targets}
    assert "voordracht" not in ids
    assert "decision_positive" not in ids
    assert "goedgevonden" in ids
    assert "requeste" in ids
    assert all(t["canonic"] for t in targets)
    assert len(targets) == sum(1 for h in hinges if h.get("canonic"))


def test_band_cuts() -> None:
    assert band_for_sim(0.90) == "near"
    assert band_for_sim(NEAR_CUT) == "near"
    assert band_for_sim(0.65) == "mid"
    assert band_for_sim(MID_CUT) == "mid"
    assert band_for_sim(0.49) == "far"
    assert band_for_sim(0.49, near_cut=0.9, mid_cut=0.4) == "mid"


def test_fixture_adjudication_shape_and_gates() -> None:
    hinges = default_seed_rows()
    witnesses = load_witness_fixture()
    rows = adjudicate_witnesses(hinges, witnesses)
    assert len(rows) == len(witnesses)
    for r in rows:
        assert set(ADJUDICATION_COLUMNS) <= set(r.keys())
        assert r["band"] in BANDS
        assert r["best_hinge_id"]
        assert isinstance(r["best_sim"], float)
        assert r["human_keep"] is None
        assert r["human_note"] is None

    targets = hinge_targets(hinges)
    m = adjudication_metrics(rows, n_hinge_targets=len(targets))
    assert m["step"] == "STEPT1ai"
    assert m["n_witnesses"] == len(rows)
    assert m["n_hinge_targets"] == len(targets)
    assert sum(m["by_band"].values()) == len(rows)
    assert m["near_cut"] == NEAR_CUT
    assert m["mid_cut"] == MID_CUT
    assert m["vectorizer"]["analyzer"] == "char_wb"
    assert m["vectorizer"]["ngram_range"] == [3, 5]


def test_near_exact_canonic_hits_expected_hinge() -> None:
    hinges = default_seed_rows()
    witnesses = [
        {
            "witness_id": "exact_geen",
            "witness_text": "geen resolutie",
            "witness_norm": "geen resolutie",
            "phrase_freq": 1,
            "source": "test",
        },
        {
            "witness_id": "exact_requeste",
            "witness_text": "Requeste",
            "witness_norm": "requeste",
            "phrase_freq": 1,
            "source": "test",
        },
    ]
    rows = adjudicate_witnesses(hinges, witnesses)
    by_id = {r["witness_id"]: r for r in rows}
    assert by_id["exact_geen"]["best_hinge_id"] == "geen_resolutie"
    assert by_id["exact_geen"]["band"] == "near"
    assert by_id["exact_requeste"]["best_hinge_id"] == "requeste"
    assert by_id["exact_requeste"]["band"] == "near"


def test_far_person_string_not_near() -> None:
    hinges = default_seed_rows()
    witnesses = [
        {
            "witness_id": "person",
            "witness_text": "Johan de Witt tot den Briel",
            "witness_norm": "johan de witt tot den briel",
            "phrase_freq": 1,
            "source": "test",
        }
    ]
    rows = adjudicate_witnesses(hinges, witnesses)
    assert rows[0]["band"] == "far"
    assert rows[0]["best_sim"] < MID_CUT


def test_witnesses_from_families_maps_exemplar() -> None:
    fams = [
        {
            "family_id": "f_001",
            "exemplar": "in handen van",
            "exemplar_norm": "in handen van",
            "phrase_freq_max": 9,
        },
        {"family_id": "f_empty", "exemplar": None},
    ]
    wits = witnesses_from_families(fams)
    assert len(wits) == 1
    assert wits[0]["witness_id"] == "f_001"
    assert wits[0]["phrase_freq"] == 9
    assert wits[0]["source"] == "formula_family_candidates"


def test_does_not_invent_hinges() -> None:
    hinges = default_seed_rows()
    before = {h["hinge_id"] for h in hinges}
    witnesses = load_witness_fixture()
    rows = adjudicate_witnesses(hinges, witnesses)
    after = {h["hinge_id"] for h in hinges}
    assert before == after
    target_ids = {t["hinge_id"] for t in hinge_targets(hinges)}
    for r in rows:
        assert r["best_hinge_id"] in target_ids
