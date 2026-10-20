"""STEPT1j: characterise the empty composition band (+ optional fp_cut sweep).

Universe = STEPT1i ``motif_class == empty`` (no known formula hits). Structural
profile (ES type mix, length, flag catalogue) + fingerprint cut sweep to see
whether a tighter ``fp_cut`` splits the one-mass cluster. Do **not** mint
blueprints from cluster n.
"""

from __future__ import annotations

from collections import Counter
from typing import Any, Sequence

import numpy as np
import pandas as pd

from data_io import load
from formulation.boundary.tfidf_windows import POC_YEAR
from formulation.content_fingerprint import (
    DEFAULT_FP_CUT,
    ContentFingerprint,
    greedy_clusters,
    nearest_neighbor_sims,
)
from formulation.missive_subtype_profile import (
    CHAR_FLAG_FOCUS,
    attach_word_counts,
    load_partition_scores,
)
from formulation.ontfangen_partition import FLAG_FOCUS, _flag_rates, _type_mix
from formulation.residual_structure import (
    _length_tercile,
    combo_catalogue,
)
from formulation.typology_sample import (
    NONE_TYPE_KEY,
    _resolution_index_from_id,
    join_outcome_flags,
)

DEFAULT_YEAR = POC_YEAR
DEFAULT_SAMPLE_SEED = 20261020
DEFAULT_SAMPLE_PER_STRATUM = 4
# Baseline (STEPT1i) then tighter candidates — fit similarity once, re-cluster.
DEFAULT_FP_CUTS: tuple[float, ...] = (0.15, 0.30, 0.45, 0.60)
# Operating cut for sample strata / per-id cluster labels (tighter than T1i).
DEFAULT_OPERATING_FP_CUT = 0.45

__all__ = (
    "CHAR_FLAG_FOCUS",
    "DEFAULT_FP_CUTS",
    "DEFAULT_OPERATING_FP_CUT",
    "DEFAULT_SAMPLE_PER_STRATUM",
    "DEFAULT_SAMPLE_SEED",
    "DEFAULT_YEAR",
    "build_empty_band_frame",
    "draw_empty_sample",
    "fixture_empty_frame",
    "load_empty_universe",
    "summarize_empty_band",
    "sweep_fingerprint_cuts",
)


def load_empty_universe(*, year: int = DEFAULT_YEAR) -> pd.DataFrame:
    """Ids with ``motif_class == empty`` from STEPT1i scores."""
    raw = load("composition_unknown_scores")
    frame = pd.DataFrame(raw) if not isinstance(raw, pd.DataFrame) else raw
    frame = frame.copy()
    frame["id"] = frame["id"].astype(str)
    frame["year"] = pd.to_numeric(frame["year"], errors="coerce")
    slice_ = frame.loc[frame["year"] == int(year)].copy()
    if slice_.empty:
        raise ValueError(f"No composition_unknown_scores for year={year}")
    empty = slice_.loc[slice_["motif_class"].astype(str) == "empty"].copy()
    if empty.empty:
        raise ValueError(f"No empty-motif rows for year={year}")
    return empty


def build_empty_band_frame(
    empty: pd.DataFrame,
    *,
    year: int = DEFAULT_YEAR,
    join_flags: bool = True,
    join_text_length: bool = True,
    join_partition: bool = True,
) -> pd.DataFrame:
    """Empty ids + ES/known (from STEPT1e scores) + flags + word counts."""
    frame = empty[["id", "year"]].copy()
    frame["id"] = frame["id"].astype(str)
    frame["year"] = pd.to_numeric(frame["year"], errors="coerce").fillna(int(year))
    frame["motif_class"] = "empty"

    if join_partition:
        part = load_partition_scores(year=year)
        keep = [
            c
            for c in (
                "id",
                "proposition_type",
                "session_date",
                "es_joined",
                "ontfangen_present",
                "is_l1",
                "is_r1",
                "is_advies_gold",
                "residual_not_l1",
                "resolution_index",
            )
            if c in part.columns
        ]
        frame = frame.merge(part[keep], on="id", how="left")
        if "es_joined" in frame.columns:
            frame["es_joined"] = frame["es_joined"].fillna(False).astype(bool)
        if "ontfangen_present" in frame.columns:
            frame["ontfangen_present"] = (
                frame["ontfangen_present"].fillna(False).astype(bool)
            )
        for col in ("is_l1", "is_r1", "is_advies_gold", "residual_not_l1"):
            if col in frame.columns:
                frame[col] = frame[col].fillna(False).astype(bool)
        if "proposition_type" in frame.columns:
            missing = frame["proposition_type"].isna()
            frame.loc[missing, "proposition_type"] = NONE_TYPE_KEY
    else:
        frame["proposition_type"] = NONE_TYPE_KEY
        frame["session_date"] = pd.NA
        frame["es_joined"] = False
        frame["ontfangen_present"] = False
        frame["is_l1"] = False
        frame["is_r1"] = False
        frame["is_advies_gold"] = False
        frame["residual_not_l1"] = False

    if "resolution_index" not in frame.columns:
        frame["resolution_index"] = frame["id"].map(_resolution_index_from_id)

    flag_cols: list[str] = []
    if join_flags:
        if "outcome_joined" in frame.columns:
            frame = frame.drop(columns=["outcome_joined"])
        frame = join_outcome_flags(frame)
        flag_cols = list(frame.attrs.get("flag_columns") or [])
    else:
        frame["outcome_joined"] = False

    if join_text_length:
        frame = attach_word_counts(frame)
        flag_cols = flag_cols or list(frame.attrs.get("flag_columns") or [])
    else:
        frame["n_words"] = pd.NA
        frame["text_joined"] = False

    frame.attrs["flag_columns"] = flag_cols
    return frame


def _length_summary(series: pd.Series) -> dict[str, Any]:
    valid = pd.to_numeric(series, errors="coerce").dropna()
    if valid.empty:
        return {"n": 0, "median": None, "q1": None, "q3": None}
    q1, med, q3 = valid.quantile([0.25, 0.5, 0.75])
    return {
        "n": int(len(valid)),
        "median": float(med),
        "q1": float(q1),
        "q3": float(q3),
    }


def _fingerprint_cut_summary(
    labels: np.ndarray,
    nn: np.ndarray,
) -> dict[str, Any]:
    counts = Counter(labels.tolist())
    n = len(labels)
    largest = max(counts.values()) if counts else 0
    return {
        "n_scored": int(n),
        "n_clusters": int(len(counts)),
        "n_singletons": int(sum(1 for c in counts.values() if c == 1)),
        "share_largest_cluster": (largest / n) if n else None,
        "nn_sim_p50": float(np.median(nn)) if n else None,
        "nn_sim_p90": float(np.quantile(nn, 0.9)) if n else None,
        "cluster_sizes_top5": [
            {"cluster_id": int(cid), "n": int(sz)}
            for cid, sz in counts.most_common(5)
        ],
    }


def sweep_fingerprint_cuts(
    frame: pd.DataFrame,
    *,
    fp_cuts: Sequence[float] = DEFAULT_FP_CUTS,
    operating_cut: float = DEFAULT_OPERATING_FP_CUT,
    join_text: bool = True,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Fit fingerprint once; re-cluster at each cut. Attach operating labels."""
    out = frame.copy()
    out["fp_cluster_id"] = pd.NA
    out["nn_sim"] = pd.NA
    out["fp_scored"] = False

    meta: dict[str, Any] = {
        "fingerprint_ran": False,
        "fp_cuts": [float(c) for c in fp_cuts],
        "operating_fp_cut": float(operating_cut),
        "by_cut": [],
        "note": "skipped or too few texts",
    }
    if len(out) < 2:
        return out, meta

    if join_text or "resolutions_text" not in out.columns:
        ids = set(out["id"].astype(str))
        flat = load("resolutions_flat")
        sub = flat.loc[
            flat["id"].astype(str).isin(ids), ["id", "resolutions_text"]
        ].copy()
        sub["id"] = sub["id"].astype(str)
        sub["resolutions_text"] = sub["resolutions_text"].fillna("").astype(str)
        if "resolutions_text" in out.columns:
            out = out.drop(columns=["resolutions_text"])
        out = out.merge(sub, on="id", how="left")
        out["resolutions_text"] = out["resolutions_text"].fillna("")

    texts = out["resolutions_text"].fillna("").astype(str).tolist()
    if sum(1 for t in texts if t.strip()) < 2:
        return out, meta

    fp = ContentFingerprint().fit(texts)
    sim = fp.similarity_matrix(texts)
    nn = nearest_neighbor_sims(sim)

    by_cut: list[dict[str, Any]] = []
    operating_labels: np.ndarray | None = None
    for cut in fp_cuts:
        labels = greedy_clusters(sim, cut=float(cut))
        summary = _fingerprint_cut_summary(labels, nn)
        summary["fp_cut"] = float(cut)
        by_cut.append(summary)
        if abs(float(cut) - float(operating_cut)) < 1e-9:
            operating_labels = labels

    if operating_labels is None:
        operating_labels = greedy_clusters(sim, cut=float(operating_cut))
        by_cut.append(
            {
                **_fingerprint_cut_summary(operating_labels, nn),
                "fp_cut": float(operating_cut),
                "note": "operating_cut not in fp_cuts; computed extra",
            }
        )

    out["nn_sim"] = nn
    out["fp_cluster_id"] = operating_labels.astype(int)
    out["fp_scored"] = True
    # Preserve flag attrs through merges.
    flag_cols = list(frame.attrs.get("flag_columns") or [])
    out.attrs["flag_columns"] = flag_cols

    meta = {
        "fingerprint_ran": True,
        "fp_cuts": [float(c) for c in fp_cuts],
        "operating_fp_cut": float(operating_cut),
        "by_cut": by_cut,
        "baseline_fp_cut": float(DEFAULT_FP_CUT),
        "note": (
            "Similarity fit once on empty texts; clusters re-cut per fp_cut. "
            "operating_fp_cut labels written to scores. Clusters ≠ types."
        ),
    }
    return out, meta


def summarize_empty_band(
    frame: pd.DataFrame,
    *,
    year: int,
    fingerprint_meta: dict[str, Any] | None = None,
) -> dict[str, Any]:
    n = len(frame)
    flag_cols: list[str] = list(frame.attrs.get("flag_columns") or [])
    if not flag_cols:
        skip = {
            "es_joined",
            "outcome_joined",
            "text_joined",
            "ontfangen_present",
            "is_l1",
            "is_r1",
            "is_advies_gold",
            "residual_not_l1",
            "fp_scored",
            "composition_unknown",
        }
        flag_cols = [
            c
            for c in frame.columns
            if str(frame[c].dtype) == "boolean" and c not in skip
        ]

    type_mix = _type_mix(frame) if "proposition_type" in frame.columns else []
    length = _length_summary(frame["n_words"]) if "n_words" in frame.columns else {}

    # Per-type length medians (top types only — characteristics, not subtypes).
    by_type: list[dict[str, Any]] = []
    if "proposition_type" in frame.columns and "n_words" in frame.columns:
        for ptype, grp in frame.groupby(
            frame["proposition_type"].astype(str), sort=False
        ):
            if len(grp) < 5:
                continue
            by_type.append(
                {
                    "proposition_type": str(ptype),
                    "n": int(len(grp)),
                    "frac": len(grp) / n if n else None,
                    "length": _length_summary(grp["n_words"]),
                    "flag_rates_focus": _flag_rates(
                        grp, flag_cols, focus=tuple(CHAR_FLAG_FOCUS)
                    ),
                }
            )
        by_type.sort(key=lambda r: -r["n"])

    catalogue = combo_catalogue(frame, flag_cols) if flag_cols else {
        "n_unique": 0,
        "top": [],
        "note": "no flags",
    }

    known = {
        "n_l1": int(frame["is_l1"].sum()) if "is_l1" in frame.columns else 0,
        "n_r1": int(frame["is_r1"].sum()) if "is_r1" in frame.columns else 0,
        "n_advies_gold": int(frame["is_advies_gold"].sum())
        if "is_advies_gold" in frame.columns
        else 0,
        "n_ontfangen_present": int(frame["ontfangen_present"].sum())
        if "ontfangen_present" in frame.columns
        else 0,
        "note": (
            "Empty = no presence hits at operating cuts; ontfangen_present "
            "should be ~0 (sanity). Known-set hits are cover leakage."
        ),
    }

    return {
        "step": "STEPT1j",
        "method": "empty_band_characterisation",
        "year": int(year),
        "universe": "composition_unknown motif_class=empty",
        "constraint": "characterise_do_not_mint_blueprints",
        "n_empty": n,
        "type_mix": type_mix,
        "length": length,
        "by_proposition_type": by_type[:12],
        "flag_rates_focus": _flag_rates(
            frame, flag_cols, focus=tuple(dict.fromkeys((*FLAG_FOCUS, *CHAR_FLAG_FOCUS)))
        ),
        "combo_catalogue": catalogue,
        "known_set_leakage": known,
        "fingerprint_sweep": fingerprint_meta or {"fingerprint_ran": False},
        "notes": (
            "Empty band = unexplained composition (no known formula hits). "
            "Read sample shapes; use fp_cut sweep only to ask whether "
            "fingerprints separate structure. Do not mint blueprints from "
            "cluster n or top flag combos."
        ),
    }


def draw_empty_sample(
    frame: pd.DataFrame,
    *,
    per_stratum: int = DEFAULT_SAMPLE_PER_STRATUM,
    seed: int = DEFAULT_SAMPLE_SEED,
) -> pd.DataFrame:
    """Stratify by proposition_type × length tercile (+ fp cluster when scored)."""
    out = frame.copy()
    if out.empty:
        return out.head(0)

    if "n_words" not in out.columns:
        out["n_words"] = pd.NA
    out["length_stratum"] = _length_tercile(out["n_words"])
    if "proposition_type" not in out.columns:
        out["proposition_type"] = NONE_TYPE_KEY
    out["ptype_stratum"] = out["proposition_type"].astype(str)

    if "resolutions_text" not in out.columns:
        ids = set(out["id"].astype(str))
        flat = load("resolutions_flat")
        sub = flat.loc[
            flat["id"].astype(str).isin(ids), ["id", "resolutions_text"]
        ].copy()
        sub["id"] = sub["id"].astype(str)
        out = out.merge(sub, on="id", how="left")

    group_cols = ["ptype_stratum", "length_stratum"]
    if "fp_cluster_id" in out.columns and out["fp_cluster_id"].notna().any():
        # Cap cluster strata: only top-size clusters get dedicated rows.
        counts = out["fp_cluster_id"].value_counts()
        top = set(counts.head(6).index)
        out["fp_stratum"] = out["fp_cluster_id"].map(
            lambda c: str(int(c)) if c in top else "other"
        )
        group_cols = ["ptype_stratum", "length_stratum", "fp_stratum"]

    parts: list[pd.DataFrame] = []
    rng = seed
    for key, group in out.groupby(group_cols, sort=True):
        if isinstance(key, tuple) and "unknown" in key:
            continue
        take = min(int(per_stratum), len(group))
        if take <= 0:
            continue
        sampled = group.sample(n=take, random_state=rng).copy()
        rng += 1
        sampled["sample_stratum"] = "|".join(str(k) for k in (key if isinstance(key, tuple) else (key,)))
        parts.append(sampled)

    if not parts:
        return out.head(0)
    result = pd.concat(parts, ignore_index=True)
    keep = [
        "id",
        "year",
        "proposition_type",
        "n_words",
        "length_stratum",
        "nn_sim",
        "fp_cluster_id",
        "is_l1",
        "is_r1",
        "sample_stratum",
        "resolutions_text",
    ]
    cols = [c for c in keep if c in result.columns]
    result = result[cols].copy()
    if "resolutions_text" in result.columns:
        result["resolutions_text"] = (
            result["resolutions_text"].fillna("").astype(str).str.slice(0, 1200)
        )
    return result


def fixture_empty_frame() -> pd.DataFrame:
    """Tiny in-memory empty-band frame (no parquet / no ES)."""
    rows = [
        {
            "id": "e1",
            "year": 1780,
            "motif_class": "empty",
            "proposition_type": "rekest",
            "session_date": "1780-01-01",
            "es_joined": True,
            "ontfangen_present": False,
            "is_l1": False,
            "is_r1": False,
            "is_advies_gold": False,
            "residual_not_l1": False,
            "n_words": 120,
            "text_joined": True,
            "outcome_joined": True,
            "requeste_start": True,
            "goedgevonden": True,
            "geen_resolutie": False,
            "advertentie": False,
            "ontfangen_start": False,
            "resolutions_text": (
                "is gelesen de requeste van den suppliant houdende verzoek"
            ),
        },
        {
            "id": "e2",
            "year": 1780,
            "motif_class": "empty",
            "proposition_type": "rekest",
            "session_date": "1780-01-02",
            "es_joined": True,
            "ontfangen_present": False,
            "is_l1": False,
            "is_r1": False,
            "is_advies_gold": False,
            "residual_not_l1": False,
            "n_words": 95,
            "text_joined": True,
            "outcome_joined": True,
            "requeste_start": True,
            "goedgevonden": False,
            "geen_resolutie": False,
            "advertentie": False,
            "ontfangen_start": False,
            "resolutions_text": (
                "is gelesen de requeste van den suppliant om paspoort"
            ),
        },
        {
            "id": "e3",
            "year": 1780,
            "motif_class": "empty",
            "proposition_type": "rapport",
            "session_date": "1780-01-03",
            "es_joined": True,
            "ontfangen_present": False,
            "is_l1": False,
            "is_r1": False,
            "is_advies_gold": False,
            "residual_not_l1": False,
            "n_words": 200,
            "text_joined": True,
            "outcome_joined": True,
            "requeste_start": False,
            "goedgevonden": True,
            "geen_resolutie": False,
            "advertentie": False,
            "ontfangen_start": False,
            "rapport_start": True,
            "resolutions_text": (
                "gehoort het rapport van de gecommitteerden rakende de saeck"
            ),
        },
        {
            "id": "e4",
            "year": 1780,
            "motif_class": "empty",
            "proposition_type": "rapport",
            "session_date": "1780-01-04",
            "es_joined": True,
            "ontfangen_present": False,
            "is_l1": False,
            "is_r1": False,
            "is_advies_gold": False,
            "residual_not_l1": False,
            "n_words": 180,
            "text_joined": True,
            "outcome_joined": True,
            "requeste_start": False,
            "goedgevonden": True,
            "geen_resolutie": False,
            "advertentie": False,
            "ontfangen_start": False,
            "rapport_start": True,
            "resolutions_text": (
                "gehoort het rapport van de gecommitteerden over den brief"
            ),
        },
        {
            "id": "e5",
            "year": 1780,
            "motif_class": "empty",
            "proposition_type": "onbekend",
            "session_date": "1780-01-05",
            "es_joined": True,
            "ontfangen_present": False,
            "is_l1": False,
            "is_r1": False,
            "is_advies_gold": False,
            "residual_not_l1": False,
            "n_words": 40,
            "text_joined": True,
            "outcome_joined": False,
            "requeste_start": False,
            "goedgevonden": False,
            "geen_resolutie": False,
            "advertentie": False,
            "ontfangen_start": False,
            "resolutions_text": "korte onduidelijke notitie zonder formules",
        },
        {
            "id": "e6",
            "year": 1780,
            "motif_class": "empty",
            "proposition_type": "memorie",
            "session_date": "1780-01-06",
            "es_joined": True,
            "ontfangen_present": False,
            "is_l1": False,
            "is_r1": False,
            "is_advies_gold": False,
            "residual_not_l1": False,
            "n_words": 150,
            "text_joined": True,
            "outcome_joined": True,
            "requeste_start": False,
            "goedgevonden": False,
            "geen_resolutie": False,
            "advertentie": False,
            "ontfangen_start": False,
            "resolutions_text": (
                "overgegeven eene memorie van den ambassadeur rakende "
            ),
        },
    ]
    frame = pd.DataFrame(rows)
    flag_names = (
        "requeste_start",
        "goedgevonden",
        "geen_resolutie",
        "advertentie",
        "ontfangen_start",
        "rapport_start",
    )
    for col in flag_names:
        if col not in frame.columns:
            frame[col] = False
        frame[col] = frame[col].fillna(False).astype("boolean")
    frame.attrs["flag_columns"] = list(flag_names)
    return frame
