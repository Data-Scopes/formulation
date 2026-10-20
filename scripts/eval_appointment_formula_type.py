#!/usr/bin/env python3
"""STEPT1a: measure appointment formula-type (slot-cloud + DAG) vs wording baselines.

    uv run python scripts/eval_appointment_formula_type.py
    uv run python scripts/eval_appointment_formula_type.py --fixture-only
"""

from __future__ import annotations

import argparse
import json
from typing import Any

from data_io import save_semi_structured
from formulation.appointment_formula_type import (
    FALLBACK_CUT,
    HOLDOUT_FRAC,
    NEG_N,
    RNG,
    YEAR_MAX,
    YEAR_MIN,
    build_appointment_clouds,
    calibrate_cut,
    fixture_smoke_frames,
    load_selected_18c,
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
        help="Tiny in-memory smoke (no resolutions_flat / selected join)",
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
        help="Optional cap on 18c gold rows (POC)",
    )
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)

    if args.fixture_only:
        gold, neg = fixture_smoke_frames()
        boot, hold = split_bootstrap_holdout(
            gold, holdout_frac=0.34, random_state=args.random_state
        )
        exclude = set(gold["id"].astype(str))
    else:
        gold = load_selected_18c()
        if args.limit_gold is not None:
            gold = gold.head(int(args.limit_gold)).copy()
        boot, hold = split_bootstrap_holdout(
            gold,
            holdout_frac=float(args.holdout_frac),
            random_state=int(args.random_state),
        )
        exclude = set(gold["id"].astype(str)) | set(boot["id"].astype(str))
        neg = sample_negatives(
            exclude_ids=exclude,
            n=int(args.neg_n),
            random_state=int(args.random_state),
            year_min=YEAR_MIN,
            year_max=YEAR_MAX,
        )

    boot_texts = boot["resolutions_text"].astype(str).tolist()
    welkom_cloud, sessie_cloud, cloud_notes = build_appointment_clouds(boot_texts)

    gold_scored = score_frame(gold, welkom_cloud, sessie_cloud, role="gold")
    hold_scored = score_frame(hold, welkom_cloud, sessie_cloud, role="holdout")
    neg_scored = score_frame(neg, welkom_cloud, sessie_cloud, role="negative")

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
    )
    metrics["operating_cut_rule"] = cut_rule
    metrics["fixture_only"] = bool(args.fixture_only)
    metrics["holdout_score_mean"] = (
        round(float(hold_scored["score"].mean()), 4) if len(hold_scored) else None
    )

    corpus_rate = float((metrics.get("popularity") or {}).get("corpus_rate_proxy") or 0.0)
    score_rows = pd_concat_scores(
        gold_scored, neg_scored, cut=cut, corpus_rate=corpus_rate
    )

    parents = None if args.fixture_only else ["aanstelling_selected", "resolutions_flat"]
    save_semi_structured(
        [metrics],
        logical_name="formula_type_appointment_metrics",
        script=__file__,
        description="STEPT1a appointment formula-type eval metrics",
        parent_sources=parents,
    )
    save_semi_structured(
        score_rows,
        logical_name="formula_type_appointment_scores",
        script=__file__,
        description="STEPT1a per-id align scores (gold + negatives)",
        parent_sources=parents,
    )

    print(json.dumps(metrics, indent=2, ensure_ascii=False, default=str))
    print(
        f"wrote formula_type_appointment_metrics / "
        f"formula_type_appointment_scores ({len(score_rows)} score rows)"
    )


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
        # Drop bulky text from provenanced scores (keep id/year/scores/flags).
        if "resolutions_text" in f.columns:
            f = f.drop(columns=["resolutions_text"])
        frames.append(f)
    out = pd.concat(frames, ignore_index=True)
    return out.to_dict(orient="records")


if __name__ == "__main__":
    main()
