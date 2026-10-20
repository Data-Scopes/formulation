#!/usr/bin/env python3
"""Finalize R1 selection from Excel review + refreshed rough names.

Reads ``aanstelling_retrieval_xlsx``, bulk-fills blank ``review`` labels on
``review_suspect`` with the agreed rules, re-extracts rough / Holland-multi
names, writes:

- ``aanstelling_review_labels`` — id + review + source (human|rule)
- ``aanstelling_selected`` — gold + ingest keeps + review keeps with names
- updates the Excel with filled labels, a ``selected`` sheet, and refreshed names
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from data_io import resolve, save_parquet, save_semi_structured
from formulation.aanstelling_cues import add_aanstelling_cues, add_rough_names
from formulation.aanstelling_selection import (
    bulk_fill_review_suspect,
    norm_review_label,
)

LOGICAL_XLSX = "aanstelling_retrieval_xlsx"


def _norm_label(value: object) -> str:
    return norm_review_label(value)

def _refresh_names(frame: pd.DataFrame) -> pd.DataFrame:
    if "resolutions_text" not in frame.columns:
        return frame
    base = frame.drop(
        columns=[
            c
            for c in frame.columns
            if c.startswith("cue_")
            or c
            in {
                "has_aanstelling_cue",
                "cue_hits",
                "rough_names",
                "n_rough_names",
                "holland_multi_names",
                "n_holland_multi_names",
            }
        ],
        errors="ignore",
    )
    # preserve review columns through cue refresh
    keep_cols = [c for c in ("review", "review_source") if c in frame.columns]
    extras = frame[keep_cols] if keep_cols else None
    refreshed = add_rough_names(add_aanstelling_cues(base))
    if extras is not None:
        for col in keep_cols:
            refreshed[col] = extras[col].values
    return refreshed


def _selected_rows(
    gold: pd.DataFrame,
    ingest_cued: pd.DataFrame,
    ingest_suspect: pd.DataFrame,
    review_suspect: pd.DataFrame,
    review_cued: pd.DataFrame,
) -> pd.DataFrame:
    parts: list[pd.DataFrame] = []

    def take(frame: pd.DataFrame, source: str, band: str) -> pd.DataFrame:
        cols = [
            c
            for c in (
                "id",
                "date",
                "year",
                "proba_aanstelling",
                "cos_gold",
                "suspect",
                "cue_hits",
                "rough_names",
                "n_rough_names",
                "holland_multi_names",
                "n_holland_multi_names",
                "resolutions_text",
                "review",
            )
            if c in frame.columns
        ]
        out = frame.loc[:, cols].copy()
        out.insert(0, "selection_source", source)
        out.insert(1, "selection_band", band)
        return out

    parts.append(take(gold, "gold", "gold"))
    parts.append(take(ingest_cued, "ingest_cued", "ingest_p_gt_0_5"))
    keep_ing = ingest_suspect.loc[
        ingest_suspect["review"].map(_norm_label).eq("keep")
    ]
    parts.append(take(keep_ing, "ingest_suspect_keep", "ingest_p_gt_0_5"))
    # shape-ok grey cued (not in suspect sheet)
    if "suspect" in review_cued.columns:
        review_ok = review_cued.loc[~review_cued["suspect"].astype(bool)].copy()
        suspect_ids = set(review_suspect["id"].astype(str))
        review_ok = review_ok.loc[~review_ok["id"].astype(str).isin(suspect_ids)]
        parts.append(take(review_ok, "review_cued_shape_ok", "review_0_15_to_0_5"))
    keep_rev = review_suspect.loc[
        review_suspect["review"].map(_norm_label).eq("keep")
    ]
    parts.append(take(keep_rev, "review_suspect_keep", "review_0_15_to_0_5"))

    selected = pd.concat(parts, ignore_index=True)
    selected["id"] = selected["id"].astype(str)
    # Prefer gold over harvest duplicates
    source_rank = {
        "gold": 0,
        "ingest_cued": 1,
        "ingest_suspect_keep": 2,
        "review_cued_shape_ok": 3,
        "review_suspect_keep": 4,
    }
    selected["_rank"] = selected["selection_source"].map(source_rank).fillna(9)
    selected = (
        selected.sort_values(["id", "_rank"])
        .drop_duplicates(subset=["id"], keep="first")
        .drop(columns=["_rank"])
        .sort_values(["year", "date", "id"], na_position="last")
        .reset_index(drop=True)
    )
    return selected


def main() -> None:
    xlsx = Path(resolve(LOGICAL_XLSX))
    gold = pd.read_excel(xlsx, sheet_name="gold")
    ingest_cued = pd.read_excel(xlsx, sheet_name="ingest_cued")
    ingest_suspect = pd.read_excel(xlsx, sheet_name="ingest_suspect")
    review_cued = pd.read_excel(xlsx, sheet_name="review_cued")
    review_suspect = pd.read_excel(xlsx, sheet_name="review_suspect")

    # Ensure ingest_suspect has review_source for humans
    if "review" in ingest_suspect.columns:
        ingest_suspect = ingest_suspect.copy()
        ingest_suspect["review_source"] = ingest_suspect["review"].map(
            lambda v: "human" if _norm_label(v) else ""
        )

    before_blank = int(
        review_suspect.get("review", pd.Series(dtype=str))
        .map(_norm_label)
        .eq("")
        .sum()
    )
    review_suspect = bulk_fill_review_suspect(review_suspect)
    after_blank = int(review_suspect["review"].map(_norm_label).eq("").sum())
    n_rule = int((review_suspect.get("review_source") == "rule").sum())

    gold = _refresh_names(gold)
    ingest_cued = _refresh_names(ingest_cued)
    ingest_suspect = _refresh_names(ingest_suspect)
    review_cued = _refresh_names(review_cued)
    review_suspect = _refresh_names(review_suspect)

    selected = _selected_rows(
        gold, ingest_cued, ingest_suspect, review_suspect, review_cued
    )

    # Review label sidecar (suspect sheets only — the adjudicated pile)
    label_rows = []
    for sheet, frame in (
        ("ingest_suspect", ingest_suspect),
        ("review_suspect", review_suspect),
    ):
        if "review" not in frame.columns:
            continue
        for _, row in frame.iterrows():
            lab = _norm_label(row.get("review"))
            if not lab:
                continue
            label_rows.append(
                {
                    "id": str(row["id"]),
                    "sheet": sheet,
                    "review": lab,
                    "review_source": row.get("review_source", "human"),
                    "year": int(row["year"]) if pd.notna(row.get("year")) else None,
                    "cue_hits": row.get("cue_hits", ""),
                    "rough_names": row.get("rough_names", ""),
                }
            )
    labels = pd.DataFrame(label_rows)

    labels_path = save_semi_structured(
        labels.to_dict(orient="records"),
        logical_name="aanstelling_review_labels",
        parent_sources=[LOGICAL_XLSX],
        script=__file__,
    )
    selected_path = save_parquet(
        selected,
        logical_name="aanstelling_selected",
        parent_sources=[
            LOGICAL_XLSX,
            "aanstelling_labelled",
            "aanstelling_tfidf_harvest",
        ],
        script=__file__,
    )

    # Rewrite Excel: refresh names / filled reviews + selected sheet
    # Keep other sheets from the existing workbook where possible.
    existing = {
        name: pd.read_excel(xlsx, sheet_name=name)
        for name in pd.ExcelFile(xlsx).sheet_names
    }
    existing["gold"] = gold
    existing["ingest_cued"] = ingest_cued
    existing["ingest_suspect"] = ingest_suspect
    existing["review_cued"] = review_cued
    existing["review_suspect"] = review_suspect
    existing["selected"] = selected
    # also mirror filled review onto full ingest/review sheets if present
    for sheet in ("ingest_p_gt_0_5", "review_0_15_to_0_5"):
        if sheet not in existing:
            continue
        frame = _refresh_names(existing[sheet])
        existing[sheet] = frame

    with pd.ExcelWriter(xlsx, engine="openpyxl") as writer:
        for name, frame in existing.items():
            frame.to_excel(writer, sheet_name=name[:31], index=False)

    n_named = int((selected["n_rough_names"].fillna(0) > 0).sum())
    print(
        f"review_suspect blank {before_blank} → {after_blank} "
        f"(rule-filled {n_rule})"
    )
    print(
        f"selected {len(selected)} "
        f"(named {n_named}, {n_named / len(selected):.0%}); "
        f"by source:\n{selected['selection_source'].value_counts().to_string()}"
    )
    print(f"labels → {labels_path}")
    print(f"selected → {selected_path}")
    print(f"xlsx → {xlsx}")


if __name__ == "__main__":
    main()
