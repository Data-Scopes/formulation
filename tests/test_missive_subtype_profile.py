"""Unit smoke for STEPT1f missive subtype characterisation (no parquet)."""

from __future__ import annotations

from formulation.formula_type_composition_graph import COMPOSITION_ROOT
from formulation.missive_subtype_profile import (
    SUBTYPE_DECISIONFUL,
    SUBTYPE_INFO,
    fixture_characterisation_frame,
    summarize_missive_subtypes,
)


def test_fixture_summarize_subtypes_and_contrast() -> None:
    frame = fixture_characterisation_frame()
    metrics = summarize_missive_subtypes(frame, year=1780)

    assert metrics["composition_root"] == COMPOSITION_ROOT
    assert metrics["n_ontfangen_plus"] == 3
    assert metrics["n_missive"] == 3
    assert metrics["n_non_missive_leakage"] == 0

    by_id = {r["missive_subtype"]: r for r in metrics["subtypes"]}
    assert by_id[SUBTYPE_INFO]["n"] == 1
    assert by_id[SUBTYPE_DECISIONFUL]["n"] == 2
    assert by_id[SUBTYPE_INFO]["length"]["n_words_median"] == 40.0
    assert by_id[SUBTYPE_DECISIONFUL]["known"]["n_r1"] == 1

    contrast = metrics["contrast"]
    assert contrast["n_words_median_delta_decisionful_minus_info"] > 0
    assert contrast["n_r1_decisionful"] == 1
    assert contrast["n_r1_info"] == 0

    info_rates = by_id[SUBTYPE_INFO]["flags"]["flag_rates"]
    assert info_rates.get("geen_resolutie") == 1.0
