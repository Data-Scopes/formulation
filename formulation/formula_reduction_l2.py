"""STEPT1v: Doc B L1→L2 formula reduction on ``requeste_geleesen``.

Bootstrap the long-opener cloud once, then score the same gold/negatives under
configs that differ only in ``optional_slots``. Each config gets its own p20
cut (``calibrate_cut``). Measurement only — does not touch the frozen 4.5 cut
or ``ACCEPTED_TYPE_IDS``.
"""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from formulation.appointment_formula_type import (
    FALLBACK_CUT,
    HOLDOUT_FRAC,
    NEG_N,
    RNG,
    align_tokenize,
    calibrate_cut,
    sample_negatives,
    split_bootstrap_holdout,
)
from formulation.boundary.align_dag import align_dag
from formulation.boundary.metrics import token_iou
from formulation.boundary.slot_cloud import cloud_variant_lists
from formulation.requeste_formula_type import (
    REQUESTE_CANONIC,
    build_requeste_cloud,
    load_rekest_gold_18c,
    requeste_template,
)
from formulation.requeste_formula_type import (
    score_frame as _score_frame_default_optional,
)
from formulation.requeste_op_de_formula_type import is_long_requeste_head

DEFAULT_LIMIT_GOLD: int | None = None
DEFAULT_NEG_N = NEG_N
DEFAULT_HOLDOUT_FRAC = HOLDOUT_FRAC
DEFAULT_RNG = RNG
# Ablation is "safe" if recall drop ≤ this and FP rise ≤ this vs all_required.
SAFE_RECALL_DROP = 0.05
SAFE_FP_RISE = 0.03
# "Hinge" if recall drops by at least this vs all_required.
HINGE_RECALL_DROP = 0.10

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
    "ablation_configs",
    "calibrate_cut",
    "exhaustive_configs",
    "fixture_smoke",
    "load_long_head_gold",
    "metrics_at_cut",
    "sample_negatives",
    "score_frame_with_optional",
    "score_text_with_optional",
    "slot_labels",
    "span_iou_vs_ref",
    "split_bootstrap_holdout",
    "summarize_reduction",
)


def slot_labels(cloud: dict[str, Any] | None = None) -> list[str]:
    """Canonic token per slot index (fallback: tokenize REQUESTE_CANONIC)."""
    if cloud and cloud.get("slots"):
        return [str(s.get("canonical") or f"slot_{s.get('index')}") for s in cloud["slots"]]
    return list(requeste_template())


def load_long_head_gold(
    *,
    limit: int | None = DEFAULT_LIMIT_GOLD,
    random_state: int = DEFAULT_RNG,
) -> pd.DataFrame:
    """ES rekest gold filtered to long opener head."""
    gold = load_rekest_gold_18c()
    mask = gold["resolutions_text"].map(is_long_requeste_head)
    out = gold.loc[mask].copy()
    if out.empty:
        raise ValueError("long-head rekest gold empty after filter")
    out["gold_source"] = "es_rekest_long_head"
    if limit is not None and int(limit) < len(out):
        out = out.sample(n=int(limit), random_state=int(random_state))
    return out.reset_index(drop=True)


def score_text_with_optional(
    text: str,
    cloud: dict[str, Any],
    optional_slots: list[int],
) -> dict[str, Any]:
    tokens = align_tokenize(str(text or ""))
    variants = cloud.get("variant_lists") or cloud_variant_lists(cloud)
    res = align_dag(variants, tokens, optional_slots=list(optional_slots))
    return {
        "score": float(res.score),
        "start_idx": int(res.start_idx),
        "end_idx": int(res.end_idx),
    }


def score_frame_with_optional(
    frame: pd.DataFrame,
    cloud: dict[str, Any],
    optional_slots: list[int],
    *,
    role: str,
    progress_every: int = 2000,
) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    total = len(frame)
    for i, rec in enumerate(frame.to_dict(orient="records"), start=1):
        text = str(rec.get("resolutions_text") or "")
        scored = score_text_with_optional(text, cloud, optional_slots)
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
                f"  score[{role}|opt={optional_slots}]: {i}/{total}",
                flush=True,
            )
    return pd.DataFrame(rows)


def ablation_configs(n_slots: int, *, bootstrap_optional: list[int]) -> list[dict[str, Any]]:
    """Baseline + all_required + single-slot optional ablations."""
    configs: list[dict[str, Any]] = [
        {
            "config_id": "full",
            "optional_slots": sorted({int(i) for i in bootstrap_optional}),
            "kind": "bootstrap_optional",
        },
        {
            "config_id": "all_required",
            "optional_slots": [],
            "kind": "baseline_required",
        },
    ]
    for i in range(int(n_slots)):
        configs.append(
            {
                "config_id": f"ablate_{i}",
                "optional_slots": [int(i)],
                "kind": "single_slot_optional",
                "ablated_slot": int(i),
            }
        )
    return configs


def exhaustive_configs(n_slots: int) -> list[dict[str, Any]]:
    """All subsets of optional slots (2^n). Required = complement."""
    n = int(n_slots)
    configs: list[dict[str, Any]] = []
    for mask in range(1 << n):
        optional = [i for i in range(n) if mask & (1 << i)]
        required = [i for i in range(n) if not (mask & (1 << i))]
        configs.append(
            {
                "config_id": f"mask_{mask:0{n}b}",
                "optional_slots": optional,
                "required_slots": required,
                "kind": "exhaustive_mask",
                "mask": int(mask),
            }
        )
    return configs


def metrics_at_cut(
    gold: pd.DataFrame,
    neg: pd.DataFrame,
    *,
    cut: float,
) -> dict[str, Any]:
    g_pred = gold["score"] >= float(cut)
    n_fp = int((neg["score"] >= float(cut)).sum()) if len(neg) else 0
    n_neg = int(len(neg))
    return {
        "cut": round(float(cut), 4),
        "n_gold": int(len(gold)),
        "recall": round(float(g_pred.mean()), 4) if len(gold) else None,
        "n_neg": n_neg,
        "n_fp": n_fp,
        "fp_rate": round(n_fp / n_neg, 4) if n_neg else None,
        "score_p20_gold": (
            round(float(np.percentile(gold["score"], 20)), 4) if len(gold) else None
        ),
        "score_median_gold": (
            round(float(gold["score"].median()), 4) if len(gold) else None
        ),
    }


def span_iou_vs_ref(
    scored: pd.DataFrame,
    ref: pd.DataFrame,
) -> dict[str, Any]:
    if scored.empty or ref.empty:
        return {"n_paired": 0, "iou_median": None}
    merged = scored[["id", "start_idx", "end_idx"]].merge(
        ref[["id", "start_idx", "end_idx"]],
        on="id",
        suffixes=("", "_ref"),
    )
    if merged.empty:
        return {"n_paired": 0, "iou_median": None}
    ious = [
        token_iou(
            (int(r.start_idx), int(r.end_idx)),
            (int(r.start_idx_ref), int(r.end_idx_ref)),
        )
        for r in merged.itertuples(index=False)
    ]
    return {
        "n_paired": int(len(ious)),
        "iou_median": round(float(np.median(ious)), 4),
        "iou_p20": round(float(np.percentile(ious, 20)), 4),
    }


def summarize_reduction(
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
    """Provenanced metrics + hinge/safe calls vs ``all_required``."""
    by_id = {r["config_id"]: r for r in config_rows}
    baseline = by_id.get("all_required") or by_id.get("full")
    base_recall = float(baseline["recall"] or 0.0) if baseline else 0.0
    base_fp = float(baseline["fp_rate"] or 0.0) if baseline else 0.0

    hinge_slots: list[dict[str, Any]] = []
    safe_slots: list[dict[str, Any]] = []
    for row in config_rows:
        if row.get("kind") != "single_slot_optional":
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
            "recall_drop_vs_all_required": round(drop, 4),
            "fp_rise_vs_all_required": round(rise, 4),
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
        "step": "STEPT1v",
        "method": "formula_reduction_l2",
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
        "safe_ablate_slots": safe_slots,
        "l2_required_tokens_guess": required_guess,
        "constraint": "measure_only_do_not_change_frozen_cut",
    }


def fixture_smoke() -> tuple[pd.DataFrame, pd.DataFrame, dict[str, Any], dict[str, Any]]:
    """Tiny in-memory positive/negative frames + cloud."""
    gold = pd.DataFrame(
        [
            {
                "id": "g1",
                "year": 1780,
                "resolutions_text": (
                    "IS ter Vergaderinge geleesen de Requeste van den suppliant"
                ),
            },
            {
                "id": "g2",
                "year": 1775,
                "resolutions_text": (
                    "is ter Vergaderinge gelesen de requeste van den coopman"
                ),
            },
            {
                "id": "g3",
                "year": 1760,
                "resolutions_text": (
                    "IS ter Vergaderinge geleesen de Requeste van Jan Jansen"
                ),
            },
        ]
    )
    neg = pd.DataFrame(
        [
            {
                "id": "n1",
                "year": 1780,
                "resolutions_text": "Ontfangen een missive van den Raad van Staate",
            },
            {
                "id": "n2",
                "year": 1780,
                "resolutions_text": "IS gehoord het rapport van de Heeren",
            },
        ]
    )
    cloud, notes = build_requeste_cloud(gold["resolutions_text"].tolist())
    return gold, neg, cloud, notes


# Re-export for scripts that still want default-optional scoring.
score_frame_default = _score_frame_default_optional
