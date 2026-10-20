#!/usr/bin/env python3
"""Score the unlabelled remainder into high / grey / low (STEPR3).

POC (``--poc``): harvest-cut metrics on the frozen STEPR2 holdout, then score
one year of remainder (default 1780) for volume and timing. Does not rewrite
``aanstelling_tfidf_metrics``.

Full run: refit the frozen architecture on all labelled rows and score every
non-gold row in ``resolutions_flat``.
"""

from __future__ import annotations

import argparse
import time
from typing import Any

from data_io import load, save_parquet, save_semi_structured
from formulation.aanstelling_harvest import (
    HIGH_CUT,
    LOGICAL_HARVEST,
    LOGICAL_HARVEST_POC,
    LOGICAL_POC_METRICS,
    LOW_CUT,
    POC_YEAR,
    drop_gold,
    gold_resolution_ids,
    harvest_holdout_metrics,
    load_resolutions_flat,
    remainder_bucket_counts,
    score_remainder,
)
from formulation.aanstelling_tfidf import fit_on_all_labelled


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--poc",
        action="store_true",
        help="Holdout harvest-cut metrics + one-year remainder (not the full table)",
    )
    parser.add_argument(
        "--year",
        type=int,
        default=None,
        help=f"POC remainder year (default {POC_YEAR}; requires --poc)",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Cap POC remainder rows after the year filter (requires --poc)",
    )
    return parser.parse_args(argv)


def _print_holdout_metrics(metrics: dict[str, Any]) -> None:
    print(
        f"holdout@0.5 recall {metrics['recall']:.6f} "
        f"precision {metrics['precision']:.6f} f1 {metrics['f1']:.6f} "
        f"(STEPR2 frozen; not rewritten)"
    )
    print(
        f"holdout@high>{metrics['high_cut']} "
        f"recall {metrics['high_recall']:.6f} "
        f"precision {metrics['high_precision']:.6f} "
        f"f1 {metrics['high_f1']:.6f}"
    )
    print(
        f"holdout@high_or_grey recall {metrics['high_or_grey_recall']:.6f} "
        f"precision {metrics['high_or_grey_precision']:.6f} "
        f"f1 {metrics['high_or_grey_f1']:.6f}"
    )
    print(
        "gold buckets high/grey/low "
        f"{metrics['n_gold_high']}/{metrics['n_gold_grey']}/{metrics['n_gold_low']} "
        f"of {metrics['n_test_aanstelling']}"
    )
    print(
        "overig buckets high/grey/low "
        f"{metrics['n_overig_high']}/{metrics['n_overig_grey']}/{metrics['n_overig_low']}"
    )


def _run_poc(args: argparse.Namespace) -> None:
    holdout = load("aanstelling_tfidf_holdout")
    labelled = load("aanstelling_labelled")
    metrics = harvest_holdout_metrics(holdout, high_cut=HIGH_CUT, low_cut=LOW_CUT)
    _print_holdout_metrics(metrics)

    year = POC_YEAR if args.year is None else args.year
    pipeline = fit_on_all_labelled(labelled)
    gold_ids = gold_resolution_ids(labelled)
    started = time.perf_counter()
    remainder = drop_gold(load_resolutions_flat(year=year, limit=args.limit), gold_ids)
    scored = score_remainder(remainder, pipeline)
    elapsed = time.perf_counter() - started
    counts = remainder_bucket_counts(scored)
    docs_per_s = counts["n_remainder"] / elapsed if elapsed else 0.0
    harvest_path = save_parquet(
        scored,
        logical_name=LOGICAL_HARVEST_POC,
        parent_sources=["resolutions_flat", "aanstelling_labelled"],
        script=__file__,
    )
    metrics.update(
        {
            "poc_year": int(year),
            "poc_limit": args.limit,
            "score_seconds": float(elapsed),
            "docs_per_s": float(docs_per_s),
            **counts,
        }
    )
    metrics_path = save_semi_structured(
        [metrics],
        logical_name=LOGICAL_POC_METRICS,
        parent_sources=["aanstelling_tfidf_holdout", LOGICAL_HARVEST_POC],
        script=__file__,
    )
    print(f"wrote {harvest_path}")
    print(f"wrote {metrics_path}")
    print(
        f"remainder year {year} n {counts['n_remainder']} "
        f"high/grey/low {counts['n_remainder_high']}/"
        f"{counts['n_remainder_grey']}/{counts['n_remainder_low']}"
    )
    print(f"scored {counts['n_remainder']} docs in {elapsed:.1f}s ({docs_per_s:.1f}/s)")
    if docs_per_s:
        est = 692156 / docs_per_s
        print(f"full-corpus estimate ~{est / 60:.0f} min at this rate (692156 rows)")


def _run_full() -> None:
    labelled = load("aanstelling_labelled")
    pipeline = fit_on_all_labelled(labelled)
    gold_ids = gold_resolution_ids(labelled)
    remainder = drop_gold(load("resolutions_flat"), gold_ids)
    started = time.perf_counter()
    scored = score_remainder(remainder, pipeline)
    elapsed = time.perf_counter() - started
    counts = remainder_bucket_counts(scored)
    path = save_parquet(
        scored,
        logical_name=LOGICAL_HARVEST,
        parent_sources=["resolutions_flat", "aanstelling_labelled"],
        script=__file__,
    )
    print(f"wrote {path}")
    print(
        f"remainder n {counts['n_remainder']} "
        f"high/grey/low {counts['n_remainder_high']}/"
        f"{counts['n_remainder_grey']}/{counts['n_remainder_low']}"
    )
    print(f"scored {counts['n_remainder']} docs in {elapsed:.1f}s")


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)
    if not args.poc and (args.year is not None or args.limit is not None):
        raise SystemExit("--year and --limit require --poc (will not overwrite the full harvest)")
    if args.poc:
        _run_poc(args)
        return
    _run_full()


if __name__ == "__main__":
    main()
