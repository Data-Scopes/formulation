#!/usr/bin/env python3
"""STEPS2: bootstrap a slot-cloud from TF-IDF hit windows (SW aggregate, no MSA).

Does not run DAG span harvest (STEPS3) or GysBERT. Does not calibrate STEPS1
cosine thresholds.
"""

from __future__ import annotations

import argparse
from typing import Any

from data_io import load, save_semi_structured
from formulation.boundary.slot_cloud import (
    OPTIONAL_SKIP_RATE,
    MIN_MATCHED_SLOT_RATIO,
    bootstrap_slot_cloud,
    default_template,
    fixture_hit_texts,
    hit_texts_from_windows,
)
from formulation.boundary.tfidf_windows import (
    POC_YEAR,
    frame_documents,
    load_resolution_slice,
)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    src = parser.add_mutually_exclusive_group()
    src.add_argument(
        "--fixture-only",
        action="store_true",
        help="Bootstrap from built-in 18c OCR-noise seeds (no resolutions_flat)",
    )
    src.add_argument(
        "--from-windows",
        action="store_true",
        help="Load STEPS1 formula_tfidf_windows candidates",
    )
    parser.add_argument(
        "--year",
        type=int,
        default=None,
        help=f"Frame resolutions_flat year then bootstrap (default {POC_YEAR})",
    )
    parser.add_argument(
        "--year-min",
        type=int,
        default=None,
        help="Period metadata / optional lower year bound for --year slice",
    )
    parser.add_argument(
        "--year-max",
        type=int,
        default=None,
        help="Period metadata / optional upper year bound for --year slice",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Cap resolutions when framing a year slice (POC)",
    )
    parser.add_argument(
        "--period",
        type=str,
        default="18c",
        help="Period label recorded on the cloud (17c deferred)",
    )
    parser.add_argument(
        "--optional-skip-rate",
        type=float,
        default=OPTIONAL_SKIP_RATE,
        help=f"Hypothesis skip rate for optional slots (default {OPTIONAL_SKIP_RATE})",
    )
    parser.add_argument(
        "--min-matched-ratio",
        type=float,
        default=MIN_MATCHED_SLOT_RATIO,
        help=f"Min matched-slot ratio to accept a hit (default {MIN_MATCHED_SLOT_RATIO})",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)
    template_id, template_tokens = default_template()

    year_min = args.year_min
    year_max = args.year_max
    parent_sources: list[str] | None
    slice_note: str

    if args.fixture_only:
        if args.year is not None or args.limit is not None:
            raise SystemExit("--year / --limit require a resolutions_flat slice")
        hit_texts = fixture_hit_texts()
        parent_sources = None
        slice_note = "fixture_only"
    elif args.from_windows:
        windows = load("formula_tfidf_windows")
        hit_texts = hit_texts_from_windows(windows)
        parent_sources = ["formula_tfidf_windows"]
        slice_note = "from_windows"
    else:
        year = POC_YEAR if args.year is None else int(args.year)
        if year_min is None:
            year_min = year
        if year_max is None:
            year_max = year
        if year_min is not None and year_max is not None and year_min > year_max:
            raise SystemExit("--year-min must be <= --year-max")
        # Single-year framing; period is metadata + year choice (multi-year join later).
        frame = load_resolution_slice(year=year, limit=args.limit)
        _scored, candidates, _notes = frame_documents(
            frame, template_tokens, template_id=template_id
        )
        hit_texts = hit_texts_from_windows(candidates)
        parent_sources = ["resolutions_flat"]
        slice_note = f"year={year}" + (f" limit={args.limit}" if args.limit else "")

    cloud, notes = bootstrap_slot_cloud(
        hit_texts,
        template_tokens,
        template_id=template_id,
        period=args.period,
        year_min=year_min,
        year_max=year_max,
        optional_skip_rate=args.optional_skip_rate,
        min_matched_ratio=args.min_matched_ratio,
    )
    notes["slice"] = slice_note

    cloud_path = save_semi_structured(
        [cloud],
        logical_name="formula_slot_cloud",
        parent_sources=parent_sources,
        script=__file__,
    )
    metrics_path = save_semi_structured(
        [notes],
        logical_name="formula_slot_cloud_metrics",
        parent_sources=["formula_slot_cloud"],
        script=__file__,
    )
    print(f"wrote {cloud_path}")
    print(f"wrote {metrics_path}")
    print(
        f"slice {slice_note} hits_in {notes['n_hits_in']} "
        f"accepted {notes['n_hits_accepted']} rejected {notes['n_hits_rejected']} "
        f"optional_slots {notes['optional_slots']}"
    )
    _print_slot_summary(cloud)


def _print_slot_summary(cloud: dict[str, Any]) -> None:
    for slot in cloud.get("slots") or []:
        top = ", ".join(
            f"{v['token']}×{v['count']}" for v in (slot.get("variants") or [])[:4]
        )
        opt = " optional" if slot.get("optional") else ""
        print(f"  slot {slot['index']} {slot['canonical']}{opt}: {top}")


if __name__ == "__main__":
    main()
