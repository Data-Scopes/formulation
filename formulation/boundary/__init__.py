"""Track S: formula boundary alignment (SW single/cloud, DAG) + TF-IDF framing."""

from formulation.boundary.align_dag import align_dag
from formulation.boundary.align_sw import align_sw_cloud, align_sw_pairs, align_sw_single
from formulation.boundary.benchmark import run_benchmark
from formulation.boundary.metrics import MatchResult, boundary_deltas, token_iou
from formulation.boundary.slot_cloud import bootstrap_slot_cloud, cloud_variant_lists
from formulation.boundary.span_harvest import harvest_spans
from formulation.boundary.tfidf_windows import (
    frame_documents,
    make_vectorizer,
    score_windows,
)

__all__ = [
    "MatchResult",
    "align_dag",
    "align_sw_cloud",
    "align_sw_pairs",
    "align_sw_single",
    "bootstrap_slot_cloud",
    "boundary_deltas",
    "cloud_variant_lists",
    "frame_documents",
    "harvest_spans",
    "make_vectorizer",
    "run_benchmark",
    "score_windows",
    "token_iou",
]
