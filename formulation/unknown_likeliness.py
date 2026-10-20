"""STEPT1h: unknown-likeliness scoring (accepted cover set only).

Per-id: how little the cover set explains a resolution. High unknown =
triage for later content characterisation — not a residual subtype id.
"""

from __future__ import annotations

from typing import Any

import pandas as pd

from data_io import load
from formulation.advies_formula_type import FORMULA_TYPE_ID as ADVIES_ID
from formulation.appointment_formula_type import FORMULA_TYPE_ID as APPOINTMENT_ID
from formulation.boundary.tfidf_windows import POC_YEAR
from formulation.missive_subtype_profile import attach_word_counts
from formulation.ontfangen_partition import (
    load_known_id_sets,
    load_presence_universe,
)
from formulation.typology_sample import _resolution_index_from_id

DEFAULT_YEAR = POC_YEAR
DEFAULT_SAMPLE_SEED = 20261020
DEFAULT_SAMPLE_PER_STRATUM = 5

# Accepted evidence only — not ontfangen-alone, not flag rates, not ES type.
COVER_AXES = (
    "cover_l1",
    "cover_r1",
    "cover_appointment",
    "cover_advies",
)

__all__ = (
    "COVER_AXES",
    "DEFAULT_SAMPLE_PER_STRATUM",
    "DEFAULT_SAMPLE_SEED",
    "DEFAULT_YEAR",
    "attach_cover_axes",
    "build_unknown_frame",
    "draw_high_unknown_sample",
    "fixture_unknown_frame",
    "load_unknown_universe",
    "score_unknown",
    "summarize_unknown_likeliness",
)


def load_unknown_universe(*, year: int = DEFAULT_YEAR) -> pd.DataFrame:
    """Presence-score year slice (one row per resolution id)."""
    return load_presence_universe(year=year)


def attach_cover_axes(
    frame: pd.DataFrame,
    *,
    year: int = DEFAULT_YEAR,
    known: dict[str, set[str]] | None = None,
    join_presence: bool = True,
) -> pd.DataFrame:
    """Tag accepted cover flags (L1, R1, appointment, advies)."""
    out = frame.copy()
    out["id"] = out["id"].astype(str)
    known = known if known is not None else load_known_id_sets(year=year)

    out["cover_l1"] = out["id"].isin(known.get("missive_receipt", set()))
    out["cover_r1"] = out["id"].isin(known.get("aanstelling_selected", set()))

    if join_presence:
        presence = pd.DataFrame(load("formula_type_presence_scores"))
        presence["id"] = presence["id"].astype(str)
        presence["year"] = pd.to_numeric(presence["year"], errors="coerce")
        slice_ = presence.loc[presence["year"] == int(year)].copy()
        slice_["present"] = slice_["present"].astype(bool)

        appt_hits = set(
            slice_.loc[
                (slice_["formula_type_id"] == APPOINTMENT_ID) & slice_["present"],
                "id",
            ].astype(str)
        )
        advies_hits = set(
            slice_.loc[
                (slice_["formula_type_id"] == ADVIES_ID) & slice_["present"],
                "id",
            ].astype(str)
        )
        out["cover_appointment"] = out["id"].isin(appt_hits)
        out["cover_advies"] = out["id"].isin(advies_hits) | out["id"].isin(
            known.get("advies_es_gold", set())
        )
    else:
        out["cover_appointment"] = False
        out["cover_advies"] = out["id"].isin(known.get("advies_es_gold", set()))

    return out


def score_unknown(frame: pd.DataFrame) -> pd.DataFrame:
    """Add n_cover_hits + unknown_score in [0, 1] (1 = unexplained)."""
    out = frame.copy()
    missing = [c for c in COVER_AXES if c not in out.columns]
    if missing:
        raise ValueError(f"Missing cover axes: {missing}")
    hits = out[list(COVER_AXES)].astype(bool)
    out["n_cover_hits"] = hits.sum(axis=1).astype(int)
    n_axes = float(len(COVER_AXES))
    out["unknown_score"] = 1.0 - (out["n_cover_hits"].astype(float) / n_axes)
    out["high_unknown"] = out["n_cover_hits"] == 0
    return out


def build_unknown_frame(
    universe: pd.DataFrame,
    *,
    year: int = DEFAULT_YEAR,
    known: dict[str, set[str]] | None = None,
    join_presence: bool = True,
    join_text_length: bool = True,
) -> pd.DataFrame:
    """Universe + cover + score (+ optional word counts for sample strata)."""
    frame = attach_cover_axes(
        universe,
        year=year,
        known=known,
        join_presence=join_presence,
    )
    frame = score_unknown(frame)
    if "resolution_index" not in frame.columns:
        frame["resolution_index"] = frame["id"].map(_resolution_index_from_id)
    if join_text_length:
        frame = attach_word_counts(frame)
    else:
        frame["n_words"] = pd.NA
        frame["text_joined"] = False
    return frame


def _length_tercile(series: pd.Series) -> pd.Series:
    valid = series.dropna()
    if valid.empty:
        return pd.Series(["unknown"] * len(series), index=series.index)
    q1, q2 = valid.quantile([1 / 3, 2 / 3])
    out = pd.Series(["mid"] * len(series), index=series.index, dtype=object)
    out.loc[series.isna()] = "unknown"
    out.loc[series <= q1] = "short"
    out.loc[series > q2] = "long"
    mid_mask = series.notna() & (series > q1) & (series <= q2)
    out.loc[mid_mask] = "mid"
    return out


def draw_high_unknown_sample(
    frame: pd.DataFrame,
    *,
    per_stratum: int = DEFAULT_SAMPLE_PER_STRATUM,
    seed: int = DEFAULT_SAMPLE_SEED,
) -> pd.DataFrame:
    """Length-tercile sample of high-unknown rows (truncated text)."""
    high = frame.loc[frame["high_unknown"]].copy()
    if high.empty:
        return high.head(0)

    if "n_words" not in high.columns:
        high["n_words"] = pd.NA
    high["length_stratum"] = _length_tercile(high["n_words"])

    ids = set(high["id"].astype(str))
    flat = load("resolutions_flat")
    sub = flat.loc[flat["id"].astype(str).isin(ids), ["id", "resolutions_text"]].copy()
    sub["id"] = sub["id"].astype(str)
    high = high.merge(sub, on="id", how="left")

    parts: list[pd.DataFrame] = []
    rng = seed
    for length_s, group in high.groupby("length_stratum", sort=True):
        if length_s == "unknown":
            continue
        take = min(int(per_stratum), len(group))
        if take <= 0:
            continue
        sampled = group.sample(n=take, random_state=rng).copy()
        rng += 1
        sampled["sample_stratum"] = str(length_s)
        parts.append(sampled)

    if not parts:
        return high.head(0)

    out = pd.concat(parts, ignore_index=True)
    keep = [
        "id",
        "year",
        "n_words",
        "length_stratum",
        "n_cover_hits",
        "unknown_score",
        "sample_stratum",
        "resolutions_text",
        *COVER_AXES,
    ]
    cols = [c for c in keep if c in out.columns]
    result = out[cols].copy()
    if "resolutions_text" in result.columns:
        result["resolutions_text"] = (
            result["resolutions_text"]
            .fillna("")
            .astype(str)
            .str.slice(0, 1200)
        )
    return result


def summarize_unknown_likeliness(
    frame: pd.DataFrame,
    *,
    year: int,
) -> dict[str, Any]:
    """Provenanced metrics: band size + cover axis hits (no subtype ids)."""
    n = len(frame)
    high = frame["high_unknown"] if "high_unknown" in frame.columns else pd.Series(
        [False] * n
    )
    n_high = int(high.sum()) if n else 0

    cover: dict[str, Any] = {}
    for axis in COVER_AXES:
        if axis in frame.columns and n:
            hits = int(frame[axis].astype(bool).sum())
            cover[axis] = {"n": hits, "frac": hits / n}
        else:
            cover[axis] = {"n": 0, "frac": None}

    # Score mass at each distinct level (0, 0.25, 0.5, 0.75, 1.0 with 4 axes).
    hist: dict[str, int] = {}
    if n and "unknown_score" in frame.columns:
        for score, cnt in frame["unknown_score"].value_counts().sort_index().items():
            hist[f"{float(score):.2f}"] = int(cnt)

    return {
        "step": "STEPT1h",
        "method": "unknown_likeliness",
        "year": int(year),
        "universe": "presence_year_slice",
        "cover_axes": list(COVER_AXES),
        "constraint": "unknown_first_accepted_cover_only",
        "n_universe": n,
        "n_high_unknown": n_high,
        "frac_high_unknown": (n_high / n) if n else None,
        "cover": cover,
        "unknown_score_hist": hist,
        "notes": (
            "Unknown-likeliness under accepted cover (L1, R1, appointment, "
            "advies). High-unknown band is triage for characterisation — not "
            "a subtype id. Not ontfangen-alone / flag rates / ES type as cover."
        ),
    }


def fixture_unknown_frame() -> pd.DataFrame:
    """Tiny in-memory frame (no parquet): mixed cover + one high-unknown."""
    rows = [
        # L1 covered
        {
            "id": "session-0-num-1-resolution-1",
            "year": 1780,
            "ontfangen_present": True,
            "cover_l1": True,
            "cover_r1": False,
            "cover_appointment": False,
            "cover_advies": False,
            "n_words": 40,
        },
        # R1 + appointment
        {
            "id": "session-0-num-1-resolution-2",
            "year": 1780,
            "ontfangen_present": True,
            "cover_l1": False,
            "cover_r1": True,
            "cover_appointment": True,
            "cover_advies": False,
            "n_words": 120,
        },
        # Advies gold/present
        {
            "id": "session-0-num-1-resolution-3",
            "year": 1780,
            "ontfangen_present": False,
            "cover_l1": False,
            "cover_r1": False,
            "cover_appointment": False,
            "cover_advies": True,
            "n_words": 80,
        },
        # High unknown
        {
            "id": "session-0-num-1-resolution-4",
            "year": 1780,
            "ontfangen_present": True,
            "cover_l1": False,
            "cover_r1": False,
            "cover_appointment": False,
            "cover_advies": False,
            "n_words": 200,
        },
        # Another high unknown (short)
        {
            "id": "session-0-num-1-resolution-5",
            "year": 1780,
            "ontfangen_present": False,
            "cover_l1": False,
            "cover_r1": False,
            "cover_appointment": False,
            "cover_advies": False,
            "n_words": 25,
        },
    ]
    frame = pd.DataFrame(rows)
    frame["text_joined"] = True
    frame["resolution_index"] = frame["id"].map(_resolution_index_from_id)
    return score_unknown(frame)
