#!/usr/bin/env python3
"""STEPT1a2: measure advies formula-type (slot-cloud + DAG) vs wording baseline.

    uv run python scripts/eval_advies_formula_type.py --refresh-gold
    uv run python scripts/eval_advies_formula_type.py
    uv run python scripts/eval_advies_formula_type.py --fixture-only
"""

from __future__ import annotations

import argparse
import json
from typing import Any

from data_io import save_semi_structured
from formulation.advies_formula_type import (
    FALLBACK_CUT,
    HOLDOUT_FRAC,
    NEG_N,
    RNG,
    YEAR_MAX,
    YEAR_MIN,
    build_advies_cloud,
    calibrate_cut,
    fixture_smoke_frames,
    load_advies_gold_18c,
    refresh_advies_es_gold,
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
        "--refresh-gold",
        action="store_true",
        help="Re-fetch ES proposition_type=advies and rewrite advies_es_gold",
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

    if args.fixture_only:
        gold, neg = fixture_smoke_frames()
        boot, hold = split_bootstrap_holdout(
            gold, holdout_frac=0.34, random_state=args.random_state
        )
        exclude = set(gold["id"].astype(str))
        parents = None
    else:
        if args.refresh_gold:
            gold = refresh_advies_es_gold(year_min=YEAR_MIN, year_max=YEAR_MAX)
            # Scores store without text; gold keeps text for eval then we
            # also persist a lean gold table (id/year/text for re-runs).
            gold_rows = gold.to_dict(orient="records")
            save_semi_structured(
                gold_rows,
                logical_name="advies_es_gold",
                script=__file__,
                description=(
                    "STEPT1a2: ES proposition_type=advies ids + resolutions_flat "
                    "text (1705–1796)"
                ),
                parent_sources=["resolutions_flat"],
            )
            print(f"wrote advies_es_gold ({len(gold_rows)} rows)")
        else:
            gold = load_advies_gold_18c()
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
        parents = ["advies_es_gold", "resolutions_flat"]

    boot_texts = boot["resolutions_text"].astype(str).tolist()
    cloud, cloud_notes = build_advies_cloud(boot_texts)

    gold_scored = score_frame(gold, cloud, role="gold")
    hold_scored = score_frame(hold, cloud, role="holdout")
    neg_scored = score_frame(neg, cloud, role="negative")

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
    n_accepted = (cloud_notes.get("n_hits_accepted") if cloud_notes else None)
    metrics["pass_cloud_accepts_gt_0"] = bool(n_accepted and int(n_accepted) > 0)

    corpus_rate = float((metrics.get("popularity") or {}).get("corpus_rate_proxy") or 0.0)
    score_rows = pd_concat_scores(
        gold_scored, neg_scored, cut=cut, corpus_rate=corpus_rate
    )

    save_semi_structured(
        [metrics],
        logical_name="formula_type_advies_metrics",
        script=__file__,
        description="STEPT1a2 advies formula-type eval metrics",
        parent_sources=parents,
    )
    save_semi_structured(
        score_rows,
        logical_name="formula_type_advies_scores",
        script=__file__,
        description="STEPT1a2 per-id align scores (gold + negatives)",
        parent_sources=parents,
    )

    print(json.dumps(metrics, indent=2, ensure_ascii=False, default=str))
    print(
        f"wrote formula_type_advies_metrics / "
        f"formula_type_advies_scores ({len(score_rows)} score rows)"
    )


if __name__ == "__main__":
    main()
