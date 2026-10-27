#!/usr/bin/env python3
"""STEPT1ai: adjudicate archaeology witnesses vs hinge archetypes.

    uv run python scripts/run_formula_hinge_witness.py --fixture-only
    uv run python scripts/run_formula_hinge_witness.py
    uv run python scripts/run_formula_hinge_witness.py --limit 200
"""

from __future__ import annotations

import argparse
import sys

from data_io import load, save_semi_structured
from formulation.formula_hinge_witness import (
    LOGICAL_NAME,
    METRICS_NAME,
    MID_CUT,
    NEAR_CUT,
    adjudicate_witnesses,
    adjudication_metrics,
    default_hinge_rows,
    hinge_targets,
    load_witness_fixture,
    witnesses_from_families,
)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument(
        "--fixture-only",
        action="store_true",
        help="Score fixture witnesses; print metrics; do not write",
    )
    p.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Cap family witnesses (skim runs)",
    )
    p.add_argument(
        "--near-cut",
        type=float,
        default=NEAR_CUT,
        help=f"near band floor (default {NEAR_CUT})",
    )
    p.add_argument(
        "--mid-cut",
        type=float,
        default=MID_CUT,
        help=f"mid band floor (default {MID_CUT})",
    )
    p.add_argument("--no-write", action="store_true")
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if args.mid_cut > args.near_cut:
        print("STEPT1ai: mid-cut must be <= near-cut", file=sys.stderr)
        return 1

    hinges = default_hinge_rows()
    targets = hinge_targets(hinges)
    if not targets:
        print("STEPT1ai: no hinge targets with canonic", file=sys.stderr)
        return 1

    if args.fixture_only:
        witnesses = load_witness_fixture()
    else:
        families = list(load("formula_family_candidates"))
        if args.limit is not None:
            families = families[: max(0, args.limit)]
        witnesses = witnesses_from_families(families)

    rows = adjudicate_witnesses(
        hinges,
        witnesses,
        near_cut=args.near_cut,
        mid_cut=args.mid_cut,
    )
    m = adjudication_metrics(
        rows,
        n_hinge_targets=len(targets),
        near_cut=args.near_cut,
        mid_cut=args.mid_cut,
    )

    print(
        f"STEPT1ai: n_witnesses={m['n_witnesses']} "
        f"n_targets={m['n_hinge_targets']} by_band={m['by_band']} "
        f"p50={m['best_sim_p50']} p90={m['best_sim_p90']}"
    )
    near_hist = m.get("by_hinge_near") or {}
    if near_hist:
        top = sorted(near_hist.items(), key=lambda kv: (-kv[1], kv[0]))[:8]
        print("  near by hinge:", dict(top))
    for r in rows[:8]:
        print(
            f"  {r['band']:4} {r['best_sim']:.3f} → {r['best_hinge_id']:20} "
            f"| {str(r['witness_text'])[:50]}"
        )

    if args.fixture_only or args.no_write:
        return 0

    save_semi_structured(
        [m],
        logical_name=METRICS_NAME,
        script=__file__,
        description="STEPT1ai hinge witness adjudication metrics (band cuts + vectorizer)",
    )
    save_semi_structured(
        rows,
        logical_name=LOGICAL_NAME,
        script=__file__,
        description="STEPT1ai soft membership of family exemplars vs hinge canonics",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
