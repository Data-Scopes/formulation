#!/usr/bin/env python3
"""Enrich aanstelling Excel with ES, shape, cues, rough names, and pattern matches.

Reads gold + harvest bands, adds ``n_chars`` / ``cos_gold`` / ``suspect``,
aanstelling formula cues (*creditief*, *sessie genomen*, *verwelkomt*, …),
rough extracted names, optionally ES fields, then rewrites
``aanstelling_retrieval_xlsx``.
"""

from __future__ import annotations

import argparse
import time
from pathlib import Path

import pandas as pd
import pyarrow.parquet as pq

from data_io import load, resolve
from formulation.aanstelling import LABEL_AANSTELLING
from formulation.aanstelling_cues import (
    add_aanstelling_cues,
    add_rough_names,
    cue_summary,
)
from formulation.aanstelling_shape import (
    MIN_CHARS,
    add_shape_scores,
    fit_gold_centroid,
    shape_cut_summary,
)
from formulation.attendance_activity import load_attendance_spans
from formulation.delegate_patterns import (
    add_delegate_matches,
    build_pattern_index,
    load_unique_delegates,
    match_summary,
)
from formulation.republic_es import (
    RepublicEsClient,
    enrich_resolution_rows,
    load_elasticsearch_config,
)

LOGICAL_XLSX = "aanstelling_retrieval_xlsx"
HARVEST_COLS = [
    "id",
    "date",
    "year",
    "weekday",
    "proba_aanstelling",
    "bucket",
    "y_pred",
    "resolutions_text",
]
GOLD_COLS = [
    "id",
    "date",
    "year",
    "weekday",
    "delegate_fullnames",
    "delegate_ids",
    "gold_urns",
    "join_recovery",
    "resolutions_text",
]


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Cap rows per sheet (smoke / POC)",
    )
    parser.add_argument(
        "--no-es",
        action="store_true",
        help="Skip Elasticsearch (shape scores only)",
    )
    parser.add_argument(
        "--no-text-regions",
        action="store_true",
        help="Skip session_text_regions (faster; no IIIF columns)",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=100,
        help="mget / terms batch size (default 100)",
    )
    parser.add_argument(
        "--min-chars",
        type=int,
        default=MIN_CHARS,
        help=f"Suspect if shorter than this (default {MIN_CHARS})",
    )
    parser.add_argument(
        "--no-delegate-match",
        action="store_true",
        help="Skip unique-delegate pattern matching",
    )
    return parser.parse_args(argv)


def _gold_frame(limit: int | None) -> pd.DataFrame:
    labelled = load("aanstelling_labelled")
    gold = labelled.loc[labelled["label"].eq(LABEL_AANSTELLING)].copy()
    cols = [c for c in GOLD_COLS if c in gold.columns]
    gold = gold[cols].sort_values(["date", "id"]).reset_index(drop=True)
    if limit is not None:
        gold = gold.head(int(limit))
    return gold


def _harvest_bands(limit: int | None) -> tuple[pd.DataFrame, pd.DataFrame]:
    path = resolve("aanstelling_tfidf_harvest")
    frame = pq.read_table(path, columns=HARVEST_COLS).to_pandas()
    frame["proba_aanstelling"] = frame["proba_aanstelling"].astype(float)
    frame = frame.sort_values(
        ["proba_aanstelling", "date"], ascending=[False, True]
    ).reset_index(drop=True)
    ingest = frame.loc[frame["proba_aanstelling"] > 0.5].copy()
    review = frame.loc[
        (frame["proba_aanstelling"] > 0.15) & (frame["proba_aanstelling"] <= 0.5)
    ].copy()
    ingest.insert(0, "band", "ingest_p_gt_0_5")
    review.insert(0, "band", "review_0_15_to_0_5")
    if limit is not None:
        ingest = ingest.head(int(limit))
        review = review.head(int(limit))
    return ingest.reset_index(drop=True), review.reset_index(drop=True)


def _apply_shape(
    gold: pd.DataFrame,
    ingest: pd.DataFrame,
    review: pd.DataFrame,
    *,
    min_chars: int,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, float]:
    # Centroid always fitted on the full labelled gold set (not --limit slice).
    labelled = load("aanstelling_labelled")
    gold_texts = labelled.loc[
        labelled["label"].eq(LABEL_AANSTELLING), "resolutions_text"
    ]
    vectorizer, centroid, cos_cut = fit_gold_centroid(gold_texts)
    gold = add_shape_scores(
        gold, vectorizer, centroid, cos_cut=cos_cut, min_chars=min_chars
    )
    ingest = add_shape_scores(
        ingest, vectorizer, centroid, cos_cut=cos_cut, min_chars=min_chars
    )
    review = add_shape_scores(
        review, vectorizer, centroid, cos_cut=cos_cut, min_chars=min_chars
    )
    return gold, ingest, review, cos_cut


def _apply_cues_and_names(
    gold: pd.DataFrame,
    ingest: pd.DataFrame,
    review: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    gold = add_rough_names(add_aanstelling_cues(gold))
    ingest = add_rough_names(add_aanstelling_cues(ingest))
    review = add_rough_names(add_aanstelling_cues(review))
    return gold, ingest, review


def _summary(
    gold: pd.DataFrame,
    ingest: pd.DataFrame,
    review: pd.DataFrame,
    *,
    config_host: str,
    elapsed: float,
    cos_cut: float,
    min_chars: int,
    used_es: bool,
) -> pd.DataFrame:
    review_cued = (
        int(review["has_aanstelling_cue"].sum())
        if "has_aanstelling_cue" in review
        else 0
    )
    rows = [
        {"item": "gold_aanstellingen", "value": len(gold)},
        {"item": "ingest_p_gt_0_5", "value": len(ingest)},
        {"item": "review_0_15_to_0_5", "value": len(review)},
        {"item": "review_with_aanstelling_cue", "value": review_cued},
        *shape_cut_summary(
            min_chars=min_chars,
            cos_cut=cos_cut,
            gold=gold,
            ingest=ingest,
            review=review,
        ),
        *cue_summary(ingest),
        *match_summary(ingest),
        {
            "item": "es_resolution_found_ingest",
            "value": int(ingest["es_resolution_found"].sum())
            if "es_resolution_found" in ingest
            else "",
        },
        {
            "item": "es_session_found_ingest",
            "value": int(ingest["es_session_found"].sum())
            if "es_session_found" in ingest
            else "",
        },
        {"item": "es_used", "value": used_es},
        {"item": "es_host", "value": config_host if used_es else ""},
        {"item": "enrich_seconds", "value": round(elapsed, 1)},
        {"item": "holdout_recall", "value": 0.860465},
        {"item": "holdout_precision", "value": 0.973684},
        {"item": "holdout_f1", "value": 0.913580},
        {"item": "holdout_high_or_grey_recall", "value": 0.976744},
        {
            "item": "decision",
            "value": "stop after TF-IDF; no residual neural pass",
        },
        {"item": "source_harvest", "value": "aanstelling_tfidf_harvest"},
        {"item": "source_gold", "value": "aanstelling_labelled"},
    ]
    return pd.DataFrame(rows)


def _front_columns(frame: pd.DataFrame) -> pd.DataFrame:
    """Put shape / score / cue / name columns near the left for eyeballing."""
    preferred = [
        "band",
        "has_aanstelling_cue",
        "cue_hits",
        "cue_holland_multi",
        "holland_multi_names",
        "n_holland_multi_names",
        "rough_names",
        "n_rough_names",
        "suspect",
        "suspect_reason",
        "n_chars",
        "n_words",
        "cos_gold",
        "proba_aanstelling",
        "matched_fullname",
        "matched_delegate_id",
        "match_score",
        "match_in_cue",
        "match_patterns",
        "match_alternates",
        "bucket",
        "y_pred",
        "id",
        "date",
        "year",
        "weekday",
        "session_id",
        "delegate_fullnames",
        "resolutions_text",
    ]
    front = [c for c in preferred if c in frame.columns]
    rest = [c for c in frame.columns if c not in front]
    return frame[front + rest]


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)
    gold = _gold_frame(args.limit)
    ingest, review = _harvest_bands(args.limit)
    print(f"rows gold {len(gold)} ingest {len(ingest)} review {len(review)}")

    started = time.perf_counter()
    gold, ingest, review, cos_cut = _apply_shape(
        gold, ingest, review, min_chars=args.min_chars
    )
    print(
        f"shape min_chars={args.min_chars} cos_cut={cos_cut:.4f} "
        f"suspects gold/ingest/review "
        f"{int(gold['suspect'].sum())}/"
        f"{int(ingest['suspect'].sum())}/"
        f"{int(review['suspect'].sum())}"
    )

    gold, ingest, review = _apply_cues_and_names(gold, ingest, review)
    print(
        "aanstelling cues gold/ingest/review "
        f"{int(gold['has_aanstelling_cue'].sum())}/"
        f"{int(ingest['has_aanstelling_cue'].sum())}/"
        f"{int(review['has_aanstelling_cue'].sum())}; "
        f"rough_names non-empty ingest "
        f"{int((ingest['n_rough_names'] > 0).sum())}; "
        f"holland_multi ingest/review "
        f"{int(ingest['cue_holland_multi'].sum())}/"
        f"{int(review['cue_holland_multi'].sum())}"
    )

    if not args.no_delegate_match:
        unique = load_unique_delegates()
        index = build_pattern_index(unique)
        attendance = load_attendance_spans()
        print(
            f"delegate patterns indexed {len(index)} from {len(unique)} unique rows; "
            f"attendance spans {len(attendance)}"
        )
        gold = add_delegate_matches(
            gold, index, only_non_suspect=False, attendance=attendance
        )
        ingest = add_delegate_matches(
            ingest, index, only_non_suspect=True, attendance=attendance
        )
        review = add_delegate_matches(
            review, index, only_non_suspect=True, attendance=attendance
        )
        for label, frame in ("ingest", ingest), ("review", review):
            bits = match_summary(frame)
            rate = next((b["value"] for b in bits if b["item"] == "delegate_match_rate"), None)
            hit = next((b["value"] for b in bits if b["item"] == "delegate_match_hit"), None)
            print(f"delegate match {label}: hit {hit} rate {rate}")

    config_host = ""
    used_es = not args.no_es
    if used_es:
        config = load_elasticsearch_config()
        config_host = config.host
        client = RepublicEsClient(config)
        print(f"ES base {config.base_url}")
        kwargs = {
            "batch_size": args.batch_size,
            "with_text_regions": not args.no_text_regions,
        }
        gold = enrich_resolution_rows(gold, client, **kwargs)
        ingest = enrich_resolution_rows(ingest, client, **kwargs)
        review = enrich_resolution_rows(review, client, **kwargs)
    elapsed = time.perf_counter() - started

    gold = _front_columns(gold)
    ingest = _front_columns(ingest)
    review = _front_columns(review)
    # Priority eyeballing: cues first, then score
    if "has_aanstelling_cue" in ingest.columns:
        ingest = ingest.sort_values(
            ["has_aanstelling_cue", "suspect", "cos_gold", "proba_aanstelling"],
            ascending=[False, False, True, False],
        ).reset_index(drop=True)
        review = review.sort_values(
            ["has_aanstelling_cue", "suspect", "cos_gold", "proba_aanstelling"],
            ascending=[False, False, True, False],
        ).reset_index(drop=True)

    review_cued = review.loc[review["has_aanstelling_cue"]].copy()
    review_suspect = review.loc[
        review["suspect"] & review["has_aanstelling_cue"]
    ].copy()
    ingest_suspect = ingest.loc[
        ingest["suspect"] & ingest["has_aanstelling_cue"]
    ].copy()
    ingest_matched = (
        ingest.loc[
            (~ingest["suspect"])
            & ingest["has_aanstelling_cue"]
            & ingest["matched_delegate_id"].astype(str).str.len().gt(0)
        ].copy()
        if "matched_delegate_id" in ingest.columns
        else ingest.iloc[0:0]
    )
    # Prefer cue-positive ingest for the working list
    ingest_cued = ingest.loc[
        ingest["has_aanstelling_cue"] & ~ingest["suspect"]
    ].copy()

    summary = _summary(
        gold,
        ingest,
        review,
        config_host=config_host,
        elapsed=elapsed,
        cos_cut=cos_cut,
        min_chars=args.min_chars,
        used_es=used_es,
    )
    out = Path(resolve(LOGICAL_XLSX))
    out.parent.mkdir(parents=True, exist_ok=True)
    with pd.ExcelWriter(out, engine="openpyxl") as writer:
        summary.to_excel(writer, sheet_name="summary", index=False)
        gold.to_excel(writer, sheet_name="gold", index=False)
        ingest_cued.to_excel(writer, sheet_name="ingest_cued", index=False)
        ingest.to_excel(writer, sheet_name="ingest_p_gt_0_5", index=False)
        review_cued.to_excel(writer, sheet_name="review_cued", index=False)
        review.to_excel(writer, sheet_name="review_0_15_to_0_5", index=False)
        if not review_suspect.empty:
            review_suspect.to_excel(writer, sheet_name="review_suspect", index=False)
        if not ingest_suspect.empty:
            ingest_suspect.to_excel(writer, sheet_name="ingest_suspect", index=False)
        if not ingest_matched.empty:
            ingest_matched.to_excel(writer, sheet_name="ingest_matched", index=False)
    print(f"wrote {out} ({out.stat().st_size / 1e6:.2f} MB) in {elapsed:.1f}s")
    if used_es and "es_resolution_found" in ingest.columns:
        print(
            "ingest ES resolution hit rate "
            f"{ingest['es_resolution_found'].mean():.3f}; "
            "session "
            f"{ingest['es_session_found'].mean():.3f}"
        )


if __name__ == "__main__":
    main()
