#!/usr/bin/env python3
"""STEPT1e: ontfangen± partition probe (ES types + flags + known sets).

    uv run python scripts/run_ontfangen_partition_probe.py --fixture-only
    uv run python scripts/run_ontfangen_partition_probe.py --year 1780
"""

from __future__ import annotations

import argparse
import json
from typing import Any

from data_io import save_semi_structured
from formulation.ontfangen_partition import (
    DEFAULT_YEAR,
    build_partition_frame,
    fetch_es_metadata,
    fixture_partition_frame,
    load_known_id_sets,
    load_presence_universe,
    summarize_partition,
)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument(
        "--fixture-only",
        action="store_true",
        help="Tiny in-memory smoke (no ES / no presence parquet)",
    )
    p.add_argument(
        "--year",
        type=int,
        default=DEFAULT_YEAR,
        help=f"Calendar year (default {DEFAULT_YEAR})",
    )
    p.add_argument(
        "--no-flags",
        action="store_true",
        help="Skip formula_documents join (ES types + known sets only)",
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
        "ontfangen_present",
        "proposition_type",
        "session_date",
        "is_r1",
        "is_l1",
        "is_advies_gold",
        "residual_not_l1",
        "es_joined",
        "outcome_joined",
    ]
    cols = [c for c in keep if c in frame.columns]
    return frame[cols].to_dict(orient="records")


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if args.fixture_only:
        frame = fixture_partition_frame()
        known = {
            "aanstelling_selected": {"session-3835-num-1-resolution-2"},
            "missive_receipt": {"session-3835-num-1-resolution-1"},
            "advies_es_gold": {"session-3835-num-1-resolution-3"},
        }
        year = int(frame["year"].iloc[0])
    else:
        year = int(args.year)
        universe = load_presence_universe(year=year)
        known = load_known_id_sets(year=year)
        es_meta = fetch_es_metadata(universe["id"].astype(str).tolist())
        frame = build_partition_frame(
            universe,
            known=known,
            es_meta=es_meta,
            join_flags=not args.no_flags,
        )

    metrics = summarize_partition(frame, year=year, known=known)
    print(json.dumps(metrics, indent=2, default=str))

    if args.no_write:
        return 0

    save_semi_structured(
        [metrics],
        logical_name="ontfangen_partition_metrics",
        script=__file__,
        description=(
            f"STEPT1e: ontfangen± ES type mix + flags + known sets "
            f"(year={year}; fixture={args.fixture_only})"
        ),
    )
    save_semi_structured(
        _scores_rows(frame),
        logical_name="ontfangen_partition_scores",
        script=__file__,
        description=(
            f"STEPT1e: per-id ontfangen partition tags + ES type "
            f"(year={year}; no full text)"
        ),
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
