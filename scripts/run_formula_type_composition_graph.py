#!/usr/bin/env python3
"""STEPT1d: composition graph (co-presence arcs; not Track S align_dag).

Cheap 1780 smoke first; ``--period-bins`` only if dynamics still open.

    uv run python scripts/run_formula_type_composition_graph.py --fixture-only
    uv run python scripts/run_formula_type_composition_graph.py --year 1780 --limit 200
    uv run python scripts/run_formula_type_composition_graph.py --period-bins
"""

from __future__ import annotations

import argparse
import json
from typing import Any

from data_io import save_semi_structured
from formulation.advies_formula_type import FORMULA_TYPE_ID as ADVIES_ID
from formulation.appointment_formula_type import FORMULA_TYPE_ID as APPOINTMENT_ID
from formulation.appointment_formula_type import RNG, YEAR_MAX, YEAR_MIN
from formulation.formula_period_bins import (
    CANDIDATE_CAP_PER_BIN,
    OPENING_FAMILIES,
    bin_bounds,
    list_bins_in_range,
)
from formulation.formula_type_composition_graph import (
    CLOSE_CUT,
    DEFAULT_YEAR,
    OPENING_CUT,
    fixture_composition_frames,
    fixture_composition_models,
    load_bin_slice,
    score_composition_frame,
    summarize_composition_graph,
    summarize_period_matrix,
)
from formulation.formula_type_presence import (
    fit_advies_presence_model,
    fit_appointment_presence_model,
    fit_opening_presence_model,
    load_year_slice,
)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument(
        "--fixture-only",
        action="store_true",
        help="Tiny in-memory smoke (no resolutions_flat)",
    )
    p.add_argument(
        "--year",
        type=int,
        default=DEFAULT_YEAR,
        help=f"Calendar year smoke (default {DEFAULT_YEAR})",
    )
    p.add_argument(
        "--period-bins",
        action="store_true",
        help="Full 25y period matrix (heavy; only if 1780 leaves dynamics open)",
    )
    p.add_argument(
        "--no-openings",
        action="store_true",
        help="Skip provisional ontfangen/requeste",
    )
    p.add_argument(
        "--no-advies",
        action="store_true",
        help="Skip accepted advies",
    )
    p.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Optional cap on slice rows (POC smoke)",
    )
    p.add_argument(
        "--cut",
        type=float,
        default=None,
        help="Override appointment operating cut (default: frozen STEPT1a)",
    )
    p.add_argument(
        "--advies-cut",
        type=float,
        default=None,
        help="Override advies operating cut (default: frozen STEPT1a2)",
    )
    p.add_argument(
        "--candidate-cap",
        type=int,
        default=CANDIDATE_CAP_PER_BIN,
        help=f"Opening candidate cap per bin (default {CANDIDATE_CAP_PER_BIN})",
    )
    p.add_argument(
        "--random-state",
        type=int,
        default=RNG,
        help=f"RNG seed (default {RNG})",
    )
    p.add_argument(
        "--opening-cut",
        type=float,
        default=OPENING_CUT,
        help=f"mid_norm < cut → opening (default {OPENING_CUT})",
    )
    p.add_argument(
        "--close-cut",
        type=float,
        default=CLOSE_CUT,
        help=f"mid_norm >= cut → close (default {CLOSE_CUT})",
    )
    return p.parse_args(argv)


def _build_models(
    args: argparse.Namespace,
    *,
    year_for_openings: int,
) -> list[dict[str, Any]]:
    if args.fixture_only:
        models = fixture_composition_models()
        if args.no_advies:
            models = [m for m in models if m["formula_type_id"] != ADVIES_ID]
        if args.no_openings:
            models = [m for m in models if not m.get("provisional")]
        return models

    models: list[dict[str, Any]] = [
        fit_appointment_presence_model(
            random_state=int(args.random_state),
            cut=args.cut,
        )
    ]
    if not args.no_advies:
        models.append(
            fit_advies_presence_model(
                random_state=int(args.random_state),
                cut=args.advies_cut,
            )
        )
    if not args.no_openings:
        for family in sorted(OPENING_FAMILIES):
            m = fit_opening_presence_model(
                family,
                int(year_for_openings),
                candidate_cap=int(args.candidate_cap),
                random_state=int(args.random_state),
            )
            if m is not None:
                models.append(m)
            else:
                print(f"skip opening {family}: no candidates for year {year_for_openings}")
    return models


def _score_rows(scores: Any) -> list[dict[str, Any]]:
    """Compact per-id present bags for scores JSONL (no full text)."""
    if scores is None or len(scores) == 0:
        return []
    present = scores.loc[scores["present"]]
    rows: list[dict[str, Any]] = []
    all_ids = scores["id"].astype(str).unique()
    by_id: dict[str, list[dict[str, Any]]] = {}
    if len(present):
        for rid, grp in present.groupby("id", sort=False):
            hits = [
                {
                    "formula_type_id": str(r.formula_type_id),
                    "zone": str(r.zone) if r.zone is not None else None,
                    "mid_norm": (
                        float(r.mid_norm) if r.mid_norm is not None else None
                    ),
                    "provisional": bool(r.provisional),
                    "score": float(r.score),
                }
                for r in grp.itertuples(index=False)
            ]
            hits.sort(
                key=lambda h: (
                    h["mid_norm"] if h["mid_norm"] is not None else 0.0,
                    h["formula_type_id"],
                )
            )
            by_id[str(rid)] = hits
    for rid in all_ids:
        year_val = scores.loc[scores["id"].astype(str) == rid, "year"]
        year = None
        if len(year_val):
            y0 = year_val.iloc[0]
            year = int(y0) if y0 is not None and y0 == y0 else None
        hits = by_id.get(str(rid), [])
        rows.append(
            {
                "id": str(rid),
                "year": year,
                "n_present": len(hits),
                "bag_types": sorted({h["formula_type_id"] for h in hits}),
                "ordered_by_mid": [h["formula_type_id"] for h in hits],
                "hits": hits,
            }
        )
    return rows


def _parents(models: list[dict[str, Any]]) -> list[str]:
    parents = ["resolutions_flat", "aanstelling_selected"]
    if any(m["formula_type_id"] == ADVIES_ID for m in models):
        parents.extend(["advies_es_gold", "formula_type_advies_metrics"])
    return parents


def _run_single(
    args: argparse.Namespace,
    *,
    frame: Any,
    models: list[dict[str, Any]],
    year: int | None,
    period_bin: str | None,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    scores = score_composition_frame(
        frame,
        models,
        opening_cut=float(args.opening_cut),
        close_cut=float(args.close_cut),
    )
    metrics = summarize_composition_graph(
        scores,
        models,
        year=year,
        period_bin=period_bin,
        random_state=int(args.random_state),
        limit=args.limit,
        opening_cut=float(args.opening_cut),
        close_cut=float(args.close_cut),
    )
    return metrics, _score_rows(scores)


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)

    if args.fixture_only and args.period_bins:
        raise SystemExit("use either --fixture-only or --period-bins, not both")

    if args.period_bins:
        bin_metrics: list[dict[str, Any]] = []
        all_score_rows: list[dict[str, Any]] = []
        for label in list_bins_in_range(YEAR_MIN, YEAR_MAX):
            y0, y1 = bin_bounds(label)
            y0 = max(y0, YEAR_MIN)
            y1 = min(y1, YEAR_MAX)
            mid_year = (y0 + y1) // 2
            frame = load_bin_slice(label, limit=args.limit)
            if frame.empty:
                print(f"skip bin {label}: empty slice")
                continue
            models = _build_models(args, year_for_openings=mid_year)
            if not models:
                print(f"skip bin {label}: no models")
                continue
            metrics, score_rows = _run_single(
                args,
                frame=frame,
                models=models,
                year=None,
                period_bin=label,
            )
            bin_metrics.append(metrics)
            for row in score_rows:
                row["period_bin"] = label
            all_score_rows.extend(score_rows)
            print(
                f"bin {label}: n={metrics['n_resolutions']} "
                f"shape={metrics['graph_shape']} "
                f"n_aa={metrics['n_accepted_accepted_edges']}"
            )

        if not bin_metrics:
            raise SystemExit("no period bins produced metrics")

        summary = summarize_period_matrix(
            bin_metrics,
            random_state=int(args.random_state),
            limit=args.limit,
        )
        parents = _parents(models)
        save_semi_structured(
            [summary],
            logical_name="formula_type_composition_graph_metrics",
            script=__file__,
            parent_sources=parents,
            description=(
                "STEPT1d composition graph period matrix; "
                f"bins={len(bin_metrics)} "
                f"shape_over_time={summary['shape_over_time'].get('shape_counts')}"
            ),
        )
        save_semi_structured(
            all_score_rows,
            logical_name="formula_type_composition_graph_scores",
            script=__file__,
            parent_sources=["formula_type_composition_graph_metrics"],
            description=(
                f"STEPT1d composition graph per-id bags across bins "
                f"({len(all_score_rows)} rows)"
            ),
        )
        print(json.dumps(summary, indent=2, default=str))
        sot = summary["shape_over_time"]
        print(
            f"wrote formula_type_composition_graph_metrics / _scores; "
            f"all_star={sot.get('all_star')} "
            f"any_accepted={sot.get('any_accepted_co_presence')} "
            f"max_n_aa={sot.get('max_n_accepted_accepted_edges')}"
        )
        return

    year = int(args.year)
    if args.fixture_only:
        frame = fixture_composition_frames()
    else:
        frame = load_year_slice(year, limit=args.limit)

    models = _build_models(args, year_for_openings=year)
    if not models:
        raise SystemExit("no formula-type models to score")

    metrics, score_rows = _run_single(
        args,
        frame=frame,
        models=models,
        year=year,
        period_bin=None,
    )

    # Single-slice metrics wrap as a one-bin period_matrix for a stable schema.
    wrapped = {
        **metrics,
        "period_matrix": [
            {
                "period_bin": metrics.get("period_bin"),
                "n_resolutions": metrics.get("n_resolutions"),
                "nodes": metrics.get("nodes"),
                "arcs": metrics.get("arcs"),
                "n_arcs": metrics.get("n_arcs"),
                "n_accepted_accepted_edges": metrics.get(
                    "n_accepted_accepted_edges"
                ),
                "graph_shape": metrics.get("graph_shape"),
            }
        ],
        "shape_over_time": None,
    }

    parents = _parents(models)
    save_semi_structured(
        [wrapped],
        logical_name="formula_type_composition_graph_metrics",
        script=__file__,
        parent_sources=parents,
        description=(
            f"STEPT1d composition graph year={year} "
            f"n={metrics.get('n_resolutions')} "
            f"shape={metrics.get('graph_shape')} "
            f"n_aa={metrics.get('n_accepted_accepted_edges')}"
        ),
    )
    save_semi_structured(
        score_rows,
        logical_name="formula_type_composition_graph_scores",
        script=__file__,
        parent_sources=["formula_type_composition_graph_metrics"],
        description=(
            f"STEPT1d composition graph per-id bags year={year} "
            f"({len(score_rows)} rows)"
        ),
    )

    print(json.dumps(wrapped, indent=2, default=str))
    print(
        f"wrote formula_type_composition_graph_metrics / "
        f"formula_type_composition_graph_scores ({len(score_rows)} rows); "
        f"graph_shape={metrics.get('graph_shape')} "
        f"n_accepted_accepted_edges={metrics.get('n_accepted_accepted_edges')}"
    )


if __name__ == "__main__":
    main()
