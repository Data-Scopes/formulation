"""Human-review text blocks with session date (and optional weekday)."""

from __future__ import annotations

import pandas as pd

DEFAULT_TEXT_COL = "resolutions_text"
DEFAULT_SNIPPET_COL = "review_snippet"


def _format_date(date: object) -> str:
    if date is None or (isinstance(date, float) and pd.isna(date)):
        return ""
    if isinstance(date, pd.Timestamp):
        return date.strftime("%Y-%m-%d")
    text = str(date).strip()
    if not text or text.lower() == "nat":
        return ""
    if " " in text:
        text = text.split(" ", 1)[0]
    return text


def format_review_snippet(
    date: object,
    weekday: object,
    text: object,
    *,
    max_chars: int | None = None,
) -> str:
    """Prefix resolution text with ``[YYYY-MM-DD (weekday)]`` for Excel review."""
    date_s = _format_date(date)
    wd = "" if weekday is None or pd.isna(weekday) else str(weekday).strip()
    header = date_s
    if wd:
        header = f"{header} ({wd})" if header else wd
    if header:
        header = f"[{header}]"
    body = "" if text is None or pd.isna(text) else str(text).strip()
    if not header:
        out = body
    elif not body:
        out = header
    else:
        out = f"{header}\n{body}"
    if max_chars is not None and len(out) > max_chars:
        return out[:max_chars]
    return out


def add_review_snippet(
    frame: pd.DataFrame,
    *,
    date_col: str = "date",
    weekday_col: str = "weekday",
    text_col: str = DEFAULT_TEXT_COL,
    snippet_col: str = DEFAULT_SNIPPET_COL,
    max_chars: int | None = None,
) -> pd.DataFrame:
    out = frame.copy()
    if text_col not in out.columns:
        raise ValueError(f"Frame missing {text_col!r}")
    date_series = out[date_col] if date_col in out.columns else pd.Series([None] * len(out))
    wd_series = out[weekday_col] if weekday_col in out.columns else pd.Series([None] * len(out))
    out[snippet_col] = [
        format_review_snippet(d, w, t, max_chars=max_chars)
        for d, w, t in zip(date_series, wd_series, out[text_col], strict=True)
    ]
    return out
