#!/usr/bin/env python3
"""STEPT1aa: stream-profile phrases_5gram_18th (freq gate + rare sidecar).

    uv run python scripts/run_phrases_5gram_profile.py --fixture-only
    uv run python scripts/run_phrases_5gram_profile.py
    uv run python scripts/run_phrases_5gram_profile.py --year 1780 --min-freq 500
    # Smoke on first N occurrence rows:
    uv run python scripts/run_phrases_5gram_profile.py --max-rows 500000
"""

from __future__ import annotations

import argparse
from pathlib import Path

from data_io import resolve, save_semi_structured
from formulation.phrases_5gram_profile import (
    DEFAULT_MIN_FREQ,
    DEFAULT_RARE_MIN_FREQ,
    DEFAULT_RARE_TOP_N,
    fixture_profile,
    profile_phrases_stream,
    write_profile_xlsx,
)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--fixture-only", action="store_true")
    p.add_argument("--min-freq", type=int, default=DEFAULT_MIN_FREQ)
    p.add_argument("--rare-min-freq", type=int, default=DEFAULT_RARE_MIN_FREQ)
    p.add_argument("--rare-top-n", type=int, default=DEFAULT_RARE_TOP_N)
    p.add_argument("--chunksize", type=int, default=200_000)
    p.add_argument("--max-rows", type=int, default=None)
    p.add_argument(
        "--year",
        type=int,
        default=None,
        help="Optional doc_id year substr filter (e.g. 1780)",
    )
    p.add_argument("--no-write", action="store_true")
    p.add_argument("--no-xlsx", action="store_true")
    p.add_argument(
        "--top-n-xlsx",
        type=int,
        default=200,
        help="Cap rows written to Excel skim sheets",
    )
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)
    if args.fixture_only:
        result = fixture_profile()
    else:
        path = resolve("phrases_5gram_18th")
        year_substr = str(args.year) if args.year is not None else None
        result = profile_phrases_stream(
            path,
            min_freq=args.min_freq,
            rare_min_freq=args.rare_min_freq,
            rare_top_n=args.rare_top_n,
            chunksize=args.chunksize,
            max_rows=args.max_rows,
            year_substr=year_substr,
        )

    metrics = result["metrics"]
    high = result["high_freq"]
    rare = result["rare_sidecar"]
    print(
        f"STEPT1aa: scanned={metrics.get('rows_scanned')} "
        f"n_high={metrics.get('n_high_freq')} "
        f"n_protected_below={metrics.get('n_protected_below_gate')} "
        f"n_sidecar={metrics.get('n_rare_sidecar')}"
    )

    if args.no_write:
        return

    save_semi_structured(
        [metrics],
        logical_name="phrases_5gram_profile_metrics",
        script=__file__,
        description="STEPT1aa phrases_5gram stream profile metrics",
    )
    save_semi_structured(
        high,
        logical_name="phrases_5gram_high_freq",
        script=__file__,
        description="STEPT1aa high-freq unique phrases (Pass A)",
    )
    save_semi_structured(
        rare,
        logical_name="phrases_5gram_rare_sidecar",
        script=__file__,
        description="STEPT1aa protected/rare sidecar",
    )
    if not args.no_xlsx:
        xlsx = Path(resolve("phrases_5gram_profile_metrics")).with_name(
            "phrases_5gram_profile.xlsx"
        )
        write_profile_xlsx(
            xlsx,
            high_freq=high,
            rare_sidecar=rare,
            metrics=metrics,
            top_n=args.top_n_xlsx,
        )
        print(f"wrote skim xlsx → {xlsx}")


if __name__ == "__main__":
    main()
