#!/usr/bin/env python3
"""STEPT1s: measure short requeste opener ``Op de Requeste`` (slot-cloud + DAG).

    uv run python scripts/eval_requeste_op_de_formula_type.py --fixture-only
    uv run python scripts/eval_requeste_op_de_formula_type.py
"""

from __future__ import annotations

import argparse
import json
from typing import Any

from data_io import save_semi_structured
from formulation.requeste_formula_type import load_rekest_gold_18c
from formulation.requeste_op_de_formula_type import (
    FALLBACK_CUT,
    HOLDOUT_FRAC,
    NEG_N,
    RNG,
    YEAR_MAX,
    YEAR_MIN,
    build_requeste_op_de_cloud,
    calibrate_cut,
    fixture_smoke_frames,
    load_long_head_rekest_sample,
    load_short_requeste_gold_18c,
    sample_negatives,
    score_frame,
    split_bootstrap_holdout,
    summarize_eval,
)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument(
        "--fixture-only",
        action="store_true",
        help="Tiny in-memory smoke (no ES / resolutions_flat)",
    )
    p.add_argument(
        "--neg-n",
        type=int,
        default=NEG_N,
        help=f"Negative sample size (default {NEG_N})",
    )
    p.add_argument(
        "--holdout-frac",
        type=float,
        default=HOLDOUT_FRAC,
        help=f"Holdout fraction of gold ids (default {HOLDOUT_FRAC})",
    )
    p.add_argument(
        "--random-state",
        type=int,
        default=RNG,
        help=f"RNG seed (default {RNG})",
    )
    p.add_argument(
        "--cut",
        type=float,
        default=None,
        help="Freeze operating cut; default = p20 of holdout positive scores",
    )
    p.add_argument(
        "--limit-gold",
        type=int,
        default=None,
        help="Optional cap on short-form gold rows (POC)",
    )
    return p.parse_args(argv)


def pd_concat_scores(
    gold: Any,
    neg: Any,
    *,
    cut: float,
    corpus_rate: float,
) -> list[dict[str, Any]]:
    import pandas as pd

    from formulation.appointment_formula_type import apply_popularity

    frames = []
    for frame in (gold, neg):
        f = frame.copy()
        f["pred"] = f["score"] >= float(cut)
        f["score_weighted"] = f["score"].map(
            lambda s: apply_popularity(float(s), corpus_rate)
        )
        if "resolutions_text" in f.columns:
            f = f.drop(columns=["resolutions_text"])
        frames.append(f)
    out = pd.concat(frames, ignore_index=True)
    return out.to_dict(orient="records")


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)

    n_rekest_total: int | None = None
    long_scored = None

    if args.fixture_only:
        gold, neg = fixture_smoke_frames()
        boot, hold = split_bootstrap_holdout(
            gold, holdout_frac=0.34, random_state=args.random_state
        )
        parents = None
    else:
        full = load_rekest_gold_18c()
        n_rekest_total = int(len(full))
        gold = load_short_requeste_gold_18c()
        if args.limit_gold is not None:
            gold = gold.head(int(args.limit_gold)).copy()
        boot, hold = split_bootstrap_holdout(
            gold,
            holdout_frac=float(args.holdout_frac),
            random_state=int(args.random_state),
        )
        # Exclude *full* ES rekest (long + short) from negatives.
        exclude = set(full["id"].astype(str)) | set(boot["id"].astype(str))
        neg = sample_negatives(
            exclude_ids=exclude,
            n=int(args.neg_n),
            random_state=int(args.random_state),
            year_min=YEAR_MIN,
            year_max=YEAR_MAX,
        )
        parents = ["rekest_es_gold", "resolutions_flat"]

    boot_texts = boot["resolutions_text"].astype(str).tolist()
    cloud, cloud_notes = build_requeste_op_de_cloud(boot_texts)

    gold_scored = score_frame(gold, cloud, role="gold")
    hold_scored = score_frame(hold, cloud, role="holdout")
    neg_scored = score_frame(neg, cloud, role="negative")

    if not args.fixture_only:
        long_sample = load_long_head_rekest_sample(
            exclude_ids=set(gold["id"].astype(str)),
            random_state=int(args.random_state),
        )
        if len(long_sample):
            long_scored = score_frame(long_sample, cloud, role="long_head_rekest")

    if args.cut is not None:
        cut = float(args.cut)
        cut_rule = "cli"
    else:
        cut = calibrate_cut(hold_scored["score"].tolist(), fallback=FALLBACK_CUT)
        cut_rule = "p20_holdout_positive_scores"

    metrics = summarize_eval(
        gold_scored,
        neg_scored,
        cut=cut,
        cloud_notes=cloud_notes,
        bootstrap_ids=boot["id"].astype(str).tolist(),
        holdout_ids=hold["id"].astype(str).tolist(),
        random_state=int(args.random_state),
        long_head_scored=long_scored,
        n_rekest_total=n_rekest_total,
    )
    metrics["operating_cut_rule"] = cut_rule
    metrics["fixture_only"] = bool(args.fixture_only)
    metrics["holdout_score_mean"] = (
        round(float(hold_scored["score"].mean()), 4) if len(hold_scored) else None
    )
    n_accepted = cloud_notes.get("n_hits_accepted") if cloud_notes else None
    metrics["pass_cloud_accepts_gt_0"] = bool(n_accepted and int(n_accepted) > 0)

    corpus_rate = float((metrics.get("popularity") or {}).get("corpus_rate_proxy") or 0.0)
    score_rows = pd_concat_scores(
        gold_scored, neg_scored, cut=cut, corpus_rate=corpus_rate
    )

    save_semi_structured(
        [metrics],
        logical_name="formula_type_requeste_op_de_metrics",
        script=__file__,
        description="STEPT1s short requeste opener (Op de Requeste) formula-type eval",
        parent_sources=parents,
    )
    save_semi_structured(
        score_rows,
        logical_name="formula_type_requeste_op_de_scores",
        script=__file__,
        description="STEPT1s per-id align scores (short-form rekest gold + negatives)",
        parent_sources=parents,
    )

    print(json.dumps(metrics, indent=2, ensure_ascii=False, default=str))
    print(
        f"wrote formula_type_requeste_op_de_metrics / "
        f"formula_type_requeste_op_de_scores ({len(score_rows)} score rows)"
    )


if __name__ == "__main__":
    main()
