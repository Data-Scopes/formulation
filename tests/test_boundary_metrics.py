"""STEPS0: IoU helpers and SW/DAG smoke on fixture-shaped cases."""

from __future__ import annotations

from formulation.boundary.align_dag import align_dag
from formulation.boundary.align_sw import align_sw_cloud, align_sw_single
from formulation.boundary.benchmark import evaluate_case, run_benchmark
from formulation.boundary.metrics import boundary_deltas, token_iou


def test_token_iou_perfect_and_partial() -> None:
    assert token_iou((1, 7), (1, 7)) == 1.0
    assert token_iou((1, 5), (1, 7)) == 4 / 6
    assert token_iou((0, 0), (1, 3)) == 0.0


def test_boundary_deltas() -> None:
    assert boundary_deltas((1, 7), (1, 7)) == (0, 0)
    assert boundary_deltas((2, 6), (1, 7)) == (1, 1)


def test_sw_cloud_finds_ocr_noisy_opening() -> None:
    ocr = [
        "agendapunt",
        "g3presenteert",
        "en",
        "g3lesen",
        "seijnde",
        "d'",
        "Reqweste",
        "van",
        "Pieter",
    ]
    cloud = [
        ["Gepraesenteert", "Gepresenteert", "g3presenteert"],
        ["ende", "en", "eñ"],
        ["gelesen", "g3lesen"],
        ["sijnde", "seijnde"],
        ["de", "d'"],
        ["Requeste", "Reqweste"],
    ]
    result = align_sw_cloud(cloud, ocr)
    assert result.start_idx == 1
    assert result.end_idx == 7
    assert "g3presenteert" in result.matched_tokens
    assert "Reqweste" in result.matched_tokens


def test_dag_handles_skipped_optional_slots() -> None:
    ocr = [
        "agendapunt",
        "g3presenteert",
        "g3lesen",
        "d'",
        "Reqweste",
        "van",
        "Pieter",
    ]
    cloud = [
        ["Gepraesenteert", "Gepresenteert", "g3presenteert"],
        ["ende", "en", "eñ"],
        ["gelesen", "g3lesen"],
        ["sijnde", "seijnde"],
        ["de", "d'"],
        ["Requeste", "Reqweste"],
    ]
    dag = align_dag(cloud, ocr, optional_slots=[1, 3])
    gold = (1, 5)
    iou = token_iou((dag.start_idx, dag.end_idx), gold)
    single = align_sw_single(
        ["Gepraesenteert", "ende", "gelesen", "sijnde", "de", "Requeste"],
        ocr,
    )
    single_iou = token_iou((single.start_idx, single.end_idx), gold)
    assert iou >= 0.5
    assert iou >= single_iou


def test_run_benchmark_three_methods_per_case() -> None:
    case = {
        "case_id": "opening_clean",
        "ocr_tokens": [
            "Gepraesenteert",
            "ende",
            "gelesen",
            "sijnde",
            "de",
            "Requeste",
            "van",
            "Jan",
        ],
        "gt_start": 0,
        "gt_end": 6,
        "template": [
            "Gepraesenteert",
            "ende",
            "gelesen",
            "sijnde",
            "de",
            "Requeste",
        ],
        "slot_cloud": [
            ["Gepraesenteert", "g3presenteert"],
            ["ende", "en"],
            ["gelesen", "g3lesen"],
            ["sijnde"],
            ["de", "d'"],
            ["Requeste", "Reqweste"],
        ],
        "optional_slots": [1, 3],
    }
    rows = evaluate_case(case)
    assert len(rows) == 3
    methods = {r["method_name"] for r in rows}
    assert "SW (Single Template)" in methods
    assert "SW (Slot Cloud)" in methods
    assert "DAG / Graph Alignment" in methods
    assert all(r["iou"] == 1.0 for r in rows)

    flat = run_benchmark([case])
    assert len(flat) == 3
