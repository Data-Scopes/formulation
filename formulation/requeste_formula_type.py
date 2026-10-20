"""STEPT1k: requeste opener formula-type (slot-cloud + DAG), STEPT1a2-style.

Gold = ES ``proposition_type == rekest`` joined to ``resolutions_flat``.
Wording baseline (``requeste`` / ``rekest`` / ``reqte``) is for deltas only —
not the type definition. Empirical canonic from empty-band / Track S:
``IS ter Vergaderinge geleesen de Requeste``.
"""

from __future__ import annotations

import re
from typing import Any

import numpy as np
import pandas as pd
import pyarrow.parquet as pq

from data_io import resolve
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

FORMULA_TYPE_ID = "requeste_geleesen"
# Majority opener on ES-typed rekest / empty-band head near 1780.
REQUESTE_CANONIC = "IS ter Vergaderinge geleesen de Requeste"
CUE_PAD = 6

REQUESTE_SLOT_SEEDS = (
    "Requeste",
    "requeste",
    "Request",
    "request",
    "Rekest",
    "rekest",
    "Reqte",
    "reqte",
    "Reqte.",
    "reqte.",
)
GELEESEN_SLOT_SEEDS = (
    "geleesen",
    "gelesen",
    "gelezen",
)
VERGADERINGE_SLOT_SEEDS = (
    "Vergaderinge",
    "vergaderinge",
    "Vergadering",
    "vergadering",
)

_REQUESTE_WORD_RE = re.compile(
    r"(?i)\b(?:requeste?|rekest|reqte)\b",
)
_REQUESTE_TOKEN_RE = re.compile(
    r"(?i)^(?:requeste?|rekest|reqte)[\W_]*$",
)


def wording_flags(text: str) -> dict[str, bool]:
    """Boolean wording matcher for baseline deltas (not the formula type)."""
    has = bool(_REQUESTE_WORD_RE.search(str(text or "")))
    return {"requeste_wording": has}


def requeste_template() -> list[str]:
    return align_tokenize(REQUESTE_CANONIC)


def requeste_bootstrap_texts(
    texts: list[str],
    *,
    pad: int = CUE_PAD,
) -> tuple[list[str], dict[str, Any]]:
    """Cue-window texts around requeste/rekest tokens; fallback full stripped."""
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


def build_requeste_cloud(
    bootstrap_texts: list[str],
    *,
    period: str = "18c",
    year_min: int | None = YEAR_MIN,
    year_max: int | None = YEAR_MAX,
    cue_pad: int = CUE_PAD,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Bootstrap requeste cloud from cue windows; inject spelling seeds."""
    hits, window_notes = requeste_bootstrap_texts(bootstrap_texts, pad=cue_pad)
    cloud, notes = bootstrap_slot_cloud(
        hits,
        requeste_template(),
        template_id=FORMULA_TYPE_ID,
        period=period,
        year_min=year_min,
        year_max=year_max,
    )
    cloud = inject_seed_variants(
        cloud,
        seeds_by_canonical={
            "requeste": REQUESTE_SLOT_SEEDS,
            "geleesen": GELEESEN_SLOT_SEEDS,
            "vergaderinge": VERGADERINGE_SLOT_SEEDS,
        },
    )
    notes = {
        **notes,
        "bootstrap_input": window_notes,
        "canonic": REQUESTE_CANONIC,
        "seed_surfaces_requeste": list(REQUESTE_SLOT_SEEDS),
        "seed_surfaces_geleesen": list(GELEESEN_SLOT_SEEDS),
        "seed_surfaces_vergaderinge": list(VERGADERINGE_SLOT_SEEDS),
    }
    return cloud, notes


def score_text(text: str, cloud: dict[str, Any]) -> dict[str, Any]:
    """DAG align score of requeste cloud on full text."""
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


def fetch_es_rekest_ids(
    *,
    year_min: int = YEAR_MIN,
    year_max: int = YEAR_MAX,
    page_size: int = 1000,
) -> list[dict[str, Any]]:
    """All ES ``proposition_type=rekest`` ids in the year window (search_after)."""
    from formulation.republic_es import RepublicEsClient

    client = RepublicEsClient()
    rows: list[dict[str, Any]] = []
    search_after: list[Any] | None = None
    while True:
        body: dict[str, Any] = {
            "size": int(page_size),
            "sort": [{"_id": "asc"}],
            "_source": ["id", "metadata.id", "metadata.session_year"],
            "query": {
                "bool": {
                    "filter": [
                        {
                            "term": {
                                "metadata.proposition_type.keyword": "rekest"
                            }
                        },
                        {
                            "range": {
                                "metadata.session_year": {
                                    "gte": int(year_min),
                                    "lte": int(year_max),
                                }
                            }
                        },
                    ]
                }
            },
        }
        if search_after is not None:
            body["search_after"] = search_after
        response = client.search(client.config.resolutions_index, body)
        hits = response.get("hits", {}).get("hits") or []
        if not hits:
            break
        for hit in hits:
            src = hit.get("_source") or {}
            meta = src.get("metadata") or {}
            rid = meta.get("id") or src.get("id") or hit.get("_id")
            year = meta.get("session_year")
            if rid is None:
                continue
            rows.append(
                {
                    "id": str(rid),
                    "year": int(year) if year is not None else None,
                    "proposition_type": "rekest",
                    "gold_source": "es_proposition_type",
                }
            )
        search_after = hits[-1].get("sort")
        if search_after is None:
            break
    seen: set[str] = set()
    uniq: list[dict[str, Any]] = []
    for row in rows:
        if row["id"] in seen:
            continue
        seen.add(row["id"])
        uniq.append(row)
    return uniq


def join_texts_from_flat(id_year_rows: list[dict[str, Any]]) -> pd.DataFrame:
    """Attach ``resolutions_text`` from ``resolutions_flat`` by id (year chunks)."""
    if not id_year_rows:
        return pd.DataFrame(
            columns=["id", "year", "resolutions_text", "proposition_type"]
        )
    path = resolve("resolutions_flat")
    meta = pd.DataFrame(id_year_rows)
    meta["id"] = meta["id"].astype(str)
    meta["year"] = pd.to_numeric(meta["year"], errors="coerce")
    missing_year = meta["year"].isna()
    if missing_year.any():
        flat_meta = pq.read_table(
            path,
            columns=["id", "year"],
            filters=[
                ("year", ">=", int(YEAR_MIN)),
                ("year", "<=", int(YEAR_MAX)),
            ],
        ).to_pandas()
        flat_meta["id"] = flat_meta["id"].astype(str)
        year_map = flat_meta.set_index("id")["year"]
        meta.loc[missing_year, "year"] = meta.loc[missing_year, "id"].map(year_map)
    meta["year"] = pd.to_numeric(meta["year"], errors="coerce")
    meta = meta.dropna(subset=["year"]).copy()
    meta["year"] = meta["year"].astype(int)

    by_year = meta.groupby("year")["id"].apply(set)
    texts: dict[str, str] = {}
    for year, id_set in by_year.items():
        chunk = pq.read_table(
            path,
            columns=["id", "resolutions_text"],
            filters=[("year", "=", int(year))],
        ).to_pandas()
        chunk["id"] = chunk["id"].astype(str)
        hit = chunk.loc[chunk["id"].isin(id_set)]
        for rec in hit.to_dict(orient="records"):
            texts[str(rec["id"])] = str(rec.get("resolutions_text") or "")

    out_rows: list[dict[str, Any]] = []
    for rec in meta.to_dict(orient="records"):
        rid = str(rec["id"])
        if rid not in texts:
            continue
        out_rows.append(
            {
                "id": rid,
                "year": int(rec["year"]),
                "resolutions_text": texts[rid],
                "proposition_type": rec.get("proposition_type") or "rekest",
                "gold_source": rec.get("gold_source") or "es_proposition_type",
            }
        )
    return pd.DataFrame(out_rows).reset_index(drop=True)


def refresh_rekest_es_gold(
    *,
    year_min: int = YEAR_MIN,
    year_max: int = YEAR_MAX,
) -> pd.DataFrame:
    """ES typed ids → flat texts (caller saves as ``rekest_es_gold``)."""
    rows = fetch_es_rekest_ids(year_min=year_min, year_max=year_max)
    frame = join_texts_from_flat(rows)
    if frame.empty:
        raise ValueError("rekest ES gold empty after text join")
    return frame


def load_rekest_gold_18c() -> pd.DataFrame:
    """Frozen ``rekest_es_gold`` rows with text (run ``--refresh-gold`` first)."""
    from data_io import load

    gold = load("rekest_es_gold")
    if not isinstance(gold, pd.DataFrame):
        gold = pd.DataFrame(gold)
    out = gold.copy()
    out["year"] = pd.to_numeric(out["year"], errors="coerce")
    out = out.loc[out["year"].between(YEAR_MIN, YEAR_MAX, inclusive="both")].copy()
    out["resolutions_text"] = out["resolutions_text"].fillna("").astype(str)
    out["id"] = out["id"].astype(str)
    return out.reset_index(drop=True)


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
) -> dict[str, Any]:
    """Provenanced metrics for STEPT1k requeste opener."""
    g = gold_scored.copy()
    g["pred"] = g["score"] >= float(cut)
    g["period"] = g["year"].map(period_bucket)
    if "requeste_wording" not in g.columns:
        g["requeste_wording"] = g["resolutions_text"].map(
            lambda t: wording_flags(t)["requeste_wording"]
        )

    def _slice_metrics(frame: pd.DataFrame) -> dict[str, Any]:
        return {
            "n": int(len(frame)),
            "recall_model": _recall(frame["pred"]),
            "recall_requeste_wording": _recall(frame["requeste_wording"]),
            "delta_model_minus_wording": (
                round(
                    float(frame["pred"].mean() - frame["requeste_wording"].mean()),
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
    return {
        "formula_type_id": FORMULA_TYPE_ID,
        "method": "slot_cloud_dag_requeste_geleesen",
        "msa": False,
        "gold_definition": "es_proposition_type_rekest_joined_resolutions_flat",
        "year_min": YEAR_MIN,
        "year_max": YEAR_MAX,
        "year_split": YEAR_SPLIT,
        "operating_cut": float(cut),
        "operating_cut_rule": "p20_holdout_positive_scores",
        "random_state": int(random_state),
        "n_bootstrap_ids": int(len(bootstrap_ids)),
        "n_holdout_ids": int(len(holdout_ids)),
        "n_gold_18c": int(len(g)),
        "n_negatives": n_neg,
        "negative_definition": (
            f"stratified random sample n={n_neg} from resolutions_flat "
            f"{YEAR_MIN}-{YEAR_MAX}, excluding ES rekest gold and "
            "bootstrap-pool ids; not flag-filtered"
        ),
        "fp_count": n_fp,
        "fp_rate": fp_rate,
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
        "canonic": REQUESTE_CANONIC,
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
                "id": "fix-req-1",
                "year": 1720,
                "resolutions_text": (
                    "IS ter Vergaderinge geleesen de Requeste van den suppliant"
                ),
            },
            {
                "id": "fix-req-2",
                "year": 1750,
                "resolutions_text": (
                    "is ter Vergaderinge gelesen de requeste van den coopman"
                ),
            },
            {
                "id": "fix-req-3",
                "year": 1780,
                "resolutions_text": (
                    "IS ter Vergaderinge geleesen de Requeste van Jan Jansen "
                    "houdende verzoek om paspoort"
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
        ]
    )
    return gold, neg


__all__ = (
    "FALLBACK_CUT",
    "FORMULA_TYPE_ID",
    "HOLDOUT_FRAC",
    "NEG_N",
    "REQUESTE_CANONIC",
    "RNG",
    "YEAR_MAX",
    "YEAR_MIN",
    "build_requeste_cloud",
    "calibrate_cut",
    "fixture_smoke_frames",
    "load_rekest_gold_18c",
    "refresh_rekest_es_gold",
    "requeste_bootstrap_texts",
    "sample_negatives",
    "score_frame",
    "score_text",
    "split_bootstrap_holdout",
    "summarize_eval",
    "wording_flags",
)
