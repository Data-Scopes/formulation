"""Character n-gram TF-IDF + LR baseline (Track L, STEPL2).

Same frozen architecture as STEPR2 (char_wb 3–5 + liblinear LR). Positive
class is ``missive_receipt``. Fit only on the stratified train split.
"""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd
from sklearn.metrics import f1_score, precision_score, recall_score
from sklearn.pipeline import Pipeline

from formulation.aanstelling_tfidf import (
    ANALYZER,
    CLASSIFIER_STEP,
    MAX_ITER,
    NGRAM_RANGE,
    RANDOM_STATE,
    SPLIT_TEST,
    TEST_SIZE,
    make_tfidf_pipeline,
    stratified_holdout_frames,
)
from formulation.missive_receipt import LABEL_MISSIVE

REQUIRED_COLS = ("resolutions_text", "label")
SCORE_COLS = ("split", "y_pred", "proba_missive_receipt")


def missive_proba(pipeline: Pipeline, texts: pd.Series | list[str]) -> np.ndarray:
    """P(missive_receipt) aligned to ``pipeline.classes_``."""
    classes = list(pipeline.named_steps[CLASSIFIER_STEP].classes_)
    try:
        idx = classes.index(LABEL_MISSIVE)
    except ValueError as exc:
        raise ValueError(
            f"Fitted classifier has no {LABEL_MISSIVE!r} class; got {classes}"
        ) from exc
    return pipeline.predict_proba(texts)[:, idx]


def holdout_class_metrics(y_true: pd.Series, y_pred: np.ndarray | pd.Series) -> dict[str, float]:
    """Headline retrieval metrics. Accuracy is intentionally omitted."""
    return {
        "recall": float(
            recall_score(y_true, y_pred, pos_label=LABEL_MISSIVE, zero_division=0)
        ),
        "precision": float(
            precision_score(y_true, y_pred, pos_label=LABEL_MISSIVE, zero_division=0)
        ),
        "f1": float(f1_score(y_true, y_pred, pos_label=LABEL_MISSIVE, zero_division=0)),
    }


def fit_on_all_labelled(
    labelled: pd.DataFrame,
    *,
    random_state: int = RANDOM_STATE,
) -> Pipeline:
    """Refit the frozen STEPL2 architecture on every labelled row (STEPL3)."""
    _require_labelled(labelled)
    pipeline = make_tfidf_pipeline(random_state=random_state)
    pipeline.fit(_texts(labelled), labelled["label"])
    return pipeline


def evaluate_holdout(
    labelled: pd.DataFrame,
    *,
    test_size: float = TEST_SIZE,
    random_state: int = RANDOM_STATE,
) -> tuple[pd.DataFrame, dict[str, Any], Pipeline]:
    """Fit on train only; score the test split; keep archival columns."""
    _require_labelled(labelled)
    train, test = stratified_holdout_frames(
        labelled, test_size=test_size, random_state=random_state
    )
    overlap = set(train["id"].astype(str)) & set(test["id"].astype(str))
    if overlap:
        raise ValueError(f"Train/test id leakage: {sorted(overlap)[:5]}")

    train_text = _texts(train)
    test_text = _texts(test)
    pipeline = make_tfidf_pipeline(random_state=random_state)
    pipeline.fit(train_text, train["label"])

    y_pred = pipeline.predict(test_text)
    proba = missive_proba(pipeline, test_text)
    scored = test.copy()
    scored["split"] = SPLIT_TEST
    scored["y_pred"] = y_pred
    scored["proba_missive_receipt"] = proba

    metrics = _jsonable(
        {
            **holdout_class_metrics(test["label"], y_pred),
            "n_labelled": int(len(labelled)),
            "n_train": int(len(train)),
            "n_test": int(len(test)),
            "n_train_missive_receipt": int(train["label"].eq(LABEL_MISSIVE).sum()),
            "n_test_missive_receipt": int(test["label"].eq(LABEL_MISSIVE).sum()),
            "vectorizer": "TfidfVectorizer",
            "analyzer": ANALYZER,
            "ngram_range": f"{NGRAM_RANGE[0]}-{NGRAM_RANGE[1]}",
            "classifier": "LogisticRegression",
            "solver": "liblinear",
            "max_iter": MAX_ITER,
            "test_size": test_size,
            "random_state": random_state,
            "tuned_on_test": False,
            "headline_metric": "recall",
            "positive_label": LABEL_MISSIVE,
            "track": "L1",
            "step": "STEPL2",
        }
    )
    return scored, metrics, pipeline


def _require_labelled(labelled: pd.DataFrame) -> None:
    missing = [c for c in REQUIRED_COLS if c not in labelled.columns]
    if missing:
        raise ValueError(f"Labelled table missing columns: {missing}")
    if "id" not in labelled.columns:
        raise ValueError("Labelled table missing id column")


def _texts(frame: pd.DataFrame) -> pd.Series:
    return frame["resolutions_text"].fillna("").astype(str)


def _jsonable(metrics: dict[str, Any]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for key, value in metrics.items():
        if isinstance(value, (np.floating, float)):
            out[key] = float(value)
        elif isinstance(value, (np.integer, int)) and not isinstance(value, bool):
            out[key] = int(value)
        elif isinstance(value, np.bool_):
            out[key] = bool(value)
        else:
            out[key] = value
    return out
