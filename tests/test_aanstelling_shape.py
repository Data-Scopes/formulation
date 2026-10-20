"""Length + TF-IDF cosine-to-gold shape scores for harvest cleaning."""

from __future__ import annotations

import pandas as pd

from formulation.aanstelling_shape import (
    MIN_CHARS,
    add_shape_scores,
    cosine_to_centroid,
    fit_gold_centroid,
    text_lengths,
)


def test_text_lengths() -> None:
    lengths = text_lengths(pd.Series(["Heer", "een twee drie"]))
    assert lengths["n_chars"].tolist() == [4, 13]
    assert lengths["n_words"].tolist() == [1, 3]


def test_short_stub_flagged() -> None:
    gold = pd.Series(
        [
            (
                f"is goedgevonden ende verstaen den heer naam{i} "
                "te committeren tot gedeputeerde ter generaliteit "
                "van wegen de provincie holland"
            )
            for i in range(20)
        ]
    )
    vectorizer, centroid, cos_cut = fit_gold_centroid(gold)
    frame = pd.DataFrame(
        {
            "id": ["stub"],
            "resolutions_text": ["Heer"],
        }
    )
    scored = add_shape_scores(frame, vectorizer, centroid, cos_cut=cos_cut)
    assert bool(scored.loc[0, "suspect"])
    assert scored.loc[0, "suspect_reason"] in {"short", "short+low_cos"}
    assert int(scored.loc[0, "n_chars"]) < MIN_CHARS


def test_explicit_low_cos_reason() -> None:
    gold = pd.Series(
        [
            "is goedgevonden ende verstaen den heer te committeren tot gedeputeerde"
            for _ in range(10)
        ]
    )
    vectorizer, centroid, _ = fit_gold_centroid(gold)
    long_other = (
        "WAAR op gedelibereert zynde heeft den aanweesende Heer Gedeputeerde "
        "van de Provincie van Zeeland aangenoomen sig in weinige dagen nader "
        "daar op te sullen verklaaren over de missive"
    )
    frame = pd.DataFrame({"id": ["other"], "resolutions_text": [long_other]})
    scored = add_shape_scores(frame, vectorizer, centroid, cos_cut=0.99, min_chars=50)
    assert bool(scored.loc[0, "suspect"])
    assert scored.loc[0, "suspect_reason"] == "low_cos"


def test_weighted_centroid_favors_heavy_row() -> None:
    anchor = (
        "is goedgevonden ende verstaen den heer te committeren tot gedeputeerde "
        "ter generaliteit van wegen de provincie holland"
    )
    other = "WAAR op gedelibereert zynde heeft den aanweesende Heer Gedeputeerde"
    gold = pd.Series([anchor, other])
    vec, cent_equal, _ = fit_gold_centroid(gold)
    _, cent_heavy, _ = fit_gold_centroid(gold, sample_weight=[10.0, 1.0])
    cos_anchor_equal = cosine_to_centroid(pd.Series([anchor]), vec, cent_equal)[0]
    cos_anchor_heavy = cosine_to_centroid(pd.Series([anchor]), vec, cent_heavy)[0]
    assert cos_anchor_heavy > cos_anchor_equal


def test_cos_cut_is_gold_percentile() -> None:
    gold = pd.Series(
        [
            f"is goedgevonden den heer N{i} te committeren tot gedeputeerde ter generaliteit"
            for i in range(20)
        ]
    )
    _, _, cos_cut = fit_gold_centroid(gold)
    assert 0.0 < cos_cut <= 1.0
