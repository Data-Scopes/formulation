"""Unit tests for STEPT1z probabilistic sequence matrix (no parquet)."""

from __future__ import annotations

import math

from formulation.formula_sequence_matrix import (
    EMPTY_ID,
    END_ID,
    PICK_RULE,
    build_archetypal_examples,
    build_probabilistic_matrix,
    fixture_matrix,
    fixture_sequences,
    fixture_texts_by_id,
    harvest_catalog,
    node_meta_catalog,
)
from formulation.missive_formula_type import FORMULA_TYPE_ID as MISSIVE_ID


def test_fixture_rows_sum_to_one() -> None:
    matrix = fixture_matrix()
    assert matrix["primary"] == "p_adjacent_row_stochastic"
    assert matrix["row_sum_ok"] is True
    assert END_ID in matrix["columns"]
    n_from_map = {n["formula_id"]: int(n["n_from"]) for n in matrix["nodes"]}
    for from_id, dist in matrix["P_adjacent"].items():
        if n_from_map.get(from_id, 0) <= 0:
            continue
        assert math.isclose(sum(dist.values()), 1.0, abs_tol=1e-4), from_id


def test_fixture_has_blueprints_harvest_sentinels() -> None:
    matrix = fixture_matrix()
    ids = {n["formula_id"] for n in matrix["nodes"]}
    assert MISSIVE_ID in ids
    assert EMPTY_ID in ids
    assert END_ID in ids
    assert any(n["role"] == "harvest" for n in matrix["nodes"])
    harvest = harvest_catalog()
    pockets = {h["formula_id"] for h in harvest if h.get("pocket")}
    assert "harvest_voordracht_voorgedragen" in pockets
    assert "harvest_conclusie_handen" in pockets


def test_missive_transition_probs() -> None:
    matrix = fixture_matrix()
    dist = matrix["P_adjacent"][MISSIVE_ID]
    # 2× missive→goedgevonden, 1× missive→END → P=2/3, 1/3
    assert math.isclose(dist["harvest_scheme_goedgevonden"], 2 / 3, abs_tol=1e-5)
    assert math.isclose(dist[END_ID], 1 / 3, abs_tol=1e-5)
    n = matrix["N_adjacent"][MISSIVE_ID]
    assert n["harvest_scheme_goedgevonden"] == 2
    assert n[END_ID] == 1


def test_empty_goes_to_end() -> None:
    matrix = fixture_matrix()
    dist = matrix["P_adjacent"][EMPTY_ID]
    assert math.isclose(dist[END_ID], 1.0, abs_tol=1e-5)


def test_companion_n_on_edges() -> None:
    matrix = fixture_matrix()
    positive = [e for e in matrix["edges"] if e["n_adjacent"] > 0]
    assert positive
    for e in positive:
        assert e["n_from"] >= e["n_adjacent"]
        assert 0.0 <= float(e["p_adjacent"]) <= 1.0 + 1e-6


def test_build_from_fixture_sequences_roundtrip() -> None:
    seqs = fixture_sequences()
    harvest = harvest_catalog()
    meta = node_meta_catalog(harvest)
    m = build_probabilistic_matrix(seqs, node_meta=meta, year=1780)
    assert m["n_resolutions"] == len(seqs)
    assert m["n_empty"] == 1


def test_archetypal_node_examples_shortest_first() -> None:
    matrix = fixture_matrix()
    seqs = fixture_sequences()
    texts = fixture_texts_by_id()
    nodes, edges = build_archetypal_examples(
        seqs, texts, matrix, per_node=3, min_edge_n=1
    )
    assert nodes
    assert all(r["pick_rule"] == PICK_RULE for r in nodes)
    missive = [r for r in nodes if r["formula_id"] == MISSIVE_ID]
    assert len(missive) == 3  # f8, f1/f2 — three missive seqs
    # shortest among f1/f2/f8 should rank first
    assert missive[0]["example_rank"] == 1
    assert missive[0]["n_tokens"] <= missive[-1]["n_tokens"]
    assert missive[0]["text_trunc"]
    empty = [r for r in nodes if r["formula_id"] == EMPTY_ID]
    assert empty and empty[0]["id"] == "f4"
    # edge examples with min_n=1 include missive→goedgevonden
    assert any(
        e["from_id"] == MISSIVE_ID and "goedgevonden" in e["to_id"] for e in edges
    )
