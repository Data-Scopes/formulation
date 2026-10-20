"""Unit tests for family × 25y bin measurements (fixture, no parquet)."""

from __future__ import annotations

import pandas as pd

from formulation.formula_period_bins import (
    BIN_WIDTH,
    compare_model_to_formula_documents,
    evaluate_family,
    fixture_appointment_bins,
    fixture_sparse_then_rich_bins,
    formula_documents_bin_rates,
    year_bin,
)


def test_year_bin_25y_origin_1700():
    assert year_bin(1710) == "1700-1724"
    assert year_bin(1725) == "1725-1749"
    assert year_bin(1780) == "1775-1799"
    assert BIN_WIDTH == 25


def test_fixture_eval_has_measurements_and_matrix():
    summary, matrix = evaluate_family(
        "appointment",
        min_bin_n=30,
        fixture_frames=fixture_appointment_bins(),
    )
    assert summary["bins_modeled"]
    assert "diagonal_recall" in summary
    assert "popularity" in summary
    assert "eval_gates" in summary
    assert "measurements" in summary
    assert matrix
    assert {r["model_bin"] for r in matrix} <= set(summary["bins_modeled"])
    # Cross cells exist (2 modeled bins → 4 cells).
    assert len(matrix) == len(summary["bins_modeled"]) ** 2


def test_formula_documents_bin_rates_resolutions_only():
    rates = formula_documents_bin_rates(("welkom", "sessie"))
    assert rates["status"] == "ok"
    assert "welkom" in rates["flag_rates"]
    assert rates["bin_n"]
    # Attendance excluded ⇒ rates are on resolution rows; welkom should be
    # near-zero before 1731 bin if STEPT0 story holds.
    early = rates["flag_rates"]["welkom"].get("1700-1724") or rates[
        "flag_rates"
    ]["welkom"].get("1725-1749")
    assert early is not None


def test_compare_model_to_documents_structure():
    cmp_ = compare_model_to_formula_documents(
        "appointment_installation",
        {"1725-1749": 0.8, "1750-1774": 0.7},
    )
    assert cmp_["status"] == "ok"
    assert cmp_["per_bin"]
    assert "delta_abs_mean" in cmp_


def test_sparse_bin_borrows_next_period_model():
    summary, matrix = evaluate_family(
        "appointment",
        min_bin_n=30,
        fixture_frames=fixture_sparse_then_rich_bins(),
    )
    assert summary["n_borrowed_bins"] == 1
    assert "1700-1724" in summary["bins_modeled_borrowed"]
    borrow = summary["borrow_from_next_period"][0]
    assert borrow["status"] in {
        "borrowed_next_period",
        "borrowed_previous_period",
    }
    assert borrow["borrowed_from"] == "1725-1749"
    assert borrow["n_sparse"] == 2
    assert borrow["recall_on_sparse"] is not None
    # Borrowed bin appears as a model row in the matrix.
    assert any(
        r["model_bin"] == "1700-1724" and r.get("model_source", "").startswith("borrowed")
        for r in matrix
    )


def test_late_sparse_bin_borrows_previous_period():
    rich = fixture_appointment_bins()["1700-1724"]
    sparse = pd.DataFrame(
        [
            {
                "id": "late0",
                "year": 1780,
                "resolutions_text": "sessie genomen in de vergaderinge",
            },
            {
                "id": "late1",
                "year": 1785,
                "resolutions_text": "heeft sessie genomen",
            },
        ]
    )
    summary, _matrix = evaluate_family(
        "appointment",
        min_bin_n=30,
        fixture_frames={"1700-1724": rich, "1775-1799": sparse},
    )
    assert summary["n_borrowed_bins"] == 1
    borrow = summary["borrow_from_next_period"][0]
    assert borrow["status"] == "borrowed_previous_period"
    assert borrow["borrowed_from"] == "1700-1724"
