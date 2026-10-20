#!/usr/bin/env python3
"""STEPS3: provenanced SW/DAG spans on STEPS1 windows + STEPS2 slot-cloud.

Does not calibrate STEPS1 cosine thresholds or run GysBERT (STEPS4).
"""

from __future__ import annotations

import argparse
from typing import Any

from data_io import load, save_semi_structured
from formulation.boundary.slot_cloud import (
    bootstrap_slot_cloud,
    default_template,
    fixture_hit_texts,
    hit_texts_from_windows,
)
from formulation.boundary.span_harvest import (
    fixture_windows,
    harvest_spans,
    normalize_cloud,
    windows_from_records,
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
        help="Harvest on built-in 18c seeds (incl. shortened); cloud from fixtures",
    )
    src.add_argument(
        "--from-windows",
        action="store_true",
        help="Load formula_tfidf_windows + formula_slot_cloud",
    )
    parser.add_argument(
        "--year",
        type=int,
        default=None,
        help=f"Frame resolutions_flat year then harvest (default {POC_YEAR})",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Cap resolutions when framing a year slice (POC)",
    )
    parser.add_argument(
        "--cloud-from-fixtures",
        action="store_true",
        help="With --from-windows / --year: rebuild cloud from hits instead of load",
    )
    return parser.parse_args(argv)


def _load_or_bootstrap_cloud(
    *,
    hit_texts: list[str] | None,
    force_bootstrap: bool,
) -> tuple[dict[str, Any], list[str] | None]:
    """Prefer registered formula_slot_cloud unless forced or missing."""
    if not force_bootstrap:
        try:
            loaded = load("formula_slot_cloud")
            return normalize_cloud(loaded), ["formula_slot_cloud"]
        except (FileNotFoundError, ValueError, KeyError):
            pass
    if not hit_texts:
        raise SystemExit(
            "No formula_slot_cloud and no hit texts to bootstrap; "
            "run STEPS2 or pass --fixture-only"
        )
    template_id, template_tokens = default_template()
    cloud, _notes = bootstrap_slot_cloud(
        hit_texts,
        template_tokens,
        template_id=template_id,
        period="18c",
    )
    return cloud, None


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)
    parent_sources: list[str] = []
    slice_note: str

    if args.fixture_only:
        if args.year is not None or args.limit is not None:
            raise SystemExit("--year / --limit require a resolutions_flat slice")
        windows = fixture_windows()
        cloud, cloud_parents = _load_or_bootstrap_cloud(
            hit_texts=fixture_hit_texts(),
            force_bootstrap=True,
        )
        if cloud_parents:
            parent_sources.extend(cloud_parents)
        slice_note = "fixture_only"
    elif args.from_windows:
        windows_raw = load("formula_tfidf_windows")
        windows = windows_from_records(windows_raw)
        parent_sources.append("formula_tfidf_windows")
        hit_texts = hit_texts_from_windows(windows_raw)
        cloud, cloud_parents = _load_or_bootstrap_cloud(
            hit_texts=hit_texts,
            force_bootstrap=args.cloud_from_fixtures,
        )
        if cloud_parents:
            parent_sources.extend(cloud_parents)
        slice_note = "from_windows"
    else:
        year = POC_YEAR if args.year is None else int(args.year)
        template_id, template_tokens = default_template()
        frame = load_resolution_slice(year=year, limit=args.limit)
        _scored, candidates, _notes = frame_documents(
            frame, template_tokens, template_id=template_id
        )
        windows = windows_from_records(candidates)
        parent_sources.append("resolutions_flat")
        hit_texts = hit_texts_from_windows(candidates)
        cloud, cloud_parents = _load_or_bootstrap_cloud(
            hit_texts=hit_texts,
            force_bootstrap=args.cloud_from_fixtures,
        )
        if cloud_parents:
            parent_sources.extend(cloud_parents)
        slice_note = f"year={year}" + (f" limit={args.limit}" if args.limit else "")

    spans, notes = harvest_spans(windows, cloud)
    notes["slice"] = slice_note

    spans_path = save_semi_structured(
        spans,
        logical_name="formula_boundary_spans",
        parent_sources=parent_sources or None,
        script=__file__,
    )
    metrics_path = save_semi_structured(
        [notes],
        logical_name="formula_boundary_span_metrics",
        parent_sources=["formula_boundary_spans"],
        script=__file__,
    )
    print(f"wrote {spans_path}")
    print(f"wrote {metrics_path}")
    agree = notes.get("sw_cloud_dag_span_agreement") or {}
    print(
        f"slice {slice_note} windows {notes['n_windows']} "
        f"span_rows {notes['n_span_rows']} "
        f"cloud↔dag agree {agree.get('rate')}"
    )
    for method, entry in (notes.get("per_method") or {}).items():
        print(
            f"  {method}: n={entry.get('n_rows')} "
            f"score_mean={entry.get('score_mean')} "
            f"ms_mean={entry.get('latency_ms_mean')} "
            f"empty={entry.get('n_empty_span')}"
        )


if __name__ == "__main__":
    main()
