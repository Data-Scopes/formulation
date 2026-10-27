"""STEPT1s: short requeste opener ``Op de Requeste`` (slot-cloud + DAG).

Sibling of STEPT1k ``requeste_geleesen``. Gold = ES ``proposition_type=rekest``
rows whose head matches the STEPT1r-named short opener — not full rekest
(only ~37% of clean gold is short-form). Wording baseline is the same head
surface for deltas; FP on non-rekest negatives is the hard gate (3-token
canonic).
"""

from __future__ import annotations

import re
from typing import Any

import numpy as np
import pandas as pd

from formulation.appointment_formula_type import (
    FALLBACK_CUT,
    HOLDOUT_FRAC,
    NEG_N,
    RNG,
    YEAR_MAX,
    YEAR_MIN,
    YEAR_SPLIT,
    align_tokenize,
    apply_popularity,
    calibrate_cut,
    cue_windows,
    inject_seed_variants,
    popularity_weight,
    sample_negatives,
    split_bootstrap_holdout,
)
from formulation.boundary.align_dag import align_dag
from formulation.boundary.slot_cloud import bootstrap_slot_cloud, cloud_variant_lists
from formulation.requeste_formula_type import (
    REQUESTE_SLOT_SEEDS,
    load_rekest_gold_18c,
)

FORMULA_TYPE_ID = "requeste_op_de"
# STEPT1r human name / canonic (confirmed 2026-10-22).
REQUESTE_OP_DE_CANONIC = "Op de Requeste"
CUE_PAD = 6
HEAD_SCAN = 12
LONG_HEAD_SAMPLE_N = 200

OP_SLOT_SEEDS = (
    "Op",
    "OP",
    "op",
)

_REQUESTE_TOKEN_RE = re.compile(
    r"(?i)^(?:requeste?|rekest|reqte)[\W_]*$",
)
_OP_DE_HEAD_WORDING_RE = re.compile(
    r"(?i)^\s*op\s+de\s+(?:requeste?|rekest|reqte)\b",
)


def is_op_de_requeste_head(text: str, *, max_scan: int = HEAD_SCAN) -> bool:
    """True if early tokens are Op/OP/op + de + requeste-surface."""
    tokens = align_tokenize(text)
    n = len(tokens)
    if n < 3:
        return False
    # i..i+2 must stay in-bounds; triple should sit inside the first max_scan tokens.
    last_i = min(n - 3, max(0, int(max_scan) - 3))
    for i in range(last_i + 1):
        if (
            tokens[i].casefold() == "op"
            and tokens[i + 1].casefold() == "de"
            and bool(_REQUESTE_TOKEN_RE.match(tokens[i + 2]))
        ):
            return True
    return False


def is_long_requeste_head(text: str, *, max_scan: int = HEAD_SCAN) -> bool:
    """Heuristic long opener head: IS … ter … Vergaderinge in early tokens."""
    tokens = [t.casefold() for t in align_tokenize(text)[: max(0, int(max_scan))]]
    if len(tokens) < 3:
        return False
    has_is = any(t == "is" for t in tokens[:4])
    has_ter = "ter" in tokens
    has_verg = any(t.startswith("vergader") for t in tokens)
    return bool(has_is and has_ter and has_verg)


def wording_flags(text: str) -> dict[str, bool]:
    """Head wording matcher for baseline deltas (not the formula type)."""
    blob = str(text or "")
    return {"op_de_requeste_wording": bool(_OP_DE_HEAD_WORDING_RE.search(blob))}


def requeste_op_de_template() -> list[str]:
    return align_tokenize(REQUESTE_OP_DE_CANONIC)


def requeste_op_de_bootstrap_texts(
    texts: list[str],
    *,
    pad: int = CUE_PAD,
) -> tuple[list[str], dict[str, Any]]:
    """Cue-window texts around requeste tokens; fallback full stripped."""
    windows: list[str] = []
    n_with_cue = 0
    for text in texts:
        wins = cue_windows(text, _REQUESTE_TOKEN_RE, pad=pad)
        if wins:
            n_with_cue += 1
            windows.extend(wins)
    if windows:
        return windows, {
            "mode": "cue_windows",
            "n_source_texts": int(len(texts)),
            "n_texts_with_cue": int(n_with_cue),
            "n_windows": int(len(windows)),
            "cue_pad_tokens": int(pad),
        }
    stripped = [" ".join(align_tokenize(t)) for t in texts]
    stripped = [t for t in stripped if t]
    return stripped, {
        "mode": "full_text_stripped_fallback",
        "n_source_texts": int(len(texts)),
        "n_texts_with_cue": 0,
        "n_windows": 0,
        "cue_pad_tokens": int(pad),
    }


def build_requeste_op_de_cloud(
    bootstrap_texts: list[str],
    *,
    period: str = "18c",
    year_min: int | None = YEAR_MIN,
    year_max: int | None = YEAR_MAX,
    cue_pad: int = CUE_PAD,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Bootstrap short-opener cloud from cue windows; inject Op / Requeste seeds."""
    hits, window_notes = requeste_op_de_bootstrap_texts(bootstrap_texts, pad=cue_pad)
    cloud, notes = bootstrap_slot_cloud(
        hits,
        requeste_op_de_template(),
        template_id=FORMULA_TYPE_ID,
        period=period,
        year_min=year_min,
        year_max=year_max,
    )
    cloud = inject_seed_variants(
        cloud,
        seeds_by_canonical={
            "op": OP_SLOT_SEEDS,
            "requeste": REQUESTE_SLOT_SEEDS,
        },
    )
    notes = {
        **notes,
        "bootstrap_input": window_notes,
        "canonic": REQUESTE_OP_DE_CANONIC,
        "seed_surfaces_op": list(OP_SLOT_SEEDS),
        "seed_surfaces_requeste": list(REQUESTE_SLOT_SEEDS),
    }
    return cloud, notes


def score_text(text: str, cloud: dict[str, Any]) -> dict[str, Any]:
    """DAG align score of short requeste cloud on full text."""
    tokens = align_tokenize(str(text or ""))
    variants = cloud.get("variant_lists") or cloud_variant_lists(cloud)
    optional = list(cloud.get("optional_slots") or [])
    res = align_dag(variants, tokens, optional_slots=optional)
    return {
        "score": float(res.score),
        "start_idx": int(res.start_idx),
        "end_idx": int(res.end_idx),
    }


def period_bucket(year: int | None) -> str:
    if year is None or (isinstance(year, float) and np.isnan(year)):
        return "unknown"
    return "pre_1731" if int(year) < YEAR_SPLIT else "post_1731"


def load_short_requeste_gold_18c() -> pd.DataFrame:
    """Frozen ``rekest_es_gold`` filtered to ``Op de Requeste`` head."""
    gold = load_rekest_gold_18c()
    mask = gold["resolutions_text"].map(is_op_de_requeste_head)
    out = gold.loc[mask].copy()
    if out.empty:
        raise ValueError(
            "short requeste gold empty after Op-de-Requeste head filter; "
            "check rekest_es_gold + resolutions_text"
        )
    out["gold_source"] = "es_rekest_op_de_requeste_head"
    return out.reset_index(drop=True)


def load_long_head_rekest_sample(
    *,
    n: int = LONG_HEAD_SAMPLE_N,
    random_state: int = RNG,
    exclude_ids: set[str] | None = None,
) -> pd.DataFrame:
    """Sample of long-opener rekest for cross-fire diagnostic."""
    gold = load_rekest_gold_18c()
    excl = exclude_ids or set()
    mask = gold["resolutions_text"].map(is_long_requeste_head) & ~gold["id"].isin(excl)
    pool = gold.loc[mask]
    if pool.empty:
        return pool.copy()
    take = min(int(n), len(pool))
    return pool.sample(n=take, random_state=int(random_state)).reset_index(drop=True)


def score_frame(
    frame: pd.DataFrame, cloud: dict[str, Any], *, role: str, progress_every: int = 2000
) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    total = len(frame)
    for i, rec in enumerate(frame.to_dict(orient="records"), start=1):
        text = str(rec.get("resolutions_text") or "")
        scored = score_text(text, cloud)
        flags = wording_flags(text)
        rows.append(
            {
                "id": str(rec["id"]),
                "year": int(rec["year"]) if rec.get("year") is not None else None,
                "role": role,
                "resolutions_text": text,
                **scored,
                **flags,
            }
        )
        if progress_every and i % progress_every == 0:
            print(f"  score_frame[{role}]: {i}/{total}", flush=True)
    return pd.DataFrame(rows)


def _recall(hits: pd.Series) -> float | None:
    if len(hits) == 0:
        return None
    return round(float(hits.mean()), 4)


def summarize_eval(
    gold_scored: pd.DataFrame,
    neg_scored: pd.DataFrame,
    *,
    cut: float,
    cloud_notes: dict[str, Any],
    bootstrap_ids: list[str],
    holdout_ids: list[str],
    random_state: int,
    long_head_scored: pd.DataFrame | None = None,
    n_rekest_total: int | None = None,
) -> dict[str, Any]:
    """Provenanced metrics for STEPT1s short requeste opener."""
    g = gold_scored.copy()
    g["pred"] = g["score"] >= float(cut)
    g["period"] = g["year"].map(period_bucket)
    if "op_de_requeste_wording" not in g.columns:
        g["op_de_requeste_wording"] = g["resolutions_text"].map(
            lambda t: wording_flags(t)["op_de_requeste_wording"]
        )

    def _slice_metrics(frame: pd.DataFrame) -> dict[str, Any]:
        return {
            "n": int(len(frame)),
            "recall_model": _recall(frame["pred"]),
            "recall_op_de_requeste_wording": _recall(frame["op_de_requeste_wording"]),
            "delta_model_minus_wording": (
                round(
                    float(
                        frame["pred"].mean() - frame["op_de_requeste_wording"].mean()
                    ),
                    4,
                )
                if len(frame)
                else None
            ),
            "score_mean": round(float(frame["score"].mean()), 4) if len(frame) else None,
            "score_p20": (
                round(float(np.percentile(frame["score"], 20)), 4) if len(frame) else None
            ),
        }

    pre = g.loc[g["period"] == "pre_1731"]
    post = g.loc[g["period"] == "post_1731"]
    n_fp = int((neg_scored["score"] >= float(cut)).sum()) if len(neg_scored) else 0
    n_neg = int(len(neg_scored))
    corpus_rate_proxy = (n_fp / n_neg) if n_neg else 0.0
    pop_w = popularity_weight(corpus_rate_proxy)
    g["score_weighted"] = g["score"].map(lambda s: apply_popularity(s, corpus_rate_proxy))
    if len(neg_scored):
        neg_scored = neg_scored.copy()
        neg_scored["score_weighted"] = neg_scored["score"].map(
            lambda s: apply_popularity(s, corpus_rate_proxy)
        )
    overall_recall = _recall(g["pred"])
    fp_rate = round(n_fp / n_neg, 4) if n_neg else None

    cross_fire: dict[str, Any] | None = None
    if long_head_scored is not None and len(long_head_scored):
        lh = long_head_scored.copy()
        lh["pred"] = lh["score"] >= float(cut)
        cross_fire = {
            "n": int(len(lh)),
            "fire_rate_at_cut": _recall(lh["pred"]),
            "score_mean": round(float(lh["score"].mean()), 4),
            "note": (
                "short model on long-head rekest sample; expect low fire "
                "(specificity within rekest)"
            ),
        }

    return {
        "formula_type_id": FORMULA_TYPE_ID,
        "method": "slot_cloud_dag_requeste_op_de",
        "msa": False,
        "gold_definition": (
            "es_proposition_type_rekest_joined_resolutions_flat_filtered_"
            "op_de_requeste_head"
        ),
        "year_min": YEAR_MIN,
        "year_max": YEAR_MAX,
        "year_split": YEAR_SPLIT,
        "operating_cut": float(cut),
        "operating_cut_rule": "p20_holdout_positive_scores",
        "random_state": int(random_state),
        "n_bootstrap_ids": int(len(bootstrap_ids)),
        "n_holdout_ids": int(len(holdout_ids)),
        "n_gold_18c": int(len(g)),
        "n_rekest_es_gold_total": n_rekest_total,
        "short_form_share_of_rekest": (
            round(float(len(g) / n_rekest_total), 4)
            if n_rekest_total and n_rekest_total > 0
            else None
        ),
        "n_negatives": n_neg,
        "negative_definition": (
            f"stratified random sample n={n_neg} from resolutions_flat "
            f"{YEAR_MIN}-{YEAR_MAX}, excluding full ES rekest gold and "
            "bootstrap-pool ids; not flag-filtered"
        ),
        "fp_count": n_fp,
        "fp_rate": fp_rate,
        "cross_fire_long_head_rekest": cross_fire,
        "popularity": {
            "corpus_rate_proxy": round(float(corpus_rate_proxy), 4),
            "corpus_rate_proxy_note": (
                "hit rate on explicit negatives at operating cut"
            ),
            "weight": round(float(pop_w), 4),
            "weight_formula": "log(1 / clip(rate))",
            "score_weighted_gold_mean": (
                round(float(g["score_weighted"].mean()), 4) if len(g) else None
            ),
            "score_weighted_neg_mean": (
                round(float(neg_scored["score_weighted"].mean()), 4)
                if len(neg_scored)
                else None
            ),
        },
        "overall": _slice_metrics(g),
        "pre_1731": _slice_metrics(pre),
        "post_1731": _slice_metrics(post),
        "pass_overall_recall_ge_0_70": (
            overall_recall is not None and overall_recall >= 0.70
        ),
        "pass_fp_rate_le_0_05": (fp_rate is not None and fp_rate <= 0.05),
        "canonic": REQUESTE_OP_DE_CANONIC,
        "cloud_notes": cloud_notes,
        "align_score_gold": {
            "min": round(float(g["score"].min()), 4) if len(g) else None,
            "max": round(float(g["score"].max()), 4) if len(g) else None,
            "mean": round(float(g["score"].mean()), 4) if len(g) else None,
        },
        "align_score_neg": {
            "min": round(float(neg_scored["score"].min()), 4) if len(neg_scored) else None,
            "max": round(float(neg_scored["score"].max()), 4) if len(neg_scored) else None,
            "mean": round(float(neg_scored["score"].mean()), 4) if len(neg_scored) else None,
        },
    }


def fixture_smoke_frames() -> tuple[pd.DataFrame, pd.DataFrame]:
    """Tiny positive / negative frames for CI (no ES / parquet)."""
    gold = pd.DataFrame(
        [
            {
                "id": "fix-opde-1",
                "year": 1720,
                "resolutions_text": (
                    "Op de Requeste van den suppliant IS na deliberatie "
                    "goedgevonden en verstaan"
                ),
            },
            {
                "id": "fix-opde-2",
                "year": 1750,
                "resolutions_text": (
                    "OP de requeste van den coopman is goedgevonden"
                ),
            },
            {
                "id": "fix-opde-3",
                "year": 1780,
                "resolutions_text": (
                    "Op de Rekest van Jan Jansen houdende verzoek om paspoort "
                    "is goedgevonden"
                ),
            },
        ]
    )
    neg = pd.DataFrame(
        [
            {
                "id": "fix-neg-1",
                "year": 1780,
                "resolutions_text": "Ontfangen een missive van den ambassadeur",
            },
            {
                "id": "fix-neg-2",
                "year": 1720,
                "resolutions_text": (
                    "IS ter Vergaderinge geleesen het Advis van 's Lands Advocaten"
                ),
            },
            {
                "id": "fix-neg-3",
                "year": 1760,
                "resolutions_text": (
                    "IS ter Vergaderinge geleesen de Requeste van den suppliant"
                ),
            },
        ]
    )
    return gold, neg


__all__ = (
    "FALLBACK_CUT",
    "FORMULA_TYPE_ID",
    "HOLDOUT_FRAC",
    "NEG_N",
    "REQUESTE_OP_DE_CANONIC",
    "RNG",
    "YEAR_MAX",
    "YEAR_MIN",
    "build_requeste_op_de_cloud",
    "calibrate_cut",
    "fixture_smoke_frames",
    "is_long_requeste_head",
    "is_op_de_requeste_head",
    "load_long_head_rekest_sample",
    "load_short_requeste_gold_18c",
    "requeste_op_de_bootstrap_texts",
    "sample_negatives",
    "score_frame",
    "score_text",
    "split_bootstrap_holdout",
    "summarize_eval",
    "wording_flags",
)
