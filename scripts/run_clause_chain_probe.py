#!/usr/bin/env python3
"""STEPT1p: clause chains vs coarse bags (confined: appointment welkom/sessie).

    uv run python scripts/run_clause_chain_probe.py --fixture-only
    uv run python scripts/run_clause_chain_probe.py --year 1780
    uv run python scripts/run_clause_chain_probe.py --year 1780 --with-openers
"""

from __future__ import annotations

import argparse
import json
from typing import Any

from data_io import save_semi_structured
from formulation.clause_chain import (
    DEFAULT_MIN_SUPPORT,
    DEFAULT_YEAR,
    build_appointment_clause_specs,
    build_chain_frame,
    fixture_clause_specs,
    load_gold_appointment_frame,
    fixture_year_frame,
    load_review_labels,
    summarize_clause_chains,
)
from formulation.formula_type_presence import (
    load_frozen_appointment_cut,
    load_year_slice,
)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--fixture-only", action="store_true")
    p.add_argument("--year", type=int, default=DEFAULT_YEAR)
    p.add_argument("--limit", type=int, default=None)
    p.add_argument("--min-support", type=int, default=DEFAULT_MIN_SUPPORT)
    p.add_argument(
        "--cut",
        type=float,
        default=None,
        help="Override clause cut (default: frozen STEPT1a appointment cut)",
    )
    p.add_argument(
        "--with-openers",
        action="store_true",
        help="Add advies/requeste/missive openers as clause nodes (slower)",
    )
    p.add_argument(
        "--per-clause-cuts",
        action="store_true",
        help=(
            "Calibrate each clause node on its own holdout p20 instead of "
            "sharing the frozen type-level cut. Does not change "
            "appointment_installation's frozen cut. Required for any "
            "multi-clause chain to be possible (see STEPT1p NOTES)."
        ),
    )
    p.add_argument(
        "--on-gold",
        action="store_true",
        help=(
            "Run on aanstelling_labelled (213 human-harvested appointment "
            "positives + overig) instead of a year slice. Year slices are a "
            "poor universe for appointment clause work: 1780 holds 1 gold row."
        ),
    )
    p.add_argument("--no-write", action="store_true")
    return p.parse_args(argv)


def _opener_clause_specs() -> list[dict[str, Any]]:
    """The three accepted single-cloud openers as additional clause nodes."""
    from formulation.clause_chain import _clause_spec
    from formulation.formula_type_presence import (
        fit_advies_presence_model,
        fit_missive_presence_model,
        fit_requeste_presence_model,
    )

    specs: list[dict[str, Any]] = []
    for label, fit in (
        ("advies", fit_advies_presence_model),
        ("requeste", fit_requeste_presence_model),
        ("missive", fit_missive_presence_model),
    ):
        model = fit()
        specs.append(
            _clause_spec(
                label,
                model["cloud"],
                float(model["operating_cut"]),
                source=str(model["formula_type_id"]),
            )
        )
    return specs


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)

    if args.fixture_only:
        frame = fixture_year_frame()
        clause_specs = fixture_clause_specs()
        year = int(frame["year"].iloc[0])
        review = None
        parents = None
    elif args.on_gold:
        frame = load_gold_appointment_frame()
        if args.limit is not None:
            frame = frame.head(int(args.limit)).copy()
        year = -1  # mixed years (1685-1791); recorded as universe, not a slice
        frozen = load_frozen_appointment_cut()
        cut = float(args.cut) if args.cut is not None else float(frozen or 2.0)
        clause_specs = build_appointment_clause_specs(
            cut=cut, per_clause_cuts=bool(args.per_clause_cuts)
        )
        if args.with_openers:
            clause_specs.extend(_opener_clause_specs())
        review = load_review_labels()
        parents = ["aanstelling_labelled", "delegates_resolutie_refs"]
    else:
        year = int(args.year)
        frame = load_year_slice(year, limit=args.limit)
        frozen = load_frozen_appointment_cut()
        cut = float(args.cut) if args.cut is not None else float(frozen or 2.0)
        clause_specs = build_appointment_clause_specs(
            cut=cut, per_clause_cuts=bool(args.per_clause_cuts)
        )
        if args.with_openers:
            clause_specs.extend(_opener_clause_specs())
        review = load_review_labels()
        parents = ["resolutions_flat", "aanstelling_selected"]

    print(
        f"clauses: {[s['clause_id'] for s in clause_specs]} "
        f"cuts={[s['cut'] for s in clause_specs]} n_rows={len(frame)}"
    )
    chain_frame, hit_frame = build_chain_frame(frame, clause_specs)
    metrics = summarize_clause_chains(
        chain_frame,
        hit_frame,
        year=year,
        clause_specs=clause_specs,
        min_support=int(args.min_support),
        review_labels=review,
    )
    metrics["fixture_only"] = bool(args.fixture_only)
    metrics["with_openers"] = bool(args.with_openers)
    metrics["per_clause_cuts"] = bool(args.per_clause_cuts)
    metrics["limit"] = args.limit
    metrics["on_gold"] = bool(args.on_gold)

    print(json.dumps(metrics, indent=2, default=str))

    if args.no_write:
        return 0

    save_semi_structured(
        [metrics],
        logical_name="clause_chain_metrics",
        script=__file__,
        parent_sources=parents,
        description=(
            f"STEPT1p clause-chain vs bag metrics year={year} "
            f"clauses={len(clause_specs)} fixture={args.fixture_only}"
        ),
    )
    save_semi_structured(
        chain_frame.to_dict(orient="records"),
        logical_name="clause_chain_scores",
        script=__file__,
        parent_sources=["clause_chain_metrics"],
        description=(
            f"STEPT1p per-resolution clause chain + bag year={year} "
            f"({len(chain_frame)} rows; no full text)"
        ),
    )
    collapse = metrics.get("collapse") or {}
    order = metrics.get("order_stability") or {}
    print(
        "wrote clause_chain_metrics / clause_chain_scores; "
        f"bags={collapse.get('n_distinct_bags')} "
        f"chains={collapse.get('n_distinct_chains')} "
        f"frac_multi={collapse.get('frac_resolutions_in_multi_chain_bag')} "
        f"order_stability={order.get('support_weighted_dominant_order_frac')}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
