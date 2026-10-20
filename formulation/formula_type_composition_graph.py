"""STEPT1d: formula-type composition as a co-presence graph.

Nodes = types (IDF-weighted by in-bin hit rate); arcs = co-presence directed
by mid_norm (earlier → later). Not document-order sequences (parked T1d order).
Not Track S token-span ``align_dag``.
"""

from __future__ import annotations

import math
from collections import Counter, defaultdict
from typing import Any

import pandas as pd
import pyarrow.parquet as pq

from data_io import resolve
from formulation.advies_formula_type import FORMULA_TYPE_ID as ADVIES_ID
from formulation.appointment_formula_type import (
    FORMULA_TYPE_ID as APPOINTMENT_ID,
    YEAR_MAX,
    YEAR_MIN,
    popularity_weight,
)
from formulation.boundary.tfidf_windows import POC_YEAR
from formulation.formula_period_bins import (
    BIN_ORIGIN,
    BIN_WIDTH,
    bin_bounds,
    list_bins_in_range,
    year_bin,
)
from formulation.formula_type_order import (
    fixture_order_frames,
    fixture_order_models,
)
from formulation.formula_type_position import (
    CLOSE_CUT,
    OPENING_CUT,
    score_position_frame,
)

DEFAULT_YEAR = POC_YEAR
COMPOSITION_ROOT = "ontfangen_start"
ACCEPTED_TYPES = frozenset({APPOINTMENT_ID, ADVIES_ID})

__all__ = (
    "ACCEPTED_TYPES",
    "CLOSE_CUT",
    "COMPOSITION_ROOT",
    "DEFAULT_YEAR",
    "OPENING_CUT",
    "build_composition_graph",
    "classify_graph_shape",
    "fixture_composition_frames",
    "fixture_composition_models",
    "load_bin_slice",
    "score_composition_frame",
    "shape_over_time",
    "summarize_composition_graph",
    "summarize_period_matrix",
)


def fixture_composition_frames() -> pd.DataFrame:
    """Reuse order fixtures (multi-hit docs) for graph smoke."""
    return fixture_order_frames()


def fixture_composition_models() -> list[dict[str, Any]]:
    return fixture_order_models()


def score_composition_frame(
    frame: pd.DataFrame,
    models: list[dict[str, Any]],
    *,
    opening_cut: float = OPENING_CUT,
    close_cut: float = CLOSE_CUT,
) -> pd.DataFrame:
    """Long position scores (span + zone) — input to the composition graph."""
    return score_position_frame(
        frame,
        models,
        opening_cut=opening_cut,
        close_cut=close_cut,
    )


def load_bin_slice(
    bin_label: str,
    *,
    limit: int | None = None,
) -> pd.DataFrame:
    """Load ``id`` / ``year`` / ``resolutions_text`` for one 25y period bin."""
    y0, y1 = bin_bounds(bin_label)
    y0 = max(y0, YEAR_MIN)
    y1 = min(y1, YEAR_MAX)
    path = resolve("resolutions_flat")
    frame = pq.read_table(
        path,
        columns=["id", "year", "resolutions_text"],
        filters=[
            ("year", ">=", int(y0)),
            ("year", "<=", int(y1)),
        ],
    ).to_pandas()
    frame["id"] = frame["id"].astype(str)
    frame["year"] = pd.to_numeric(frame["year"], errors="coerce").astype("Int64")
    frame["resolutions_text"] = frame["resolutions_text"].fillna("").astype(str)
    if limit is not None:
        frame = frame.head(int(limit)).copy()
    return frame.reset_index(drop=True)


def _node_role(formula_type_id: str, provisional: bool) -> str:
    if formula_type_id == COMPOSITION_ROOT:
        return "root"
    if provisional or formula_type_id not in ACCEPTED_TYPES:
        return "provisional"
    return "accepted"


def build_composition_graph(
    scores: pd.DataFrame,
    models: list[dict[str, Any]],
) -> dict[str, Any]:
    """Build nodes + directed co-presence arcs from long presence/position scores."""
    n_ids = int(scores["id"].nunique()) if len(scores) else 0

    nodes: list[dict[str, Any]] = []
    weights: dict[str, float] = {}
    provisional_map: dict[str, bool] = {}
    for model in models:
        ft = str(model["formula_type_id"])
        sub = scores.loc[scores["formula_type_id"] == ft] if len(scores) else scores
        n = int(len(sub))
        n_present = int(sub["present"].sum()) if n else 0
        hit_rate = (n_present / n) if n else 0.0
        weight = float(popularity_weight(hit_rate))
        provisional = bool(model.get("provisional"))
        role = _node_role(ft, provisional)
        weights[ft] = weight
        provisional_map[ft] = provisional
        mid_med = None
        if n_present and "mid_norm" in sub.columns:
            present = sub.loc[sub["present"], "mid_norm"]
            if present.notna().any():
                mid_med = round(float(present.median()), 4)
        nodes.append(
            {
                "formula_type_id": ft,
                "role": role,
                "provisional": provisional,
                "model_role": model.get("role"),
                "n": n,
                "n_present": n_present,
                "hit_rate": round(float(hit_rate), 4),
                "weight": round(weight, 4),
                "weight_formula": "log(1 / clip(rate))",
                "mid_norm_median": mid_med,
            }
        )

    # Directed arcs: per id, every unordered pair of presents → earlier mid → later.
    edge_n: Counter[tuple[str, str]] = Counter()
    edge_zone: dict[tuple[str, str], Counter[str]] = defaultdict(Counter)
    if len(scores):
        present = scores.loc[scores["present"]].copy()
        if len(present):
            for _rid, grp in present.groupby("id", sort=False):
                hits = list(grp.itertuples(index=False))
                if len(hits) < 2:
                    continue
                # Stable sort by mid_norm then start_idx then type id.
                hits.sort(
                    key=lambda r: (
                        float(r.mid_norm)
                        if r.mid_norm is not None and not (isinstance(r.mid_norm, float) and math.isnan(r.mid_norm))
                        else float(r.start_idx),
                        int(r.start_idx),
                        str(r.formula_type_id),
                    )
                )
                for i in range(len(hits)):
                    for j in range(i + 1, len(hits)):
                        a = str(hits[i].formula_type_id)
                        b = str(hits[j].formula_type_id)
                        if a == b:
                            continue
                        key = (a, b)
                        edge_n[key] += 1
                        za = str(hits[i].zone) if hits[i].zone else "?"
                        zb = str(hits[j].zone) if hits[j].zone else "?"
                        edge_zone[key][f"{za}->{zb}"] += 1

    arcs: list[dict[str, Any]] = []
    for (a, b), n in sorted(edge_n.items(), key=lambda x: (-x[1], x[0])):
        wa = weights.get(a, 0.0)
        wb = weights.get(b, 0.0)
        zone_counts = edge_zone[(a, b)]
        top_zone = zone_counts.most_common(1)[0][0] if zone_counts else None
        both_accepted = (
            a in ACCEPTED_TYPES
            and b in ACCEPTED_TYPES
            and not provisional_map.get(a, True)
            and not provisional_map.get(b, True)
        )
        arcs.append(
            {
                "from": a,
                "to": b,
                "n": int(n),
                "n_weighted": round(float(n) * wa * wb, 4),
                "zone_arc": top_zone,
                "zone_arc_counts": {
                    k: int(v) for k, v in zone_counts.most_common(5)
                },
                "both_accepted": both_accepted,
                "from_role": _node_role(a, provisional_map.get(a, a not in ACCEPTED_TYPES)),
                "to_role": _node_role(b, provisional_map.get(b, b not in ACCEPTED_TYPES)),
            }
        )

    n_acc_acc = sum(1 for e in arcs if e["both_accepted"] and e["n"] > 0)
    shape = classify_graph_shape(nodes, arcs, n_accepted_accepted_edges=n_acc_acc)

    return {
        "n_resolutions": n_ids,
        "n_types": int(len(models)),
        "nodes": nodes,
        "arcs": arcs,
        "n_arcs": int(len(arcs)),
        "n_accepted_accepted_edges": int(n_acc_acc),
        "graph_shape": shape,
        "model_ids": [str(m["formula_type_id"]) for m in models],
        "composition_root": COMPOSITION_ROOT,
    }


def classify_graph_shape(
    nodes: list[dict[str, Any]],
    arcs: list[dict[str, Any]],
    *,
    n_accepted_accepted_edges: int | None = None,
) -> str:
    """Cheap shape label for NOTES gates.

    - ``empty``: no co-presence arcs
    - ``provisional_root_star``: arcs exist but none accepted↔accepted (hub via root)
    - ``accepted_co_presence``: at least one accepted↔accepted edge
    """
    if not arcs or all(int(e.get("n") or 0) == 0 for e in arcs):
        return "empty"
    n_aa = (
        n_accepted_accepted_edges
        if n_accepted_accepted_edges is not None
        else sum(1 for e in arcs if e.get("both_accepted") and int(e.get("n") or 0) > 0)
    )
    if int(n_aa) > 0:
        return "accepted_co_presence"
    # Prefer naming star when composition root participates as from-hub.
    root_out = sum(
        int(e.get("n") or 0)
        for e in arcs
        if e.get("from") == COMPOSITION_ROOT
    )
    if root_out > 0:
        return "provisional_root_star"
    return "provisional_spoke"


def shape_over_time(period_matrix: list[dict[str, Any]]) -> dict[str, Any]:
    """Cross-bin shape summary (only meaningful when ``--period-bins`` ran)."""
    shapes = [str(p.get("graph_shape") or "unknown") for p in period_matrix]
    counts = Counter(shapes)
    n_aa = [int(p.get("n_accepted_accepted_edges") or 0) for p in period_matrix]
    return {
        "n_bins": int(len(period_matrix)),
        "shape_counts": {k: int(v) for k, v in sorted(counts.items())},
        "shapes_in_order": [
            {"period_bin": p.get("period_bin"), "graph_shape": p.get("graph_shape")}
            for p in period_matrix
        ],
        "all_star": bool(shapes) and all(
            s in {"provisional_root_star", "provisional_spoke", "empty"}
            for s in shapes
        ),
        "any_accepted_co_presence": any(s == "accepted_co_presence" for s in shapes),
        "n_accepted_accepted_edges_by_bin": n_aa,
        "max_n_accepted_accepted_edges": max(n_aa) if n_aa else 0,
        "judgment_prompt": (
            "Does graph_shape change over bins, or stay a provisional-root star? "
            "If star everywhere → do not invent sequence features; "
            "next another A family or sieve residual."
        ),
    }


def summarize_composition_graph(
    scores: pd.DataFrame,
    models: list[dict[str, Any]],
    *,
    year: int | None,
    period_bin: str | None = None,
    random_state: int,
    limit: int | None,
    opening_cut: float = OPENING_CUT,
    close_cut: float = CLOSE_CUT,
) -> dict[str, Any]:
    """Single-slice (year or bin) provenanced metrics."""
    graph = build_composition_graph(scores, models)
    label = period_bin
    if label is None and year is not None:
        label = year_bin(int(year), origin=BIN_ORIGIN, width=BIN_WIDTH)
    return {
        "step": "STEPT1d",
        "method": "composition_graph_co_presence",
        "year": int(year) if year is not None else None,
        "period_bin": label,
        "random_state": int(random_state),
        "limit": limit,
        "zone_cuts": {
            "opening_lt": float(opening_cut),
            "body_lt": float(close_cut),
            "close_ge": float(close_cut),
            "rule": "mid_norm = (start_idx+end_idx)/2 / n_tokens",
        },
        "arc_rule": (
            "co-presence on same id; direction = earlier mid_norm → later "
            "(tie-break start_idx, type id)"
        ),
        "appointment_accepted": any(
            m.get("formula_type_id") == APPOINTMENT_ID and not m.get("provisional")
            for m in models
        ),
        "advies_accepted": any(
            m.get("formula_type_id") == ADVIES_ID and not m.get("provisional")
            for m in models
        ),
        "openings_provisional": any(bool(m.get("provisional")) for m in models),
        "composition_root": COMPOSITION_ROOT,
        "n_resolutions": graph["n_resolutions"],
        "n_types": graph["n_types"],
        "nodes": graph["nodes"],
        "arcs": graph["arcs"],
        "n_arcs": graph["n_arcs"],
        "n_accepted_accepted_edges": graph["n_accepted_accepted_edges"],
        "graph_shape": graph["graph_shape"],
        "judgment_prompt": (
            "1780 smoke: n_accepted_accepted_edges and graph_shape "
            "(provisional_root_star vs accepted_co_presence). "
            "If accepted↔accepted is 0, skip --period-bins unless diachronic "
            "confirmation of the same star is needed."
        ),
    }


def summarize_period_matrix(
    bin_metrics: list[dict[str, Any]],
    *,
    random_state: int,
    limit: int | None,
    year_min: int = YEAR_MIN,
    year_max: int = YEAR_MAX,
) -> dict[str, Any]:
    """Wrap per-bin graph summaries + shape_over_time."""
    matrix: list[dict[str, Any]] = []
    for m in bin_metrics:
        matrix.append(
            {
                "period_bin": m.get("period_bin"),
                "n_resolutions": m.get("n_resolutions"),
                "nodes": m.get("nodes"),
                "arcs": m.get("arcs"),
                "n_arcs": m.get("n_arcs"),
                "n_accepted_accepted_edges": m.get("n_accepted_accepted_edges"),
                "graph_shape": m.get("graph_shape"),
            }
        )
    return {
        "step": "STEPT1d",
        "method": "composition_graph_period_matrix",
        "year_min": int(year_min),
        "year_max": int(year_max),
        "bin_origin": BIN_ORIGIN,
        "bin_width": BIN_WIDTH,
        "random_state": int(random_state),
        "limit": limit,
        "period_matrix": matrix,
        "shape_over_time": shape_over_time(matrix),
        "bins_available": list_bins_in_range(year_min, year_max),
        "composition_root": COMPOSITION_ROOT,
    }
