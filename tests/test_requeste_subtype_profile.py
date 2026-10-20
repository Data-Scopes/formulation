"""Unit smoke for STEPT1l requeste+ routing subtype characterisation (no parquet)."""

from __future__ import annotations

from formulation.formula_type_composition_graph import COMPOSITION_ROOT
from formulation.requeste_subtype_profile import (
    SUBTYPE_GRANTED,
    SUBTYPE_REFERRED,
    SUBTYPE_UNCLEAR,
    fixture_characterisation_frame,
    summarize_requeste_subtypes,
)


def test_fixture_summarize_subtypes_and_contrast() -> None:
    frame = fixture_characterisation_frame()
    metrics = summarize_requeste_subtypes(frame, year=1780)

    assert metrics["composition_root"] == COMPOSITION_ROOT
    assert metrics["n_requeste_plus"] == 3
    assert metrics["n_recall_miss"] == 1

    by_id = {r["requeste_subtype"]: r for r in metrics["subtypes"]}
    assert by_id[SUBTYPE_REFERRED]["n"] == 1
    assert by_id[SUBTYPE_GRANTED]["n"] == 1
    assert by_id[SUBTYPE_UNCLEAR]["n"] == 1
    assert by_id[SUBTYPE_REFERRED]["length"]["n_words_median"] == 60.0

    contrast = metrics["contrast"]
    assert contrast["advies_rate_referred"] == 1.0
    assert contrast["advies_rate_granted_direct"] == 0.0
    assert contrast["n_routing_unclear"] == 1
