"""Span overlap and boundary distance for Track S benchmarks."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class MatchResult:
    method_name: str
    start_idx: int
    end_idx: int
    score: float
    execution_time_ms: float
    matched_tokens: tuple[str, ...] = ()


def token_iou(pred: tuple[int, int], gold: tuple[int, int]) -> float:
    """Intersection over Union for half-open token spans ``[start, end)``."""
    p_start, p_end = pred
    g_start, g_end = gold
    if p_end < p_start or g_end < g_start:
        return 0.0
    intersection = max(0, min(p_end, g_end) - max(p_start, g_start))
    union = max(p_end, g_end) - min(p_start, g_start)
    return intersection / union if union > 0 else 0.0


def boundary_deltas(
    pred: tuple[int, int], gold: tuple[int, int]
) -> tuple[int, int]:
    """Absolute token distance on start and (exclusive) end."""
    return abs(pred[0] - gold[0]), abs(pred[1] - gold[1])
