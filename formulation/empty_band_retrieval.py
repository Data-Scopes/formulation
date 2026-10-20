"""STEPT1j2: score empty band with frozen R1 / L1 TF-IDF+LR contrast.

R1: join ``aanstelling_tfidf_harvest`` (already scored). L1: refit frozen
architecture on ``missive_receipt_labelled`` (``fit_on_all_labelled``) and
score empty texts. Diagnostic only — not a harvest, not new types.
"""

from __future__ import annotations

from collections import Counter
from typing import Any

import numpy as np
import pandas as pd

from data_io import load
from formulation.aanstelling_harvest import (
    BUCKET_GREY,
    BUCKET_HIGH,
    BUCKET_LOW,
    HIGH_CUT,
    LOW_CUT,
    assign_buckets,
)
from formulation.boundary.tfidf_windows import POC_YEAR
from formulation.empty_band import load_empty_universe
from formulation.missive_receipt_tfidf import fit_on_all_labelled, missive_proba
from formulation.typology_sample import NONE_TYPE_KEY

DEFAULT_YEAR = POC_YEAR
SCORE_BATCH = 512

__all__ = (
    "DEFAULT_YEAR",
    "HIGH_CUT",
    "LOW_CUT",
    "attach_r1_scores",
    "build_retrieval_frame",
    "fixture_retrieval_frame",
    "score_l1_on_empty",
    "summarize_empty_retrieval",
)


def _band_summary(proba: pd.Series, bucket: pd.Series) -> dict[str, Any]:
    valid = pd.to_numeric(proba, errors="coerce").dropna()
    counts = Counter(bucket.dropna().astype(str).tolist())
    n = int(len(bucket))
    return {
        "n": n,
        "n_high": int(counts.get(BUCKET_HIGH, 0)),
        "n_grey": int(counts.get(BUCKET_GREY, 0)),
        "n_low": int(counts.get(BUCKET_LOW, 0)),
        "frac_high": (counts.get(BUCKET_HIGH, 0) / n) if n else None,
        "frac_grey": (counts.get(BUCKET_GREY, 0) / n) if n else None,
        "frac_low": (counts.get(BUCKET_LOW, 0) / n) if n else None,
        "proba_median": float(valid.median()) if len(valid) else None,
        "proba_p90": float(valid.quantile(0.9)) if len(valid) else None,
    }


def attach_r1_scores(empty: pd.DataFrame) -> pd.DataFrame:
    """Join frozen R1 harvest proba/bucket onto empty ids."""
    out = empty.copy()
    out["id"] = out["id"].astype(str)
    harvest = load("aanstelling_tfidf_harvest")
    if not isinstance(harvest, pd.DataFrame):
        harvest = pd.DataFrame(harvest)
    sub = harvest.loc[
        harvest["id"].astype(str).isin(set(out["id"])),
        ["id", "proba_aanstelling", "bucket"],
    ].copy()
    sub["id"] = sub["id"].astype(str)
    sub = sub.rename(
        columns={
            "proba_aanstelling": "proba_r1",
            "bucket": "bucket_r1",
        }
    )
    out = out.merge(sub, on="id", how="left")
    out["r1_joined"] = out["proba_r1"].notna()
    return out


def score_l1_on_empty(
    frame: pd.DataFrame,
    *,
    join_text: bool = True,
    batch_size: int = SCORE_BATCH,
    high_cut: float = HIGH_CUT,
    low_cut: float = LOW_CUT,
) -> pd.DataFrame:
    """Refit L1 on all labelled rows; score empty texts; assign R1-style buckets."""
    out = frame.copy()
    out["id"] = out["id"].astype(str)
    if join_text or "resolutions_text" not in out.columns:
        ids = set(out["id"])
        flat = load("resolutions_flat")
        sub = flat.loc[
            flat["id"].astype(str).isin(ids), ["id", "resolutions_text"]
        ].copy()
        sub["id"] = sub["id"].astype(str)
        if "resolutions_text" in out.columns:
            out = out.drop(columns=["resolutions_text"])
        out = out.merge(sub, on="id", how="left")
    out["resolutions_text"] = out["resolutions_text"].fillna("").astype(str)

    labelled = load("missive_receipt_labelled")
    pipeline = fit_on_all_labelled(labelled)
    texts = out["resolutions_text"]
    n = len(texts)
    proba = np.empty(n, dtype=np.float64)
    step = max(int(batch_size), 1)
    for start in range(0, n, step):
        chunk = texts.iloc[start : start + step]
        proba[start : start + len(chunk)] = missive_proba(pipeline, chunk)
    out["proba_l1"] = proba
    out["bucket_l1"] = assign_buckets(
        out["proba_l1"], high_cut=high_cut, low_cut=low_cut
    )
    out["l1_scored"] = True
    return out


def build_retrieval_frame(
    *,
    year: int = DEFAULT_YEAR,
    score_l1: bool = True,
    join_partition: bool = True,
) -> pd.DataFrame:
    """Empty universe + ES type (from STEPT1e) + R1 join + optional L1 scores."""
    empty = load_empty_universe(year=year)
    frame = empty[["id", "year", "motif_class"]].copy()
    frame["id"] = frame["id"].astype(str)

    if join_partition:
        part = pd.DataFrame(load("ontfangen_partition_scores"))
        part["id"] = part["id"].astype(str)
        part["year"] = pd.to_numeric(part["year"], errors="coerce")
        slice_ = part.loc[part["year"] == int(year), ["id", "proposition_type"]]
        frame = frame.merge(slice_, on="id", how="left")
        missing = frame["proposition_type"].isna()
        frame.loc[missing, "proposition_type"] = NONE_TYPE_KEY
    else:
        frame["proposition_type"] = NONE_TYPE_KEY

    frame = attach_r1_scores(frame)
    if score_l1:
        frame = score_l1_on_empty(frame, join_text=True)
    else:
        frame["proba_l1"] = pd.NA
        frame["bucket_l1"] = pd.NA
        frame["l1_scored"] = False
    return frame


def summarize_empty_retrieval(
    frame: pd.DataFrame,
    *,
    year: int,
    high_cut: float = HIGH_CUT,
    low_cut: float = LOW_CUT,
) -> dict[str, Any]:
    n = len(frame)

    def _by_type(bucket_col: str, proba_col: str) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []
        if "proposition_type" not in frame.columns or bucket_col not in frame.columns:
            return rows
        for ptype, grp in frame.groupby(
            frame["proposition_type"].astype(str), sort=False
        ):
            if len(grp) < 2:
                continue
            rows.append(
                {
                    "proposition_type": str(ptype),
                    "n": int(len(grp)),
                    **{
                        k: v
                        for k, v in _band_summary(grp[proba_col], grp[bucket_col]).items()
                        if k != "n"
                    },
                }
            )
        rows.sort(key=lambda r: -r["n"])
        return rows

    r1 = (
        _band_summary(frame["proba_r1"], frame["bucket_r1"])
        if "proba_r1" in frame.columns
        else {}
    )
    l1_ran = (
        "l1_scored" in frame.columns
        and bool(frame["l1_scored"].fillna(False).astype(bool).any())
    )
    l1 = (
        _band_summary(frame["proba_l1"], frame["bucket_l1"])
        if l1_ran and "proba_l1" in frame.columns
        else {"note": "l1 not scored"}
    )

    # Crosstab: L1 high × ES type (head)
    l1_high_types: list[dict[str, Any]] = []
    if "bucket_l1" in frame.columns and "proposition_type" in frame.columns:
        high = frame.loc[frame["bucket_l1"].astype(str) == BUCKET_HIGH]
        counts = Counter(high["proposition_type"].astype(str).tolist())
        l1_high_types = [
            {"proposition_type": k, "n": int(v)} for k, v in counts.most_common(8)
        ]

    return {
        "step": "STEPT1j2",
        "method": "empty_band_r1_l1_retrieval_probe",
        "year": int(year),
        "universe": "composition_unknown motif_class=empty",
        "constraint": "diagnostic_reuse_frozen_r1_l1_not_new_types",
        "n_empty": n,
        "n_r1_joined": int(frame["r1_joined"].sum()) if "r1_joined" in frame.columns else 0,
        "cuts": {"high": float(high_cut), "low": float(low_cut), "note": "R1 harvest cuts; L1 diagnostic same cuts"},
        "r1": r1,
        "l1": l1,
        "r1_by_proposition_type": _by_type("bucket_r1", "proba_r1")[:12],
        "l1_by_proposition_type": _by_type("bucket_l1", "proba_l1")[:12],
        "l1_high_type_mix": l1_high_types,
        "notes": (
            "R1 from frozen harvest join; L1 = fit_on_all_labelled + score empty. "
            "High/grey/low = diagnostic bands, not L3 harvest. "
            "Ask: does L1 light up empty missives? does R1 stay low (expected)?"
        ),
    }


def fixture_retrieval_frame() -> pd.DataFrame:
    """Tiny frame with synthetic R1/L1 scores (no parquet)."""
    return pd.DataFrame(
        [
            {
                "id": "e1",
                "year": 1780,
                "motif_class": "empty",
                "proposition_type": "rekest",
                "proba_r1": 0.02,
                "bucket_r1": BUCKET_LOW,
                "r1_joined": True,
                "proba_l1": 0.08,
                "bucket_l1": BUCKET_LOW,
                "l1_scored": True,
            },
            {
                "id": "e2",
                "year": 1780,
                "motif_class": "empty",
                "proposition_type": "rekest",
                "proba_r1": 0.03,
                "bucket_r1": BUCKET_LOW,
                "r1_joined": True,
                "proba_l1": 0.12,
                "bucket_l1": BUCKET_LOW,
                "l1_scored": True,
            },
            {
                "id": "e3",
                "year": 1780,
                "motif_class": "empty",
                "proposition_type": "missive",
                "proba_r1": 0.01,
                "bucket_r1": BUCKET_LOW,
                "r1_joined": True,
                "proba_l1": 0.92,
                "bucket_l1": BUCKET_HIGH,
                "l1_scored": True,
            },
            {
                "id": "e4",
                "year": 1780,
                "motif_class": "empty",
                "proposition_type": "missive",
                "proba_r1": 0.04,
                "bucket_r1": BUCKET_LOW,
                "r1_joined": True,
                "proba_l1": 0.88,
                "bucket_l1": BUCKET_HIGH,
                "l1_scored": True,
            },
            {
                "id": "e5",
                "year": 1780,
                "motif_class": "empty",
                "proposition_type": "missive",
                "proba_r1": 0.20,
                "bucket_r1": BUCKET_GREY,
                "r1_joined": True,
                "proba_l1": 0.40,
                "bucket_l1": BUCKET_GREY,
                "l1_scored": True,
            },
            {
                "id": "e6",
                "year": 1780,
                "motif_class": "empty",
                "proposition_type": "voordracht",
                "proba_r1": 0.05,
                "bucket_r1": BUCKET_LOW,
                "r1_joined": True,
                "proba_l1": 0.10,
                "bucket_l1": BUCKET_LOW,
                "l1_scored": True,
            },
        ]
    )
