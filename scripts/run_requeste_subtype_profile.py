#!/usr/bin/env python3
"""STEPT1l: requeste+ routing subtype characterisation.

    uv run python scripts/run_requeste_subtype_profile.py --fixture-only
    uv run python scripts/run_requeste_subtype_profile.py
    uv run python scripts/run_requeste_subtype_profile.py --year 1780
"""

from __future__ import annotations

import argparse
import json
from typing import Any

from data_io import save_semi_structured
from formulation.requeste_subtype_profile import (
    build_characterisation_frame,
    fixture_characterisation_frame,
    load_requeste_scores,
    summarize_requeste_subtypes,
)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument(
        "--fixture-only",
        action="store_true",
        help="Tiny in-memory smoke (no parquet / no formula_documents)",
    )
    p.add_argument(
        "--year",
        type=int,
        default=None,
        help="Optional single calendar year slice (default: full 1705-1796 ES gold)",
    )
    p.add_argument(
        "--no-flags",
        action="store_true",
        help="Skip formula_documents join",
    )
    p.add_argument(
        "--no-text-length",
        action="store_true",
        help="Skip resolutions_flat word counts",
    )
    p.add_argument(
        "--no-write",
        action="store_true",
        help="Print metrics JSON only; do not write provenanced outputs",
    )
    return p.parse_args(argv)


def _scores_rows(frame) -> list[dict[str, Any]]:
    keep = [
        "id",
        "year",
        "requeste_subtype",
        "score",
        "pred",
        "goedgevonden",
        "handen",
        "in handen",
        "advies",
        "gedelibereert_start",
        "n_words",
        "text_joined",
        "outcome_joined",
    ]
    cols = [c for c in keep if c in frame.columns]
    return frame[cols].to_dict(orient="records")


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if args.fixture_only:
        frame = fixture_characterisation_frame()
        year: int | None = int(frame["year"].iloc[0])
    else:
        year = args.year
        scores = load_requeste_scores(year=year)
        frame = build_characterisation_frame(
            scores,
            join_flags=not args.no_flags,
            join_text_length=not args.no_text_length,
        )

    metrics = summarize_requeste_subtypes(frame, year=year)
    print(json.dumps(metrics, indent=2, default=str))

    if args.no_write:
        return 0

    save_semi_structured(
        [metrics],
        logical_name="requeste_subtype_metrics",
        script=__file__,
        description=(
            f"STEPT1l: requeste+ routing subtype characterisation "
            f"(year={year}; fixture={args.fixture_only})"
        ),
    )
    save_semi_structured(
        _scores_rows(frame),
        logical_name="requeste_subtype_scores",
        script=__file__,
        description=(
            f"STEPT1l: per-id requeste+ routing subtype "
            f"(year={year}; no full text)"
        ),
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
