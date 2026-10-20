"""Unit smoke for STEPT1d composition graph (no parquet)."""

from __future__ import annotations

import pandas as pd

from formulation.advies_formula_type import FORMULA_TYPE_ID as ADVIES_ID
from formulation.appointment_formula_type import FORMULA_TYPE_ID as APPOINTMENT_ID
from formulation.formula_type_composition_graph import (
    COMPOSITION_ROOT,
    build_composition_graph,
    classify_graph_shape,
    fixture_composition_frames,
    fixture_composition_models,
    score_composition_frame,
    shape_over_time,
    summarize_composition_graph,
)


def _synthetic_scores() -> tuple[pd.DataFrame, list[dict]]:
    """Two ids: root→appt star; one id with accepted↔accepted."""
    models = [
        {
            "formula_type_id": COMPOSITION_ROOT,
            "role": "opening",
            "provisional": True,
        },
        {
            "formula_type_id": APPOINTMENT_ID,
            "role": "appointment",
            "provisional": False,
        },
        {
            "formula_type_id": ADVIES_ID,
            "role": "advies",
            "provisional": False,
        },
    ]
    rows = [
        # id-a: ontfangen (opening) + appointment (close) → star spoke
        {
            "id": "a",
            "year": 1780,
            "formula_type_id": COMPOSITION_ROOT,
            "role": "opening",
            "provisional": True,
            "present": True,
            "score": 5.0,
            "operating_cut": 2.0,
            "start_idx": 0,
            "end_idx": 4,
            "n_tokens": 100,
            "mid_norm": 0.02,
            "zone": "opening",
        },
        {
            "id": "a",
            "year": 1780,
            "formula_type_id": APPOINTMENT_ID,
            "role": "appointment",
            "provisional": False,
            "present": True,
            "score": 6.0,
            "operating_cut": 2.0,
            "start_idx": 80,
            "end_idx": 90,
            "n_tokens": 100,
            "mid_norm": 0.85,
            "zone": "close",
        },
        {
            "id": "a",
            "year": 1780,
            "formula_type_id": ADVIES_ID,
            "role": "advies",
            "provisional": False,
            "present": False,
            "score": 0.0,
            "operating_cut": 2.0,
            "start_idx": 0,
            "end_idx": 0,
            "n_tokens": 100,
            "mid_norm": None,
            "zone": None,
        },
        # id-b: advies (opening) + appointment (close) → accepted co-presence
        {
            "id": "b",
            "year": 1780,
            "formula_type_id": COMPOSITION_ROOT,
            "role": "opening",
            "provisional": True,
            "present": False,
            "score": 0.0,
            "operating_cut": 2.0,
            "start_idx": 0,
            "end_idx": 0,
            "n_tokens": 100,
            "mid_norm": None,
            "zone": None,
        },
        {
            "id": "b",
            "year": 1780,
            "formula_type_id": ADVIES_ID,
            "role": "advies",
            "provisional": False,
            "present": True,
            "score": 5.0,
            "operating_cut": 2.0,
            "start_idx": 5,
            "end_idx": 15,
            "n_tokens": 100,
            "mid_norm": 0.10,
            "zone": "opening",
        },
        {
            "id": "b",
            "year": 1780,
            "formula_type_id": APPOINTMENT_ID,
            "role": "appointment",
            "provisional": False,
            "present": True,
            "score": 6.0,
            "operating_cut": 2.0,
            "start_idx": 70,
            "end_idx": 85,
            "n_tokens": 100,
            "mid_norm": 0.78,
            "zone": "close",
        },
    ]
    return pd.DataFrame(rows), models


def test_classify_graph_shape_labels():
    star_nodes = [
        {"formula_type_id": COMPOSITION_ROOT, "role": "root"},
        {"formula_type_id": APPOINTMENT_ID, "role": "accepted"},
    ]
    star_arcs = [
        {
            "from": COMPOSITION_ROOT,
            "to": APPOINTMENT_ID,
            "n": 3,
            "both_accepted": False,
        }
    ]
    assert classify_graph_shape(star_nodes, star_arcs) == "provisional_root_star"
    acc_arcs = [
        {
            "from": ADVIES_ID,
            "to": APPOINTMENT_ID,
            "n": 1,
            "both_accepted": True,
        }
    ]
    assert classify_graph_shape([], acc_arcs) == "accepted_co_presence"
    assert classify_graph_shape([], []) == "empty"


def test_synthetic_graph_has_accepted_edge():
    scores, models = _synthetic_scores()
    graph = build_composition_graph(scores, models)
    assert graph["n_accepted_accepted_edges"] >= 1
    assert graph["graph_shape"] == "accepted_co_presence"
    roles = {n["formula_type_id"]: n["role"] for n in graph["nodes"]}
    assert roles[COMPOSITION_ROOT] == "root"
    assert roles[APPOINTMENT_ID] == "accepted"
    # Root→appt spoke still counted among arcs.
    assert any(
        e["from"] == COMPOSITION_ROOT and e["to"] == APPOINTMENT_ID
        for e in graph["arcs"]
    )
    aa = next(
        e
        for e in graph["arcs"]
        if e["from"] == ADVIES_ID and e["to"] == APPOINTMENT_ID
    )
    assert aa["both_accepted"] is True
    assert aa["zone_arc"] == "opening->close"
    assert aa["n_weighted"] > 0


def test_star_only_subset():
    scores, models = _synthetic_scores()
    # Drop id-b so only provisional-root star remains.
    scores = scores.loc[scores["id"] == "a"].copy()
    graph = build_composition_graph(scores, models)
    assert graph["n_accepted_accepted_edges"] == 0
    assert graph["graph_shape"] == "provisional_root_star"


def test_fixture_composition_smoke():
    frame = fixture_composition_frames()
    models = fixture_composition_models()
    scores = score_composition_frame(frame, models)
    metrics = summarize_composition_graph(
        scores,
        models,
        year=1780,
        random_state=0,
        limit=None,
    )
    assert metrics["step"] == "STEPT1d"
    assert metrics["method"] == "composition_graph_co_presence"
    assert metrics["composition_root"] == COMPOSITION_ROOT
    assert "nodes" in metrics
    assert "arcs" in metrics
    assert "n_accepted_accepted_edges" in metrics
    assert "graph_shape" in metrics
    # Multi-hit order fixtures produce at least root→accepted spokes.
    assert metrics["n_arcs"] >= 1


def test_shape_over_time():
    matrix = [
        {
            "period_bin": "1750-1774",
            "graph_shape": "provisional_root_star",
            "n_accepted_accepted_edges": 0,
        },
        {
            "period_bin": "1775-1799",
            "graph_shape": "provisional_root_star",
            "n_accepted_accepted_edges": 0,
        },
    ]
    summary = shape_over_time(matrix)
    assert summary["all_star"] is True
    assert summary["any_accepted_co_presence"] is False
    assert summary["max_n_accepted_accepted_edges"] == 0
