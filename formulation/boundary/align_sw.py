"""Word-level Smith-Waterman alignment (single template and slot-cloud)."""

from __future__ import annotations

import time

import numpy as np
from rapidfuzz.distance import Levenshtein

from formulation.boundary.metrics import MatchResult


def word_similarity(w1: str, w2: str) -> float:
    """Relative Levenshtein similarity in ``[0.0, 1.0]``."""
    max_len = max(len(w1), len(w2))
    if max_len == 0:
        return 1.0
    dist = Levenshtein.distance(w1.lower(), w2.lower())
    return 1.0 - (dist / max_len)


def _match_score(sim: float) -> float:
    return (sim * 3.0) - 1.5


def _traceback_span(
    H: np.ndarray, max_pos: tuple[int, int]
) -> tuple[int, int]:
    """Return half-open OCR span ``[start, end)`` from DP matrix peak."""
    i, j = max_pos
    end_idx = j
    while i > 0 and j > 0 and H[i, j] > 0:
        diag = H[i - 1, j - 1]
        up = H[i - 1, j]
        left = H[i, j - 1]
        best = int(np.argmax([diag, up, left]))
        if best == 0:
            i -= 1
            j -= 1
        elif best == 1:
            i -= 1
        else:
            j -= 1
    return j, end_idx


def _fill_sw_matrix(
    left_tokens: list[str] | list[list[str]],
    ocr_tokens: list[str],
    *,
    gap_penalty: float,
    cloud: bool,
) -> tuple[np.ndarray, float, tuple[int, int]]:
    """Build SW score matrix; ``left_tokens`` is a template or slot-cloud."""
    m, n = len(left_tokens), len(ocr_tokens)
    H = np.zeros((m + 1, n + 1))
    max_score = 0.0
    max_pos = (0, 0)
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if cloud:
                variants = left_tokens[i - 1]
                sim = max(word_similarity(v, ocr_tokens[j - 1]) for v in variants)
            else:
                sim = word_similarity(left_tokens[i - 1], ocr_tokens[j - 1])
            match = H[i - 1, j - 1] + _match_score(sim)
            delete = H[i - 1, j] - gap_penalty
            insert = H[i, j - 1] - gap_penalty
            H[i, j] = max(0.0, match, delete, insert)
            if H[i, j] > max_score:
                max_score = float(H[i, j])
                max_pos = (i, j)
    return H, max_score, max_pos


def _traceback_pairs(
    H: np.ndarray,
    max_pos: tuple[int, int],
    *,
    gap_penalty: float,
    left_tokens: list[str] | list[list[str]],
    ocr_tokens: list[str],
    cloud: bool,
) -> list[tuple[int, int | None]]:
    """Template-slot → OCR index pairs along the optimal path (match or skip).

    ``(slot_idx, ocr_idx)`` on a diagonal match; ``(slot_idx, None)`` on delete
    (template slot skipped). Inserts do not emit pairs. Order is slot-ascending.
    """
    i, j = max_pos
    rev: list[tuple[int, int | None]] = []
    while i > 0 and j > 0 and H[i, j] > 0:
        if cloud:
            variants = left_tokens[i - 1]
            sim = max(word_similarity(v, ocr_tokens[j - 1]) for v in variants)
        else:
            sim = word_similarity(left_tokens[i - 1], ocr_tokens[j - 1])
        match = H[i - 1, j - 1] + _match_score(sim)
        delete = H[i - 1, j] - gap_penalty
        insert = H[i, j - 1] - gap_penalty
        cell = H[i, j]
        # Prefer match, then delete, then insert when scores tie.
        if abs(cell - match) <= 1e-9 and match >= delete and match >= insert:
            rev.append((i - 1, j - 1))
            i -= 1
            j -= 1
        elif abs(cell - delete) <= 1e-9 and delete >= insert:
            rev.append((i - 1, None))
            i -= 1
        else:
            j -= 1
    while i > 0 and H[i, j] > 0:
        rev.append((i - 1, None))
        i -= 1
    rev.reverse()
    return rev


def align_sw_pairs(
    template: list[str],
    ocr_tokens: list[str],
    *,
    gap_penalty: float = 1.0,
) -> tuple[MatchResult, list[tuple[int, int | None]]]:
    """Smith-Waterman plus slot→OCR pairs for cloud bootstrap (STEPS2)."""
    t0 = time.perf_counter()
    m, n = len(template), len(ocr_tokens)
    if m == 0 or n == 0:
        empty = MatchResult(
            method_name="SW (Single Template)",
            start_idx=0,
            end_idx=0,
            score=0.0,
            execution_time_ms=(time.perf_counter() - t0) * 1000,
        )
        return empty, []

    H, max_score, max_pos = _fill_sw_matrix(
        template, ocr_tokens, gap_penalty=gap_penalty, cloud=False
    )
    start_idx, end_idx = _traceback_span(H, max_pos)
    pairs = _traceback_pairs(
        H,
        max_pos,
        gap_penalty=gap_penalty,
        left_tokens=template,
        ocr_tokens=ocr_tokens,
        cloud=False,
    )
    matched = tuple(ocr_tokens[start_idx:end_idx])
    result = MatchResult(
        method_name="SW (Single Template)",
        start_idx=start_idx,
        end_idx=end_idx,
        score=max_score,
        execution_time_ms=(time.perf_counter() - t0) * 1000,
        matched_tokens=matched,
    )
    return result, pairs


def align_sw_single(
    template: list[str],
    ocr_tokens: list[str],
    *,
    gap_penalty: float = 1.0,
) -> MatchResult:
    """Smith-Waterman against one canonical template word sequence."""
    result, _pairs = align_sw_pairs(
        template, ocr_tokens, gap_penalty=gap_penalty
    )
    return result


def align_sw_cloud(
    slot_cloud: list[list[str]],
    ocr_tokens: list[str],
    *,
    gap_penalty: float = 1.0,
) -> MatchResult:
    """Smith-Waterman scoring each slot against its variant cloud."""
    t0 = time.perf_counter()
    m, n = len(slot_cloud), len(ocr_tokens)
    if m == 0 or n == 0:
        return MatchResult(
            method_name="SW (Slot Cloud)",
            start_idx=0,
            end_idx=0,
            score=0.0,
            execution_time_ms=(time.perf_counter() - t0) * 1000,
        )

    H, max_score, max_pos = _fill_sw_matrix(
        slot_cloud, ocr_tokens, gap_penalty=gap_penalty, cloud=True
    )
    start_idx, end_idx = _traceback_span(H, max_pos)
    matched = tuple(ocr_tokens[start_idx:end_idx])
    return MatchResult(
        method_name="SW (Slot Cloud)",
        start_idx=start_idx,
        end_idx=end_idx,
        score=max_score,
        execution_time_ms=(time.perf_counter() - t0) * 1000,
        matched_tokens=matched,
    )
