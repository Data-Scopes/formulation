"""STEPR3: harvest buckets on frozen holdout; remainder excludes gold."""

from __future__ import annotations

import pandas as pd
import pytest

from formulation.aanstelling import LABEL_AANSTELLING, LABEL_OVERIG
from formulation.aanstelling_harvest import (
    BUCKET_GREY,
    BUCKET_HIGH,
    BUCKET_LOW,
    HIGH_CUT,
    LOW_CUT,
    assign_buckets,
    drop_gold,
    gold_resolution_ids,
    harvest_holdout_metrics,
    score_remainder,
)
from formulation.aanstelling_tfidf import fit_on_all_labelled, make_tfidf_pipeline
from scripts.harvest_aanstelling_scores import parse_args


def _labelled(n_per_class: int = 10) -> pd.DataFrame:
    aanstelling = [
        {
            "id": f"session-1-num-1-resolution-{i}",
            "resolutions_text": (
                f"is goedgevonden ende verstaen den heer N{i} te committeren "
                "tot gedeputeerde ter generaliteit"
            ),
            "label": LABEL_AANSTELLING,
            "inventory": "1",
            "paragraph_texts": '["is goedgevonden"]',
            "date": "1780-01-01",
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
            "inventory": "1",
            "paragraph_texts": '["de missive"]',
            "date": "1780-01-02",
        }
        for i in range(n_per_class)
    ]
    return pd.DataFrame(aanstelling + overig)


def test_bucket_cuts_treat_equality_as_grey() -> None:
    scores = pd.Series([0.86, 0.85, 0.5, 0.15, 0.14])
    buckets = assign_buckets(scores)
    assert buckets.tolist() == [
        BUCKET_HIGH,
        BUCKET_GREY,
        BUCKET_GREY,
        BUCKET_GREY,
        BUCKET_LOW,
    ]
    assert HIGH_CUT == 0.85
    assert LOW_CUT == 0.15


def test_drop_gold_keeps_overig_and_archival_columns() -> None:
    labelled = _labelled()
    extra = pd.DataFrame(
        [
            {
                "id": "session-1-num-9-resolution-0",
                "resolutions_text": "een derde resolutie zonder label",
                "inventory": "1",
                "paragraph_texts": '["een derde"]',
                "date": "1780-03-01",
            }
        ]
    )
    remainder = drop_gold(pd.concat([labelled, extra], ignore_index=True), gold_resolution_ids(labelled))
    assert "session-1-num-1-resolution-0" not in set(remainder["id"])
    assert "session-1-num-2-resolution-0" in set(remainder["id"])
    assert "session-1-num-9-resolution-0" in set(remainder["id"])
    for col in ("inventory", "paragraph_texts", "date", "resolutions_text"):
        assert col in remainder.columns


def test_holdout_harvest_metrics_count_gold_per_bucket() -> None:
    holdout = pd.DataFrame(
        {
            "id": ["a", "b", "c", "d"],
            "label": [LABEL_AANSTELLING, LABEL_AANSTELLING, LABEL_OVERIG, LABEL_OVERIG],
            "y_pred": [LABEL_AANSTELLING, LABEL_OVERIG, LABEL_OVERIG, LABEL_AANSTELLING],
            "proba_aanstelling": [0.92, 0.40, 0.05, 0.90],
        }
    )
    metrics = harvest_holdout_metrics(holdout)
    assert metrics["tuned_on_test"] is False
    assert metrics["holdout_metrics_rewritten"] is False
    assert metrics["n_gold_high"] == 1
    assert metrics["n_gold_grey"] == 1
    assert metrics["n_gold_low"] == 0
    assert metrics["n_overig_high"] == 1
    assert metrics["n_overig_low"] == 1
    assert metrics["high_recall"] == pytest.approx(0.5)
    assert metrics["high_precision"] == pytest.approx(0.5)
    assert metrics["high_or_grey_recall"] == pytest.approx(1.0)
    assert "accuracy" not in metrics


def test_score_remainder_keeps_text_and_buckets() -> None:
    labelled = _labelled()
    pipeline = fit_on_all_labelled(labelled)
    remainder = drop_gold(labelled, gold_resolution_ids(labelled))
    scored = score_remainder(remainder, pipeline, batch_size=3)
    assert set(scored["bucket"]).issubset({BUCKET_HIGH, BUCKET_GREY, BUCKET_LOW})
    assert "resolutions_text" in scored.columns
    assert "paragraph_texts" in scored.columns
    assert scored["proba_aanstelling"].between(0.0, 1.0).all()


def test_fit_on_all_labelled_includes_every_row() -> None:
    labelled = _labelled()
    labelled.loc[labelled.index[-1], "resolutions_text"] = "zzzqq unique marker text overig"
    pipe_all = fit_on_all_labelled(labelled)
    vocab = pipe_all.named_steps["tfidf"].vocabulary_
    assert any("zzzqq" in gram for gram in vocab)
    train_only = labelled.iloc[:-1]
    pipe_train = make_tfidf_pipeline()
    pipe_train.fit(train_only["resolutions_text"].astype(str), train_only["label"])
    assert not any("zzzqq" in gram for gram in pipe_train.named_steps["tfidf"].vocabulary_)


def test_year_and_limit_require_poc_flag() -> None:
    args = parse_args(["--poc", "--year", "1780", "--limit", "100"])
    assert args.poc is True
    assert args.year == 1780
    assert args.limit == 100
    args = parse_args([])
    assert args.poc is False
    assert args.year is None
