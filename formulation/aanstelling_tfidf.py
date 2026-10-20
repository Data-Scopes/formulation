"""Character n-gram TF-IDF + logistic regression baseline (Track R, STEPR2).

Fits only on the stratified train split. Holdout metrics are recall, precision,
and F1 for the aanstelling class. Does not call FormulaSearch or Elasticsearch.
"""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import f1_score, precision_score, recall_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline

from formulation.aanstelling import LABEL_AANSTELLING

ANALYZER = "char_wb"
NGRAM_RANGE = (3, 5)
TEST_SIZE = 0.2
RANDOM_STATE = 42
MAX_ITER = 1000
SPLIT_TEST = "test"
VECTORIZER_STEP = "tfidf"
CLASSIFIER_STEP = "lr"

REQUIRED_COLS = ("resolutions_text", "label")
SCORE_COLS = ("split", "y_pred", "proba_aanstelling")


def make_tfidf_pipeline(
    *,
    random_state: int = RANDOM_STATE,
) -> Pipeline:
    """char_wb 3–5 TF-IDF plus logistic regression. Hyperparameters are fixed."""
    return Pipeline(
        [
            (
                VECTORIZER_STEP,
                TfidfVectorizer(analyzer=ANALYZER, ngram_range=NGRAM_RANGE),
            ),
            (
                CLASSIFIER_STEP,
                LogisticRegression(
                    max_iter=MAX_ITER,
                    random_state=random_state,
                    solver="liblinear",
                ),
            ),
        ]
    )


def stratified_holdout_frames(
    labelled: pd.DataFrame,
    *,
    test_size: float = TEST_SIZE,
    random_state: int = RANDOM_STATE,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """80/20 stratified split on ``label``. Test rows are never passed to ``fit``."""
    _require_labelled(labelled)
    counts = labelled["label"].value_counts()
    if counts.min() < 2:
        raise ValueError(
            "Stratified split needs at least two rows per label; "
            f"got {counts.to_dict()}"
        )
    train, test = train_test_split(
        labelled,
        test_size=test_size,
        stratify=labelled["label"],
        random_state=random_state,
    )
    return train.reset_index(drop=True), test.reset_index(drop=True)


def aanstelling_proba(pipeline: Pipeline, texts: pd.Series | list[str]) -> np.ndarray:
    """P(aanstelling) aligned to ``pipeline.classes_``."""
    classes = list(pipeline.named_steps[CLASSIFIER_STEP].classes_)
    try:
        idx = classes.index(LABEL_AANSTELLING)
    except ValueError as exc:
        raise ValueError(
            f"Fitted classifier has no {LABEL_AANSTELLING!r} class; got {classes}"
        ) from exc
    return pipeline.predict_proba(texts)[:, idx]


def holdout_class_metrics(y_true: pd.Series, y_pred: np.ndarray | pd.Series) -> dict[str, float]:
    """Headline retrieval metrics. Accuracy is intentionally omitted."""
    return {
        "recall": float(
            recall_score(y_true, y_pred, pos_label=LABEL_AANSTELLING, zero_division=0)
        ),
        "precision": float(
            precision_score(y_true, y_pred, pos_label=LABEL_AANSTELLING, zero_division=0)
        ),
        "f1": float(f1_score(y_true, y_pred, pos_label=LABEL_AANSTELLING, zero_division=0)),
    }


def fit_on_all_labelled(
    labelled: pd.DataFrame,
    *,
    random_state: int = RANDOM_STATE,
) -> Pipeline:
    """Refit the frozen STEPR2 architecture on every labelled row (STEPR3).

    Does not touch holdout metrics. Those stay on the train-only split.
    """
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
    """Fit on train only; score the test split; keep archival columns.

    Returns ``(holdout_rows, metrics, fitted_train_pipeline)``. The pipeline is
    not refit on the test split. STEPR3 refits the same architecture on all
    labelled rows after these metrics are frozen.
    """
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
    proba = aanstelling_proba(pipeline, test_text)
    scored = test.copy()
    scored["split"] = SPLIT_TEST
    scored["y_pred"] = y_pred
    scored["proba_aanstelling"] = proba

    metrics = _jsonable(
        {
            **holdout_class_metrics(test["label"], y_pred),
            "n_labelled": int(len(labelled)),
            "n_train": int(len(train)),
            "n_test": int(len(test)),
            "n_train_aanstelling": int(train["label"].eq(LABEL_AANSTELLING).sum()),
            "n_test_aanstelling": int(test["label"].eq(LABEL_AANSTELLING).sum()),
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
