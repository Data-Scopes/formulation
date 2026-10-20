"""Run SW single / SW cloud / DAG on the same boundary cases."""

from __future__ import annotations

from typing import Any

from formulation.boundary.align_dag import align_dag
from formulation.boundary.align_sw import align_sw_cloud, align_sw_single
from formulation.boundary.metrics import MatchResult, boundary_deltas, token_iou


def _case_methods(case: dict[str, Any]) -> list[MatchResult]:
    ocr = list(case["ocr_tokens"])
    template = list(case["template"])
    cloud = [list(slot) for slot in case["slot_cloud"]]
    optional = list(case.get("optional_slots") or [])
    return [
        align_sw_single(template, ocr),
        align_sw_cloud(cloud, ocr),
        align_dag(cloud, ocr, optional_slots=optional),
    ]


def evaluate_case(case: dict[str, Any]) -> list[dict[str, Any]]:
    """Score all methods for one fixture case."""
    gold = (int(case["gt_start"]), int(case["gt_end"]))
    rows: list[dict[str, Any]] = []
    for result in _case_methods(case):
        pred = (result.start_idx, result.end_idx)
        start_delta, end_delta = boundary_deltas(pred, gold)
        rows.append(
            {
                "case_id": case["case_id"],
                "method_name": result.method_name,
                "iou": token_iou(pred, gold),
                "start_delta": start_delta,
                "end_delta": end_delta,
                "start_idx": result.start_idx,
                "end_idx": result.end_idx,
                "score": result.score,
                "execution_time_ms": result.execution_time_ms,
                "matched_tokens": list(result.matched_tokens),
            }
        )
    return rows


def run_benchmark(cases: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Flatten per-case method rows for all fixtures."""
    rows: list[dict[str, Any]] = []
    for case in cases:
        rows.extend(evaluate_case(case))
    return rows


def format_table(rows: list[dict[str, Any]]) -> str:
    header = (
        f"{'Case':<24} | {'Method':<24} | {'IoU':<6} | "
        f"{'Δstart':<6} | {'Δend':<6} | {'ms':<8}"
    )
    lines = [header, "-" * len(header)]
    for row in rows:
        lines.append(
            f"{row['case_id']:<24} | {row['method_name']:<24} | "
            f"{row['iou']:<6.2f} | {row['start_delta']:<6} | "
            f"{row['end_delta']:<6} | {row['execution_time_ms']:<8.3f}"
        )
    return "\n".join(lines)
