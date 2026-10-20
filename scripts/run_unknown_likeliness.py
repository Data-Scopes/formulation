#!/usr/bin/env python3
"""STEPT1h: unknown-likeliness POC (accepted cover set).

    uv run python scripts/run_unknown_likeliness.py --fixture-only
    uv run python scripts/run_unknown_likeliness.py --year 1780
"""

from __future__ import annotations

import argparse
import json
from typing import Any

from data_io import save_semi_structured
from formulation.unknown_likeliness import (
    COVER_AXES,
    DEFAULT_SAMPLE_PER_STRATUM,
    DEFAULT_SAMPLE_SEED,
    DEFAULT_YEAR,
    build_unknown_frame,
    draw_high_unknown_sample,
    fixture_unknown_frame,
    load_unknown_universe,
    summarize_unknown_likeliness,
)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--fixture-only", action="store_true")
    p.add_argument("--year", type=int, default=DEFAULT_YEAR)
    p.add_argument("--no-presence", action="store_true")
    p.add_argument("--no-text-length", action="store_true")
    p.add_argument("--no-sample", action="store_true")
    p.add_argument(
        "--sample-per-stratum",
        type=int,
        default=DEFAULT_SAMPLE_PER_STRATUM,
    )
    p.add_argument("--sample-seed", type=int, default=DEFAULT_SAMPLE_SEED)
    p.add_argument("--no-write", action="store_true")
    return p.parse_args(argv)


def _scores_rows(frame) -> list[dict[str, Any]]:
    keep = [
        "id",
        "year",
        "n_words",
        "n_cover_hits",
        "unknown_score",
        "high_unknown",
        "text_joined",
        *COVER_AXES,
    ]
    cols = [c for c in keep if c in frame.columns]
    return frame[cols].to_dict(orient="records")


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if args.fixture_only:
        frame = fixture_unknown_frame()
        year = int(frame["year"].iloc[0])
        sample = frame.head(0)
    else:
        year = int(args.year)
        universe = load_unknown_universe(year=year)
        frame = build_unknown_frame(
            universe,
            year=year,
            join_presence=not args.no_presence,
            join_text_length=not args.no_text_length,
        )
        if args.no_sample:
            sample = frame.head(0)
        else:
            sample = draw_high_unknown_sample(
                frame,
                per_stratum=int(args.sample_per_stratum),
                seed=int(args.sample_seed),
            )

    metrics = summarize_unknown_likeliness(frame, year=year)
    metrics["n_sample_rows"] = int(len(sample))
    print(json.dumps(metrics, indent=2, default=str))

    if args.no_write:
        return 0

    save_semi_structured(
        [metrics],
        logical_name="resolution_unknown_metrics",
        script=__file__,
        description=(
            f"STEPT1h: unknown-likeliness band + cover axis hits "
            f"(year={year}; fixture={args.fixture_only})"
        ),
    )
    save_semi_structured(
        _scores_rows(frame),
        logical_name="resolution_unknown_scores",
        script=__file__,
        description=(
            f"STEPT1h: per-id cover flags + unknown_score "
            f"(year={year}; no full text)"
        ),
    )
    if not args.no_sample:
        # Fixture writes an empty sample so the manifest path exists before 1780.
        save_semi_structured(
            sample.to_dict(orient="records") if len(sample) else [],
            logical_name="resolution_unknown_sample",
            script=__file__,
            description=(
                f"STEPT1h: high-unknown stratified text sample "
                f"(year={year}; truncated text; fixture={args.fixture_only})"
            ),
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
