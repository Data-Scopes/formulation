from __future__ import annotations

import pandas as pd

from formulation.review_snippet import add_review_snippet, format_review_snippet


def test_format_review_snippet_includes_date_and_weekday() -> None:
    out = format_review_snippet("1579-07-22", "Tuesday", "Is mede gheresolueert")
    assert out.startswith("[1579-07-22 (Tuesday)]")
    assert "Is mede gheresolueert" in out


def test_add_review_snippet_column() -> None:
    frame = pd.DataFrame(
        {
            "date": ["1621-11-10"],
            "weekday": ["Wednesday"],
            "resolutions_text": ["Is ter vergaderinge gecompareert"],
        }
    )
    out = add_review_snippet(frame)
    assert "review_snippet" in out.columns
    assert "[1621-11-10 (Wednesday)]" in out.loc[0, "review_snippet"]
