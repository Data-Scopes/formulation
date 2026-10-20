#!/usr/bin/env python3
"""Build Excel workbook to score pre-1705 resolutions for new aanstelling gold.

Prioritises the earliest calendar years among cue-positive or review-band harvest
rows not already in hand gold. Writes ``aanstelling_pre1705_gold_review_xlsx``.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd
import pyarrow.parquet as pq

from data_io import resolve
from data_io.jsonl_io import save_semi_structured
from formulation.aanstelling import LABEL_AANSTELLING
from formulation.aanstelling_cues import add_aanstelling_cues, add_rough_names
from formulation.aanstelling_shape import add_shape_scores, fit_gold_centroid
from formulation.review_snippet import add_review_snippet

LOGICAL_XLSX = "aanstelling_pre1705_gold_review_xlsx"
HARVEST_COLS = [
    "id",
    "date",
    "year",
    "weekday",
    "proba_aanstelling",
    "bucket",
    "resolutions_text",
]
TEXT_EXCEL_MAX = 12_000


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument(
        "--limit",
        type=int,
        default=350,
        help="Max rows on to_score sheet (default 350)",
    )
    p.add_argument(
        "--min-proba",
        type=float,
        default=0.15,
        help="Include harvest rows with proba above this (default 0.15)",
    )
    p.add_argument(
        "--year-max",
        type=int,
        default=1704,
        help="Upper year inclusive (default 1704)",
    )
    p.add_argument(
        "--exclude-reviewed-ids",
        action=argparse.BooleanOptionalAction,
        default=True,
        help=(
            "Drop ids already on gold_pre1705 (keep) or filled gold_label in "
            "an existing workbook (default: true)"
        ),
    )
    return p.parse_args()


def _load_labelled_gold_ids() -> set[str]:
    from data_io import load

    labelled = load("aanstelling_labelled")
    gold = labelled.loc[labelled["label"].eq(LABEL_AANSTELLING), "id"].astype(str)
    return set(gold)


def _load_pre1705_harvest(year_max: int) -> pd.DataFrame:
    path = resolve("aanstelling_tfidf_harvest")
    frame = pq.read_table(path, columns=HARVEST_COLS).to_pandas()
    frame["year"] = pd.to_numeric(frame["year"], errors="coerce")
    return frame.loc[frame["year"] <= year_max].copy()


def _prioritize_candidates(
    frame: pd.DataFrame,
    *,
    gold_ids: set[str],
    min_proba: float,
    limit: int,
) -> pd.DataFrame:
    pool = frame.loc[~frame["id"].astype(str).isin(gold_ids)].copy()
    pool = add_aanstelling_cues(pool)
    pool = pool.loc[
        pool["has_aanstelling_cue"]
        | pool["proba_aanstelling"].astype(float).gt(min_proba)
    ]
    pool = pool.sort_values(
        ["year", "has_aanstelling_cue", "proba_aanstelling"],
        ascending=[True, False, False],
    )
    return pool.head(int(limit)).reset_index(drop=True)


def _truncate_text(series: pd.Series) -> pd.Series:
    return series.fillna("").astype(str).str.slice(0, TEXT_EXCEL_MAX)


def _load_existing_workbook(path: Path) -> dict[str, pd.DataFrame] | None:
    if not path.exists():
        return None
    return pd.read_excel(path, sheet_name=None)


def _reviewed_ids_from_workbook(book: dict[str, pd.DataFrame] | None) -> set[str]:
    if not book:
        return set()
    out: set[str] = set()
    if "gold_pre1705" in book:
        gp = book["gold_pre1705"]
        if "review" in gp.columns:
            keep = gp["review"].fillna("").astype(str).str.strip().str.lower().eq("keep")
            out |= set(gp.loc[keep, "id"].astype(str))
        out |= set(gp["id"].astype(str))
    if "to_score" in book:
        ts = book["to_score"]
        if "gold_label" in ts.columns:
            scored = ts["gold_label"].fillna("").astype(str).str.strip().ne("")
            out |= set(ts.loc[scored, "id"].astype(str))
    return out


def _with_snippet(frame: pd.DataFrame) -> pd.DataFrame:
    if "resolutions_text" not in frame.columns:
        return frame
    out = add_review_snippet(frame, max_chars=TEXT_EXCEL_MAX)
    cols = [c for c in out.columns if c != "review_snippet"]
    if "resolutions_text" in cols:
        idx = cols.index("resolutions_text")
        cols.insert(idx, "review_snippet")
        return out[cols]
    return out


def _instructions(limit: int) -> pd.DataFrame:
    rows = [
        (
            "to_score",
            f"Read ``review_snippet`` (date + text). Fill ``gold_label``: yes | no | "
            f"maybe | other_appointment. Up to {limit} rows, earliest years first.",
        ),
        ("gold_pre1705", "Existing hand gold (reference only)."),
        (
            "selected_pre1705",
            "R1 frozen keeps before 1705 — confirm or reject as new gold exemplars.",
        ),
        (
            "notes",
            "Resolution cuts in early period may be wrong (~70% at best); note segmentation in notes.",
        ),
    ]
    return pd.DataFrame(rows, columns=["sheet", "purpose"])


def main() -> None:
    args = parse_args()
    xlsx_path = Path(resolve(LOGICAL_XLSX))
    existing = _load_existing_workbook(xlsx_path)
    gold_ids = _load_labelled_gold_ids()
    if args.exclude_reviewed_ids:
        gold_ids |= _reviewed_ids_from_workbook(existing)
    harvest = _load_pre1705_harvest(args.year_max)
    to_score = _prioritize_candidates(
        harvest,
        gold_ids=gold_ids,
        min_proba=args.min_proba,
        limit=args.limit,
    )

    from data_io import load

    labelled = load("aanstelling_labelled")
    gold_pre = labelled.loc[
        labelled["label"].eq(LABEL_AANSTELLING)
        & pd.to_numeric(labelled["year"], errors="coerce").le(args.year_max)
    ].copy()
    gold_pre = add_aanstelling_cues(gold_pre)
    gold_pre = add_rough_names(gold_pre)
    gold_pre["resolutions_text"] = _truncate_text(gold_pre["resolutions_text"])
    gold_pre = _with_snippet(gold_pre)

    selected = load("aanstelling_selected")
    selected["year"] = pd.to_numeric(selected["year"], errors="coerce")
    sel_pre = selected.loc[selected["year"] <= args.year_max].copy()
    sel_pre = sel_pre.sort_values(["year", "proba_aanstelling"]).reset_index(drop=True)
    sel_pre["resolutions_text"] = _truncate_text(sel_pre["resolutions_text"])
    sel_pre = _with_snippet(sel_pre)

    gold_pos = labelled.loc[labelled["label"].eq(LABEL_AANSTELLING)]
    vectorizer, centroid, cos_cut = fit_gold_centroid(gold_pos["resolutions_text"])
    to_score = add_shape_scores(
        to_score, vectorizer, centroid, cos_cut=cos_cut
    )
    to_score = add_rough_names(to_score)
    to_score["resolutions_text"] = _truncate_text(to_score["resolutions_text"])
    to_score["gold_label"] = ""
    to_score["notes"] = ""
    to_score["in_r1_selected"] = to_score["id"].astype(str).isin(
        set(sel_pre["id"].astype(str))
    )

    out_cols = [
        "id",
        "date",
        "year",
        "weekday",
        "proba_aanstelling",
        "bucket",
        "has_aanstelling_cue",
        "cue_hits",
        "rough_names",
        "n_chars",
        "cos_gold",
        "suspect",
        "in_r1_selected",
        "gold_label",
        "notes",
        "resolutions_text",
    ]
    to_score = to_score[[c for c in out_cols if c in to_score.columns]]
    to_score = _with_snippet(to_score)

    gold_pre1705_out = (
        existing["gold_pre1705"]
        if existing and "gold_pre1705" in existing
        else gold_pre
    )
    if "resolutions_text" in gold_pre1705_out.columns:
        gold_pre1705_out = _with_snippet(gold_pre1705_out)

    xlsx_path.parent.mkdir(parents=True, exist_ok=True)
    with pd.ExcelWriter(xlsx_path, engine="openpyxl") as writer:
        _instructions(args.limit).to_excel(writer, sheet_name="instructions", index=False)
        to_score.to_excel(writer, sheet_name="to_score", index=False)
        gold_pre1705_out.to_excel(writer, sheet_name="gold_pre1705", index=False)
        sel_pre.to_excel(writer, sheet_name="selected_pre1705", index=False)
        summary = pd.DataFrame(
            [
                {"item": "to_score_rows", "value": len(to_score)},
                {"item": "year_min", "value": int(to_score["year"].min())},
                {"item": "year_max", "value": int(to_score["year"].max())},
                {"item": "gold_pre1705", "value": len(gold_pre1705_out)},
                {"item": "selected_pre1705", "value": len(sel_pre)},
            ]
        )
        summary.to_excel(writer, sheet_name="summary", index=False)

    meta_path = save_semi_structured(
        [summary.to_dict(orient="records")],
        logical_name="aanstelling_pre1705_gold_review_meta",
        description="Build stats for pre1705 gold review xlsx",
        script=__file__,
    )
    print(f"wrote {xlsx_path}")
    print(f"meta {meta_path}")
    print(summary.to_string(index=False))


if __name__ == "__main__":
    main()
