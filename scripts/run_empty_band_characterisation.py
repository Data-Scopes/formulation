#!/usr/bin/env python3
"""STEPT1j: characterise empty composition band (+ optional fp_cut sweep).

    uv run python scripts/run_empty_band_characterisation.py --fixture-only
    uv run python scripts/run_empty_band_characterisation.py --year 1780
    uv run python scripts/run_empty_band_characterisation.py --year 1780 --skip-fingerprint
"""

from __future__ import annotations

import argparse
import json
from typing import Any

from data_io import save_semi_structured
from formulation.content_fingerprint import ContentFingerprint, greedy_clusters, nearest_neighbor_sims
from formulation.empty_band import (
    DEFAULT_FP_CUTS,
    DEFAULT_OPERATING_FP_CUT,
    DEFAULT_SAMPLE_PER_STRATUM,
    DEFAULT_SAMPLE_SEED,
    DEFAULT_YEAR,
    build_empty_band_frame,
    draw_empty_sample,
    fixture_empty_frame,
    load_empty_universe,
    summarize_empty_band,
    sweep_fingerprint_cuts,
)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--fixture-only", action="store_true")
    p.add_argument("--year", type=int, default=DEFAULT_YEAR)
    p.add_argument("--skip-fingerprint", action="store_true")
    p.add_argument(
        "--fp-cuts",
        type=str,
        default=",".join(str(c) for c in DEFAULT_FP_CUTS),
        help="Comma-separated fp_cut values for the sweep",
    )
    p.add_argument(
        "--operating-fp-cut",
        type=float,
        default=DEFAULT_OPERATING_FP_CUT,
        help="Cut whose cluster labels are written to scores/sample",
    )
    p.add_argument("--no-flags", action="store_true")
    p.add_argument("--no-text-length", action="store_true")
    p.add_argument("--no-partition", action="store_true")
    p.add_argument("--no-sample", action="store_true")
    p.add_argument(
        "--sample-per-stratum",
        type=int,
        default=DEFAULT_SAMPLE_PER_STRATUM,
    )
    p.add_argument("--sample-seed", type=int, default=DEFAULT_SAMPLE_SEED)
    p.add_argument("--no-write", action="store_true")
    return p.parse_args(argv)


def _parse_cuts(raw: str) -> list[float]:
    parts = [p.strip() for p in raw.split(",") if p.strip()]
    return [float(p) for p in parts]


def _scores_rows(frame) -> list[dict[str, Any]]:
    keep = [
        "id",
        "year",
        "motif_class",
        "proposition_type",
        "n_words",
        "ontfangen_present",
        "is_l1",
        "is_r1",
        "is_advies_gold",
        "nn_sim",
        "fp_cluster_id",
        "fp_scored",
        "outcome_joined",
        "text_joined",
        "es_joined",
    ]
    cols = [c for c in keep if c in frame.columns]
    return frame[cols].to_dict(orient="records")


def _fixture_fingerprint(frame, args):
    """Sweep on fixture texts without parquet."""
    if args.skip_fingerprint:
        return frame, {"fingerprint_ran": False, "note": "skipped"}
    texts = frame["resolutions_text"].fillna("").astype(str).tolist()
    if sum(1 for t in texts if t.strip()) < 2:
        return frame, {"fingerprint_ran": False, "note": "too few texts"}
    cuts = _parse_cuts(args.fp_cuts)
    fp = ContentFingerprint().fit(texts)
    sim = fp.similarity_matrix(texts)
    nn = nearest_neighbor_sims(sim)
    by_cut = []
    operating = None
    for cut in cuts:
        labels = greedy_clusters(sim, cut=float(cut))
        counts = {}
        for lab in labels.tolist():
            counts[lab] = counts.get(lab, 0) + 1
        largest = max(counts.values()) if counts else 0
        by_cut.append(
            {
                "fp_cut": float(cut),
                "n_scored": len(labels),
                "n_clusters": len(counts),
                "n_singletons": sum(1 for c in counts.values() if c == 1),
                "share_largest_cluster": largest / len(labels) if len(labels) else None,
            }
        )
        if abs(float(cut) - float(args.operating_fp_cut)) < 1e-9:
            operating = labels
    if operating is None:
        operating = greedy_clusters(sim, cut=float(args.operating_fp_cut))
    out = frame.copy()
    out["nn_sim"] = nn
    out["fp_cluster_id"] = operating.astype(int)
    out["fp_scored"] = True
    out.attrs["flag_columns"] = list(frame.attrs.get("flag_columns") or [])
    meta = {
        "fingerprint_ran": True,
        "fp_cuts": cuts,
        "operating_fp_cut": float(args.operating_fp_cut),
        "by_cut": by_cut,
        "note": "fixture fingerprint sweep",
    }
    return out, meta


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    fp_meta: dict[str, Any] = {"fingerprint_ran": False}
    cuts = _parse_cuts(args.fp_cuts)

    if args.fixture_only:
        frame = fixture_empty_frame()
        year = int(frame["year"].iloc[0])
        frame, fp_meta = _fixture_fingerprint(frame, args)
        sample = frame.head(0)
        if not args.no_sample and not args.skip_fingerprint:
            sample = draw_empty_sample(
                frame,
                per_stratum=int(args.sample_per_stratum),
                seed=int(args.sample_seed),
            )
    else:
        year = int(args.year)
        empty = load_empty_universe(year=year)
        frame = build_empty_band_frame(
            empty,
            year=year,
            join_flags=not args.no_flags,
            join_text_length=not args.no_text_length,
            join_partition=not args.no_partition,
        )
        if args.skip_fingerprint:
            fp_meta = {"fingerprint_ran": False, "note": "skipped"}
        else:
            frame, fp_meta = sweep_fingerprint_cuts(
                frame,
                fp_cuts=cuts,
                operating_cut=float(args.operating_fp_cut),
                join_text=True,
            )
        if args.no_sample:
            sample = frame.head(0)
        else:
            sample = draw_empty_sample(
                frame,
                per_stratum=int(args.sample_per_stratum),
                seed=int(args.sample_seed),
            )

    metrics = summarize_empty_band(
        frame, year=year, fingerprint_meta=fp_meta
    )
    metrics["n_sample_rows"] = int(len(sample))
    print(json.dumps(metrics, indent=2, default=str))

    if args.no_write:
        return 0

    save_semi_structured(
        [metrics],
        logical_name="empty_band_metrics",
        script=__file__,
        description=(
            f"STEPT1j: empty-band type/length/flags + fp_cut sweep "
            f"(year={year}; fixture={args.fixture_only})"
        ),
    )
    save_semi_structured(
        _scores_rows(frame),
        logical_name="empty_band_scores",
        script=__file__,
        description=(
            f"STEPT1j: per-id empty characterisation "
            f"(year={year}; no full text)"
        ),
    )
    save_semi_structured(
        sample.to_dict(orient="records") if len(sample) else [],
        logical_name="empty_band_sample",
        script=__file__,
        description=(
            f"STEPT1j: stratified empty text sample "
            f"(year={year}; truncated; fixture={args.fixture_only})"
        ),
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
