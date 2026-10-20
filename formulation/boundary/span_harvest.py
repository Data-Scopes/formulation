"""STEPS3: harvest exact formula spans via SW single / SW cloud / DAG.

Runs on STEPS1 candidate windows with the STEPS2 slot-cloud. Does not calibrate
TF-IDF thresholds or invoke GysBERT.
"""

from __future__ import annotations

from typing import Any

from formulation.boundary.align_dag import align_dag
from formulation.boundary.align_sw import align_sw_cloud, align_sw_single
from formulation.boundary.metrics import MatchResult, boundary_deltas, token_iou
from formulation.boundary.slot_cloud import (
    FIXTURE_HIT_TEXTS,
    cloud_variant_lists,
    default_template,
)
from formulation.boundary.tfidf_windows import (
    HYPOTHESIS_THRESHOLD,
    TEMPLATE_ID_OPENING,
    tokenize,
)

METHOD_SW_SINGLE = "sw_single"
METHOD_SW_CLOUD = "sw_cloud"
METHOD_DAG = "dag"
METHODS = (METHOD_SW_SINGLE, METHOD_SW_CLOUD, METHOD_DAG)

# Shortened 18c openings (optional middle tokens dropped) for fixture smoke.
FIXTURE_SHORTENED_TEXTS: list[str] = [
    "IS Vergaderinge geleesen Requeste van Jan Jansen",
    "Is ter geleesen de Requeste van Pieter",
    "IS ter Vergaderinge Requeste van de weduwe",
]


def normalize_cloud(cloud: dict[str, Any] | list[dict[str, Any]] | Any) -> dict[str, Any]:
    """Accept a cloud record or a one-row list/DataFrame from ``load``."""
    if hasattr(cloud, "to_dict") and hasattr(cloud, "iloc"):
        if len(cloud) == 0:
            raise ValueError("formula_slot_cloud is empty")
        return dict(cloud.iloc[0].to_dict())
    if isinstance(cloud, list):
        if not cloud:
            raise ValueError("formula_slot_cloud is empty")
        return dict(cloud[0])
    if isinstance(cloud, dict):
        return cloud
    raise TypeError(f"Unexpected cloud type: {type(cloud)!r}")


def cloud_align_inputs(
    cloud: dict[str, Any],
) -> tuple[str, list[str], list[list[str]], list[int]]:
    """template_id, canonical template, variant_lists, optional_slots."""
    template_id = str(cloud.get("template_id") or TEMPLATE_ID_OPENING)
    variant_lists = cloud.get("variant_lists")
    if not variant_lists:
        variant_lists = cloud_variant_lists(cloud)
    variant_lists = [list(slot) for slot in variant_lists]
    if not variant_lists:
        raise ValueError("slot-cloud has no variant_lists / slots")
    template = [slot[0] for slot in variant_lists]
    optional = [int(i) for i in (cloud.get("optional_slots") or [])]
    return template_id, template, variant_lists, optional


def fixture_windows() -> list[dict[str, Any]]:
    """Synthetic STEPS1-like windows from 18c seeds (incl. shortened clerks)."""
    texts = list(FIXTURE_HIT_TEXTS) + list(FIXTURE_SHORTENED_TEXTS)
    rows: list[dict[str, Any]] = []
    for i, text in enumerate(texts):
        tokens = tokenize(text)
        rows.append(
            {
                "id": f"fixture_{i}",
                "token_start": 0,
                "token_end": len(tokens),
                "align_start": 0,
                "align_end": len(tokens),
                "score": 1.0,
                "template_id": TEMPLATE_ID_OPENING,
                "window_text": text,
                "n_tokens_doc": len(tokens),
            }
        )
    return rows


def windows_from_records(rows: list[dict[str, Any]] | Any) -> list[dict[str, Any]]:
    """Normalise STEPS1 candidate rows (list or DataFrame)."""
    if hasattr(rows, "to_dict"):
        records = rows.to_dict(orient="records")
    else:
        records = list(rows)
    out: list[dict[str, Any]] = []
    for row in records:
        text = row.get("window_text")
        if not text and row.get("ocr_tokens") is not None:
            text = " ".join(str(t) for t in row["ocr_tokens"])
        if not text:
            continue
        tokens = tokenize(str(text))
        token_start = int(row.get("token_start") or 0)
        token_end = int(row.get("token_end") or (token_start + len(tokens)))
        out.append(
            {
                "id": str(row.get("id") or row.get("case_id") or ""),
                "token_start": token_start,
                "token_end": token_end,
                "align_start": int(row["align_start"])
                if row.get("align_start") is not None
                else token_start,
                "align_end": int(row["align_end"])
                if row.get("align_end") is not None
                else token_end,
                "score": float(row["score"]) if row.get("score") is not None else None,
                "template_id": str(row.get("template_id") or TEMPLATE_ID_OPENING),
                "window_text": str(text),
                "n_tokens_doc": int(row["n_tokens_doc"])
                if row.get("n_tokens_doc") is not None
                else None,
                "gt_start": int(row["gt_start"]) if row.get("gt_start") is not None else None,
                "gt_end": int(row["gt_end"]) if row.get("gt_end") is not None else None,
            }
        )
    return out


def _align_methods(
    ocr_tokens: list[str],
    template: list[str],
    variant_lists: list[list[str]],
    optional_slots: list[int],
) -> list[tuple[str, MatchResult]]:
    return [
        (METHOD_SW_SINGLE, align_sw_single(template, ocr_tokens)),
        (METHOD_SW_CLOUD, align_sw_cloud(variant_lists, ocr_tokens)),
        (
            METHOD_DAG,
            align_dag(variant_lists, ocr_tokens, optional_slots=optional_slots),
        ),
    ]


def harvest_window(
    window: dict[str, Any],
    *,
    template: list[str],
    variant_lists: list[list[str]],
    optional_slots: list[int],
    template_id: str,
) -> list[dict[str, Any]]:
    """Align one window with all three methods; emit span rows."""
    ocr = tokenize(str(window["window_text"]))
    doc_base = int(window.get("token_start") or 0)
    rows: list[dict[str, Any]] = []
    gold = None
    if window.get("gt_start") is not None and window.get("gt_end") is not None:
        gold = (int(window["gt_start"]), int(window["gt_end"]))

    for method_key, result in _align_methods(
        ocr, template, variant_lists, optional_slots
    ):
        local = (int(result.start_idx), int(result.end_idx))
        doc_span = (doc_base + local[0], doc_base + local[1])
        row: dict[str, Any] = {
            "id": window.get("id"),
            "template_id": template_id,
            "method": method_key,
            "method_name": result.method_name,
            "local_start": local[0],
            "local_end": local[1],
            "doc_start": doc_span[0],
            "doc_end": doc_span[1],
            "window_token_start": doc_base,
            "window_token_end": int(window.get("token_end") or (doc_base + len(ocr))),
            "tfidf_score": window.get("score"),
            "align_score": float(result.score),
            "execution_time_ms": float(result.execution_time_ms),
            "matched_tokens": list(result.matched_tokens),
            "n_matched_tokens": len(result.matched_tokens),
            "window_text": window.get("window_text"),
            "span_text": " ".join(result.matched_tokens),
        }
        if gold is not None:
            row["gt_start"] = gold[0]
            row["gt_end"] = gold[1]
            row["iou"] = token_iou(local, gold)
            start_d, end_d = boundary_deltas(local, gold)
            row["start_delta"] = start_d
            row["end_delta"] = end_d
        rows.append(row)
    return rows


def harvest_spans(
    windows: list[dict[str, Any]],
    cloud: dict[str, Any],
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Harvest SW/DAG spans for all windows; return rows + summary metrics."""
    template_id, template, variant_lists, optional = cloud_align_inputs(cloud)
    if not windows:
        notes = _empty_notes(template_id, cloud, optional)
        return [], notes

    span_rows: list[dict[str, Any]] = []
    for window in windows:
        span_rows.extend(
            harvest_window(
                window,
                template=template,
                variant_lists=variant_lists,
                optional_slots=optional,
                template_id=template_id,
            )
        )
    notes = summarize_spans(span_rows, cloud=cloud, n_windows=len(windows))
    return span_rows, notes


def summarize_spans(
    span_rows: list[dict[str, Any]],
    *,
    cloud: dict[str, Any],
    n_windows: int,
) -> dict[str, Any]:
    """Per-method latency / score / length notes + cloud↔DAG agreement."""
    template_id = str(cloud.get("template_id") or TEMPLATE_ID_OPENING)
    optional = [int(i) for i in (cloud.get("optional_slots") or [])]
    by_method: dict[str, list[dict[str, Any]]] = {m: [] for m in METHODS}
    for row in span_rows:
        by_method.setdefault(str(row["method"]), []).append(row)

    method_notes: dict[str, Any] = {}
    for method in METHODS:
        rows = by_method.get(method) or []
        scores = [float(r["align_score"]) for r in rows]
        times = [float(r["execution_time_ms"]) for r in rows]
        lengths = [int(r["n_matched_tokens"]) for r in rows]
        empty = sum(1 for r in rows if r["local_end"] <= r["local_start"])
        entry: dict[str, Any] = {
            "n_rows": len(rows),
            "n_empty_span": empty,
            "score_mean": _mean(scores),
            "score_min": min(scores) if scores else None,
            "score_max": max(scores) if scores else None,
            "latency_ms_mean": _mean(times),
            "latency_ms_max": max(times) if times else None,
            "span_len_mean": _mean([float(x) for x in lengths]),
        }
        ious = [float(r["iou"]) for r in rows if r.get("iou") is not None]
        if ious:
            entry["iou_mean"] = _mean(ious)
            entry["iou_min"] = min(ious)
            entry["iou_max"] = max(ious)
        method_notes[method] = entry

    agreement = _span_agreement(by_method.get(METHOD_SW_CLOUD), by_method.get(METHOD_DAG))

    return {
        "template_id": template_id,
        "period": cloud.get("period"),
        "year_min": cloud.get("year_min"),
        "year_max": cloud.get("year_max"),
        "optional_slots": optional,
        "n_windows": int(n_windows),
        "n_span_rows": len(span_rows),
        "methods": list(METHODS),
        "per_method": method_notes,
        "sw_cloud_dag_span_agreement": agreement,
        "threshold_calibrated": not HYPOTHESIS_THRESHOLD,
        "gysbert": False,
        "default_template_id": default_template()[0],
    }


def _span_agreement(
    cloud_rows: list[dict[str, Any]] | None,
    dag_rows: list[dict[str, Any]] | None,
) -> dict[str, Any]:
    cloud_rows = cloud_rows or []
    dag_rows = dag_rows or []
    by_id = {r["id"]: r for r in dag_rows}
    n = 0
    n_equal = 0
    for crow in cloud_rows:
        drow = by_id.get(crow["id"])
        if drow is None:
            continue
        n += 1
        if (
            crow["local_start"] == drow["local_start"]
            and crow["local_end"] == drow["local_end"]
        ):
            n_equal += 1
    return {
        "n_compared": n,
        "n_equal": n_equal,
        "rate": (n_equal / n) if n else None,
    }


def _empty_notes(
    template_id: str, cloud: dict[str, Any], optional: list[int]
) -> dict[str, Any]:
    return {
        "template_id": template_id,
        "period": cloud.get("period"),
        "year_min": cloud.get("year_min"),
        "year_max": cloud.get("year_max"),
        "optional_slots": optional,
        "n_windows": 0,
        "n_span_rows": 0,
        "methods": list(METHODS),
        "per_method": {},
        "sw_cloud_dag_span_agreement": {"n_compared": 0, "n_equal": 0, "rate": None},
        "threshold_calibrated": not HYPOTHESIS_THRESHOLD,
        "gysbert": False,
    }


def _mean(values: list[float]) -> float | None:
    return float(sum(values) / len(values)) if values else None
