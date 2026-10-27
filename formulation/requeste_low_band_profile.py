"""STEPT1r: characterise the requeste low-score band (no new fetch).

STEPT1q found `dag_frozen_score` for the requeste opener is bimodal (6 of 6
canonic tokens matched -> 9.0, or exactly half -> 4.5), not a smooth
recall/FP tradeoff: 512/1380 clean-gold rows sit in the low band, median 69
tokens vs the high band's 175 (`docs/proofs/multi-template-registry/
STEPT1q-formula-retrieval.md`). This module characterises that split using
data already on disk -- `formula_retrieval_arms_scores` (STEPT1q, the clean
1380-row stratified gold) and `requeste_subtype_scores` (STEPT1l, the full
66,657-row model-predicted-positive population) -- joined by `id`. Neither
needs `resolutions_flat` or ES, so this runs with the external data volume
unmounted.

It does NOT read resolution text. Whether the low band is a genuinely
different (shorter) opener wording, an OCR/variant-coverage gap, or noise is
a hand-read question for a follow-up once `resolutions_flat` is reachable --
see STEPT1r guide, part B. This module answers the quantitative half: does
the low band correlate with routing subtype, period, or (most informatively)
the `gedelibereert_start` decision-stage marker already extracted in
STEPT1l?
"""

from __future__ import annotations

from typing import Any

import pandas as pd

from data_io import load
from formulation.es_gold_sample import wilson
from formulation.requeste_subtype_profile import ROUTING_FLAG_FOCUS

BAND_LOW_MAX = 4.6
BAND_HIGH_MIN = 8.0


def band_of(score: float | None) -> str | None:
    """low (<=4.6) / mid (4.6-8.0) / high (>=8.0); None if score is missing."""
    if score is None or (isinstance(score, float) and pd.isna(score)):
        return None
    if score <= BAND_LOW_MAX:
        return "low"
    if score >= BAND_HIGH_MIN:
        return "high"
    return "mid"


def load_clean_gold_bands() -> pd.DataFrame:
    """STEPT1q's 1380-row clean stratified requeste gold, banded."""
    rows = load("formula_retrieval_arms_scores")
    frame = pd.DataFrame(rows)
    frame = frame[(frame["type"] == "requeste") & (frame["role"] == "gold")].copy()
    frame["band"] = frame["dag_frozen_score"].map(band_of)
    return frame[["id", "year", "n_tokens", "dag_frozen_score", "band"]]


def load_full_population_bands() -> pd.DataFrame:
    """STEPT1l's 66,657-row model-predicted-positive requeste+ population, banded."""
    rows = load("requeste_subtype_scores")
    frame = pd.DataFrame(rows)
    frame["band"] = frame["score"].map(band_of)
    return frame


def fixture_bands() -> tuple[pd.DataFrame, pd.DataFrame]:
    """Tiny in-memory stand-in for both frames (no parquet / jsonl)."""
    clean = pd.DataFrame(
        [
            {"id": "a", "year": 1705, "n_tokens": 65, "dag_frozen_score": 4.5},
            {"id": "b", "year": 1705, "n_tokens": 70, "dag_frozen_score": 4.5},
            {"id": "c", "year": 1705, "n_tokens": 180, "dag_frozen_score": 9.0},
        ]
    )
    clean["band"] = clean["dag_frozen_score"].map(band_of)
    full = pd.DataFrame(
        [
            {
                "id": "a",
                "year": 1705,
                "score": 4.5,
                "requeste_subtype": "granted_direct",
                "goedgevonden": True,
                "handen": False,
                "in handen": False,
                "advies": False,
                "gedelibereert_start": False,
                "n_words": 60,
            },
            {
                "id": "b",
                "year": 1705,
                "score": 4.5,
                "requeste_subtype": "granted_direct",
                "goedgevonden": True,
                "handen": False,
                "in handen": False,
                "advies": False,
                "gedelibereert_start": False,
                "n_words": 72,
            },
            {
                "id": "c",
                "year": 1705,
                "score": 9.0,
                "requeste_subtype": "referred",
                "goedgevonden": True,
                "handen": True,
                "in handen": True,
                "advies": True,
                "gedelibereert_start": True,
                "n_words": 190,
            },
        ]
    )
    full["band"] = full["score"].map(band_of)
    return clean, full


def _band_counts(frame: pd.DataFrame) -> list[dict[str, Any]]:
    n_total = int(len(frame))
    out = []
    for band in ("low", "mid", "high"):
        n = int((frame["band"] == band).sum())
        lo, hi = wilson(n, n_total) if n_total else (0.0, 0.0)
        out.append(
            {
                "band": band,
                "n": n,
                "share": round(n / n_total, 4) if n_total else None,
                "share_ci95": [round(lo, 4), round(hi, 4)],
            }
        )
    return out


def summarize_clean_gold(frame: pd.DataFrame) -> dict[str, Any]:
    """Band sizes (with Wilson CI), length-by-band, decade-by-band -- 1380-row sample."""
    length_by_band = (
        frame.groupby("band")["n_tokens"]
        .agg(median="median", p25=lambda s: s.quantile(0.25), p75=lambda s: s.quantile(0.75))
        .round(1)
        .to_dict(orient="index")
    )
    decade = frame.assign(decade=(frame["year"] // 10) * 10)
    decade_table = (
        decade.groupby("decade")["band"]
        .value_counts(normalize=True)
        .unstack(fill_value=0.0)
        .round(3)
        .to_dict(orient="index")
    )
    return {
        "n": int(len(frame)),
        "bands": _band_counts(frame),
        "n_tokens_by_band": length_by_band,
        "band_share_by_decade": decade_table,
    }


def summarize_full_population(frame: pd.DataFrame) -> dict[str, Any]:
    """Band vs routing subtype, lexical flags, decade -- 66,657-row predicted-positive set."""
    n_total = int(len(frame))
    subtype_ct = (
        frame.groupby("band")["requeste_subtype"]
        .value_counts(normalize=True, dropna=True)
        .unstack(fill_value=0.0)
        .round(4)
        .to_dict(orient="index")
    )
    flag_rates: dict[str, dict[str, float]] = {}
    for flag in ROUTING_FLAG_FOCUS:
        if flag not in frame.columns:
            continue
        rates = (
            frame.groupby("band")[flag]
            .apply(lambda s: float(s.fillna(False).astype(bool).mean()))
            .round(4)
            .to_dict()
        )
        flag_rates[flag] = rates
    length_by_band = (
        frame.groupby("band")["n_words"]
        .agg(median="median", p25=lambda s: s.quantile(0.25), p75=lambda s: s.quantile(0.75))
        .round(1)
        .to_dict(orient="index")
    )
    decade = frame.assign(decade=(frame["year"] // 10) * 10)
    decade_table = (
        decade.groupby("decade")["band"]
        .value_counts(normalize=True)
        .unstack(fill_value=0.0)
        .round(3)
        .to_dict(orient="index")
    )
    return {
        "n": n_total,
        "bands": _band_counts(frame),
        "requeste_subtype_by_band": subtype_ct,
        "lexical_flag_rate_by_band": flag_rates,
        "n_words_by_band": length_by_band,
        "band_share_by_decade": decade_table,
    }


def build_low_band_profile(
    clean_frame: pd.DataFrame, full_frame: pd.DataFrame
) -> dict[str, Any]:
    """Combined STEPT1r part-A metrics: clean-gold sample + full predicted population."""
    return {
        "step": "STEPT1r",
        "part": "A-quantitative (no resolutions_flat / no ES)",
        "clean_gold_sample": summarize_clean_gold(clean_frame),
        "full_predicted_population": summarize_full_population(full_frame),
        "naming_gate": {
            "auto_mint": False,
            "rule": (
                "New template_id / blueprint split requires a human NOTES call "
                "after part B sample read — measurements do not name types."
            ),
            "call_options": [
                "keep_one_type_accept_fp_tradeoff",
                "split_short_form_subtype_after_human_name",
                "characteristics_only_no_new_id",
            ],
        },
        "composition_note": (
            "Standard opening/decision formulas scaffold bags; rarer carriers "
            "often decide type and are easier to localise once named. "
            "Wording drift → period/slot variants, not automatic new ids."
        ),
        "part_b_pending": (
            "Hand-read of low-band vs high-band resolution text "
            "(resolutions_flat / external volume unmounted this session) -- "
            "settles whether the low band is a genuinely different short-form "
            "opener wording, an OCR/variant-coverage gap in the existing "
            "slot cloud, or noise. See STEPT1r guide part B."
        ),
    }
