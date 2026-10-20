"""Finalize helpers: review bulk-fill rules for R1 selection."""

from __future__ import annotations

import pandas as pd

KEEP_CUES = frozenset({"sessie_genomen", "sessie_genomen;aengenaem"})
DROP_CUES = frozenset({"verwelkom"})


def norm_review_label(value: object) -> str:
    text = str(value or "").strip().lower()
    if text in ("", "nan", "none"):
        return ""
    return text


def bulk_fill_review_suspect(frame: pd.DataFrame) -> pd.DataFrame:
    """Fill blank review cells: sessie(±aengenaem)→keep, bare verwelkom→drop."""
    out = frame.copy()
    if "review" not in out.columns:
        out["review"] = ""
    labels = out["review"].map(norm_review_label)
    cues = out.get("cue_hits", pd.Series("", index=out.index)).fillna("").astype(str)
    blank = labels.eq("")
    out["review_source"] = ""
    out.loc[labels.ne(""), "review_source"] = "human"
    rule_keep = blank & cues.isin(KEEP_CUES)
    rule_drop = blank & cues.isin(DROP_CUES)
    out.loc[rule_keep, "review"] = "keep"
    out.loc[rule_keep, "review_source"] = "rule"
    out.loc[rule_drop, "review"] = "drop"
    out.loc[rule_drop, "review_source"] = "rule"
    return out
