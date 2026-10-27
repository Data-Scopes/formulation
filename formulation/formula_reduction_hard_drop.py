"""STEPT1v2: Doc B L1→L2 hard-drop reduction on ``requeste_geleesen``.

STEPT1v soft ``optional_slots`` was a no-op (DAG still took the full path).
Here each config **removes** slot *i* from ``variant_lists`` (forced absence),
recalibrates p20, and compares recall/FP/span to the full six-slot baseline.

Measurement only — does not touch the frozen 4.5 cut or ``ACCEPTED_TYPE_IDS``.
"""

from __future__ import annotations

import copy
from itertools import combinations
from typing import Any

import pandas as pd

from formulation.appointment_formula_type import align_tokenize
from formulation.boundary.align_dag import align_dag
from formulation.boundary.slot_cloud import cloud_variant_lists
from formulation.formula_reduction_l2 import (
    DEFAULT_HOLDOUT_FRAC,
    DEFAULT_LIMIT_GOLD,
    DEFAULT_NEG_N,
    DEFAULT_RNG,
    FALLBACK_CUT,
    HINGE_RECALL_DROP,
    REQUESTE_CANONIC,
    SAFE_FP_RISE,
    SAFE_RECALL_DROP,
    calibrate_cut,
    fixture_smoke,
    load_long_head_gold,
    metrics_at_cut,
    sample_negatives,
    slot_labels,
    span_iou_vs_ref,
    split_bootstrap_holdout,
)

__all__ = (
    "DEFAULT_HOLDOUT_FRAC",
    "DEFAULT_LIMIT_GOLD",
    "DEFAULT_NEG_N",
    "DEFAULT_RNG",
    "FALLBACK_CUT",
    "HINGE_RECALL_DROP",
    "REQUESTE_CANONIC",
    "SAFE_FP_RISE",
    "SAFE_RECALL_DROP",
    "calibrate_cut",
    "fixture_smoke",
    "hard_drop_configs",
    "hard_drop_variants",
    "leave_k_configs",
    "load_long_head_gold",
    "metrics_at_cut",
    "sample_negatives",
    "score_frame_hard_drop",
    "score_text_hard_drop",
    "slot_labels",
    "span_iou_vs_ref",
    "split_bootstrap_holdout",
    "summarize_hard_drop",
)


def hard_drop_variants(
    cloud: dict[str, Any],
    drop_slots: list[int] | set[int],
) -> list[list[str]]:
    """Return ``variant_lists`` with the given original slot indices removed."""
    variants = cloud.get("variant_lists") or cloud_variant_lists(cloud)
    drop = {int(i) for i in drop_slots}
    return [list(v) for i, v in enumerate(variants) if i not in drop]


def hard_drop_cloud(
    cloud: dict[str, Any],
    drop_slots: list[int] | set[int],
) -> dict[str, Any]:
    """Shallow-copy cloud with slots / variant_lists hard-dropped."""
    drop = {int(i) for i in drop_slots}
    out = copy.copy(cloud)
    variants = hard_drop_variants(cloud, drop)
    out["variant_lists"] = variants
    if cloud.get("slots"):
        out["slots"] = [
            s for i, s in enumerate(cloud["slots"]) if i not in drop
        ]
    out["optional_slots"] = []
    out["hard_dropped_slots"] = sorted(drop)
    return out


def hard_drop_configs(n_slots: int) -> list[dict[str, Any]]:
    """Baseline (all slots) + single-slot hard drops."""
    n = int(n_slots)
    configs: list[dict[str, Any]] = [
        {
            "config_id": "full",
            "drop_slots": [],
            "kept_slots": list(range(n)),
            "kind": "baseline_full",
        }
    ]
    for i in range(n):
        kept = [j for j in range(n) if j != i]
        configs.append(
            {
                "config_id": f"drop_{i}",
                "drop_slots": [int(i)],
                "kept_slots": kept,
                "kind": "single_slot_hard_drop",
                "ablated_slot": int(i),
            }
        )
    return configs


def leave_k_configs(n_slots: int, k: int) -> list[dict[str, Any]]:
    """All subsets that keep exactly ``k`` original slots."""
    n = int(n_slots)
    k = int(k)
    if k < 1 or k > n:
        raise ValueError(f"leave-k requires 1 <= k <= n_slots; got k={k} n={n}")
    configs: list[dict[str, Any]] = []
    for kept in combinations(range(n), k):
        kept_l = list(kept)
        drop = [i for i in range(n) if i not in kept_l]
        tag = "".join(str(i) for i in kept_l)
        configs.append(
            {
                "config_id": f"keep_{tag}",
                "drop_slots": drop,
                "kept_slots": kept_l,
                "kind": "leave_k",
                "k": k,
            }
        )
    return configs


def score_text_hard_drop(
    text: str,
    cloud: dict[str, Any],
    drop_slots: list[int],
) -> dict[str, Any]:
    tokens = align_tokenize(str(text or ""))
    variants = hard_drop_variants(cloud, drop_slots)
    res = align_dag(variants, tokens, optional_slots=[])
    return {
        "score": float(res.score),
        "start_idx": int(res.start_idx),
        "end_idx": int(res.end_idx),
        "n_slots_scored": int(len(variants)),
    }


def score_frame_hard_drop(
    frame: pd.DataFrame,
    cloud: dict[str, Any],
    drop_slots: list[int],
    *,
    role: str,
    progress_every: int = 2000,
) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    total = len(frame)
    for i, rec in enumerate(frame.to_dict(orient="records"), start=1):
        text = str(rec.get("resolutions_text") or "")
        scored = score_text_hard_drop(text, cloud, drop_slots)
        rows.append(
            {
                "id": str(rec["id"]),
                "year": int(rec["year"]) if rec.get("year") is not None else None,
                "role": role,
                **scored,
            }
        )
        if progress_every and i % progress_every == 0:
            print(
                f"  score[{role}|drop={drop_slots}]: {i}/{total}",
                flush=True,
            )
    return pd.DataFrame(rows)


def summarize_hard_drop(
    config_rows: list[dict[str, Any]],
    *,
    labels: list[str],
    cloud_notes: dict[str, Any],
    n_gold_universe: int,
    n_bootstrap: int,
    n_holdout: int,
    random_state: int,
    mode: str,
) -> dict[str, Any]:
    """Provenanced metrics + hinge/safe calls vs ``full``."""
    by_id = {r["config_id"]: r for r in config_rows}
    baseline = by_id.get("full")
    base_recall = float(baseline["recall"] or 0.0) if baseline else 0.0
    base_fp = float(baseline["fp_rate"] or 0.0) if baseline else 0.0

    hinge_slots: list[dict[str, Any]] = []
    safe_slots: list[dict[str, Any]] = []
    for row in config_rows:
        if row.get("kind") != "single_slot_hard_drop":
            continue
        i = int(row["ablated_slot"])
        tok = labels[i] if i < len(labels) else f"slot_{i}"
        recall = float(row["recall"] or 0.0)
        fp = float(row["fp_rate"] or 0.0)
        drop = base_recall - recall
        rise = fp - base_fp
        entry = {
            "slot": i,
            "token": tok,
            "recall": row["recall"],
            "fp_rate": row["fp_rate"],
            "recall_drop_vs_full": round(drop, 4),
            "fp_rise_vs_full": round(rise, 4),
            "cut": row.get("cut"),
        }
        if drop >= HINGE_RECALL_DROP:
            hinge_slots.append(entry)
        if drop <= SAFE_RECALL_DROP and rise <= SAFE_FP_RISE:
            safe_slots.append(entry)

    required_guess = [
        labels[i]
        for i in range(len(labels))
        if not any(s["slot"] == i for s in safe_slots)
    ]

    return {
        "step": "STEPT1v2",
        "method": "formula_reduction_hard_drop",
        "formula_type_id": "requeste_geleesen",
        "canonic": REQUESTE_CANONIC,
        "slot_labels": list(labels),
        "n_slots": int(len(labels)),
        "mode": mode,
        "n_gold_universe_long_head": int(n_gold_universe),
        "n_bootstrap": int(n_bootstrap),
        "n_holdout": int(n_holdout),
        "random_state": int(random_state),
        "safe_recall_drop_max": SAFE_RECALL_DROP,
        "safe_fp_rise_max": SAFE_FP_RISE,
        "hinge_recall_drop_min": HINGE_RECALL_DROP,
        "cloud_notes": cloud_notes,
        "configs": config_rows,
        "hinge_slots": hinge_slots,
        "safe_drop_slots": safe_slots,
        "l2_required_tokens_guess": required_guess,
        "constraint": "measure_only_do_not_change_frozen_cut",
        "prior_step": "STEPT1v_soft_optional_noop",
    }
