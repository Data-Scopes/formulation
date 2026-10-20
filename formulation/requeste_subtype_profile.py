"""STEPT1l: requeste+ routing subtype characterisation.

Provisional cuts (not accepted formula types):

- ``referred`` -- ``handen`` / ``in handen`` present (routed to a body before
  decision)
- ``granted_direct`` -- ``goedgevonden`` present, not referred
- ``routing_unclear`` -- outcome joined but neither flag present

Universe is model-detected requeste+: ES ``proposition_type == rekest`` gold
rows (STEPT1k) where the slot-cloud/DAG opener score clears the accepted
operating cut (``pred``). Gold rows the model missed (``pred`` False) are a
recall-gap count only -- an opener-detection miss, not a requeste+ subtype.
Reuses STEPT1k's ``formula_type_requeste_scores`` (no ES remget).
``formula_type_requeste_scores`` carries no ``session_date`` (unlike
STEPT1e/STEPT1f, built from ES metadata); it is derived here from
``resolutions_flat.date`` by id before ``join_outcome_flags``. Flags describe
routing shape -- they are not outcomes.
"""

from __future__ import annotations

from typing import Any

import pandas as pd

from data_io import load
from formulation.formula_type_composition_graph import COMPOSITION_ROOT
from formulation.ontfangen_partition import _flag_rates, _type_mix
from formulation.typology_sample import (
    _resolution_index_from_id,
    _top_flag_combinations,
    join_outcome_flags,
)

SUBTYPE_REFERRED = "referred"
SUBTYPE_GRANTED = "granted_direct"
SUBTYPE_UNCLEAR = "routing_unclear"
SUBTYPES = (SUBTYPE_REFERRED, SUBTYPE_GRANTED, SUBTYPE_UNCLEAR)

# Routing/outcome surfaces named in template-design-questions.md as the
# "answerable now" structural lever (goedgevonden vs handen/in handen vs
# advies co-occurrence), plus the decision-stage marker from STEPT1e/f.
ROUTING_FLAG_FOCUS = (
    "goedgevonden",
    "handen",
    "in handen",
    "advies",
    "gedelibereert_start",
)

__all__ = (
    "ROUTING_FLAG_FOCUS",
    "SUBTYPE_GRANTED",
    "SUBTYPE_REFERRED",
    "SUBTYPE_UNCLEAR",
    "SUBTYPES",
    "attach_session_date",
    "attach_word_counts",
    "build_characterisation_frame",
    "fixture_characterisation_frame",
    "load_requeste_scores",
    "summarize_requeste_subtypes",
)


def load_requeste_scores(*, year: int | None = None) -> pd.DataFrame:
    """Load STEPT1k per-id scores; optional single-year slice of ES gold rows."""
    raw = load("formula_type_requeste_scores")
    frame = pd.DataFrame(raw) if not isinstance(raw, pd.DataFrame) else raw
    frame = frame.copy()
    frame["id"] = frame["id"].astype(str)
    frame["year"] = pd.to_numeric(frame["year"], errors="coerce")
    frame["pred"] = frame["pred"].astype(bool)
    gold = frame.loc[frame["role"] == "gold"].copy()
    if gold.empty:
        raise ValueError("No role=='gold' rows in formula_type_requeste_scores")
    if year is not None:
        gold = gold.loc[gold["year"] == int(year)].copy()
        if gold.empty:
            raise ValueError(f"No gold rows for year={year}")
    gold["resolution_index"] = gold["id"].map(_resolution_index_from_id)
    return gold


def attach_session_date(frame: pd.DataFrame) -> pd.DataFrame:
    """Join ``session_date`` from ``resolutions_flat.date`` by id."""
    flag_cols = list(frame.attrs.get("flag_columns") or [])
    out = frame.copy()
    out["id"] = out["id"].astype(str)
    flat = load("resolutions_flat")
    ids = set(out["id"])
    sub = flat.loc[flat["id"].astype(str).isin(ids), ["id", "date"]].copy()
    sub["id"] = sub["id"].astype(str)
    sub = sub.rename(columns={"date": "session_date"})
    out = out.merge(sub, on="id", how="left")
    out.attrs["flag_columns"] = flag_cols
    return out


def attach_word_counts(frame: pd.DataFrame) -> pd.DataFrame:
    """Join whitespace word counts from ``resolutions_flat`` (vectorized)."""
    flag_cols = list(frame.attrs.get("flag_columns") or [])
    out = frame.copy()
    out["id"] = out["id"].astype(str)
    flat = load("resolutions_flat")
    ids = set(out["id"])
    sub = flat.loc[flat["id"].astype(str).isin(ids), ["id", "resolutions_text"]].copy()
    sub["id"] = sub["id"].astype(str)
    sub["n_words"] = (
        sub["resolutions_text"].fillna("").astype(str).str.split().str.len()
    )
    out = out.merge(sub[["id", "n_words"]], on="id", how="left")
    out["text_joined"] = out["n_words"].notna()
    out.attrs["flag_columns"] = flag_cols
    return out


def build_characterisation_frame(
    scores: pd.DataFrame,
    *,
    join_flags: bool = True,
    join_text_length: bool = True,
) -> pd.DataFrame:
    """Model-detected requeste+ rows (``pred``) with routing subtype label."""
    detected = scores.loc[scores["pred"]].copy()
    missed = scores.loc[~scores["pred"]].copy()
    if detected.empty:
        raise ValueError("No requeste+ (pred==True) rows in gold scores")

    if join_flags:
        detected = attach_session_date(detected)
        if "resolution_index" not in detected.columns:
            detected["resolution_index"] = detected["id"].map(_resolution_index_from_id)
        detected = join_outcome_flags(detected)
    else:
        detected["outcome_joined"] = False
        detected.attrs["flag_columns"] = []

    if join_text_length:
        detected = attach_word_counts(detected)
    else:
        detected["n_words"] = pd.NA
        detected["text_joined"] = False

    flag_cols = list(detected.attrs.get("flag_columns") or [])
    referred_flag = pd.Series(False, index=detected.index)
    for col in ("handen", "in handen"):
        if col in detected.columns:
            referred_flag = referred_flag | detected[col].fillna(False).astype(bool)
    granted_flag = (
        detected["goedgevonden"].fillna(False).astype(bool)
        if "goedgevonden" in detected.columns
        else pd.Series(False, index=detected.index)
    )
    joined = (
        detected["outcome_joined"]
        if "outcome_joined" in detected.columns
        else pd.Series(False, index=detected.index)
    )

    detected["requeste_subtype"] = pd.NA
    detected.loc[joined & referred_flag, "requeste_subtype"] = SUBTYPE_REFERRED
    detected.loc[
        joined & ~referred_flag & granted_flag, "requeste_subtype"
    ] = SUBTYPE_GRANTED
    detected.loc[
        joined & ~referred_flag & ~granted_flag, "requeste_subtype"
    ] = SUBTYPE_UNCLEAR

    detected.attrs["flag_columns"] = flag_cols
    detected.attrs["n_missed"] = int(len(missed))
    return detected


def _length_summary(group: pd.DataFrame) -> dict[str, Any]:
    words = group["n_words"].dropna() if "n_words" in group.columns else pd.Series(dtype=float)
    return {
        "n_text_joined": int(group["text_joined"].sum())
        if "text_joined" in group.columns
        else 0,
        "n_words_median": float(words.median()) if not words.empty else None,
        "n_words_q1": float(words.quantile(0.25)) if not words.empty else None,
        "n_words_q3": float(words.quantile(0.75)) if not words.empty else None,
    }


def _subtype_record(
    group: pd.DataFrame,
    *,
    subtype: str,
    n_detected: int,
    flag_cols: list[str],
) -> dict[str, Any]:
    n = len(group)
    return {
        "requeste_subtype": subtype,
        "n": n,
        "frac_of_requeste_plus": n / n_detected if n_detected else None,
        "length": _length_summary(group),
        "flags": {
            "n_outcome_joined": int(group["outcome_joined"].sum()) if n else 0,
            "flag_rates": _flag_rates(group, flag_cols, focus=ROUTING_FLAG_FOCUS),
            "top_flag_combinations": _top_flag_combinations(group, flag_cols),
        },
    }


def _contrast(
    referred: dict[str, Any],
    granted: dict[str, Any],
    unclear: dict[str, Any],
) -> dict[str, Any]:
    def _len(rec: dict[str, Any]) -> float | None:
        return (rec.get("length") or {}).get("n_words_median")

    def _rate(rec: dict[str, Any], flag: str) -> float | None:
        rates = ((rec.get("flags") or {}).get("flag_rates") or {})
        return rates.get(flag)

    med_r, med_g = _len(referred), _len(granted)
    return {
        "n_words_median_referred": med_r,
        "n_words_median_granted_direct": med_g,
        "n_words_median_delta_referred_minus_granted": (
            (med_r - med_g) if med_r is not None and med_g is not None else None
        ),
        "advies_rate_referred": _rate(referred, "advies"),
        "advies_rate_granted_direct": _rate(granted, "advies"),
        "advies_rate_routing_unclear": _rate(unclear, "advies"),
        "n_routing_unclear": unclear.get("n"),
        "frac_routing_unclear": unclear.get("frac_of_requeste_plus"),
    }


def summarize_requeste_subtypes(
    frame: pd.DataFrame,
    *,
    year: int | None,
) -> dict[str, Any]:
    """Provenanced metrics for NOTES + save."""
    flag_cols: list[str] = list(frame.attrs.get("flag_columns") or [])
    n_detected = len(frame)
    n_missed = int(frame.attrs.get("n_missed") or 0)

    by_subtype: dict[str, dict[str, Any]] = {}
    for subtype in SUBTYPES:
        group = frame[frame["requeste_subtype"] == subtype]
        by_subtype[subtype] = _subtype_record(
            group,
            subtype=subtype,
            n_detected=n_detected,
            flag_cols=flag_cols,
        )

    referred = by_subtype[SUBTYPE_REFERRED]
    granted = by_subtype[SUBTYPE_GRANTED]
    unclear = by_subtype[SUBTYPE_UNCLEAR]
    n_unlabelled = n_detected - referred["n"] - granted["n"] - unclear["n"]

    return {
        "step": "STEPT1l",
        "method": "requeste_subtype_characterisation",
        "year": int(year) if year is not None else "all_18c",
        "composition_root": COMPOSITION_ROOT,
        "universe": "requeste_plus_model_detected",
        "kind_filter": "proposition_type == rekest (ES gold, by construction)",
        "n_requeste_plus": n_detected,
        "n_recall_miss": n_missed,
        "n_outcome_unjoined": int(n_unlabelled),
        "outcome_join_coverage": (
            float(frame["outcome_joined"].mean()) if n_detected else 0.0
        ),
        "text_join_coverage": (
            float(frame["text_joined"].mean())
            if n_detected and "text_joined" in frame.columns
            else 0.0
        ),
        "subtypes": [by_subtype[s] for s in SUBTYPES],
        "contrast": _contrast(referred, granted, unclear),
        "notes": (
            "Provisional requeste+ routing subtype characterisation over "
            "model-detected requeste+ (STEPT1k pred==True on ES rekest "
            "gold). referred / granted_direct / routing_unclear are "
            "characteristics cuts, not accepted formula types. Flags are "
            "boilerplate surfaces, not archival outcomes. Recall-miss rows "
            "(ES gold the model didn't detect) are a count only, not "
            "characterised here."
        ),
    }


def fixture_characterisation_frame() -> pd.DataFrame:
    """Tiny in-memory frame (no parquet / no formula_documents)."""
    rows = [
        {
            "id": "session-3835-num-1-resolution-1",
            "year": 1780,
            "role": "gold",
            "pred": True,
            "score": 6.0,
            "session_date": "1780-01-02",
            "resolution_index": 1,
            "outcome_joined": True,
            "goedgevonden": False,
            "handen": True,
            "in handen": False,
            "advies": True,
            "gedelibereert_start": False,
            "n_words": 60,
            "text_joined": True,
        },
        {
            "id": "session-3835-num-1-resolution-2",
            "year": 1780,
            "role": "gold",
            "pred": True,
            "score": 5.0,
            "session_date": "1780-01-03",
            "resolution_index": 2,
            "outcome_joined": True,
            "goedgevonden": True,
            "handen": False,
            "in handen": False,
            "advies": False,
            "gedelibereert_start": False,
            "n_words": 30,
            "text_joined": True,
        },
        {
            "id": "session-3835-num-1-resolution-3",
            "year": 1780,
            "role": "gold",
            "pred": True,
            "score": 4.5,
            "session_date": "1780-01-04",
            "resolution_index": 3,
            "outcome_joined": True,
            "goedgevonden": False,
            "handen": False,
            "in handen": False,
            "advies": False,
            "gedelibereert_start": False,
            "n_words": 45,
            "text_joined": True,
        },
    ]
    frame = pd.DataFrame(rows)
    flag_cols = [c for c in ROUTING_FLAG_FOCUS if c in frame.columns]
    frame.attrs["flag_columns"] = flag_cols
    frame.attrs["n_missed"] = 1

    referred_flag = frame["handen"].fillna(False) | frame["in handen"].fillna(False)
    granted_flag = frame["goedgevonden"].fillna(False)
    frame["requeste_subtype"] = pd.NA
    frame.loc[referred_flag, "requeste_subtype"] = SUBTYPE_REFERRED
    frame.loc[~referred_flag & granted_flag, "requeste_subtype"] = SUBTYPE_GRANTED
    frame.loc[~referred_flag & ~granted_flag, "requeste_subtype"] = SUBTYPE_UNCLEAR
    return frame
