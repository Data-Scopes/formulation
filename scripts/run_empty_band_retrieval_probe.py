#!/usr/bin/env python3
"""STEPT1j2: score empty band with frozen R1 harvest + refit L1 TF-IDF+LR.

    uv run python scripts/run_empty_band_retrieval_probe.py --fixture-only
    uv run python scripts/run_empty_band_retrieval_probe.py --year 1780
    uv run python scripts/run_empty_band_retrieval_probe.py --year 1780 --skip-l1
"""

from __future__ import annotations

import argparse
import json
from typing import Any

from data_io import save_semi_structured
from formulation.empty_band_retrieval import (
    DEFAULT_YEAR,
    build_retrieval_frame,
    fixture_retrieval_frame,
    summarize_empty_retrieval,
)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--fixture-only", action="store_true")
    p.add_argument("--year", type=int, default=DEFAULT_YEAR)
    p.add_argument("--skip-l1", action="store_true", help="R1 harvest join only")
    p.add_argument("--no-write", action="store_true")
    return p.parse_args(argv)


def _scores_rows(frame) -> list[dict[str, Any]]:
    keep = [
        "id",
        "year",
        "motif_class",
        "proposition_type",
        "proba_r1",
        "bucket_r1",
        "r1_joined",
        "proba_l1",
        "bucket_l1",
        "l1_scored",
    ]
    cols = [c for c in keep if c in frame.columns]
    return frame[cols].to_dict(orient="records")


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if args.fixture_only:
        frame = fixture_retrieval_frame()
        year = int(frame["year"].iloc[0])
    else:
        year = int(args.year)
        frame = build_retrieval_frame(
            year=year,
            score_l1=not args.skip_l1,
            join_partition=True,
        )

    metrics = summarize_empty_retrieval(frame, year=year)
    print(json.dumps(metrics, indent=2, default=str))

    if args.no_write:
        return 0

    save_semi_structured(
        [metrics],
        logical_name="empty_band_retrieval_metrics",
        script=__file__,
        description=(
            f"STEPT1j2: empty-band R1/L1 P-bands × ES type "
            f"(year={year}; fixture={args.fixture_only})"
        ),
    )
    save_semi_structured(
        _scores_rows(frame),
        logical_name="empty_band_retrieval_scores",
        script=__file__,
        description=(
            f"STEPT1j2: per-id empty R1/L1 proba+bucket "
            f"(year={year}; no full text)"
        ),
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
