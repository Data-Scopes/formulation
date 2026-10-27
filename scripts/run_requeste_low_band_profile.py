#!/usr/bin/env python3
"""STEPT1r part A: quantitative profile of the requeste low-score band.

Reuses STEPT1q's ``formula_retrieval_arms_scores`` (clean 1380-row gold) and
STEPT1l's ``requeste_subtype_scores`` (66,657-row predicted-positive
population) -- both already on disk, no ``resolutions_flat`` / ES needed.

    uv run python scripts/run_requeste_low_band_profile.py --fixture-only
    uv run python scripts/run_requeste_low_band_profile.py
"""

from __future__ import annotations

import argparse
import json

from data_io import save_semi_structured
from formulation.requeste_low_band_profile import (
    build_low_band_profile,
    fixture_bands,
    load_clean_gold_bands,
    load_full_population_bands,
)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument(
        "--fixture-only",
        action="store_true",
        help="Tiny in-memory smoke (no jsonl reads)",
    )
    p.add_argument(
        "--no-write",
        action="store_true",
        help="Print metrics JSON only; do not write the provenanced output",
    )
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if args.fixture_only:
        clean, full = fixture_bands()
    else:
        clean = load_clean_gold_bands()
        full = load_full_population_bands()

    metrics = build_low_band_profile(clean, full)
    print(json.dumps(metrics, indent=2, default=str))

    if args.no_write:
        return 0

    save_semi_structured(
        [metrics],
        logical_name="requeste_low_band_profile_metrics",
        script=__file__,
        description=(
            f"STEPT1r part A: requeste low-band quantitative profile "
            f"(fixture={args.fixture_only})"
        ),
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
