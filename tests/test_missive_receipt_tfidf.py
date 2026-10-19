"""STEPL2: char_wb TF-IDF + LR fit on train only; missive_receipt headline metrics."""

from __future__ import annotations

import pandas as pd
import pytest

from formulation.aanstelling_tfidf import (
    ANALYZER,
    NGRAM_RANGE,
    SPLIT_TEST,
    make_tfidf_pipeline,
    stratified_holdout_frames,
)
from formulation.missive_receipt import LABEL_MISSIVE, LABEL_OVERIG
from formulation.missive_receipt_tfidf import evaluate_holdout


def _toy(n_per_class: int = 10) -> pd.DataFrame:
    positives = [
        {
            "id": f"session-1-num-1-resolution-{i}",
            "resolutions_text": (
                f"Ontfangen een missive van den heer N{i} houdende advertentie "
                "WAAR op geen resolutie is gevallen"
            ),
            "label": LABEL_MISSIVE,
            "inventory": "1",
            "positive_source": "cue_both",
            "year": 1780,
        }
        for i in range(n_per_class)
    ]
    overig = [
        {
            "id": f"session-1-num-2-resolution-{i}",
            "resolutions_text": (
                f"is goedgevonden ende verstaen den heer N{i} te committeren "
                "tot gedeputeerde ter generaliteit"
            ),
            "label": LABEL_OVERIG,
            "inventory": "1",
            "positive_source": "",
            "year": 1780,
        }
        for i in range(n_per_class)
    ]
    return pd.DataFrame(positives + overig)


def test_reuses_char_wb_3_to_5_pipeline() -> None:
    pipe = make_tfidf_pipeline()
    assert pipe.named_steps["tfidf"].analyzer == ANALYZER == "char_wb"
    assert pipe.named_steps["tfidf"].ngram_range == NGRAM_RANGE == (3, 5)


def test_split_disjoint_stratified() -> None:
    labelled = _toy()
    train, test = stratified_holdout_frames(labelled)
    assert set(train["id"]).isdisjoint(set(test["id"]))
    assert train["label"].eq(LABEL_MISSIVE).mean() == pytest.approx(0.5)


def test_holdout_keeps_fields_and_reports_headline_metrics() -> None:
    labelled = _toy()
    scored, metrics, _pipe = evaluate_holdout(labelled)
    assert set(scored["split"]) == {SPLIT_TEST}
    assert len(scored) == metrics["n_test"]
    for col in ("id", "inventory", "positive_source", "resolutions_text"):
        assert col in scored.columns
    assert "y_pred" in scored.columns
    assert "proba_missive_receipt" in scored.columns
    assert metrics["tuned_on_test"] is False
    assert metrics["headline_metric"] == "recall"
    assert metrics["positive_label"] == LABEL_MISSIVE
    assert metrics["track"] == "L1"
    assert metrics["analyzer"] == "char_wb"
    assert metrics["ngram_range"] == "3-5"
    for key in ("recall", "precision", "f1"):
        assert 0.0 <= metrics[key] <= 1.0
    assert "accuracy" not in metrics


def test_missing_text_column_raises() -> None:
    with pytest.raises(ValueError, match="resolutions_text"):
        evaluate_holdout(pd.DataFrame({"id": ["a"], "label": [LABEL_MISSIVE]}))
