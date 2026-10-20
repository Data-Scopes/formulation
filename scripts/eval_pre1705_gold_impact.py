#!/usr/bin/env python3
"""Measure whether pre-1705 review gold changes char-TF-IDF retrieval in early years.

Compares a baseline gold centroid (STEPR1 positives only) vs augmented
centroids (+ ``aanstelling_gold_pre1705_review``): equal row weight vs
review-upweighted (``--review-weight``, default 4 — ~70% centroid mass from
review keeps). Reports cosine scores and harvest ranks for review ids with
year <= --year-max (default 1658).
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow.compute as pc
import pyarrow.parquet as pq

from data_io import load, resolve
from data_io.jsonl_io import save_semi_structured
from formulation.aanstelling import LABEL_AANSTELLING
from formulation.aanstelling_shape import cosine_to_centroid, fit_gold_centroid
from formulation.aanstelling_tfidf import ANALYZER, NGRAM_RANGE

LOGICAL_METRICS = "aanstelling_pre1705_gold_impact_metrics"


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument(
        "--year-max",
        type=int,
        default=1658,
        help="Early-period ceiling for harvest rank pool (default 1658)",
    )
    p.add_argument(
        "--review-weight",
        type=float,
        default=4.0,
        help=(
            "Per-row weight for review keeps in the early-weighted centroid "
            "(18c STEPR1 gold stays at 1.0; default 4 ≈ 70%% mass from review)"
        ),
    )
    return p.parse_args()


def _labelled_gold() -> pd.DataFrame:
    labelled = load("aanstelling_labelled")
    return labelled.loc[labelled["label"].eq(LABEL_AANSTELLING)].copy()


def _review_gold() -> pd.DataFrame:
    rows = load("aanstelling_gold_pre1705_review")
    return pd.DataFrame(rows)


def _harvest_early(year_max: int) -> pd.DataFrame:
    path = resolve("aanstelling_tfidf_harvest")
    table = pq.read_table(
        path,
        columns=["id", "year", "resolutions_text"],
        filters=pc.field("year") <= year_max,
    )
    return table.to_pandas()


def _ranks(scores: np.ndarray) -> np.ndarray:
    """Rank 1 = highest score (dense rank via argsort)."""
    order = np.argsort(-scores)
    out = np.empty_like(order)
    out[order] = np.arange(1, len(scores) + 1)
    return out


def main() -> None:
    args = parse_args()
    baseline_gold = _labelled_gold()
    review = _review_gold()
    review = review.loc[pd.to_numeric(review["year"], errors="coerce").le(args.year_max)]

    vec_b, cent_b, _ = fit_gold_centroid(baseline_gold["resolutions_text"])
    combined = pd.concat(
        [
            baseline_gold[["id", "resolutions_text"]],
            review[["id", "resolutions_text"]],
        ],
        ignore_index=True,
    )
    vec_eq, cent_eq, _ = fit_gold_centroid(combined["resolutions_text"])
    n_base = len(baseline_gold)
    weights = np.concatenate(
        [
            np.ones(n_base, dtype=float),
            np.full(len(review), float(args.review_weight), dtype=float),
        ]
    )
    vec_w, cent_w, _ = fit_gold_centroid(
        combined["resolutions_text"], sample_weight=weights
    )

    cos_b = cosine_to_centroid(review["resolutions_text"], vec_b, cent_b)
    cos_eq = cosine_to_centroid(review["resolutions_text"], vec_eq, cent_eq)
    cos_w = cosine_to_centroid(review["resolutions_text"], vec_w, cent_w)

    harvest = _harvest_early(args.year_max)
    harvest_scores_b = cosine_to_centroid(harvest["resolutions_text"], vec_b, cent_b)
    harvest_scores_eq = cosine_to_centroid(
        harvest["resolutions_text"], vec_eq, cent_eq
    )
    harvest_scores_w = cosine_to_centroid(harvest["resolutions_text"], vec_w, cent_w)
    ranks_b = _ranks(harvest_scores_b)
    ranks_eq = _ranks(harvest_scores_eq)
    ranks_w = _ranks(harvest_scores_w)

    id_to_idx = {str(i): k for k, i in enumerate(harvest["id"].astype(str))}
    review_ranks_b: list[int] = []
    review_ranks_eq: list[int] = []
    review_ranks_w: list[int] = []
    for rid in review["id"].astype(str):
        idx = id_to_idx.get(rid)
        if idx is None:
            continue
        review_ranks_b.append(int(ranks_b[idx]))
        review_ranks_eq.append(int(ranks_eq[idx]))
        review_ranks_w.append(int(ranks_w[idx]))

    metrics: list[dict] = [
        {
            "item": "review_gold_n",
            "value": int(len(review)),
            "year_max": args.year_max,
        },
        {
            "item": "mean_cos_baseline_18c_gold",
            "value": round(float(np.mean(cos_b)), 4),
        },
        {
            "item": "review_weight",
            "value": float(args.review_weight),
        },
        {
            "item": "mean_cos_augmented_equal",
            "value": round(float(np.mean(cos_eq)), 4),
        },
        {
            "item": "mean_cos_augmented_weighted",
            "value": round(float(np.mean(cos_w)), 4),
        },
        {
            "item": "mean_cos_delta_equal",
            "value": round(float(np.mean(cos_eq - cos_b)), 4),
        },
        {
            "item": "mean_cos_delta_weighted",
            "value": round(float(np.mean(cos_w - cos_b)), 4),
        },
        {
            "item": "median_harvest_rank_baseline",
            "value": float(np.median(review_ranks_b)),
        },
        {
            "item": "median_harvest_rank_augmented_equal",
            "value": float(np.median(review_ranks_eq)),
        },
        {
            "item": "median_harvest_rank_augmented_weighted",
            "value": float(np.median(review_ranks_w)),
        },
        {
            "item": "harvest_pool_n",
            "value": int(len(harvest)),
        },
        {
            "item": "review_ids_in_harvest",
            "value": int(len(review_ranks_b)),
        },
    ]

    print("Pre-1705 review gold impact (char_wb centroid, year <= %s)" % args.year_max)
    for row in metrics:
        print(f"  {row['item']}: {row['value']}")

    out = save_semi_structured(
        metrics,
        logical_name=LOGICAL_METRICS,
        description="Baseline vs augmented gold centroid on pre1705 review set",
        parent_sources=[
            "aanstelling_labelled",
            "aanstelling_gold_pre1705_review",
            "aanstelling_tfidf_harvest",
        ],
        script=__file__,
    )
    print(f"metrics → {out}")


if __name__ == "__main__":
    main()
