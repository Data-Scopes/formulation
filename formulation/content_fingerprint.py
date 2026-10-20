"""Content fingerprint (word + char TF-IDF blend) for STEPT1i.

Formulation-owned; not the republic_ner ALIGNED_TO / enriched↔HTR bridge.
Used to score derivative-vs-novel on undecided resolution texts.
"""

from __future__ import annotations

from typing import Sequence

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# Match NER TrainFittedTfidfFingerprint blend (pedigree only).
WORD_WEIGHT = 0.4
CHAR_WEIGHT = 0.6
DEFAULT_FP_CUT = 0.15

__all__ = (
    "CHAR_WEIGHT",
    "ContentFingerprint",
    "DEFAULT_FP_CUT",
    "WORD_WEIGHT",
    "greedy_clusters",
    "max_sim_to_exemplars",
    "nearest_neighbor_sims",
)


def _norm_texts(texts: Sequence[str]) -> list[str]:
    return [t.strip() if t and str(t).strip() else " " for t in texts]


class ContentFingerprint:
    """Word(1–2) + char_wb(3–5) TF-IDF; cosine blend."""

    def __init__(self) -> None:
        self.word = TfidfVectorizer(ngram_range=(1, 2), sublinear_tf=True, min_df=1)
        self.char = TfidfVectorizer(
            analyzer="char_wb",
            ngram_range=(3, 5),
            sublinear_tf=True,
            min_df=1,
        )
        self._fitted = False

    def fit(self, texts: Sequence[str]) -> ContentFingerprint:
        corpus = _norm_texts(texts)
        if len(corpus) < 2:
            raise ValueError("need >= 2 texts to fit content fingerprint")
        self.word.fit(corpus)
        self.char.fit(corpus)
        self._fitted = True
        return self

    def similarity_matrix(
        self,
        texts_a: Sequence[str],
        texts_b: Sequence[str] | None = None,
    ) -> np.ndarray:
        if not self._fitted:
            raise RuntimeError("fit() before similarity_matrix()")
        a = _norm_texts(texts_a)
        b = _norm_texts(texts_b) if texts_b is not None else a
        if not a or not b:
            return np.zeros((len(a), len(b)), dtype=np.float64)
        sim_w = cosine_similarity(self.word.transform(a), self.word.transform(b))
        sim_c = cosine_similarity(self.char.transform(a), self.char.transform(b))
        return np.clip(WORD_WEIGHT * sim_w + CHAR_WEIGHT * sim_c, 0.0, 1.0)

    def pair_score(self, text_a: str, text_b: str) -> float:
        return float(self.similarity_matrix([text_a], [text_b])[0, 0])


def nearest_neighbor_sims(sim: np.ndarray) -> np.ndarray:
    """Max off-diagonal similarity per row (self excluded)."""
    n = sim.shape[0]
    if n == 0:
        return np.array([], dtype=np.float64)
    if n == 1:
        return np.array([0.0], dtype=np.float64)
    masked = sim.copy()
    np.fill_diagonal(masked, -1.0)
    return masked.max(axis=1)


def max_sim_to_exemplars(
    query_texts: Sequence[str],
    exemplar_texts: Sequence[str],
    fingerprint: ContentFingerprint,
) -> np.ndarray:
    """Per query: max cosine to any exemplar (0 if no exemplars)."""
    if not exemplar_texts:
        return np.zeros(len(query_texts), dtype=np.float64)
    if not query_texts:
        return np.array([], dtype=np.float64)
    sim = fingerprint.similarity_matrix(query_texts, exemplar_texts)
    return sim.max(axis=1)


def greedy_clusters(
    sim: np.ndarray,
    *,
    cut: float = DEFAULT_FP_CUT,
) -> np.ndarray:
    """Union-find style: link i–j if sim[i,j] >= cut; return cluster labels 0..k-1."""
    n = sim.shape[0]
    parent = list(range(n))

    def find(x: int) -> int:
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(a: int, b: int) -> None:
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[rb] = ra

    for i in range(n):
        for j in range(i + 1, n):
            if float(sim[i, j]) >= float(cut):
                union(i, j)

    roots = [find(i) for i in range(n)]
    remap: dict[int, int] = {}
    labels = np.zeros(n, dtype=int)
    next_id = 0
    for i, r in enumerate(roots):
        if r not in remap:
            remap[r] = next_id
            next_id += 1
        labels[i] = remap[r]
    return labels
