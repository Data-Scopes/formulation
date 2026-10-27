#!/usr/bin/env python3
"""STEPT1b: score a year slice for formula-type presence + popularity bags.

Includes accepted appointment + advies + requeste (+ short opener) + missive +
rapport (frozen T1a / T1a2 / T1k / T1s / T1n / T1w cuts) and optional
provisional openings.

    uv run python scripts/run_formula_type_presence.py --fixture-only
    uv run python scripts/run_formula_type_presence.py
    uv run python scripts/run_formula_type_presence.py --no-openings
    uv run python scripts/run_formula_type_presence.py --no-advies
    uv run python scripts/run_formula_type_presence.py --no-requeste
    uv run python scripts/run_formula_type_presence.py --no-requeste-op-de
    uv run python scripts/run_formula_type_presence.py --no-rapport
    uv run python scripts/run_formula_type_presence.py --limit 200
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
from formulation.formula_type_presence import (
    DEFAULT_YEAR,
    fit_advies_presence_model,
    fit_appointment_presence_model,
    fit_missive_presence_model,
    fit_opening_presence_model,
    fit_rapport_presence_model,
    fit_requeste_op_de_presence_model,
    fit_requeste_presence_model,
    fixture_presence_frames,
    fixture_presence_models,
    load_year_slice,
    score_presence_frame,
    summarize_presence,
)
from formulation.missive_formula_type import FORMULA_TYPE_ID as MISSIVE_ID
from formulation.rapport_formula_type import FORMULA_TYPE_ID as RAPPORT_ID
from formulation.requeste_formula_type import FORMULA_TYPE_ID as REQUESTE_ID
from formulation.requeste_op_de_formula_type import (
    FORMULA_TYPE_ID as REQUESTE_OP_DE_ID,
)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument(
        "--fixture-only",
        action="store_true",
        help="Tiny in-memory smoke (no resolutions_flat / gold joins)",
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
        help="Skip accepted advies (appointment + openings only)",
    )
    p.add_argument(
        "--no-requeste",
        action="store_true",
        help="Skip accepted requeste opener (STEPT1k)",
    )
    p.add_argument(
        "--no-missive",
        action="store_true",
        help="Skip accepted missive opener (STEPT1n)",
    )
    p.add_argument(
        "--no-requeste-op-de",
        action="store_true",
        help="Skip accepted short requeste opener (STEPT1s)",
    )
    p.add_argument(
        "--no-rapport",
        action="store_true",
        help="Skip accepted rapport opener (STEPT1w)",
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
        "--requeste-cut",
        type=float,
        default=None,
        help="Override requeste operating cut (default: frozen STEPT1k)",
    )
    p.add_argument(
        "--missive-cut",
        type=float,
        default=None,
        help="Override missive operating cut (default: frozen STEPT1n)",
    )
    p.add_argument(
        "--requeste-op-de-cut",
        type=float,
        default=None,
        help="Override short requeste operating cut (default: frozen STEPT1s)",
    )
    p.add_argument(
        "--rapport-cut",
        type=float,
        default=None,
        help="Override rapport operating cut (default: frozen STEPT1w)",
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
    return p.parse_args(argv)


def _build_models(args: argparse.Namespace) -> list[dict[str, Any]]:
    if args.fixture_only:
        models = fixture_presence_models()
        if args.no_advies:
            models = [m for m in models if m["formula_type_id"] != ADVIES_ID]
        if args.no_requeste:
            models = [m for m in models if m["formula_type_id"] != REQUESTE_ID]
        if args.no_requeste_op_de:
            models = [m for m in models if m["formula_type_id"] != REQUESTE_OP_DE_ID]
        if args.no_missive:
            models = [m for m in models if m["formula_type_id"] != MISSIVE_ID]
        if args.no_rapport:
            models = [m for m in models if m["formula_type_id"] != RAPPORT_ID]
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
    if not args.no_requeste:
        models.append(
            fit_requeste_presence_model(
                random_state=int(args.random_state),
                cut=args.requeste_cut,
            )
        )
    if not args.no_requeste_op_de:
        models.append(
            fit_requeste_op_de_presence_model(
                random_state=int(args.random_state),
                cut=args.requeste_op_de_cut,
            )
        )
    if not args.no_missive:
        models.append(
            fit_missive_presence_model(
                random_state=int(args.random_state),
                cut=args.missive_cut,
            )
        )
    if not args.no_rapport:
        models.append(
            fit_rapport_presence_model(
                random_state=int(args.random_state),
                cut=args.rapport_cut,
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
        frame = fixture_presence_frames()
    else:
        frame = load_year_slice(year, limit=args.limit)

    models = _build_models(args)
    if not models:
        raise SystemExit("no formula-type models to score")

    scores = score_presence_frame(frame, models)
    metrics = summarize_presence(
        scores,
        year=year,
        models=models,
        random_state=int(args.random_state),
        limit=args.limit,
    )

    score_rows = scores.to_dict(orient="records")
    parents = ["resolutions_flat", "aanstelling_selected"]
    if any(m["formula_type_id"] == ADVIES_ID for m in models):
        parents.extend(["advies_es_gold", "formula_type_advies_metrics"])
    if any(m["formula_type_id"] == REQUESTE_ID for m in models):
        parents.extend(["rekest_es_gold", "formula_type_requeste_metrics"])
    if any(m["formula_type_id"] == REQUESTE_OP_DE_ID for m in models):
        parents.extend(["rekest_es_gold", "formula_type_requeste_op_de_metrics"])
    if any(m["formula_type_id"] == MISSIVE_ID for m in models):
        parents.extend(["missive_es_gold", "formula_type_missive_metrics"])
    if any(m["formula_type_id"] == RAPPORT_ID for m in models):
        parents.extend(["rapport_es_gold", "formula_type_rapport_metrics"])

    save_semi_structured(
        [metrics],
        logical_name="formula_type_presence_metrics",
        script=__file__,
        parent_sources=parents,
        description=(
            f"STEPT1b presence metrics year={year} "
            f"n={metrics.get('n_resolutions')} types={metrics.get('n_types')} "
            f"advies={metrics.get('advies_accepted')} "
            f"requeste={metrics.get('requeste_accepted')} "
            f"requeste_op_de={metrics.get('requeste_op_de_accepted')} "
            f"missive={metrics.get('missive_accepted')} "
            f"rapport={metrics.get('rapport_accepted')}"
        ),
    )
    save_semi_structured(
        score_rows,
        logical_name="formula_type_presence_scores",
        script=__file__,
        parent_sources=["formula_type_presence_metrics"],
        description=(
            f"STEPT1b per-id×type presence scores year={year} "
            f"({len(score_rows)} rows)"
        ),
    )

    print(json.dumps(metrics, indent=2, default=str))
    bags = metrics.get("bags") or {}
    print(
        f"wrote formula_type_presence_metrics / "
        f"formula_type_presence_scores ({len(score_rows)} score rows); "
        f"frac_zero={bags.get('frac_zero')} frac_multi={bags.get('frac_multi')}; "
        f"advies_accepted={metrics.get('advies_accepted')} "
        f"requeste_accepted={metrics.get('requeste_accepted')} "
        f"requeste_op_de_accepted={metrics.get('requeste_op_de_accepted')} "
        f"rapport_accepted={metrics.get('rapport_accepted')}"
    )


if __name__ == "__main__":
    main()
