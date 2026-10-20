"""Score unlabelled resolutions into high / grey / low (Track R, STEPR3).

Holdout metrics stay frozen from STEPR2 (0.5 threshold). Harvest cuts are
separate: high > 0.85, low < 0.15, grey between. Adjust only with a written
reason in docs/DECISIONS.md.
"""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd
import pyarrow.parquet as pq
from sklearn.pipeline import Pipeline

from data_io import resolve
from formulation.aanstelling import LABEL_AANSTELLING, LABEL_OVERIG
from formulation.aanstelling_tfidf import (
    aanstelling_proba,
    holdout_class_metrics,
    _jsonable,
    _texts,
)

BUCKET_HIGH = "high"
BUCKET_GREY = "grey"
BUCKET_LOW = "low"
HIGH_CUT = 0.85
LOW_CUT = 0.15
SCORE_BATCH = 4096
POC_YEAR = 1780
LOGICAL_HARVEST = "aanstelling_tfidf_harvest"
LOGICAL_HARVEST_POC = "aanstelling_tfidf_harvest_poc"
LOGICAL_POC_METRICS = "aanstelling_tfidf_harvest_poc_metrics"
SCORE_COLS = ("y_pred", "proba_aanstelling", "bucket")


def assign_buckets(
    proba: pd.Series | np.ndarray,
    *,
    high_cut: float = HIGH_CUT,
    low_cut: float = LOW_CUT,
) -> pd.Series:
    """Vectorized high / grey / low. Equality at a cut is grey."""
    if high_cut <= low_cut:
        raise ValueError(f"high_cut ({high_cut}) must be > low_cut ({low_cut})")
    scores = pd.Series(proba, dtype="float64")
    buckets = pd.Series(BUCKET_GREY, index=scores.index, dtype="string")
    buckets = buckets.mask(scores > high_cut, BUCKET_HIGH)
    buckets = buckets.mask(scores < low_cut, BUCKET_LOW)
    return buckets


def gold_resolution_ids(labelled: pd.DataFrame) -> pd.Index:
    if "label" not in labelled.columns or "id" not in labelled.columns:
        raise ValueError("Labelled table needs id and label")
    return labelled.loc[labelled["label"].eq(LABEL_AANSTELLING), "id"].astype(str)


def drop_gold(frame: pd.DataFrame, gold_ids: pd.Series | pd.Index | set[str]) -> pd.DataFrame:
    """Unlabelled remainder: every row except known aanstelling positives."""
    if "id" not in frame.columns:
        raise ValueError("Frame missing id column")
    exclude = set(map(str, gold_ids))
    return frame.loc[~frame["id"].astype(str).isin(exclude)].reset_index(drop=True)


def score_remainder(
    frame: pd.DataFrame,
    pipeline: Pipeline,
    *,
    batch_size: int = SCORE_BATCH,
    high_cut: float = HIGH_CUT,
    low_cut: float = LOW_CUT,
) -> pd.DataFrame:
    """Keep archival columns; add y_pred / proba_aanstelling / bucket."""
    if "resolutions_text" not in frame.columns:
        raise ValueError("Remainder missing resolutions_text")
    texts = _texts(frame)
    n = len(texts)
    pred = np.empty(n, dtype=object)
    proba = np.empty(n, dtype=np.float64)
    step = max(int(batch_size), 1)
    for start in range(0, n, step):
        chunk = texts.iloc[start : start + step]
        pred[start : start + len(chunk)] = pipeline.predict(chunk)
        proba[start : start + len(chunk)] = aanstelling_proba(pipeline, chunk)
    out = frame.copy()
    out["y_pred"] = pred
    out["proba_aanstelling"] = proba
    out["bucket"] = assign_buckets(out["proba_aanstelling"], high_cut=high_cut, low_cut=low_cut)
    return out


def harvest_holdout_metrics(
    holdout: pd.DataFrame,
    *,
    high_cut: float = HIGH_CUT,
    low_cut: float = LOW_CUT,
) -> dict[str, Any]:
    """Harvest-cut metrics on the frozen STEPR2 holdout. Does not refit."""
    missing = [c for c in ("label", "proba_aanstelling") if c not in holdout.columns]
    if missing:
        raise ValueError(f"Holdout missing columns: {missing}")
    if "y_pred" not in holdout.columns:
        raise ValueError("Holdout missing y_pred")

    at_default = holdout_class_metrics(holdout["label"], holdout["y_pred"])
    proba = holdout["proba_aanstelling"].astype("float64")
    buckets = assign_buckets(proba, high_cut=high_cut, low_cut=low_cut)
    gold = holdout["label"].eq(LABEL_AANSTELLING)
    high = buckets.eq(BUCKET_HIGH)
    grey = buckets.eq(BUCKET_GREY)
    low = buckets.eq(BUCKET_LOW)
    pred_high = np.where(high, LABEL_AANSTELLING, LABEL_OVERIG)
    pred_review = np.where(high | grey, LABEL_AANSTELLING, LABEL_OVERIG)
    at_high = holdout_class_metrics(holdout["label"], pred_high)
    at_review = holdout_class_metrics(holdout["label"], pred_review)
    return _jsonable(
        {
            "recall": at_default["recall"],
            "precision": at_default["precision"],
            "f1": at_default["f1"],
            "high_recall": at_high["recall"],
            "high_precision": at_high["precision"],
            "high_f1": at_high["f1"],
            "high_or_grey_recall": at_review["recall"],
            "high_or_grey_precision": at_review["precision"],
            "high_or_grey_f1": at_review["f1"],
            "n_test": int(len(holdout)),
            "n_test_aanstelling": int(gold.sum()),
            "n_high": int(high.sum()),
            "n_grey": int(grey.sum()),
            "n_low": int(low.sum()),
            "n_gold_high": int((gold & high).sum()),
            "n_gold_grey": int((gold & grey).sum()),
            "n_gold_low": int((gold & low).sum()),
            "n_overig_high": int((~gold & high).sum()),
            "n_overig_grey": int((~gold & grey).sum()),
            "n_overig_low": int((~gold & low).sum()),
            "high_cut": float(high_cut),
            "low_cut": float(low_cut),
            "threshold_default": 0.5,
            "tuned_on_test": False,
            "holdout_metrics_rewritten": False,
            "headline_metric": "recall",
        }
    )


def load_resolutions_flat(
    *,
    year: int | None = None,
    limit: int | None = None,
) -> pd.DataFrame:
    """Read ``resolutions_flat``; optional year pushdown and head() cap (POC)."""
    path = resolve("resolutions_flat")
    filters = None if year is None else [("year", "=", int(year))]
    table = pq.read_table(path, filters=filters)
    frame = table.to_pandas()
    if year is not None and frame.empty:
        raise ValueError(f"resolutions_flat has no rows for year={year}")
    if limit is not None:
        frame = frame.head(int(limit))
    return frame


def remainder_bucket_counts(scored: pd.DataFrame) -> dict[str, int]:
    counts = scored["bucket"].value_counts()
    return {
        "n_remainder": int(len(scored)),
        "n_remainder_high": int(counts.get(BUCKET_HIGH, 0)),
        "n_remainder_grey": int(counts.get(BUCKET_GREY, 0)),
        "n_remainder_low": int(counts.get(BUCKET_LOW, 0)),
    }
