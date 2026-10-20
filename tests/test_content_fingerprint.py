"""Unit smoke for content fingerprint helpers."""

from __future__ import annotations

import numpy as np

from formulation.content_fingerprint import (
    ContentFingerprint,
    greedy_clusters,
    max_sim_to_exemplars,
    nearest_neighbor_sims,
)


def test_fit_and_self_similarity_high() -> None:
    texts = [
        "is den selven verwelkomt en sessie genomen",
        "geleesen het advis van de raaden van state",
        "ontfangen een missive houdende berigt",
    ]
    fp = ContentFingerprint().fit(texts)
    sim = fp.similarity_matrix(texts)
    assert sim.shape == (3, 3)
    assert float(sim[0, 0]) > 0.9


def test_nearest_neighbor_excludes_self() -> None:
    sim = np.array(
        [
            [1.0, 0.2, 0.8],
            [0.2, 1.0, 0.1],
            [0.8, 0.1, 1.0],
        ]
    )
    nn = nearest_neighbor_sims(sim)
    assert list(nn) == [0.8, 0.2, 0.8]


def test_greedy_clusters_and_exemplars() -> None:
    texts = [
        "aaa appointment welkom sessie",
        "aaa appointment welkom sessie taken",
        "zzz totally different procedural enclosure text",
    ]
    fp = ContentFingerprint().fit(texts)
    sim = fp.similarity_matrix(texts)
    labels = greedy_clusters(sim, cut=0.3)
    assert labels[0] == labels[1]
    der = max_sim_to_exemplars(
        [texts[2]],
        [texts[0]],
        fp,
    )
    assert float(der[0]) < float(fp.pair_score(texts[0], texts[1]))
