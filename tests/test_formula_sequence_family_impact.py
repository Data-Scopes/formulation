"""STEPT1ac family-exemplar harvest / soft containment tests."""

from __future__ import annotations

from formulation.formula_family_fold import fixture_fold, fold_phrases
from formulation.formula_sequence_family_impact import (
    catalog_impact_summary,
    family_exemplar_harvest,
    soft_containment_rate,
    surface_contained,
)
from formulation.phrases_5gram_profile import normalize_phrase


def test_exemplar_harvest_caps_and_keeps_pockets() -> None:
    fams = fixture_fold()["families"]
    harvest = family_exemplar_harvest(fams, max_n=10)
    assert any(h.get("source") == "empty_band_1780" for h in harvest)
    assert len(harvest) <= 10
    assert all(h.get("surface") for h in harvest)


def test_soft_containment_sliding_windows() -> None:
    rows = [
        {
            "phrase": "op geen resolutie is gevallen",
            "phrase_norm": normalize_phrase("op geen resolutie is gevallen"),
            "phrase_freq": 80000,
            "zone": "close",
            "lcats": "small",
            "suggested_role": "null_decision",
            "source": "high_freq",
        },
        {
            "phrase": "geen resolutie is gevallen <END>",
            "phrase_norm": normalize_phrase("geen resolutie is gevallen <END>"),
            "phrase_freq": 79000,
            "zone": "close",
            "lcats": "small",
            "suggested_role": "null_decision",
            "source": "high_freq",
        },
        {
            "phrase": "WAAR op geen resolutie is",
            "phrase_norm": normalize_phrase("WAAR op geen resolutie is"),
            "phrase_freq": 66000,
            "zone": "close",
            "lcats": "small",
            "suggested_role": "null_decision",
            "source": "high_freq",
        },
    ]
    fams = fold_phrases(rows)["families"]
    assert surface_contained("geen resolutie is gevallen", _norms(fams))
    soft = soft_containment_rate(
        [{"surface": "geen resolutie is gevallen"}],
        fams,
    )
    assert soft["n_contained"] == 1


def _norms(fams):
    from formulation.formula_sequence_family_impact import _family_norms

    return _family_norms(fams)


def test_catalog_impact_summary_fixture() -> None:
    fams = fixture_fold()["families"]
    summary = catalog_impact_summary(families=fams, max_family_harvest=12)
    assert summary["principle"] == "do science on a canonical form"
    assert summary["n_new_exemplar_harvest"] >= 1
    assert "soft_containment" in summary
