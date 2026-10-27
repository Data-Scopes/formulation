#!/usr/bin/env python3
"""STEPT1ag: triviality sieve + capped absorb/truncate review of thin families.

    uv run python scripts/run_formula_family_residual_sweep.py --fixture-only
    uv run python scripts/run_formula_family_residual_sweep.py
"""

from __future__ import annotations

import argparse

from data_io import load, save_semi_structured
from formulation.formula_family_residual_sweep import (
    DEFAULT_MIN_REVIEW_FREQ,
    DEFAULT_REVIEW_CAP,
    fixture_sweep,
    sweep_families,
)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--fixture-only", action="store_true")
    p.add_argument("--review-cap", type=int, default=DEFAULT_REVIEW_CAP)
    p.add_argument(
        "--min-freq",
        type=int,
        default=DEFAULT_MIN_REVIEW_FREQ,
        help=f"phrase_freq_max floor for review (default {DEFAULT_MIN_REVIEW_FREQ})",
    )
    p.add_argument("--no-write", action="store_true")
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)
    if args.fixture_only:
        result = fixture_sweep()
    else:
        families = list(load("formula_family_candidates"))
        result = sweep_families(
            families,
            review_cap=args.review_cap,
            min_review_freq=args.min_freq,
        )

    m = result["metrics"]
    print(
        f"STEPT1ag: input={m['n_input_families']} thin={m['n_thin']} "
        f"trivial={m['n_trivial']} review={m['n_review']} "
        f"(cap={m['review_cap']}, min_freq={m['min_review_freq']}, "
        f"overflow={m['n_review_capped_out']})"
    )
    print("  trivial_reasons:", m.get("trivial_reason_hist"))
    for row in result["review"][:8]:
        props = row.get("proposals") or []
        acts = ",".join(str(p.get("action")) for p in props) or "-"
        print(
            f"  review {row.get('family_id')}: {acts} | {str(row.get('exemplar'))[:60]}"
        )

    if args.no_write:
        return

    save_semi_structured(
        [m],
        logical_name="formula_family_residual_metrics",
        script=__file__,
        description="STEPT1ag residual sweep metrics",
    )
    save_semi_structured(
        result["trivial"],
        logical_name="formula_family_residual_trivial",
        script=__file__,
        description="STEPT1ag trivial park (not skimmed)",
    )
    save_semi_structured(
        result["review"],
        logical_name="formula_family_residual_review",
        script=__file__,
        description="STEPT1ag capped absorb/truncate review shortlist",
    )


if __name__ == "__main__":
    main()
