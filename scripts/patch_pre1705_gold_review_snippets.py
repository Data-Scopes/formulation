#!/usr/bin/env python3
"""Add or refresh ``review_snippet`` on the pre-1705 gold review workbook."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from data_io import resolve
from formulation.review_snippet import add_review_snippet

LOGICAL_XLSX = "aanstelling_pre1705_gold_review_xlsx"
TEXT_EXCEL_MAX = 12_000
SHEETS = ("to_score", "gold_pre1705", "selected_pre1705")


def _insert_snippet_column(frame: pd.DataFrame) -> pd.DataFrame:
    scored = add_review_snippet(frame, max_chars=TEXT_EXCEL_MAX)
    if "review_snippet" in frame.columns:
        cols = [c for c in scored.columns if c != "review_snippet"]
        text_idx = cols.index("resolutions_text") if "resolutions_text" in cols else len(cols)
        cols.insert(text_idx, "review_snippet")
        return scored[cols]
    return scored


def main() -> None:
    path = Path(resolve(LOGICAL_XLSX))
    if not path.exists():
        raise SystemExit(f"Workbook not found: {path}")

    book = pd.read_excel(path, sheet_name=None)
    for name in SHEETS:
        if name not in book:
            continue
        book[name] = _insert_snippet_column(book[name])

    with pd.ExcelWriter(path, engine="openpyxl") as writer:
        for name, frame in book.items():
            frame.to_excel(writer, sheet_name=name, index=False)
    print(f"updated review_snippet on {path} (sheets: {', '.join(SHEETS)})")


if __name__ == "__main__":
    main()
