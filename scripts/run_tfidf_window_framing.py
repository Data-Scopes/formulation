#!/usr/bin/env python3
"""STEPS1: char_wb TF-IDF window framing on fixtures or a year slice.

Does not run Smith-Waterman / DAG (STEPS0 scaffold; STEPS2–3) or GysBERT.
"""

from __future__ import annotations

import argparse
from typing import Any

import pandas as pd

from data_io import load, save_semi_structured
from formulation.boundary.tfidf_windows import (
    POC_YEAR,
    STRIDE,
    WINDOW_SIZE,
    ALIGN_PAD,
    candidates_records,
    default_framing_threshold,
    default_opening_template,
    frame_documents,
    load_resolution_slice,
)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--fixture-only",
        action="store_true",
        help="Score STEPS0 fixture OCR strings only (no resolutions_flat)",
    )
    parser.add_argument(
        "--year",
        type=int,
        default=None,
        help=f"resolutions_flat year slice (default {POC_YEAR} unless --fixture-only)",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Cap resolutions after the year filter (POC)",
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=None,
        help="Cosine cut (default: formula_templates framing threshold)",
    )
    parser.add_argument("--window-size", type=int, default=WINDOW_SIZE)
    parser.add_argument("--stride", type=int, default=STRIDE)
    parser.add_argument("--align-pad", type=int, default=ALIGN_PAD)
    return parser.parse_args(argv)


def _fixture_frame(cases: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for row in cases.to_dict(orient="records"):
        rows.append(
            {
                "id": str(row["case_id"]),
                "resolutions_text": " ".join(row["ocr_tokens"]),
            }
        )
    return pd.DataFrame(rows)


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)
    template_id, template_tokens = default_opening_template()
    threshold = (
        float(args.threshold)
        if args.threshold is not None
        else default_framing_threshold()
    )

    if args.fixture_only:
        if args.year is not None or args.limit is not None:
            raise SystemExit("--year / --limit require a resolutions_flat slice")
        cases = load("formula_boundary_cases")
        case_rows = cases if isinstance(cases, pd.DataFrame) else pd.DataFrame(cases)
        frame = _fixture_frame(case_rows)
        parent_sources = ["formula_boundary_cases"]
        slice_note = "fixture_only"
    else:
        year = POC_YEAR if args.year is None else int(args.year)
        frame = load_resolution_slice(year=year, limit=args.limit)
        parent_sources = ["resolutions_flat"]
        slice_note = f"year={year}" + (f" limit={args.limit}" if args.limit else "")

    _scored, candidates, notes = frame_documents(
        frame,
        template_tokens,
        template_id=template_id,
        window_size=args.window_size,
        stride=args.stride,
        threshold=threshold,
        align_pad=args.align_pad,
    )
    notes["slice"] = slice_note
    notes["n_candidates"] = int(len(candidates))

    windows_path = save_semi_structured(
        candidates_records(candidates),
        logical_name="formula_tfidf_windows",
        parent_sources=parent_sources,
        script=__file__,
    )
    metrics_path = save_semi_structured(
        [notes],
        logical_name="formula_tfidf_window_metrics",
        parent_sources=parent_sources + ["formula_tfidf_windows"],
        script=__file__,
    )
    print(f"wrote {windows_path}")
    print(f"wrote {metrics_path}")
    print(
        f"slice {slice_note} docs {notes['n_docs']} windows {notes['n_windows']} "
        f"candidates {notes['n_candidates']} threshold {notes['threshold']} "
        f"(hypothesis={notes['threshold_is_hypothesis']})"
    )
    print(
        f"score min/mean/max "
        f"{notes['score_min']:.4f}/{notes['score_mean']:.4f}/{notes['score_max']:.4f} "
        f"p95 {notes.get('p95')}"
    )


if __name__ == "__main__":
    main()
