#!/usr/bin/env python3
"""STEPT1c: score formula-type hits with DAG span → opening/body/close zone.

Includes accepted appointment + advies (frozen T1a / T1a2 cuts) and optional
provisional openings — same model set as T1b-refresh.

    uv run python scripts/run_formula_type_position.py --fixture-only
    uv run python scripts/run_formula_type_position.py
    uv run python scripts/run_formula_type_position.py --no-openings
    uv run python scripts/run_formula_type_position.py --no-advies
    uv run python scripts/run_formula_type_position.py --limit 200
"""

from __future__ import annotations

import argparse
import json
from typing import Any

from data_io import save_semi_structured
from formulation.advies_formula_type import FORMULA_TYPE_ID as ADVIES_ID
from formulation.appointment_formula_type import FORMULA_TYPE_ID as APPOINTMENT_ID
from formulation.appointment_formula_type import RNG
from formulation.formula_period_bins import CANDIDATE_CAP_PER_BIN, OPENING_FAMILIES
from formulation.formula_type_position import (
    CLOSE_CUT,
    DEFAULT_YEAR,
    OPENING_CUT,
    fixture_position_frames,
    fixture_position_models,
    score_position_frame,
    summarize_position,
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
        help=f"Calendar year to score (default {DEFAULT_YEAR})",
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
        help="Optional cap on year-slice rows (POC smoke)",
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


def _build_models(args: argparse.Namespace) -> list[dict[str, Any]]:
    if args.fixture_only:
        models = fixture_position_models()
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
                int(args.year),
                candidate_cap=int(args.candidate_cap),
                random_state=int(args.random_state),
            )
            if m is not None:
                models.append(m)
            else:
                print(f"skip opening {family}: no candidates in year bin")
    return models


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)
    year = int(args.year)

    if args.fixture_only:
        frame = fixture_position_frames()
    else:
        frame = load_year_slice(year, limit=args.limit)

    models = _build_models(args)
    if not models:
        raise SystemExit("no formula-type models to score")

    scores = score_position_frame(
        frame,
        models,
        opening_cut=float(args.opening_cut),
        close_cut=float(args.close_cut),
    )
    metrics = summarize_position(
        scores,
        year=year,
        models=models,
        random_state=int(args.random_state),
        limit=args.limit,
        opening_cut=float(args.opening_cut),
        close_cut=float(args.close_cut),
    )

    score_rows = scores.to_dict(orient="records")
    parents = ["resolutions_flat", "aanstelling_selected"]
    if any(m["formula_type_id"] == ADVIES_ID for m in models):
        parents.extend(["advies_es_gold", "formula_type_advies_metrics"])

    save_semi_structured(
        [metrics],
        logical_name="formula_type_position_metrics",
        script=__file__,
        parent_sources=parents,
        description=(
            f"STEPT1c position/zone metrics year={year} "
            f"n={metrics.get('n_resolutions')} types={metrics.get('n_types')} "
            f"advies={metrics.get('advies_accepted')}"
        ),
    )
    save_semi_structured(
        score_rows,
        logical_name="formula_type_position_scores",
        script=__file__,
        parent_sources=["formula_type_position_metrics"],
        description=(
            f"STEPT1c per-id×type span+zone scores year={year} "
            f"({len(score_rows)} rows)"
        ),
    )

    print(json.dumps(metrics, indent=2, default=str))
    bags = metrics.get("bags") or {}
    print(
        f"wrote formula_type_position_metrics / "
        f"formula_type_position_scores ({len(score_rows)} score rows); "
        f"frac_multi={bags.get('frac_multi')}; "
        f"advies_accepted={metrics.get('advies_accepted')}"
    )


if __name__ == "__main__":
    main()
