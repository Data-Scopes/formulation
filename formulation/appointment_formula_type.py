"""STEPT1a: appointment installation formula-type model (slot-cloud + DAG).

Defines a formula type by alignment, not regex. Wording baselines
(``welkom`` / ``sessie``) are reported for deltas only.
"""

from __future__ import annotations

import math
import re
from typing import Any

import numpy as np
import pandas as pd
import pyarrow.parquet as pq

from data_io import resolve
from formulation.boundary.align_dag import align_dag
from formulation.boundary.slot_cloud import (
    bootstrap_slot_cloud,
    cloud_variant_lists,
)
from formulation.boundary.tfidf_windows import tokenize

FORMULA_TYPE_ID = "appointment_installation"
# Empirical majority skeleton on aanstelling_selected 1731–96 (not datasheet
# "wordt hij welkom geheten", which matches almost no OCR).
WELKOM_CANONIC = "is den selven verwelkomt"
SESSIE_CANONIC = "sessie genomen"
YEAR_SPLIT = 1731
YEAR_MIN = 1705
YEAR_MAX = 1796
NEG_N = 500
HOLDOUT_FRAC = 0.2
RNG = 20261019
# Hypothesis operating cut when holdout yields no scores (fixture / failure).
FALLBACK_CUT = 2.0
# Floor/ceiling for IDF-style popularity weight (avoid log 0 / log inf).
POPULARITY_RATE_FLOOR = 1e-4
# Cue-window half-width (tokens) for welkom cloud bootstrap.
WELKOM_CUE_PAD = 6
_TRAIL_PUNCT = ".,;:!?\"'`()[]"


def popularity_weight(
    corpus_rate: float,
    *,
    floor: float = POPULARITY_RATE_FLOOR,
) -> float:
    """Downweight formulas that fire almost everywhere (IDF-style).

    ``goedgevonden``-like rates near 1.0 → weight near 0; rare types → large weight.
    Used to scale align scores when ranking / composing formula types — not as a
    substitute for the raw operating cut on a single-family eval.
    """
    p = float(corpus_rate)
    if p <= 0.0:
        return float(math.log(1.0 / floor))
    p = min(max(p, floor), 1.0 - floor)
    return float(math.log(1.0 / p))


def apply_popularity(
    score: float,
    corpus_rate: float,
    *,
    floor: float = POPULARITY_RATE_FLOOR,
) -> float:
    """``score * popularity_weight(corpus_rate)``."""
    return float(score) * popularity_weight(corpus_rate, floor=floor)

# Surfaces injected into clouds (seeds, not detectors).
WELKOM_SLOT_SEEDS = (
    "verwelkomt",
    "verwellekomt",
    "verwellecomen",
    "verwelkomen",
    "verwellecomt",
    "welkom",
    "welkomt",
    "verwelkom",
)
SELVEN_SLOT_SEEDS = (
    "selven",
    "selve",
    "zelven",
    "zelve",
    "deselve",
    "dezelve",
)
SESSIE_SLOT_SEEDS = (
    "sessie",
    "genomen",
    "nemen",
)

_WELKOM_RE = re.compile(
    r"welkom|verwelkom|verwellekom|verwellecom",
    re.IGNORECASE,
)
_SESSIE_RE = re.compile(r"sessie", re.IGNORECASE)
# Token-level cue for windowing (punctuation may trail the surface).
_WELKOM_TOKEN_RE = re.compile(
    r"(?i)^(?:verwe+l+e?(?:ko+m|compt)\w*|welkom\w*)[\W_]*$"
)


def align_tokenize(text: str) -> list[str]:
    """Whitespace tokens with leading/trailing punct stripped (OCR glue)."""
    out: list[str] = []
    for raw in tokenize(str(text or "")):
        tok = str(raw).strip(_TRAIL_PUNCT)
        if tok:
            out.append(tok)
    return out


def welkom_template() -> list[str]:
    return align_tokenize(WELKOM_CANONIC)


def sessie_template() -> list[str]:
    return align_tokenize(SESSIE_CANONIC)


def wording_flags(text: str) -> dict[str, bool]:
    """Boolean wording matchers for baseline deltas (not the formula type)."""
    blob = str(text or "")
    has_welkom = bool(_WELKOM_RE.search(blob))
    has_sessie = bool(_SESSIE_RE.search(blob))
    return {
        "welkom": has_welkom,
        "sessie": has_sessie,
        "welkom_or_sessie": has_welkom or has_sessie,
    }


def cue_windows(
    text: str,
    token_pattern: re.Pattern[str],
    *,
    pad: int = WELKOM_CUE_PAD,
) -> list[str]:
    """Short windows (±pad tokens) around cue-token hits; punct-stripped."""
    raw = tokenize(str(text or ""))
    if not raw:
        return []
    hits: list[int] = []
    for i, tok in enumerate(raw):
        if token_pattern.search(tok):
            hits.append(i)
    if not hits:
        return []
    windows: list[str] = []
    n = len(raw)
    pad_i = max(0, int(pad))
    for i in hits:
        start = max(0, i - pad_i)
        end = min(n, i + pad_i + 1)
        cleaned = [t.strip(_TRAIL_PUNCT) for t in raw[start:end]]
        cleaned = [t for t in cleaned if t]
        if cleaned:
            windows.append(" ".join(cleaned))
    return windows


def welkom_bootstrap_texts(
    texts: list[str],
    *,
    pad: int = WELKOM_CUE_PAD,
) -> tuple[list[str], dict[str, Any]]:
    """Cue-window texts for welkom cloud; fall back to full stripped texts."""
    windows: list[str] = []
    n_with_cue = 0
    for text in texts:
        wins = cue_windows(text, _WELKOM_TOKEN_RE, pad=pad)
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
    # Fixture / pre-cue pools: still align on punct-stripped full texts.
    stripped = [" ".join(align_tokenize(t)) for t in texts]
    stripped = [t for t in stripped if t]
    return stripped, {
        "mode": "full_text_stripped_fallback",
        "n_source_texts": int(len(texts)),
        "n_texts_with_cue": 0,
        "n_windows": 0,
        "cue_pad_tokens": int(pad),
    }


def inject_seed_variants(
    cloud: dict[str, Any],
    *,
    seeds_by_canonical: dict[str, tuple[str, ...]],
) -> dict[str, Any]:
    """Merge seed spellings into matching slots; refresh ``variant_lists``."""
    out = dict(cloud)
    slots = [dict(s) for s in (out.get("slots") or [])]
    for slot in slots:
        canon = str(slot["canonical"])
        key = canon.casefold()
        extra = seeds_by_canonical.get(key) or seeds_by_canonical.get(canon)
        if not extra:
            continue
        variants = list(slot.get("variants") or [])
        seen = {str(v["token"] if isinstance(v, dict) else v).casefold() for v in variants}
        for tok in extra:
            if tok.casefold() in seen:
                continue
            variants.append({"token": tok, "count": 0})
            seen.add(tok.casefold())
        slot["variants"] = variants
    out["slots"] = slots
    out["variant_lists"] = cloud_variant_lists(out)
    return out


def build_appointment_clouds(
    bootstrap_texts: list[str],
    *,
    period: str = "18c",
    year_min: int | None = YEAR_MIN,
    year_max: int | None = YEAR_MAX,
    welkom_cue_pad: int = WELKOM_CUE_PAD,
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    """Bootstrap welkom + sessie clouds from bootstrap texts; inject seeds.

    Welkom uses cue-windows around ``verwelkomt``-family tokens (empirical
    canonic ``is den selven verwelkomt``). Sessie still bootstraps on full
    texts (short canonic already accepts well).
    """
    welkom_hits, welkom_window_notes = welkom_bootstrap_texts(
        bootstrap_texts, pad=welkom_cue_pad
    )
    welkom_cloud, welkom_notes = bootstrap_slot_cloud(
        welkom_hits,
        welkom_template(),
        template_id=f"{FORMULA_TYPE_ID}_welkom",
        period=period,
        year_min=year_min,
        year_max=year_max,
    )
    sessie_cloud, sessie_notes = bootstrap_slot_cloud(
        [" ".join(align_tokenize(t)) for t in bootstrap_texts if str(t or "").strip()],
        sessie_template(),
        template_id=f"{FORMULA_TYPE_ID}_sessie",
        period=period,
        year_min=year_min,
        year_max=year_max,
    )
    welkom_cloud = inject_seed_variants(
        welkom_cloud,
        seeds_by_canonical={
            "verwelkomt": WELKOM_SLOT_SEEDS,
            "selven": SELVEN_SLOT_SEEDS,
        },
    )
    sessie_cloud = inject_seed_variants(
        sessie_cloud,
        seeds_by_canonical={
            "sessie": SESSIE_SLOT_SEEDS,
            "genomen": ("genomen", "nemen"),
        },
    )
    welkom_notes = {**welkom_notes, "bootstrap_input": welkom_window_notes}
    notes = {
        "welkom": welkom_notes,
        "sessie": sessie_notes,
        "seed_surfaces_welkom": list(WELKOM_SLOT_SEEDS),
        "seed_surfaces_selven": list(SELVEN_SLOT_SEEDS),
        "seed_surfaces_sessie": list(SESSIE_SLOT_SEEDS),
        "canonic_welkom": WELKOM_CANONIC,
        "canonic_sessie": SESSIE_CANONIC,
    }
    return welkom_cloud, sessie_cloud, notes


def score_text(
    text: str,
    welkom_cloud: dict[str, Any],
    sessie_cloud: dict[str, Any],
) -> dict[str, Any]:
    """Best DAG align score across welkom and sessie clouds on full text."""
    tokens = align_tokenize(str(text or ""))
    w_vars = welkom_cloud.get("variant_lists") or cloud_variant_lists(welkom_cloud)
    s_vars = sessie_cloud.get("variant_lists") or cloud_variant_lists(sessie_cloud)
    w_opt = list(welkom_cloud.get("optional_slots") or [])
    s_opt = list(sessie_cloud.get("optional_slots") or [])
    w_res = align_dag(w_vars, tokens, optional_slots=w_opt)
    s_res = align_dag(s_vars, tokens, optional_slots=s_opt)
    best_src = "welkom" if w_res.score >= s_res.score else "sessie"
    best = w_res if best_src == "welkom" else s_res
    return {
        "score": float(best.score),
        "best_cloud": best_src,
        "welkom_score": float(w_res.score),
        "sessie_score": float(s_res.score),
        "start_idx": int(best.start_idx),
        "end_idx": int(best.end_idx),
    }


def period_bucket(year: int | None) -> str:
    if year is None or (isinstance(year, float) and np.isnan(year)):
        return "unknown"
    y = int(year)
    if y < YEAR_SPLIT:
        return "pre_1731"
    return "post_1731"


def split_bootstrap_holdout(
    frame: pd.DataFrame,
    *,
    holdout_frac: float = HOLDOUT_FRAC,
    random_state: int = RNG,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """~80% bootstrap / ~20% holdout by id (fixed seed)."""
    ids = frame["id"].astype(str)
    uniq = ids.drop_duplicates()
    hold_n = max(1, int(round(len(uniq) * float(holdout_frac))))
    hold_ids = set(
        uniq.sample(n=min(hold_n, len(uniq)), random_state=random_state).tolist()
    )
    hold = frame.loc[ids.isin(hold_ids)].copy()
    boot = frame.loc[~ids.isin(hold_ids)].copy()
    if boot.empty:
        raise ValueError("bootstrap split empty; lower holdout_frac")
    return boot, hold


def load_selected_18c() -> pd.DataFrame:
    """``aanstelling_selected`` rows in 1705–1796 with text."""
    from data_io import load

    selected = load("aanstelling_selected")
    if not isinstance(selected, pd.DataFrame):
        selected = pd.DataFrame(selected)
    out = selected.copy()
    out["year"] = pd.to_numeric(out["year"], errors="coerce")
    out = out.loc[
        out["year"].between(YEAR_MIN, YEAR_MAX, inclusive="both")
    ].copy()
    out["resolutions_text"] = out["resolutions_text"].fillna("").astype(str)
    out["id"] = out["id"].astype(str)
    return out.reset_index(drop=True)


def sample_negatives(
    *,
    exclude_ids: set[str],
    n: int = NEG_N,
    random_state: int = RNG,
    year_min: int = YEAR_MIN,
    year_max: int = YEAR_MAX,
) -> pd.DataFrame:
    """Stratified-by-year sample of resolutions_flat texts (explicit negatives)."""
    path = resolve("resolutions_flat")
    meta = pq.read_table(
        path,
        columns=["id", "year"],
        filters=[
            ("year", ">=", int(year_min)),
            ("year", "<=", int(year_max)),
        ],
    ).to_pandas()
    meta["id"] = meta["id"].astype(str)
    meta["year"] = pd.to_numeric(meta["year"], errors="coerce")
    pool = meta.loc[~meta["id"].isin(exclude_ids)].copy()
    if pool.empty:
        raise ValueError("negative universe empty after exclusions")
    years = pool["year"].dropna().astype(int).unique()
    # Proportional per year, then top up to n.
    weights = pool.groupby("year").size()
    alloc = (weights / weights.sum() * int(n)).round().astype(int).clip(lower=0)
    while int(alloc.sum()) < int(n):
        alloc.loc[alloc.idxmax()] += 1
    while int(alloc.sum()) > int(n):
        grow = alloc[alloc > 0]
        alloc.loc[grow.idxmax()] -= 1
    parts: list[pd.DataFrame] = []
    rng = np.random.default_rng(int(random_state))
    for year, k in alloc.items():
        if k <= 0:
            continue
        g = pool.loc[pool["year"] == year]
        take = min(int(k), len(g))
        if take <= 0:
            continue
        idx = rng.choice(g.index.to_numpy(), size=take, replace=False)
        parts.append(g.loc[idx])
    sampled = pd.concat(parts, ignore_index=True) if parts else pool.head(0)
    if len(sampled) < int(n):
        rest = pool.loc[~pool["id"].isin(set(sampled["id"]))].copy()
        need = int(n) - len(sampled)
        if need > 0 and not rest.empty:
            extra = rest.sample(
                n=min(need, len(rest)), random_state=int(random_state) + 1
            )
            sampled = pd.concat([sampled, extra], ignore_index=True)
    sampled = sampled.head(int(n))
    # Fetch texts year-by-year for sampled ids only.
    by_year = sampled.groupby(sampled["year"].astype(int))["id"].apply(set)
    rows: list[dict[str, Any]] = []
    for year, id_set in by_year.items():
        chunk = pq.read_table(
            path,
            columns=["id", "year", "resolutions_text"],
            filters=[("year", "=", int(year))],
        ).to_pandas()
        chunk["id"] = chunk["id"].astype(str)
        hit = chunk.loc[chunk["id"].isin(id_set)]
        for rec in hit.to_dict(orient="records"):
            rows.append(
                {
                    "id": str(rec["id"]),
                    "year": int(rec["year"]),
                    "resolutions_text": str(rec.get("resolutions_text") or ""),
                }
            )
    out = pd.DataFrame(rows)
    if len(out) < int(n) * 0.9:
        raise ValueError(
            f"negative text fetch sparse: got {len(out)} of {n} sampled ids"
        )
    return out.head(int(n)).reset_index(drop=True)


def calibrate_cut(holdout_scores: list[float], *, fallback: float = FALLBACK_CUT) -> float:
    """Operating cut = 20th percentile of holdout positive scores (frozen later)."""
    if not holdout_scores:
        return float(fallback)
    return float(np.percentile(np.asarray(holdout_scores, dtype=float), 20))


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
    """Build provenanced metrics object for STEPT1a."""
    g = gold_scored.copy()
    g["pred"] = g["score"] >= float(cut)
    g["period"] = g["year"].map(period_bucket)
    if "welkom_or_sessie" not in g.columns:
        flags = g["resolutions_text"].map(wording_flags)
        g["welkom"] = flags.map(lambda d: d["welkom"])
        g["sessie"] = flags.map(lambda d: d["sessie"])
        g["welkom_or_sessie"] = flags.map(lambda d: d["welkom_or_sessie"])

    def _slice_metrics(frame: pd.DataFrame) -> dict[str, Any]:
        return {
            "n": int(len(frame)),
            "recall_model": _recall(frame["pred"]),
            "recall_welkom_or_sessie": _recall(frame["welkom_or_sessie"]),
            "recall_sessie_only": _recall(frame["sessie"]),
            "delta_model_minus_welkom_or_sessie": (
                round(
                    float(frame["pred"].mean() - frame["welkom_or_sessie"].mean()),
                    4,
                )
                if len(frame)
                else None
            ),
            "delta_model_minus_sessie_only": (
                round(float(frame["pred"].mean() - frame["sessie"].mean()), 4)
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
    # Prevalence proxy on non-gold universe ≈ FP rate at the operating cut.
    corpus_rate_proxy = (n_fp / n_neg) if n_neg else 0.0
    pop_w = popularity_weight(corpus_rate_proxy)
    g["score_weighted"] = g["score"].map(lambda s: apply_popularity(s, corpus_rate_proxy))
    if len(neg_scored):
        neg_scored = neg_scored.copy()
        neg_scored["score_weighted"] = neg_scored["score"].map(
            lambda s: apply_popularity(s, corpus_rate_proxy)
        )
    pre_recall = _recall(pre["pred"]) if len(pre) else None
    sessie_floor = 0.235
    return {
        "formula_type_id": FORMULA_TYPE_ID,
        "method": "slot_cloud_dag_max_welkom_sessie",
        "msa": False,
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
            f"{YEAR_MIN}-{YEAR_MAX}, excluding aanstelling_selected and "
            "bootstrap-pool ids; not flag-filtered"
        ),
        "fp_count": n_fp,
        "fp_rate": round(n_fp / n_neg, 4) if n_neg else None,
        "popularity": {
            "corpus_rate_proxy": round(float(corpus_rate_proxy), 4),
            "corpus_rate_proxy_note": (
                "hit rate on explicit negatives at operating cut "
                "(non-gold universe proxy); ubiquitous formulas → high rate → "
                "low weight (e.g. goedgevonden-like)"
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
        "pass_beats_sessie_floor_pre_1731": (
            pre_recall is not None and pre_recall > sessie_floor
        ),
        "sessie_only_floor_reference": sessie_floor,
        "pass_post_1731_ballpark_0_60": (
            (_recall(post["pred"]) or 0.0) >= 0.60 if len(post) else False
        ),
        "canonic_welkom": WELKOM_CANONIC,
        "canonic_sessie": SESSIE_CANONIC,
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


def score_frame(
    frame: pd.DataFrame,
    welkom_cloud: dict[str, Any],
    sessie_cloud: dict[str, Any],
    *,
    role: str,
) -> pd.DataFrame:
    """Score each row; attach wording flags and role label."""
    rows: list[dict[str, Any]] = []
    for rec in frame.to_dict(orient="records"):
        text = str(rec.get("resolutions_text") or "")
        scored = score_text(text, welkom_cloud, sessie_cloud)
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
    return pd.DataFrame(rows)


def fixture_smoke_frames() -> tuple[pd.DataFrame, pd.DataFrame]:
    """Tiny positive / negative frames for CI (no resolutions_flat)."""
    gold = pd.DataFrame(
        [
            {
                "id": "fix-pre-1",
                "year": 1720,
                "resolutions_text": (
                    "heeft dienvolgende sessie genomen in haar Hoogh Mogende Vergaderinge"
                ),
            },
            {
                "id": "fix-post-1",
                "year": 1750,
                "resolutions_text": (
                    "is den selven verwelkomt, ende heeft sessie genomen"
                ),
            },
            {
                "id": "fix-post-2",
                "year": 1780,
                "resolutions_text": (
                    "is den zelven verwellekomt, en heeft dienvolgende sessie"
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
                "resolutions_text": "Is ter Vergaderinge geleesen de Requeste",
            },
        ]
    )
    return gold, neg
