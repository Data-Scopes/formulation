#!/usr/bin/env python3
"""Export ``gold_pre1705`` sheet (review=keep) to semi-structured JSONL."""

from __future__ import annotations

import pandas as pd

from data_io import resolve
from data_io.jsonl_io import save_semi_structured

LOGICAL_OUT = "aanstelling_gold_pre1705_review"
LOGICAL_XLSX = "aanstelling_pre1705_gold_review_xlsx"


def main() -> None:
    path = resolve(LOGICAL_XLSX)
    frame = pd.read_excel(path, sheet_name="gold_pre1705")
    review = frame["review"].fillna("").astype(str).str.strip().str.lower()
    keeps = frame.loc[review.eq("keep")].copy()
    records = []
    for row in keeps.itertuples(index=False):
        rec = row._asdict()
        notes = rec.pop("Notes", None) or rec.pop("notes", None)
        records.append(
            {
                "id": str(rec["id"]),
                "date": str(rec.get("date", "")),
                "year": int(rec["year"]) if pd.notna(rec.get("year")) else None,
                "resolutions_text": str(rec.get("resolutions_text", "")),
                "cue_hits": rec.get("cue_hits"),
                "rough_names": rec.get("rough_names"),
                "proba_aanstelling": rec.get("proba_aanstelling"),
                "selection_source": rec.get("selection_source"),
                "notes": notes if pd.notna(notes) else "",
                "review": "keep",
                "source_workbook": str(path.name),
                "source_sheet": "gold_pre1705",
            }
        )
    out = save_semi_structured(
        records,
        logical_name=LOGICAL_OUT,
        description="Human-reviewed pre-1705 aanstelling keeps from gold_pre1705 sheet",
        parent_sources=["aanstelling_pre1705_gold_review_xlsx"],
        script=__file__,
    )
    print(f"wrote {len(records)} rows → {out}")


if __name__ == "__main__":
    main()
