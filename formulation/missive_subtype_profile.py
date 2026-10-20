"""STEPT1f: missive subtype characterisation under ontfangen+.

Provisional cuts (not accepted formula types):

- ``info_receipt`` — Track L labelled missive_receipt (``is_l1``)
- ``decisionful_residual`` — ontfangen+ \\ L1 (``residual_not_l1``)

Primary tables are restricted to ES ``proposition_type == missive``;
non-missive ontfangen+ is leakage only. Reuses STEPT1e partition scores
(no ES remget). Flags describe subtype shape — they are not a typology sieve.
"""

from __future__ import annotations

from typing import Any

import pandas as pd

from data_io import load
from formulation.boundary.tfidf_windows import POC_YEAR
from formulation.formula_type_composition_graph import COMPOSITION_ROOT
from formulation.ontfangen_partition import (
    FLAG_FOCUS,
    _flag_rates,
    _type_mix,
    fixture_partition_frame,
)
from formulation.typology_sample import (
    _resolution_index_from_id,
    _top_flag_combinations,
    join_outcome_flags,
)

DEFAULT_YEAR = POC_YEAR

SUBTYPE_INFO = "info_receipt"
SUBTYPE_DECISIONFUL = "decisionful_residual"
SUBTYPES = (SUBTYPE_INFO, SUBTYPE_DECISIONFUL)

# Decision/null surfaces called out in STEPT1e NOTES (plus openings).
CHAR_FLAG_FOCUS = tuple(
    dict.fromkeys(
        (
            *FLAG_FOCUS,
            "gedelibereert_start",
        )
    )
)

__all__ = (
    "CHAR_FLAG_FOCUS",
    "DEFAULT_YEAR",
    "SUBTYPE_DECISIONFUL",
    "SUBTYPE_INFO",
    "SUBTYPES",
    "attach_word_counts",
    "build_characterisation_frame",
    "fixture_characterisation_frame",
    "load_partition_scores",
    "summarize_missive_subtypes",
)


def load_partition_scores(*, year: int = DEFAULT_YEAR) -> pd.DataFrame:
    """Load STEPT1e per-id scores for one year."""
    raw = load("ontfangen_partition_scores")
    frame = pd.DataFrame(raw) if not isinstance(raw, pd.DataFrame) else raw
    frame = frame.copy()
    frame["id"] = frame["id"].astype(str)
    frame["year"] = pd.to_numeric(frame["year"], errors="coerce")
    slice_ = frame.loc[frame["year"] == int(year)].copy()
    if slice_.empty:
        raise ValueError(
            f"No ontfangen_partition_scores rows for year={year}"
        )
    for col in (
        "ontfangen_present",
        "is_l1",
        "is_r1",
        "is_advies_gold",
        "residual_not_l1",
        "es_joined",
    ):
        if col in slice_.columns:
            slice_[col] = slice_[col].astype(bool)
    if "resolution_index" not in slice_.columns:
        slice_["resolution_index"] = slice_["id"].map(_resolution_index_from_id)
    return slice_


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
    # pandas merge drops ``.attrs`` — restore flag column list for summarize.
    out.attrs["flag_columns"] = flag_cols
    return out


def build_characterisation_frame(
    scores: pd.DataFrame,
    *,
    join_flags: bool = True,
    join_text_length: bool = True,
) -> pd.DataFrame:
    """Ontfangen+ rows with subtype label, optional flags + word counts."""
    frame = scores.loc[scores["ontfangen_present"]].copy()
    if frame.empty:
        raise ValueError("No ontfangen+ rows in partition scores")

    frame["missive_subtype"] = pd.NA
    frame.loc[frame["is_l1"], "missive_subtype"] = SUBTYPE_INFO
    frame.loc[frame["residual_not_l1"], "missive_subtype"] = SUBTYPE_DECISIONFUL
    # Safety: L1 and residual are mutually exclusive under STEPT1e definition.
    both = frame["is_l1"] & frame["residual_not_l1"]
    if both.any():
        raise ValueError(
            f"is_l1 and residual_not_l1 overlap on {int(both.sum())} rows"
        )

    if join_flags:
        if "session_date" not in frame.columns:
            frame["session_date"] = pd.NA
        if "resolution_index" not in frame.columns:
            frame["resolution_index"] = frame["id"].map(_resolution_index_from_id)
        # Drop STEPT1e outcome_joined so join_outcome_flags can re-set it.
        if "outcome_joined" in frame.columns:
            frame = frame.drop(columns=["outcome_joined"])
        frame = join_outcome_flags(frame)
    else:
        frame["outcome_joined"] = False
        frame.attrs["flag_columns"] = []

    if join_text_length:
        frame = attach_word_counts(frame)
    else:
        frame["n_words"] = pd.NA
        frame["text_joined"] = False

    # Ensure attrs survive any intermediate copies.
    if "flag_columns" not in frame.attrs:
        frame.attrs["flag_columns"] = []

    return frame


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
    n_missive: int,
    flag_cols: list[str],
) -> dict[str, Any]:
    n = len(group)
    return {
        "missive_subtype": subtype,
        "n": n,
        "frac_of_missive_ontfangen_plus": n / n_missive if n_missive else None,
        "length": _length_summary(group),
        "es_type_mix": _type_mix(group),
        "flags": {
            "n_outcome_joined": int(group["outcome_joined"].sum()) if n else 0,
            "flag_rates": _flag_rates(group, flag_cols, focus=CHAR_FLAG_FOCUS),
            "top_flag_combinations": _top_flag_combinations(group, flag_cols),
        },
        "known": {
            "n_r1": int(group["is_r1"].sum()) if n else 0,
            "n_advies_gold": int(group["is_advies_gold"].sum()) if n else 0,
        },
    }


def _contrast(
    info: dict[str, Any],
    decisionful: dict[str, Any],
) -> dict[str, Any]:
    def _len(rec: dict[str, Any]) -> float | None:
        return (rec.get("length") or {}).get("n_words_median")

    def _rate(rec: dict[str, Any], flag: str) -> float | None:
        rates = ((rec.get("flags") or {}).get("flag_rates") or {})
        return rates.get(flag)

    med_i, med_d = _len(info), _len(decisionful)
    return {
        "n_words_median_info": med_i,
        "n_words_median_decisionful": med_d,
        "n_words_median_delta_decisionful_minus_info": (
            (med_d - med_i) if med_i is not None and med_d is not None else None
        ),
        "flag_rate_deltas_decisionful_minus_info": {
            flag: (
                (_rate(decisionful, flag) - _rate(info, flag))
                if _rate(decisionful, flag) is not None
                and _rate(info, flag) is not None
                else None
            )
            for flag in (
                "geen_resolutie",
                "advertentie",
                "goedgevonden",
                "gedelibereert_start",
            )
        },
        "n_r1_info": (info.get("known") or {}).get("n_r1"),
        "n_r1_decisionful": (decisionful.get("known") or {}).get("n_r1"),
    }


def summarize_missive_subtypes(
    frame: pd.DataFrame,
    *,
    year: int,
) -> dict[str, Any]:
    """Provenanced metrics for NOTES + save."""
    flag_cols: list[str] = list(frame.attrs.get("flag_columns") or [])
    n_plus = len(frame)
    missive = frame[frame["proposition_type"].astype(str) == "missive"]
    n_missive = len(missive)
    leakage = frame[frame["proposition_type"].astype(str) != "missive"]

    by_subtype: dict[str, dict[str, Any]] = {}
    for subtype in SUBTYPES:
        group = missive[missive["missive_subtype"] == subtype]
        by_subtype[subtype] = _subtype_record(
            group,
            subtype=subtype,
            n_missive=n_missive,
            flag_cols=flag_cols,
        )

    info = by_subtype[SUBTYPE_INFO]
    decisionful = by_subtype[SUBTYPE_DECISIONFUL]

    return {
        "step": "STEPT1f",
        "method": "missive_subtype_characterisation",
        "year": int(year),
        "composition_root": COMPOSITION_ROOT,
        "universe": "ontfangen_plus",
        "kind_filter": "proposition_type == missive",
        "n_ontfangen_plus": n_plus,
        "n_missive": n_missive,
        "n_non_missive_leakage": len(leakage),
        "leakage_es_type_mix": _type_mix(leakage),
        "frac_missive_of_plus": n_missive / n_plus if n_plus else None,
        "outcome_join_coverage": (
            float(frame["outcome_joined"].mean()) if n_plus else 0.0
        ),
        "text_join_coverage": (
            float(frame["text_joined"].mean())
            if n_plus and "text_joined" in frame.columns
            else 0.0
        ),
        "subtypes": [by_subtype[s] for s in SUBTYPES],
        "contrast": _contrast(info, decisionful),
        "notes": (
            "Provisional missive subtype characterisation under ontfangen+. "
            "info_receipt / decisionful_residual are characteristics cuts, "
            "not accepted formula types. Flags are boilerplate surfaces, "
            "not archival outcomes. Not STEPT1e1 (no further flag bucketing)."
        ),
    }


def fixture_characterisation_frame() -> pd.DataFrame:
    """Tiny in-memory frame (no parquet / no formula_documents)."""
    base = fixture_partition_frame()
    frame = base.loc[base["ontfangen_present"]].copy()
    frame["missive_subtype"] = pd.NA
    frame.loc[frame["is_l1"], "missive_subtype"] = SUBTYPE_INFO
    frame.loc[frame["residual_not_l1"], "missive_subtype"] = SUBTYPE_DECISIONFUL
    # Synthetic lengths: info short, decisionful longer.
    frame["n_words"] = [40, 180, 90]
    frame["text_joined"] = True
    # Keep FLAG_FOCUS boolean cols already on fixture; add gedelibereert_start.
    if "gedelibereert_start" not in frame.columns:
        frame["gedelibereert_start"] = [False, True, False]
        frame["gedelibereert_start"] = frame["gedelibereert_start"].astype("boolean")
    flag_cols = [c for c in CHAR_FLAG_FOCUS if c in frame.columns]
    frame.attrs["flag_columns"] = flag_cols
    return frame
