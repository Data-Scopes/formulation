"""Post-harvest shape checks: length + TF-IDF cosine to gold centroid.

Filters odd short / off-type candidates in ingest and review without a neural
pass. Same ``char_wb`` 3–5 vectorizer family as STEPR2.
"""

from __future__ import annotations

from typing import Any, Sequence

import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from formulation.aanstelling_tfidf import ANALYZER, NGRAM_RANGE

# Hard floor: gold min length is ~147; stubs like "Heer" are far below.
MIN_CHARS = 200
# Cosine cut is the 5th percentile of gold→centroid self-similarity.
GOLD_COS_PERCENTILE = 5.0


def text_lengths(texts: pd.Series) -> pd.DataFrame:
    cleaned = texts.fillna("").astype(str)
    return pd.DataFrame(
        {
            "n_chars": cleaned.str.len().astype(int),
            "n_words": cleaned.str.split().str.len().fillna(0).astype(int),
        },
        index=texts.index,
    )


def fit_gold_centroid(
    gold_texts: pd.Series,
    *,
    sample_weight: Sequence[float] | np.ndarray | None = None,
    analyzer: str = ANALYZER,
    ngram_range: tuple[int, int] = NGRAM_RANGE,
) -> tuple[TfidfVectorizer, np.ndarray, float]:
    """Fit char n-gram TF-IDF on gold; return vectorizer, centroid, cos cut.

    Optional ``sample_weight`` (one per row) builds a weighted centroid so
    period-specific gold can dominate without dropping other positives.
    """
    cleaned = gold_texts.fillna("").astype(str)
    if cleaned.empty:
        raise ValueError("Need at least one gold text to fit the centroid")
    vectorizer = TfidfVectorizer(analyzer=analyzer, ngram_range=ngram_range)
    matrix = vectorizer.fit_transform(cleaned)
    if sample_weight is None:
        centroid = np.asarray(matrix.mean(axis=0))
    else:
        weights = np.asarray(sample_weight, dtype=float).reshape(-1)
        if weights.shape[0] != matrix.shape[0]:
            raise ValueError("sample_weight length must match gold_texts")
        if np.any(weights < 0):
            raise ValueError("sample_weight must be non-negative")
        total = float(weights.sum())
        if total <= 0:
            raise ValueError("sample_weight must sum to a positive value")
        row = np.asarray(matrix.T.dot(weights / total)).reshape(1, -1)
        centroid = row
    self_cos = cosine_similarity(matrix, centroid).ravel()
    cos_cut = float(np.percentile(self_cos, GOLD_COS_PERCENTILE))
    return vectorizer, centroid, cos_cut


def cosine_to_centroid(
    texts: pd.Series,
    vectorizer: TfidfVectorizer,
    centroid: np.ndarray,
) -> np.ndarray:
    matrix = vectorizer.transform(texts.fillna("").astype(str))
    return cosine_similarity(matrix, centroid).ravel()


def add_shape_scores(
    frame: pd.DataFrame,
    vectorizer: TfidfVectorizer,
    centroid: np.ndarray,
    *,
    cos_cut: float,
    min_chars: int = MIN_CHARS,
    text_col: str = "resolutions_text",
) -> pd.DataFrame:
    """Add ``n_chars``, ``n_words``, ``cos_gold``, ``suspect`` (+ reason)."""
    if text_col not in frame.columns:
        raise ValueError(f"Frame missing {text_col!r}")
    out = frame.copy()
    lengths = text_lengths(out[text_col])
    out["n_chars"] = lengths["n_chars"]
    out["n_words"] = lengths["n_words"]
    out["cos_gold"] = cosine_to_centroid(out[text_col], vectorizer, centroid)
    short = out["n_chars"] < int(min_chars)
    odd = out["cos_gold"] < float(cos_cut)
    out["suspect"] = short | odd
    reason = np.where(
        short & odd,
        "short+low_cos",
        np.where(short, "short", np.where(odd, "low_cos", "")),
    )
    out["suspect_reason"] = reason
    out.attrs["shape_min_chars"] = int(min_chars)
    out.attrs["shape_cos_cut"] = float(cos_cut)
    return out


def shape_cut_summary(
    *,
    min_chars: int,
    cos_cut: float,
    gold: pd.DataFrame,
    ingest: pd.DataFrame,
    review: pd.DataFrame,
) -> list[dict[str, Any]]:
    return [
        {"item": "shape_min_chars", "value": min_chars},
        {"item": "shape_cos_cut", "value": round(float(cos_cut), 6)},
        {"item": "shape_cos_percentile", "value": GOLD_COS_PERCENTILE},
        {
            "item": "suspect_gold",
            "value": int(gold["suspect"].sum()) if "suspect" in gold else 0,
        },
        {
            "item": "suspect_ingest",
            "value": int(ingest["suspect"].sum()) if "suspect" in ingest else 0,
        },
        {
            "item": "suspect_review",
            "value": int(review["suspect"].sum()) if "suspect" in review else 0,
        },
    ]
