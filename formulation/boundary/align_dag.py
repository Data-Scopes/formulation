"""Layered DAG alignment with optional skip slots."""

from __future__ import annotations

import time
from dataclasses import dataclass

import numpy as np

from formulation.boundary.align_sw import word_similarity
from formulation.boundary.metrics import MatchResult


@dataclass(frozen=True)
class DAGNode:
    id: str
    token: str
    slot_idx: int
    is_skip: bool = False


class SequenceDAG:
    """Ordered layers of variant nodes; optional slots get a skip node."""

    def __init__(
        self,
        slot_cloud: list[list[str]],
        optional_slots: list[int] | None = None,
    ) -> None:
        optional = set(optional_slots or [])
        self.layers: list[list[DAGNode]] = []
        counter = 0
        for slot_idx, variants in enumerate(slot_cloud):
            layer: list[DAGNode] = []
            for var in variants:
                layer.append(DAGNode(f"N_{counter}", var, slot_idx))
                counter += 1
            if slot_idx in optional:
                layer.append(
                    DAGNode(f"N_{counter}_skip", "", slot_idx, is_skip=True)
                )
                counter += 1
            self.layers.append(layer)


def align_dag(
    slot_cloud: list[list[str]],
    ocr_tokens: list[str],
    *,
    optional_slots: list[int] | None = None,
    gap_penalty: float = 1.0,
) -> MatchResult:
    """Viterbi-style DP over DAG layers × OCR tokens."""
    t0 = time.perf_counter()
    dag = SequenceDAG(slot_cloud, optional_slots=optional_slots)
    num_layers = len(dag.layers)
    num_ocr = len(ocr_tokens)
    if num_layers == 0 or num_ocr == 0:
        return MatchResult(
            method_name="DAG / Graph Alignment",
            start_idx=0,
            end_idx=0,
            score=0.0,
            execution_time_ms=(time.perf_counter() - t0) * 1000,
        )

    DP = np.zeros((num_layers + 1, num_ocr + 1))
    max_score = 0.0
    max_pos = (0, 0)

    for layer_i in range(1, num_layers + 1):
        nodes = dag.layers[layer_i - 1]
        for j in range(1, num_ocr + 1):
            ocr_token = ocr_tokens[j - 1]
            best_node_score = -1.0
            for node in nodes:
                if node.is_skip:
                    # Skip consumes the layer without consuming OCR (handled via
                    # deletion path); treat skip-on-token as neutral for match.
                    sim_score = 0.0
                else:
                    sim = word_similarity(node.token, ocr_token)
                    sim_score = (sim * 3.0) - 1.5
                if sim_score > best_node_score:
                    best_node_score = sim_score

            # Prefer real token match when available; skip layers use deletion.
            has_real = any(not n.is_skip for n in nodes)
            if has_real and best_node_score < 0 and any(n.is_skip for n in nodes):
                # Allow progressing the layer without OCR via deletion below.
                pass

            match = DP[layer_i - 1, j - 1] + best_node_score
            deletion = DP[layer_i - 1, j] - (
                0.0 if any(n.is_skip for n in nodes) else gap_penalty
            )
            insertion = DP[layer_i, j - 1] - gap_penalty
            score = max(0.0, match, deletion, insertion)
            DP[layer_i, j] = score
            if score > max_score:
                max_score = float(score)
                max_pos = (layer_i, j)

    layer_i, j = max_pos
    end_idx = j
    matched_rev: list[str] = []
    while layer_i > 0 and j > 0 and DP[layer_i, j] > 0:
        scores = [
            DP[layer_i - 1, j - 1],
            DP[layer_i - 1, j],
            DP[layer_i, j - 1],
        ]
        best_dir = int(np.argmax(scores))
        if best_dir == 0:
            matched_rev.append(ocr_tokens[j - 1])
            layer_i -= 1
            j -= 1
        elif best_dir == 1:
            layer_i -= 1
        else:
            j -= 1

    start_idx = j
    matched_rev.reverse()
    return MatchResult(
        method_name="DAG / Graph Alignment",
        start_idx=start_idx,
        end_idx=end_idx,
        score=max_score,
        execution_time_ms=(time.perf_counter() - t0) * 1000,
        matched_tokens=tuple(matched_rev),
    )
