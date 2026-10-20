"""Unit smoke for STEPT1g residual structure probe (no parquet)."""

from __future__ import annotations

from formulation.appointment_formula_type import FORMULA_TYPE_ID as APPOINTMENT_ID
from formulation.formula_type_composition_graph import COMPOSITION_ROOT
from formulation.residual_structure import (
    combo_catalogue,
    fixture_residual_frame,
    summarize_residual_structure,
)


def test_fixture_summarize_pockets_and_catalogue() -> None:
    frame = fixture_residual_frame()
    metrics = summarize_residual_structure(frame, year=1780)

    assert metrics["composition_root"] == COMPOSITION_ROOT
    assert metrics["constraint"] == "probability_is_not_typology"
    # Fixture: 2 residual missive rows (ids 2 and 4); 1 L1
    assert metrics["n_residual_missive"] == 2
    assert metrics["pockets"]["n_r1_selected"] == 1
    assert metrics["pockets"]["n_appointment_present"] == 1

    cat = metrics["combo_catalogue"]
    assert cat["n_unique_combos"] >= 1
    assert "top_combos" in cat
    # High-n must not appear as subtype ids in metrics keys
    assert "subtypes" not in metrics

    bags = metrics["bags"]["top_bags"]
    labels = {r["bag_label"] for r in bags}
    assert any(APPOINTMENT_ID in lab for lab in labels) or any(
        APPOINTMENT_ID in r["bag"] for r in bags
    )


def test_combo_catalogue_is_inventory_not_rates_as_types() -> None:
    frame = fixture_residual_frame()
    residual = frame.loc[frame["residual_not_l1"]]
    cat = combo_catalogue(residual, list(frame.attrs["flag_columns"]))
    assert "note" in cat
    assert all("flags" in row and "n" in row for row in cat["top_combos"])
    # rate may be absent — inventory prefers n
    assert all("rate" not in row for row in cat["top_combos"])
