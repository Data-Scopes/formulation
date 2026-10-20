"""Unit smoke for STEPT1e ontfangen partition probe (no ES / no parquet)."""

from __future__ import annotations

from formulation.ontfangen_partition import (
    COMPOSITION_ROOT,
    fixture_partition_frame,
    summarize_partition,
)


def test_fixture_summarize_counts_and_residual() -> None:
    frame = fixture_partition_frame()
    known = {
        "aanstelling_selected": {"session-3835-num-1-resolution-2"},
        "missive_receipt": {"session-3835-num-1-resolution-1"},
        "advies_es_gold": {"session-3835-num-1-resolution-3"},
    }
    metrics = summarize_partition(frame, year=1780, known=known)

    assert metrics["composition_root"] == COMPOSITION_ROOT
    assert metrics["n_resolutions"] == 4
    assert metrics["n_ontfangen_plus"] == 3
    assert metrics["n_ontfangen_minus"] == 1
    assert metrics["residual_not_l1"]["n"] == 2

    mix_plus = {r["proposition_type"]: r["n"] for r in metrics["es_type_mix_plus"]}
    assert mix_plus.get("missive") == 3

    mix_minus = {r["proposition_type"]: r["n"] for r in metrics["es_type_mix_minus"]}
    assert mix_minus.get("advies") == 1

    cont = metrics["missive_contingency"]
    assert cont["missive_and_plus"] == 3
    assert cont["p_missive_given_plus"] == 1.0

    known_rows = {r["known_set"]: r for r in metrics["known_sets"]}
    assert known_rows["missive_receipt"]["n_ontfangen_plus"] == 1
    assert known_rows["aanstelling_selected"]["n_ontfangen_plus"] == 1
    assert known_rows["advies_es_gold"]["n_ontfangen_minus"] == 1

    assert metrics["flags_plus"]["flag_rates"]["geen_resolutie"] is not None
    assert metrics["residual_not_l1"]["n_r1"] == 1
