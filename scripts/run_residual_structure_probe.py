#!/usr/bin/env python3
"""STEPT1g: decisionful residual structure probe (ontfangen+ \\ L1).

    uv run python scripts/run_residual_structure_probe.py --fixture-only
    uv run python scripts/run_residual_structure_probe.py --year 1780
"""

from __future__ import annotations

import argparse
import json
from typing import Any

from data_io import save_semi_structured
from formulation.residual_structure import (
    DEFAULT_SAMPLE_PER_STRATUM,
    DEFAULT_SAMPLE_SEED,
    DEFAULT_YEAR,
    build_residual_frame,
    draw_stratified_sample,
    fixture_residual_frame,
    load_residual_universe,
    summarize_residual_structure,
)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--fixture-only", action="store_true")
    p.add_argument("--year", type=int, default=DEFAULT_YEAR)
    p.add_argument("--no-flags", action="store_true")
    p.add_argument("--no-text-length", action="store_true")
    p.add_argument("--no-presence", action="store_true")
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
    residual = frame.loc[
        frame["residual_not_l1"]
        & (frame["proposition_type"].astype(str) == "missive")
    ]
    keep = [
        "id",
        "year",
        "proposition_type",
        "n_words",
        "is_r1",
        "appointment_present",
        "advies_present",
        "present_bag",
        "outcome_joined",
        "text_joined",
    ]
    cols = [c for c in keep if c in residual.columns]
    rows = residual[cols].copy()
    if "present_bag" in rows.columns:
        rows["present_bag"] = rows["present_bag"].map(
            lambda b: list(b) if isinstance(b, (tuple, list)) else b
        )
    return rows.to_dict(orient="records")


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if args.fixture_only:
        frame = fixture_residual_frame()
        year = int(frame["year"].iloc[0])
        sample = frame.head(0)
    else:
        year = int(args.year)
        universe = load_residual_universe(year=year)
        frame = build_residual_frame(
            universe,
            year=year,
            join_flags=not args.no_flags,
            join_text_length=not args.no_text_length,
            join_presence=not args.no_presence,
        )
        residual = frame.loc[
            frame["residual_not_l1"]
            & (frame["proposition_type"].astype(str) == "missive")
        ]
        if args.no_sample:
            sample = residual.head(0)
        else:
            sample = draw_stratified_sample(
                residual,
                per_stratum=int(args.sample_per_stratum),
                seed=int(args.sample_seed),
            )

    metrics = summarize_residual_structure(frame, year=year)
    metrics["n_sample_rows"] = int(len(sample))
    print(json.dumps(metrics, indent=2, default=str))

    if args.no_write:
        return 0

    save_semi_structured(
        [metrics],
        logical_name="residual_structure_metrics",
        script=__file__,
        description=(
            f"STEPT1g: residual structure pockets + combo catalogue + bags "
            f"(year={year}; fixture={args.fixture_only})"
        ),
    )
    save_semi_structured(
        _scores_rows(frame),
        logical_name="residual_structure_scores",
        script=__file__,
        description=(
            f"STEPT1g: per-id missive residual tags + pockets "
            f"(year={year}; no full text)"
        ),
    )
    if not args.fixture_only and not args.no_sample:
        save_semi_structured(
            sample.to_dict(orient="records"),
            logical_name="residual_structure_sample",
            script=__file__,
            description=(
                f"STEPT1g: stratified residual text sample for NOTES reading "
                f"(year={year}; truncated text)"
            ),
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
