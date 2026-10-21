"""Unit tests for STEPT1p clause chains (no parquet / ES / gold)."""

from __future__ import annotations

import pandas as pd

from formulation.clause_chain import (
    CLAUSE_SESSIE,
    CLAUSE_WELKOM,
    bag_of,
    build_chain_frame,
    chain_of,
    detect_clauses,
    fixture_clause_specs,
    fixture_year_frame,
    summarize_clause_chains,
)


def test_detect_clauses_returns_row_per_clause_present_or_not():
    specs = fixture_clause_specs()
    hits = detect_clauses("Goedgevonden ende verstaen dat men zal", specs)
    assert {h["clause_id"] for h in hits} == {CLAUSE_WELKOM, CLAUSE_SESSIE}
    # Absence is explicit, not a missing row.
    assert all("present" in h for h in hits)
    assert all(h["n_tokens"] > 0 for h in hits)


def test_welkom_and_sessie_are_separate_nodes_with_own_spans():
    specs = fixture_clause_specs()
    text = "is den selven verwelkomt, ende heeft sessie genomen"
    hits = {h["clause_id"]: h for h in detect_clauses(text, specs)}
    assert hits[CLAUSE_WELKOM]["present"]
    assert hits[CLAUSE_SESSIE]["present"]
    # The point of decollapsing: the two clauses carry distinct spans, which
    # appointment_formula_type.score_text discards via max().
    assert (
        hits[CLAUSE_WELKOM]["start_idx"] != hits[CLAUSE_SESSIE]["start_idx"]
        or hits[CLAUSE_WELKOM]["end_idx"] != hits[CLAUSE_SESSIE]["end_idx"]
    )


def test_chain_is_ordered_by_span_and_bag_is_not():
    hits = [
        {"clause_id": CLAUSE_SESSIE, "present": True, "start_idx": 9, "end_idx": 12},
        {"clause_id": CLAUSE_WELKOM, "present": True, "start_idx": 2, "end_idx": 5},
    ]
    assert chain_of(hits) == (CLAUSE_WELKOM, CLAUSE_SESSIE)
    assert bag_of(hits) == (CLAUSE_SESSIE, CLAUSE_WELKOM)  # sorted, order-free


def test_chain_excludes_absent_clauses():
    hits = [
        {"clause_id": CLAUSE_WELKOM, "present": False, "start_idx": 0, "end_idx": 1},
        {"clause_id": CLAUSE_SESSIE, "present": True, "start_idx": 4, "end_idx": 6},
    ]
    assert chain_of(hits) == (CLAUSE_SESSIE,)
    assert bag_of(hits) == (CLAUSE_SESSIE,)


def test_order_stability_distinguishes_reversed_chains():
    chains = pd.Series(
        [
            [CLAUSE_WELKOM, CLAUSE_SESSIE],
            [CLAUSE_WELKOM, CLAUSE_SESSIE],
            [CLAUSE_WELKOM, CLAUSE_SESSIE],
            [CLAUSE_SESSIE, CLAUSE_WELKOM],
        ]
    )
    from formulation.clause_chain import _order_stability

    out = _order_stability(chains, min_support=2)
    assert out["n_multiclause_sets"] == 1
    row = out["sets"][0]
    assert row["support"] == 4
    assert row["n_distinct_orders"] == 2
    assert row["dominant_order"] == [CLAUSE_WELKOM, CLAUSE_SESSIE]
    assert row["dominant_order_frac"] == 0.75
    assert out["support_weighted_dominant_order_frac"] == 0.75


def test_collapse_counts_bag_hidden_structure():
    from formulation.clause_chain import _collapse

    frame = pd.DataFrame(
        [
            {"chain": [CLAUSE_WELKOM, CLAUSE_SESSIE], "bag": [CLAUSE_SESSIE, CLAUSE_WELKOM]},
            {"chain": [CLAUSE_SESSIE, CLAUSE_WELKOM], "bag": [CLAUSE_SESSIE, CLAUSE_WELKOM]},
            {"chain": [CLAUSE_SESSIE], "bag": [CLAUSE_SESSIE]},
        ]
    )
    out = _collapse(frame)
    assert out["n_distinct_bags"] == 2
    assert out["n_distinct_chains"] == 3
    assert out["n_multi_chain_bags"] == 1
    # Two of three resolutions sit in the bag that hides an order difference.
    assert out["n_resolutions_in_multi_chain_bag"] == 2
    assert out["frac_resolutions_in_multi_chain_bag"] == 0.6667


def test_summarize_runs_on_fixture_and_reports_gates():
    specs = fixture_clause_specs()
    frame = fixture_year_frame()
    chain_frame, hit_frame = build_chain_frame(frame, specs, progress_every=0)
    metrics = summarize_clause_chains(
        chain_frame, hit_frame, year=1780, clause_specs=specs, min_support=1
    )
    assert metrics["step"] == "STEPT1p"
    assert metrics["form_only"] is True
    assert metrics["content_markers_used"] == []
    assert metrics["n_resolutions"] == len(frame)
    assert {c["clause_id"] for c in metrics["clauses"]} == {
        CLAUSE_WELKOM,
        CLAUSE_SESSIE,
    }
    assert "g2_order_stability_ge_0_80" in metrics["gates"]
    assert metrics["independence"]["computed"] is True


def test_decollapse_groups_cover_every_resolution():
    specs = fixture_clause_specs()
    frame = fixture_year_frame()
    chain_frame, hit_frame = build_chain_frame(frame, specs, progress_every=0)
    metrics = summarize_clause_chains(
        chain_frame, hit_frame, year=1780, clause_specs=specs, min_support=1
    )
    groups = metrics["appointment_decollapse"]["groups"]
    assert sum(g["n"] for g in groups) == len(frame)
    assert {g["sub_pattern"] for g in groups} <= {
        "both",
        "welkom_only",
        "sessie_only",
        "neither",
    }
