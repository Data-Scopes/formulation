#!/usr/bin/env python3
"""STEPT1v: Doc B L1→L2 slot reduction on ``requeste_geleesen``.

    uv run python scripts/eval_formula_reduction_l2.py --fixture-only
    uv run python scripts/eval_formula_reduction_l2.py --limit-gold 2000 --neg-n 500
    uv run python scripts/eval_formula_reduction_l2.py
"""

from __future__ import annotations

import argparse
import json
from typing import Any

from data_io import save_semi_structured
from formulation.formula_reduction_l2 import (
    DEFAULT_HOLDOUT_FRAC,
    DEFAULT_NEG_N,
    DEFAULT_RNG,
    FALLBACK_CUT,
    ablation_configs,
    calibrate_cut,
    exhaustive_configs,
    fixture_smoke,
    load_long_head_gold,
    metrics_at_cut,
    sample_negatives,
    score_frame_with_optional,
    slot_labels,
    span_iou_vs_ref,
    split_bootstrap_holdout,
    summarize_reduction,
)
from formulation.requeste_formula_type import build_requeste_cloud


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--fixture-only", action="store_true")
    p.add_argument("--limit-gold", type=int, default=None)
    p.add_argument("--neg-n", type=int, default=DEFAULT_NEG_N)
    p.add_argument("--holdout-frac", type=float, default=DEFAULT_HOLDOUT_FRAC)
    p.add_argument("--random-state", type=int, default=DEFAULT_RNG)
    p.add_argument(
        "--exhaustive",
        action="store_true",
        help="All 2^n optional masks (n=6 → 64). Prefer with --limit-gold.",
    )
    p.add_argument("--no-write", action="store_true")
    p.add_argument(
        "--progress-every",
        type=int,
        default=2000,
        help="Score progress print interval (0=quiet)",
    )
    return p.parse_args(argv)


def _run_configs(
    *,
    cloud: dict[str, Any],
    hold_gold: Any,
    neg: Any,
    configs: list[dict[str, Any]],
    labels: list[str],
    progress_every: int,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], Any]:
    """Score each config; return metrics rows, score rows, baseline gold scored."""
    config_metrics: list[dict[str, Any]] = []
    score_rows: list[dict[str, Any]] = []
    baseline_gold = None

    for cfg in configs:
        opt = list(cfg["optional_slots"])
        cid = str(cfg["config_id"])
        print(f"config {cid} optional_slots={opt}", flush=True)
        g = score_frame_with_optional(
            hold_gold,
            cloud,
            opt,
            role="gold_holdout",
            progress_every=progress_every,
        )
        n = score_frame_with_optional(
            neg,
            cloud,
            opt,
            role="neg",
            progress_every=progress_every,
        )
        cut = calibrate_cut(g["score"].tolist(), fallback=FALLBACK_CUT)
        m = metrics_at_cut(g, n, cut=cut)
        row = {
            **cfg,
            "ablated_token": (
                labels[int(cfg["ablated_slot"])]
                if cfg.get("ablated_slot") is not None
                and int(cfg["ablated_slot"]) < len(labels)
                else None
            ),
            **m,
        }
        if baseline_gold is not None:
            row["span_vs_all_required"] = span_iou_vs_ref(g, baseline_gold)
        config_metrics.append(row)

        if cfg["config_id"] == "all_required":
            baseline_gold = g

        for frame, role in ((g, "gold_holdout"), (n, "neg")):
            for rec in frame.to_dict(orient="records"):
                score_rows.append(
                    {
                        "config_id": cid,
                        "optional_slots": opt,
                        "role": role,
                        "id": rec["id"],
                        "year": rec.get("year"),
                        "score": rec["score"],
                        "start_idx": rec["start_idx"],
                        "end_idx": rec["end_idx"],
                        "pred": bool(rec["score"] >= cut),
                        "cut": cut,
                    }
                )

    return config_metrics, score_rows, baseline_gold


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)

    if args.fixture_only:
        gold, neg, cloud, notes = fixture_smoke()
        boot_ids = gold["id"].tolist()[:2]
        hold_ids = gold["id"].tolist()[2:] or gold["id"].tolist()
        hold_gold = gold.loc[gold["id"].isin(hold_ids)].reset_index(drop=True)
        n_universe = len(gold)
        mode = "fixture"
    else:
        gold = load_long_head_gold(
            limit=args.limit_gold, random_state=args.random_state
        )
        n_universe = len(gold)
        print(f"long-head gold n={n_universe}", flush=True)
        boot, hold_gold = split_bootstrap_holdout(
            gold,
            holdout_frac=args.holdout_frac,
            random_state=args.random_state,
        )
        hold_gold = hold_gold.reset_index(drop=True)
        boot_ids = boot["id"].astype(str).tolist()
        hold_ids = hold_gold["id"].astype(str).tolist()
        cloud, notes = build_requeste_cloud(boot["resolutions_text"].tolist())
        print(
            f"cloud accepted={notes.get('n_hits_accepted')} "
            f"optional={cloud.get('optional_slots')}",
            flush=True,
        )
        neg = sample_negatives(
            n=args.neg_n,
            exclude_ids=set(gold["id"].astype(str)),
            random_state=args.random_state,
        )
        mode = "exhaustive" if args.exhaustive else "single_slot_ablation"

    labels = slot_labels(cloud)
    n_slots = len(labels)
    boot_opt = [int(i) for i in (cloud.get("optional_slots") or [])]
    if args.exhaustive and not args.fixture_only:
        if args.limit_gold is None and n_universe > 3000:
            raise SystemExit(
                "--exhaustive on full gold is expensive; pass --limit-gold "
                "or drop --exhaustive"
            )
        configs = exhaustive_configs(n_slots)
    else:
        configs = ablation_configs(n_slots, bootstrap_optional=boot_opt)

    # Ensure all_required is evaluated early for span baseline
    configs = sorted(
        configs,
        key=lambda c: (
            0
            if c["config_id"] == "full"
            else 1
            if c["config_id"] == "all_required"
            else 2
        ),
    )

    config_metrics, score_rows, _baseline = _run_configs(
        cloud=cloud,
        hold_gold=hold_gold,
        neg=neg,
        configs=configs,
        labels=labels,
        progress_every=args.progress_every,
    )

    # Fill span IoU now that all_required exists
    base = next((r for r in config_metrics if r["config_id"] == "all_required"), None)
    if base is not None:
        base_gold_ids = {
            r["id"]: r
            for r in score_rows
            if r["config_id"] == "all_required" and r["role"] == "gold_holdout"
        }
        import pandas as pd

        base_df = pd.DataFrame(base_gold_ids.values()) if base_gold_ids else pd.DataFrame()
        for row in config_metrics:
            if row["config_id"] == "all_required":
                row["span_vs_all_required"] = {
                    "n_paired": int(len(base_df)),
                    "iou_median": 1.0,
                }
                continue
            cfg_gold = [
                r
                for r in score_rows
                if r["config_id"] == row["config_id"] and r["role"] == "gold_holdout"
            ]
            row["span_vs_all_required"] = span_iou_vs_ref(
                pd.DataFrame(cfg_gold), base_df
            )

    cloud_notes = {
        k: notes.get(k)
        for k in (
            "n_hits_accepted",
            "n_hits_rejected",
            "bootstrap_input",
            "canonic",
            "n_optional_slots",
        )
        if k in notes
    }
    cloud_notes["optional_slots"] = boot_opt
    metrics = summarize_reduction(
        config_metrics,
        labels=labels,
        cloud_notes=cloud_notes,
        n_gold_universe=n_universe,
        n_bootstrap=len(boot_ids),
        n_holdout=len(hold_ids),
        random_state=args.random_state,
        mode=mode,
    )

    print(json.dumps(
        {
            "mode": mode,
            "n_configs": len(config_metrics),
            "hinge_slots": metrics["hinge_slots"],
            "safe_ablate_slots": metrics["safe_ablate_slots"],
            "l2_required_tokens_guess": metrics["l2_required_tokens_guess"],
            "configs_preview": [
                {
                    "config_id": c["config_id"],
                    "optional_slots": c["optional_slots"],
                    "cut": c["cut"],
                    "recall": c["recall"],
                    "fp_rate": c["fp_rate"],
                }
                for c in config_metrics
            ],
        },
        indent=2,
    ))

    if not args.no_write and not args.fixture_only:
        save_semi_structured(
            [metrics],
            logical_name="formula_reduction_l2_metrics",
            script=__file__,
        )
        save_semi_structured(
            score_rows,
            logical_name="formula_reduction_l2_scores",
            script=__file__,
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
