#!/usr/bin/env python3
"""STEPT1ac: sequence-matrix impact from family exemplars.

    # Catalog soft/hard only (fast):
    uv run python scripts/run_formula_sequence_family_impact.py --catalog-only

    # Full 1780 matrix on exemplars (slower; preserves STEPT1z outputs):
    uv run python scripts/run_formula_sequence_family_impact.py --year 1780
"""

from __future__ import annotations

import argparse
import json
from typing import Any

from data_io import load, save_semi_structured
from formulation.formula_family_fold import fixture_fold
from formulation.formula_sequence_family_impact import (
    DEFAULT_MAX_FAMILY_HARVEST,
    catalog_impact_summary,
    compare_matrix_summaries,
    family_exemplar_harvest,
    run_year_matrix_from_families,
)
from formulation.formula_sequence_matrix import harvest_catalog


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--fixture-only", action="store_true")
    p.add_argument("--catalog-only", action="store_true")
    p.add_argument("--year", type=int, default=1780)
    p.add_argument("--limit", type=int, default=None)
    p.add_argument("--max-harvest", type=int, default=DEFAULT_MAX_FAMILY_HARVEST)
    p.add_argument("--no-write", action="store_true")
    return p.parse_args(argv)


def _load_families(*, fixture: bool) -> list[dict[str, Any]]:
    if fixture:
        return list(fixture_fold()["families"])
    return list(load("formula_family_candidates"))


def _baseline_summary() -> dict[str, Any]:
    try:
        return dict(load("formula_sequence_matrix_metrics")[0])
    except FileNotFoundError:
        return {}


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    families = _load_families(fixture=args.fixture_only)
    old_harvest = harvest_catalog()
    catalog = catalog_impact_summary(
        families=families,
        old_harvest=old_harvest,
        max_family_harvest=args.max_harvest,
    )
    harvest = list(catalog.pop("new_harvest"))

    print(
        json.dumps(
            {
                "principle": catalog["principle"],
                "n_families": catalog["n_families"],
                "n_member_surfaces": catalog["n_member_surfaces"],
                "hard": catalog["hard"],
                "soft_containment": catalog["soft_containment"],
                "n_new_exemplar_harvest": catalog["n_new_exemplar_harvest"],
            },
            ensure_ascii=False,
            indent=2,
        )
    )

    impact: dict[str, Any] = {
        **catalog,
        "mode": "catalog_only" if args.catalog_only else "year_matrix",
    }

    if not args.catalog_only and not args.fixture_only:
        matrix, _sequences, harvest_used, _texts = run_year_matrix_from_families(
            families,
            year=args.year,
            max_family_harvest=args.max_harvest,
            limit=args.limit,
        )
        harvest = harvest_used
        baseline = _baseline_summary()
        impact = compare_matrix_summaries(baseline, matrix, catalog=catalog)
        impact["mode"] = "year_matrix"
        impact["year"] = args.year
        print(
            json.dumps(
                {
                    "baseline_empty": impact["baseline"].get("n_empty"),
                    "family_empty": impact["family_exemplar_matrix"].get("n_empty"),
                    "delta": impact["delta"],
                },
                ensure_ascii=False,
                indent=2,
            )
        )
    elif not args.catalog_only and args.fixture_only:
        impact["mode"] = "fixture_catalog_only"
        print("(fixture: catalog metrics only; skip year matrix)")

    if args.no_write:
        return 0

    save_semi_structured(
        [impact],
        logical_name="formula_sequence_family_impact_metrics",
        script=__file__,
        description="STEPT1ac: STEPT1z vs family-exemplar harvest impact",
    )
    save_semi_structured(
        harvest,
        logical_name="formula_sequence_family_harvest",
        script=__file__,
        description="STEPT1ac: canonical family exemplar harvest (+ pockets)",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
