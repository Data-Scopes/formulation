"""Unit smoke for STEPT1j empty-band characterisation (no parquet)."""

from __future__ import annotations

from formulation.content_fingerprint import ContentFingerprint, greedy_clusters
from formulation.empty_band import (
    DEFAULT_FP_CUTS,
    fixture_empty_frame,
    summarize_empty_band,
)


def test_fixture_has_empty_motif_and_types() -> None:
    frame = fixture_empty_frame()
    assert (frame["motif_class"] == "empty").all()
    assert frame["proposition_type"].nunique() >= 3
    assert "requeste_start" in frame.attrs["flag_columns"]


def test_summarize_empty_band_shape() -> None:
    frame = fixture_empty_frame()
    metrics = summarize_empty_band(frame, year=1780)
    assert metrics["step"] == "STEPT1j"
    assert metrics["n_empty"] == len(frame)
    assert metrics["type_mix"]
    assert metrics["length"]["median"] is not None
    assert "subtypes" not in metrics
    assert metrics["known_set_leakage"]["n_ontfangen_present"] == 0


def test_tighter_fp_cut_can_split_fixture() -> None:
    frame = fixture_empty_frame()
    texts = frame["resolutions_text"].tolist()
    fp = ContentFingerprint().fit(texts)
    sim = fp.similarity_matrix(texts)
    loose = greedy_clusters(sim, cut=0.15)
    tight = greedy_clusters(sim, cut=0.60)
    # Fixture has rekest-like vs rapport-like vs other — tight cut should
    # not collapse everything if texts differ enough.
    assert len(set(loose.tolist())) >= 1
    assert len(set(tight.tolist())) >= len(set(loose.tolist()))


def test_default_fp_cuts_include_baseline_and_tighter() -> None:
    assert 0.15 in DEFAULT_FP_CUTS
    assert max(DEFAULT_FP_CUTS) > 0.15
