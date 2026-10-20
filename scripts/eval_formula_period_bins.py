#!/usr/bin/env python3
"""STEPT1-period: measure family × 25y bins + cross-bin recalibration.

    # Appointment gold (aanstelling_selected), all 25y bins
    uv run python scripts/eval_formula_period_bins.py --family appointment

    # Independent opening sub-templates (capped candidates per bin)
    uv run python scripts/eval_formula_period_bins.py --family ontfangen_start
    uv run python scripts/eval_formula_period_bins.py --family requeste_start

    # Both openings + appointment
    uv run python scripts/eval_formula_period_bins.py --family all

    uv run python scripts/eval_formula_period_bins.py --fixture-only
"""

from __future__ import annotations

import argparse
import json
from typing import Any

from data_io import save_semi_structured
from formulation.appointment_formula_type import FORMULA_TYPE_ID as APPOINTMENT_ID
from formulation.formula_period_bins import (
    CANDIDATE_CAP_PER_BIN,
    MIN_BIN_N,
    OPENING_FAMILIES,
    RNG,
    evaluate_family,
    fixture_appointment_bins,
)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    families = ("appointment", "all", *sorted(OPENING_FAMILIES))
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument(
        "--family",
        choices=families,
        default="appointment",
        help="Formula family row (default appointment); all = appointment + openings",
    )
    p.add_argument(
        "--fixture-only",
        action="store_true",
        help="Synthetic appointment bins only (no resolutions_flat)",
    )
    p.add_argument("--min-bin-n", type=int, default=MIN_BIN_N)
    p.add_argument("--candidate-cap", type=int, default=CANDIDATE_CAP_PER_BIN)
    p.add_argument("--random-state", type=int, default=RNG)
    return p.parse_args(argv)


def _families(args: argparse.Namespace) -> list[str]:
    if args.fixture_only:
        return [APPOINTMENT_ID]
    if args.family == "all":
        return [APPOINTMENT_ID, *sorted(OPENING_FAMILIES)]
    if args.family == "appointment":
        return [APPOINTMENT_ID]
    return [args.family]


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)
    summaries: list[dict[str, Any]] = []
    matrix_rows: list[dict[str, Any]] = []

    for fam in _families(args):
        fixture = fixture_appointment_bins() if args.fixture_only else None
        if args.fixture_only and fam != APPOINTMENT_ID:
            continue
        summary, matrix = evaluate_family(
            fam,
            min_bin_n=int(args.min_bin_n) if not args.fixture_only else 30,
            candidate_cap=int(args.candidate_cap),
            random_state=int(args.random_state),
            fixture_frames=fixture,
        )
        summary["fixture_only"] = bool(args.fixture_only)
        summaries.append(summary)
        matrix_rows.extend(matrix)
        print(json.dumps(summary, indent=2, ensure_ascii=False, default=str))

    parents = (
        None
        if args.fixture_only
        else ["aanstelling_selected", "resolutions_flat", "formula_documents"]
    )
    save_semi_structured(
        summaries,
        logical_name="formula_period_bin_metrics",
        script=__file__,
        description="STEPT1-period: per-family 25y bin eval summaries",
        parent_sources=parents,
    )
    save_semi_structured(
        matrix_rows,
        logical_name="formula_period_bin_matrix",
        script=__file__,
        description="STEPT1-period: cross-bin recall matrix rows",
        parent_sources=parents,
    )
    print(
        f"wrote formula_period_bin_metrics ({len(summaries)} families) / "
        f"formula_period_bin_matrix ({len(matrix_rows)} cells)"
    )


if __name__ == "__main__":
    main()
