#!/usr/bin/env python3
"""STEPT1i: composition unknown — graph patterns + fingerprints on undecided.

    uv run python scripts/run_composition_unknown.py --fixture-only
    uv run python scripts/run_composition_unknown.py --year 1780
    uv run python scripts/run_composition_unknown.py --year 1780 --skip-fingerprint
"""

from __future__ import annotations

import argparse
import json
from typing import Any

from data_io import save_semi_structured
from formulation.composition_unknown import (
    DEFAULT_EXEMPLAR_CAP,
    DEFAULT_FP_CUT,
    DEFAULT_MIN_SUPPORT,
    DEFAULT_SAMPLE_PER_STRATUM,
    DEFAULT_SAMPLE_SEED,
    DEFAULT_YEAR,
    attach_fingerprint_undecided,
    build_composition_frame,
    draw_undecided_sample,
    fixture_composition_frame,
    load_year_bags,
    summarize_composition_unknown,
)
def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--fixture-only", action="store_true")
    p.add_argument("--year", type=int, default=DEFAULT_YEAR)
    p.add_argument("--min-support", type=int, default=DEFAULT_MIN_SUPPORT)
    p.add_argument("--skip-fingerprint", action="store_true")
    p.add_argument("--fp-cut", type=float, default=DEFAULT_FP_CUT)
    p.add_argument("--exemplar-cap", type=int, default=DEFAULT_EXEMPLAR_CAP)
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
    keep = [
        "id",
        "year",
        "motif_class",
        "composition_unknown",
        "is_proto_blueprint",
        "bag_support",
        "core_support",
        "nn_sim",
        "derivative_score",
        "fp_cluster_id",
        "fp_scored",
        "present_bag",
        "accepted_core",
    ]
    cols = [c for c in keep if c in frame.columns]
    rows = frame[cols].copy()
    for col in ("present_bag", "accepted_core"):
        if col in rows.columns:
            rows[col] = rows[col].map(
                lambda b: list(b) if isinstance(b, (tuple, list)) else b
            )
    return rows.to_dict(orient="records")


def _fixture_with_optional_fp(frame, args):
    """Attach synthetic texts so fingerprint can smoke on fixture."""
    if args.skip_fingerprint:
        return frame, {"fingerprint_ran": False, "note": "skipped"}
    texts = {
        "r1": "ontfangen een missive van den raad",
        "r2": "ontfangen een missive van den raad",
        "r3": "is den selven verwelkomt en sessie genomen",
        "r4": "is den selven verwelkomt en sessie genomen heden",
        "r5": "is den selven verwelkomt en sessie genomen",
        "r6": "is den selven verwelkomt en sessie genomen",
        "r7": "is den selven verwelkomt en sessie genomen",
        "r8": "geleesen het advis van de raaden",
        "r9": "geleesen het advis van de raaden",
        "r10": "geleesen het advis van de raaden van state",
        "r11": "geleesen het advis van de raaden",
        "r12": "geleesen het advis van de raaden",
        "r13": "geheel andere tekst zonder bekende formules alpha",
        "r14": "geheel andere tekst zonder bekende formules beta",
        "r15": "is gelesen de requeste van den suppliant",
    }
    frame = frame.copy()
    frame["resolutions_text"] = frame["id"].map(texts).fillna("")
    frame["text_joined"] = True
    return attach_fingerprint_undecided(
        frame,
        fp_cut=float(args.fp_cut),
        exemplar_cap=int(args.exemplar_cap),
        join_text=False,
    )


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    fp_meta: dict[str, Any] = {"fingerprint_ran": False}

    if args.fixture_only:
        frame = fixture_composition_frame()
        year = int(frame["year"].iloc[0])
        frame, fp_meta = _fixture_with_optional_fp(frame, args)
        sample = frame.head(0)
        if not args.no_sample and not args.skip_fingerprint:
            sample = draw_undecided_sample(
                frame,
                per_stratum=int(args.sample_per_stratum),
                seed=int(args.sample_seed),
            )
    else:
        year = int(args.year)
        bags = load_year_bags(year=year)
        frame = build_composition_frame(
            bags, min_support=int(args.min_support)
        )
        if args.skip_fingerprint:
            fp_meta = {"fingerprint_ran": False, "note": "skipped"}
        else:
            frame, fp_meta = attach_fingerprint_undecided(
                frame,
                fp_cut=float(args.fp_cut),
                exemplar_cap=int(args.exemplar_cap),
                join_text=True,
            )
        if args.no_sample:
            sample = frame.head(0)
        else:
            sample = draw_undecided_sample(
                frame,
                per_stratum=int(args.sample_per_stratum),
                seed=int(args.sample_seed),
            )

    metrics = summarize_composition_unknown(
        frame,
        year=year,
        min_support=int(args.min_support),
        fingerprint_meta=fp_meta,
    )
    metrics["n_sample_rows"] = int(len(sample))
    print(json.dumps(metrics, indent=2, default=str))

    if args.no_write:
        return 0

    save_semi_structured(
        [metrics],
        logical_name="composition_unknown_metrics",
        script=__file__,
        description=(
            f"STEPT1i: proto-blueprints + derivatives + undecided "
            f"(year={year}; fixture={args.fixture_only})"
        ),
    )
    save_semi_structured(
        _scores_rows(frame),
        logical_name="composition_unknown_scores",
        script=__file__,
        description=(
            f"STEPT1i: per-id bag/core/motif (+ fingerprint fields) "
            f"(year={year}; no full text)"
        ),
    )
    save_semi_structured(
        sample.to_dict(orient="records") if len(sample) else [],
        logical_name="composition_unknown_sample",
        script=__file__,
        description=(
            f"STEPT1i: undecided stratified sample "
            f"(year={year}; truncated text; fixture={args.fixture_only})"
        ),
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
