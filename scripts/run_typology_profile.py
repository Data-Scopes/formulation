#!/usr/bin/env python3
"""STEPT0: 18c structural profile by proposition_type (Track T).

Defaults to one year (POC_YEAR = 1780, shared with STEPS1/Track L) for a first
provisional pass; pass --full-18c or explicit --year-min/--year-max to widen —
other years are comparisons/extensions, not the baseline.

Composition is a full-population ES aggregation (no sampling error); the
characterisation sample floors rare types so they're analysable, which means
it must never be read as the population mix — see
``formulation.typology_sample`` module docstring.

    uv run python scripts/run_typology_profile.py
    uv run python scripts/run_typology_profile.py --composition-only
    uv run python scripts/run_typology_profile.py --full-18c
"""

from __future__ import annotations

import argparse

import pandas as pd

from data_io import save_semi_structured
from formulation.republic_es import RepublicEsClient
from formulation.typology_sample import (
    DEFAULT_FLOOR,
    DEFAULT_SAMPLE_TOTAL,
    DEFAULT_SEED,
    POC_YEAR_MAX,
    POC_YEAR_MIN,
    YEAR_MAX_18C,
    YEAR_MIN_18C,
    allocate_sample_sizes,
    build_profile_records,
    composition_by_type,
    draw_typed_sample,
    join_outcome_flags,
    normalize_sample_rows,
)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--year-min",
        type=int,
        default=POC_YEAR_MIN,
        help="Start with one year (default: POC_YEAR); widen explicitly to compare/extend",
    )
    parser.add_argument(
        "--year-max",
        type=int,
        default=POC_YEAR_MAX,
        help="See --year-min",
    )
    parser.add_argument(
        "--full-18c",
        action="store_true",
        help=f"Shortcut for --year-min {YEAR_MIN_18C} --year-max {YEAR_MAX_18C}",
    )
    parser.add_argument("--total", type=int, default=DEFAULT_SAMPLE_TOTAL)
    parser.add_argument("--floor", type=int, default=DEFAULT_FLOOR)
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    parser.add_argument(
        "--composition-only",
        action="store_true",
        help="Print the 3a population composition table and stop (no sample, no ES writes)",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)
    if args.full_18c:
        args.year_min, args.year_max = YEAR_MIN_18C, YEAR_MAX_18C
    client = RepublicEsClient()

    composition = composition_by_type(
        client, year_min=args.year_min, year_max=args.year_max
    )
    print(
        f"Composition {args.year_min}-{args.year_max}: "
        f"{composition.attrs['total_resolutions']} resolutions, "
        f"{len(composition)} proposition_type values"
    )
    print(composition.to_string(index=False))

    if args.composition_only:
        return

    allocation = allocate_sample_sizes(
        composition, total_target=args.total, floor=args.floor
    )
    print()
    print(
        allocation[
            ["proposition_type", "population_n", "sample_n", "capped_by_population"]
        ].to_string(index=False)
    )

    raw_rows = draw_typed_sample(
        client,
        allocation,
        year_min=args.year_min,
        year_max=args.year_max,
        seed=args.seed,
    )
    print(f"\nDrew {len(raw_rows)} resolutions across {len(allocation)} types")

    sample = normalize_sample_rows(raw_rows)
    joined = join_outcome_flags(sample)
    coverage = joined["outcome_joined"].mean() if len(joined) else 0.0
    print(f"Outcome-flag join coverage: {coverage:.1%}")

    records = build_profile_records(joined, composition)

    path = save_semi_structured(
        records,
        logical_name="typology_structural_profile",
        description=(
            f"STEPT0 structural profile, {args.year_min}-{args.year_max}, "
            f"seed={args.seed}, total_target={args.total}, floor={args.floor}"
        ),
        script="scripts/run_typology_profile.py",
    )
    print(f"\nSaved {len(records)} records -> {path}")
    summary = pd.DataFrame(
        [
            {
                "proposition_type": r["proposition_type"],
                "population_n": r["population_n"],
                "sample_n": r["sample_n"],
                "outcome_join_coverage": r["outcome_join_coverage"],
                "n_label_zones": len(r["label_zones"]),
            }
            for r in records
        ]
    )
    print(summary.to_string(index=False))


if __name__ == "__main__":
    main()
