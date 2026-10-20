"""STEPR2: char_wb TF-IDF + LR is fit on train only; headline metrics exist."""

from __future__ import annotations

import pandas as pd
import pytest
from sklearn.linear_model import LogisticRegression

from formulation.aanstelling import LABEL_AANSTELLING, LABEL_OVERIG
from formulation.aanstelling_tfidf import (
    ANALYZER,
    CLASSIFIER_STEP,
    NGRAM_RANGE,
    SPLIT_TEST,
    VECTORIZER_STEP,
    evaluate_holdout,
    make_tfidf_pipeline,
    stratified_holdout_frames,
)


def _toy(n_per_class: int = 10) -> pd.DataFrame:
    aanstelling = [
        {
            "id": f"session-1-num-1-resolution-{i}",
            "resolutions_text": (
                f"is goedgevonden ende verstaen den heer N{i} te committeren "
                "tot gedeputeerde ter generaliteit"
            ),
            "label": LABEL_AANSTELLING,
            "gold_urns": f"urn:republic:inv-1-date-1700-01-01-session-1-resolution-{i}",
            "inventory": "1",
            "paragraph_texts": '["is goedgevonden"]',
        }
        for i in range(n_per_class)
    ]
    overig = [
        {
            "id": f"session-1-num-2-resolution-{i}",
            "resolutions_text": (
                f"de missive van den raadpensionaris N{i} in handen gesteld "
                "van de heeren van de finantie"
            ),
            "label": LABEL_OVERIG,
            "gold_urns": "",
            "inventory": "1",
            "paragraph_texts": '["de missive"]',
        }
        for i in range(n_per_class)
    ]
    return pd.DataFrame(aanstelling + overig)


def test_pipeline_is_char_wb_3_to_5() -> None:
    pipe = make_tfidf_pipeline()
    vec = pipe.named_steps[VECTORIZER_STEP]
    clf = pipe.named_steps[CLASSIFIER_STEP]
    assert vec.analyzer == ANALYZER == "char_wb"
    assert vec.ngram_range == NGRAM_RANGE == (3, 5)
    assert isinstance(clf, LogisticRegression)


def test_split_is_stratified_reproducible_and_disjoint() -> None:
    labelled = _toy()
    train_a, test_a = stratified_holdout_frames(labelled)
    train_b, test_b = stratified_holdout_frames(labelled)
    assert train_a["id"].tolist() == train_b["id"].tolist()
    assert test_a["id"].tolist() == test_b["id"].tolist()
    assert set(train_a["id"]).isdisjoint(set(test_a["id"]))
    assert len(test_a) == 4
    assert train_a["label"].eq(LABEL_AANSTELLING).mean() == pytest.approx(0.5)
    assert test_a["label"].eq(LABEL_AANSTELLING).mean() == pytest.approx(0.5)


def test_vectorizer_vocabulary_excludes_held_out_marker() -> None:
    labelled = _toy()
    train, test = stratified_holdout_frames(labelled)
    test = test.copy()
    test.loc[test.index[0], "resolutions_text"] = "zzzqqqunique marker text"
    pipe = make_tfidf_pipeline()
    pipe.fit(train["resolutions_text"].astype(str), train["label"])
    vocab = pipe.named_steps[VECTORIZER_STEP].vocabulary_
    assert not any("zzzqqq" in gram for gram in vocab)
    assert any("ged" in gram for gram in vocab)


def test_holdout_keeps_archival_fields_and_reports_headline_metrics() -> None:
    labelled = _toy()
    scored, metrics, _pipe = evaluate_holdout(labelled)
    assert set(scored["split"]) == {SPLIT_TEST}
    assert len(scored) == metrics["n_test"]
    for col in ("id", "gold_urns", "inventory", "paragraph_texts", "resolutions_text"):
        assert col in scored.columns
    assert "y_pred" in scored.columns
    assert "proba_aanstelling" in scored.columns
    assert metrics["tuned_on_test"] is False
    assert metrics["headline_metric"] == "recall"
    assert metrics["analyzer"] == "char_wb"
    assert metrics["ngram_range"] == "3-5"
    for key in ("recall", "precision", "f1"):
        assert 0.0 <= metrics[key] <= 1.0
        assert key in metrics
    assert "accuracy" not in metrics


def test_missing_text_column_raises() -> None:
    with pytest.raises(ValueError, match="resolutions_text"):
        evaluate_holdout(pd.DataFrame({"id": ["a"], "label": [LABEL_AANSTELLING]}))
