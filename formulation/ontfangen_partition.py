"""STEPT1e: ontfangen± partition probe (ES types + flags + known sets).

Universe = presence-score ids for one year. Partition = ``ontfangen_start``
present at its operating cut. Ontfangen remains a provisional composition
root/partition — not an accepted formula type.
"""

from __future__ import annotations

from collections import Counter
from typing import Any

import pandas as pd

from data_io import load
from formulation.boundary.tfidf_windows import POC_YEAR
from formulation.formula_type_composition_graph import COMPOSITION_ROOT
from formulation.republic_es import RepublicEsClient
from formulation.typology_sample import (
    NONE_TYPE_KEY,
    _resolution_index_from_id,
    _top_flag_combinations,
    join_outcome_flags,
)

DEFAULT_YEAR = POC_YEAR

# Exploratory flag names called out in STEPT1e0 gap list (others still in combos).
FLAG_FOCUS = (
    "geen_resolutie",
    "advertentie",
    "goedgevonden",
    "rapport_start",
    "ontfangen_start",
    "advies",
    "requeste_start",
    "handen",
    "in handen",
)

ES_SOURCE = [
    "id",
    "metadata.id",
    "metadata.proposition_type",
    "metadata.session_date",
    "metadata.session_year",
]

__all__ = (
    "COMPOSITION_ROOT",
    "DEFAULT_YEAR",
    "FLAG_FOCUS",
    "build_partition_frame",
    "fetch_es_metadata",
    "fixture_partition_frame",
    "load_known_id_sets",
    "load_presence_universe",
    "summarize_partition",
)


def load_presence_universe(
    *,
    year: int = DEFAULT_YEAR,
    root_id: str = COMPOSITION_ROOT,
) -> pd.DataFrame:
    """One row per resolution id in the presence-score year universe."""
    scores = pd.DataFrame(load("formula_type_presence_scores"))
    scores["id"] = scores["id"].astype(str)
    scores["year"] = pd.to_numeric(scores["year"], errors="coerce")
    slice_ = scores.loc[scores["year"] == int(year)].copy()
    if slice_.empty:
        raise ValueError(
            f"No formula_type_presence_scores rows for year={year}"
        )
    root = slice_.loc[slice_["formula_type_id"] == root_id]
    if root.empty:
        raise ValueError(
            f"No {root_id!r} rows in presence scores for year={year}"
        )
    present = (
        root.set_index("id")["present"]
        .astype("boolean")
        .rename("ontfangen_present")
    )
    ids = pd.Index(sorted(slice_["id"].unique()), name="id")
    out = present.reindex(ids).fillna(False).astype(bool).reset_index()
    out["year"] = int(year)
    out["resolution_index"] = out["id"].map(_resolution_index_from_id)
    return out


def load_known_id_sets(*, year: int = DEFAULT_YEAR) -> dict[str, set[str]]:
    """Cheap id sets for tagging (same grain as STEPT1e0)."""
    selected = load("aanstelling_selected")
    selected["id"] = selected["id"].astype(str)
    selected["year"] = pd.to_numeric(selected["year"], errors="coerce")
    r1 = set(selected.loc[selected["year"] == int(year), "id"])

    labelled = load("missive_receipt_labelled")
    labelled["id"] = labelled["id"].astype(str)
    labelled["year"] = pd.to_numeric(labelled["year"], errors="coerce")
    l1 = set(
        labelled.loc[
            (labelled["year"] == int(year))
            & (labelled["label"] == "missive_receipt"),
            "id",
        ]
    )

    advies_raw = load("advies_es_gold")
    advies = pd.DataFrame(advies_raw) if not isinstance(advies_raw, pd.DataFrame) else advies_raw
    advies["id"] = advies["id"].astype(str)
    advies["year"] = pd.to_numeric(advies["year"], errors="coerce")
    advies_ids = set(advies.loc[advies["year"] == int(year), "id"])

    return {
        "aanstelling_selected": r1,
        "missive_receipt": l1,
        "advies_es_gold": advies_ids,
    }


def fetch_es_metadata(
    ids: list[str],
    *,
    client: RepublicEsClient | None = None,
) -> pd.DataFrame:
    """Lean ES ``mget``: proposition_type + session_date per id."""
    client = client or RepublicEsClient()
    sources = client.mget(
        client.config.resolutions_index,
        ids,
        ES_SOURCE,
    )
    rows: list[dict[str, Any]] = []
    for rid, src in sources.items():
        meta = src.get("metadata") or {}
        ptype = meta.get("proposition_type")
        if ptype is None or (isinstance(ptype, float) and pd.isna(ptype)):
            ptype = NONE_TYPE_KEY
        elif not str(ptype).strip():
            ptype = NONE_TYPE_KEY
        else:
            ptype = str(ptype)
        rows.append(
            {
                "id": str(rid),
                "proposition_type": ptype,
                "session_date": meta.get("session_date"),
                "es_joined": True,
            }
        )
    frame = pd.DataFrame(rows)
    if frame.empty:
        return pd.DataFrame(
            columns=["id", "proposition_type", "session_date", "es_joined"]
        )
    return frame


def build_partition_frame(
    universe: pd.DataFrame,
    *,
    known: dict[str, set[str]] | None = None,
    es_meta: pd.DataFrame | None = None,
    join_flags: bool = True,
) -> pd.DataFrame:
    """Attach ES types, known-set tags, and optional formula_documents flags."""
    frame = universe.copy()
    frame["id"] = frame["id"].astype(str)
    known = known or {}
    frame["is_r1"] = frame["id"].isin(known.get("aanstelling_selected", set()))
    frame["is_l1"] = frame["id"].isin(known.get("missive_receipt", set()))
    frame["is_advies_gold"] = frame["id"].isin(known.get("advies_es_gold", set()))
    frame["residual_not_l1"] = frame["ontfangen_present"] & ~frame["is_l1"]

    if es_meta is None:
        frame["proposition_type"] = pd.NA
        frame["session_date"] = pd.NA
        frame["es_joined"] = False
    else:
        meta = es_meta.copy()
        meta["id"] = meta["id"].astype(str)
        frame = frame.merge(
            meta[["id", "proposition_type", "session_date", "es_joined"]],
            on="id",
            how="left",
        )
        frame["es_joined"] = frame["es_joined"].fillna(False).astype(bool)
        missing = frame["proposition_type"].isna()
        frame.loc[missing, "proposition_type"] = NONE_TYPE_KEY

    if join_flags:
        if "session_date" not in frame.columns:
            frame["session_date"] = pd.NA
        if "resolution_index" not in frame.columns:
            frame["resolution_index"] = frame["id"].map(_resolution_index_from_id)
        frame = join_outcome_flags(frame)
    else:
        frame["outcome_joined"] = False
        frame.attrs["flag_columns"] = []

    return frame


def _type_mix(group: pd.DataFrame) -> list[dict[str, Any]]:
    n = len(group)
    if not n:
        return []
    counts = Counter(group["proposition_type"].astype(str))
    return [
        {"proposition_type": key, "n": int(val), "rate": val / n}
        for key, val in counts.most_common()
    ]


def _flag_rates(
    group: pd.DataFrame,
    flag_cols: list[str],
    *,
    focus: tuple[str, ...] = FLAG_FOCUS,
) -> dict[str, float | None]:
    known = group[group["outcome_joined"]] if "outcome_joined" in group else group
    if known.empty:
        return {col: None for col in focus if col in flag_cols}
    rates: dict[str, float | None] = {}
    for col in focus:
        if col not in flag_cols:
            continue
        series = known[col]
        rates[col] = None if series.isna().all() else float(series.mean())
    return rates


def _known_set_summary(
    frame: pd.DataFrame,
    known: dict[str, set[str]],
) -> list[dict[str, Any]]:
    plus = set(frame.loc[frame["ontfangen_present"], "id"].astype(str))
    minus = set(frame.loc[~frame["ontfangen_present"], "id"].astype(str))
    rows = []
    for name, ids in known.items():
        rows.append(
            {
                "known_set": name,
                "n_year": len(ids),
                "n_ontfangen_plus": len(ids & plus),
                "n_ontfangen_minus": len(ids & minus),
            }
        )
    return rows


def summarize_partition(
    frame: pd.DataFrame,
    *,
    year: int,
    known: dict[str, set[str]] | None = None,
) -> dict[str, Any]:
    """Metrics record for provenanced write + NOTES."""
    known = known or {}
    flag_cols: list[str] = list(frame.attrs.get("flag_columns") or [])
    n = len(frame)
    plus = frame[frame["ontfangen_present"]]
    minus = frame[~frame["ontfangen_present"]]
    residual = frame[frame["residual_not_l1"]]
    n_plus = len(plus)
    n_minus = len(minus)

    missive_plus = int((plus["proposition_type"] == "missive").sum())
    missive_minus = int((minus["proposition_type"] == "missive").sum())
    not_missive_plus = n_plus - missive_plus
    not_missive_minus = n_minus - missive_minus

    return {
        "step": "STEPT1e",
        "method": "ontfangen_partition_probe",
        "year": int(year),
        "composition_root": COMPOSITION_ROOT,
        "n_resolutions": n,
        "n_ontfangen_plus": n_plus,
        "n_ontfangen_minus": n_minus,
        "hit_rate": n_plus / n if n else 0.0,
        "es_join_coverage": float(frame["es_joined"].mean()) if n else 0.0,
        "outcome_join_coverage": (
            float(frame["outcome_joined"].mean()) if n else 0.0
        ),
        "es_type_mix_plus": _type_mix(plus),
        "es_type_mix_minus": _type_mix(minus),
        "missive_contingency": {
            "missive_and_plus": missive_plus,
            "missive_and_minus": missive_minus,
            "not_missive_and_plus": not_missive_plus,
            "not_missive_and_minus": not_missive_minus,
            "p_missive_given_plus": missive_plus / n_plus if n_plus else None,
            "p_missive_given_minus": (
                missive_minus / n_minus if n_minus else None
            ),
            "p_plus_given_missive": (
                missive_plus / (missive_plus + missive_minus)
                if (missive_plus + missive_minus)
                else None
            ),
        },
        "known_sets": _known_set_summary(frame, known),
        "flags_plus": {
            "n_outcome_joined": int(plus["outcome_joined"].sum())
            if n_plus
            else 0,
            "flag_rates": _flag_rates(plus, flag_cols),
            "top_flag_combinations": _top_flag_combinations(plus, flag_cols),
        },
        "flags_minus": {
            "n_outcome_joined": int(minus["outcome_joined"].sum())
            if n_minus
            else 0,
            "flag_rates": _flag_rates(minus, flag_cols),
            "top_flag_combinations": _top_flag_combinations(minus, flag_cols),
        },
        "residual_not_l1": {
            "n": len(residual),
            "frac_of_plus": len(residual) / n_plus if n_plus else None,
            "es_type_mix": _type_mix(residual),
            "flag_rates": _flag_rates(residual, flag_cols),
            "top_flag_combinations": _top_flag_combinations(
                residual, flag_cols
            ),
            "n_r1": int(residual["is_r1"].sum()) if len(residual) else 0,
            "n_advies_gold": int(residual["is_advies_gold"].sum())
            if len(residual)
            else 0,
        },
        "notes": (
            "Exploratory partition probe; ontfangen_start remains provisional "
            "root/partition, not an accepted formula type. Flags are "
            "boilerplate markers, not archival outcomes."
        ),
    }


def fixture_partition_frame() -> pd.DataFrame:
    """Tiny in-memory frame for unit smoke (no ES / no parquet)."""
    rows = [
        {
            "id": "session-3835-num-1-resolution-1",
            "year": 1780,
            "ontfangen_present": True,
            "proposition_type": "missive",
            "session_date": "1780-01-02",
            "resolution_index": 1,
            "is_r1": False,
            "is_l1": True,
            "is_advies_gold": False,
            "residual_not_l1": False,
            "es_joined": True,
            "geen_resolutie": True,
            "advertentie": True,
            "goedgevonden": False,
            "rapport_start": False,
            "ontfangen_start": True,
            "advies": False,
            "requeste_start": False,
            "handen": False,
            "in handen": False,
            "outcome_joined": True,
        },
        {
            "id": "session-3835-num-1-resolution-2",
            "year": 1780,
            "ontfangen_present": True,
            "proposition_type": "missive",
            "session_date": "1780-01-02",
            "resolution_index": 2,
            "is_r1": True,
            "is_l1": False,
            "is_advies_gold": False,
            "residual_not_l1": True,
            "es_joined": True,
            "geen_resolutie": False,
            "advertentie": False,
            "goedgevonden": True,
            "rapport_start": False,
            "ontfangen_start": True,
            "advies": False,
            "requeste_start": False,
            "handen": False,
            "in handen": False,
            "outcome_joined": True,
        },
        {
            "id": "session-3835-num-1-resolution-3",
            "year": 1780,
            "ontfangen_present": False,
            "proposition_type": "advies",
            "session_date": "1780-01-03",
            "resolution_index": 3,
            "is_r1": False,
            "is_l1": False,
            "is_advies_gold": True,
            "residual_not_l1": False,
            "es_joined": True,
            "geen_resolutie": False,
            "advertentie": False,
            "goedgevonden": False,
            "rapport_start": False,
            "ontfangen_start": False,
            "advies": True,
            "requeste_start": False,
            "handen": False,
            "in handen": False,
            "outcome_joined": True,
        },
        {
            "id": "session-3835-num-1-resolution-4",
            "year": 1780,
            "ontfangen_present": True,
            "proposition_type": "missive",
            "session_date": "1780-01-04",
            "resolution_index": 4,
            "is_r1": False,
            "is_l1": False,
            "is_advies_gold": False,
            "residual_not_l1": True,
            "es_joined": True,
            "geen_resolutie": False,
            "advertentie": True,
            "goedgevonden": False,
            "rapport_start": True,
            "ontfangen_start": True,
            "advies": False,
            "requeste_start": False,
            "handen": False,
            "in handen": False,
            "outcome_joined": True,
        },
    ]
    frame = pd.DataFrame(rows)
    flag_cols = [
        c
        for c in FLAG_FOCUS
        if c in frame.columns
    ]
    frame[flag_cols] = frame[flag_cols].astype("boolean")
    frame.attrs["flag_columns"] = flag_cols
    return frame
