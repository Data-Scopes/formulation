#!/usr/bin/env python3
"""Stream-harvest republic_ner ORG annotations into provenanced institution_patterns.

Filters to TARGET_ORG_ENTITIES ids; period keys from inventory_metadata.
Does not rewrite formula_templates. Full annotations file is ~650MB — stream only.
"""

from __future__ import annotations

import argparse
from typing import Any

from data_io import save_semi_structured
from formulation.institution_pattern_harvest import harvest_institution_patterns
from formulation.institution_patterns import LOGICAL_NAME, validate_patterns


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--min-n",
        type=int,
        default=1,
        help="Drop surfaces seen fewer than N times (default 1)",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Stop after N annotation objects (POC / smoke)",
    )
    parser.add_argument(
        "--no-seeds",
        action="store_true",
        help="Do not merge institution_patterns_seeds into the output",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)
    rows, metrics = harvest_institution_patterns(
        min_n=args.min_n,
        limit=args.limit,
        with_seeds=not args.no_seeds,
    )
    validate_patterns(rows)
    patterns_path = save_semi_structured(
        rows,
        logical_name=LOGICAL_NAME,
        parent_sources=["org_annotations", "org_entities", "inventory_metadata"],
        description=(
            "Period-/inventory-keyed institution surfaces harvested from "
            "republic_ner ORG-annotations (+ optional fixture seeds)"
        ),
        script=__file__,
    )
    metrics_row: list[dict[str, Any]] = [metrics]
    metrics_path = save_semi_structured(
        metrics_row,
        logical_name="institution_patterns_metrics",
        parent_sources=[LOGICAL_NAME],
        description="ORG stream-harvest summary for institution_patterns",
        script=__file__,
    )
    print(
        f"wrote {len(rows)} patterns → {patterns_path}\n"
        f"metrics → {metrics_path}\n"
        f"harvest_rows={metrics['n_harvest_rows']} "
        f"targets={metrics['rows_per_target']}"
    )


if __name__ == "__main__":
    main()
