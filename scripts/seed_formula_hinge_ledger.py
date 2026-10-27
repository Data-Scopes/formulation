#!/usr/bin/env python3
"""STEPT1ah: seed formula_hinge_candidates from the hand archetype ledger.

    uv run python scripts/seed_formula_hinge_ledger.py --fixture-only
    uv run python scripts/seed_formula_hinge_ledger.py
"""

from __future__ import annotations

import argparse
import sys

from data_io import save_semi_structured
from formulation.formula_hinge_ledger import (
    LOGICAL_NAME,
    METRICS_NAME,
    default_seed_rows,
    ledger_metrics,
    load_fixture_rows,
    validate_ledger,
)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument(
        "--fixture-only",
        action="store_true",
        help="Load tests/fixtures JSONL; print metrics; do not write",
    )
    p.add_argument(
        "--from-default",
        action="store_true",
        help="Use in-module DEFAULT_SEED instead of fixture file",
    )
    p.add_argument("--no-write", action="store_true")
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if args.from_default:
        rows = default_seed_rows()
    else:
        rows = load_fixture_rows()

    problems = validate_ledger(rows)
    if problems:
        print("STEPT1ah validate FAIL:", problems, file=sys.stderr)
        return 1

    m = ledger_metrics(rows)
    print(
        f"STEPT1ah: n={m['n_hinges']} "
        f"by_status={m['by_status']} by_layer={m['by_layer']}"
    )
    for r in rows:
        can = r.get("canonic") or "(unnamed)"
        print(
            f"  {r.get('status'):14} {r.get('hinge_id'):20} "
            f"{r.get('place_band'):12} {can[:40]}"
        )

    if args.fixture_only or args.no_write:
        return 0

    save_semi_structured(
        [m],
        logical_name=METRICS_NAME,
        script=__file__,
        description="STEPT1ah hinge ledger seed metrics",
    )
    save_semi_structured(
        rows,
        logical_name=LOGICAL_NAME,
        script=__file__,
        description="STEPT1ah hinge archetypes (scaffolding + blueprint L2 + pockets)",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
