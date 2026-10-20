"""STEPT1i: formula-graph patterns — proto-blueprints, derivatives, undecided.

Unknown = unexplained composition (empty / novel_tail), not gold-set miss.
Fingerprints (optional) score undecided texts toward proto-blueprint exemplars.
"""

from __future__ import annotations

from collections import Counter
from typing import Any

import numpy as np
import pandas as pd

from data_io import load
from formulation.advies_formula_type import FORMULA_TYPE_ID as ADVIES_ID
from formulation.appointment_formula_type import FORMULA_TYPE_ID as APPOINTMENT_ID
from formulation.boundary.tfidf_windows import POC_YEAR
from formulation.content_fingerprint import (
    DEFAULT_FP_CUT,
    ContentFingerprint,
    greedy_clusters,
    max_sim_to_exemplars,
    nearest_neighbor_sims,
)
from formulation.formula_type_composition_graph import COMPOSITION_ROOT
from formulation.ontfangen_partition import load_presence_universe
from formulation.requeste_formula_type import FORMULA_TYPE_ID as REQUESTE_ID

DEFAULT_YEAR = POC_YEAR
DEFAULT_MIN_SUPPORT = 5
DEFAULT_SAMPLE_SEED = 20261020
DEFAULT_SAMPLE_PER_STRATUM = 5
DEFAULT_EXEMPLAR_CAP = 40

# STEPT1m: requeste_geleesen (STEPT1k, frozen cut 4.5) joins the accepted
# core alongside appointment_installation / advies_geleesen. Only the
# opener — STEPT1l's routing subtypes stay characteristics, not core types.
ACCEPTED_TYPE_IDS = frozenset({APPOINTMENT_ID, ADVIES_ID, REQUESTE_ID})

MOTIF_FILLER = "filler_star"
MOTIF_KNOWN = "known_sparse"
MOTIF_EMPTY = "empty"
MOTIF_NOVEL = "novel_tail"

__all__ = (
    "ACCEPTED_TYPE_IDS",
    "DEFAULT_EXEMPLAR_CAP",
    "DEFAULT_FP_CUT",
    "DEFAULT_MIN_SUPPORT",
    "DEFAULT_SAMPLE_PER_STRATUM",
    "DEFAULT_SAMPLE_SEED",
    "DEFAULT_YEAR",
    "MOTIF_EMPTY",
    "MOTIF_FILLER",
    "MOTIF_KNOWN",
    "MOTIF_NOVEL",
    "accepted_core",
    "attach_fingerprint_undecided",
    "build_composition_frame",
    "classify_motif",
    "draw_undecided_sample",
    "fixture_composition_frame",
    "load_year_bags",
    "summarize_composition_unknown",
)


def accepted_core(bag: tuple[str, ...] | list[str]) -> tuple[str, ...]:
    """Structure key: bag ∩ accepted formula types only."""
    return tuple(sorted(t for t in bag if t in ACCEPTED_TYPE_IDS))


def classify_motif(
    bag: tuple[str, ...],
    core: tuple[str, ...],
    core_support: int,
    *,
    min_support: int = DEFAULT_MIN_SUPPORT,
) -> str:
    if not bag:
        return MOTIF_EMPTY
    if bag == (COMPOSITION_ROOT,):
        return MOTIF_FILLER
    if core and int(core_support) >= int(min_support):
        return MOTIF_KNOWN
    return MOTIF_NOVEL


def load_year_bags(*, year: int = DEFAULT_YEAR) -> pd.DataFrame:
    """One row per presence-universe id with present_bag from presence scores."""
    universe = load_presence_universe(year=year)
    universe["id"] = universe["id"].astype(str)

    presence = pd.DataFrame(load("formula_type_presence_scores"))
    presence["id"] = presence["id"].astype(str)
    presence["year"] = pd.to_numeric(presence["year"], errors="coerce")
    slice_ = presence.loc[presence["year"] == int(year)].copy()
    slice_["present"] = slice_["present"].astype(bool)
    present_rows = slice_.loc[slice_["present"], ["id", "formula_type_id"]]
    bags = (
        present_rows.groupby("id")["formula_type_id"]
        .apply(lambda s: tuple(sorted(str(x) for x in s)))
        .to_dict()
    )
    out = universe[["id", "year"]].copy()
    out["present_bag"] = out["id"].map(lambda i: bags.get(str(i), ()))
    return out


def build_composition_frame(
    bags: pd.DataFrame,
    *,
    min_support: int = DEFAULT_MIN_SUPPORT,
) -> pd.DataFrame:
    """Attach accepted_core, supports, motif_class, composition_unknown."""
    frame = bags.copy()
    frame["id"] = frame["id"].astype(str)
    frame["present_bag"] = frame["present_bag"].map(
        lambda b: tuple(b) if not isinstance(b, tuple) else b
    )
    frame["accepted_core"] = frame["present_bag"].map(accepted_core)

    # Support by exact bag and by accepted_core.
    bag_counts = Counter(frame["present_bag"].tolist())
    core_counts = Counter(frame["accepted_core"].tolist())
    frame["bag_support"] = frame["present_bag"].map(lambda b: int(bag_counts[b]))
    frame["core_support"] = frame["accepted_core"].map(lambda c: int(core_counts[c]))

    frame["motif_class"] = [
        classify_motif(bag, core, int(supp), min_support=min_support)
        for bag, core, supp in zip(
            frame["present_bag"],
            frame["accepted_core"],
            frame["core_support"],
            strict=True,
        )
    ]
    frame["composition_unknown"] = frame["motif_class"].isin(
        {MOTIF_EMPTY, MOTIF_NOVEL}
    )
    frame["is_proto_blueprint"] = frame["motif_class"] == MOTIF_KNOWN
    return frame


def _attach_texts(frame: pd.DataFrame) -> pd.DataFrame:
    ids = set(frame["id"].astype(str))
    flat = load("resolutions_flat")
    sub = flat.loc[flat["id"].astype(str).isin(ids), ["id", "resolutions_text"]].copy()
    sub["id"] = sub["id"].astype(str)
    sub["resolutions_text"] = sub["resolutions_text"].fillna("").astype(str)
    out = frame.merge(sub, on="id", how="left")
    out["resolutions_text"] = out["resolutions_text"].fillna("")
    out["text_joined"] = out["resolutions_text"].str.len() > 0
    return out


def attach_fingerprint_undecided(
    frame: pd.DataFrame,
    *,
    fp_cut: float = DEFAULT_FP_CUT,
    exemplar_cap: int = DEFAULT_EXEMPLAR_CAP,
    join_text: bool = True,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Fingerprint undecided rows; leave others with NA fingerprint fields."""
    out = frame.copy()
    out["nn_sim"] = pd.NA
    out["fp_cluster_id"] = pd.NA
    out["derivative_score"] = pd.NA
    out["fp_scored"] = False

    undecided = out.loc[out["composition_unknown"]].copy()
    meta: dict[str, Any] = {
        "fingerprint_ran": False,
        "n_undecided": int(len(undecided)),
        "fp_cut": float(fp_cut),
        "n_exemplars": 0,
        "n_clusters": 0,
        "n_singletons": 0,
        "share_largest_cluster": None,
        "nn_sim_p50": None,
        "nn_sim_p90": None,
        "derivative_score_p50": None,
        "note": "skipped or too few undecided texts",
    }
    if len(undecided) < 2:
        return out, meta

    if join_text and "resolutions_text" not in out.columns:
        out = _attach_texts(out)
        undecided = out.loc[out["composition_unknown"]].copy()

    texts = undecided["resolutions_text"].fillna("").astype(str).tolist()
    if sum(1 for t in texts if t.strip()) < 2:
        return out, meta

    fp = ContentFingerprint().fit(texts)
    sim = fp.similarity_matrix(texts)
    nn = nearest_neighbor_sims(sim)
    labels = greedy_clusters(sim, cut=fp_cut)

    # Proto-blueprint exemplars (known_sparse texts).
    known = out.loc[out["motif_class"] == MOTIF_KNOWN]
    if "resolutions_text" not in known.columns and join_text:
        out = _attach_texts(out)
        known = out.loc[out["motif_class"] == MOTIF_KNOWN]
    exemplars: list[str] = []
    if len(known):
        # Cap per core for balance.
        parts: list[pd.DataFrame] = []
        for _core, grp in known.groupby("accepted_core", sort=False):
            take = min(max(1, exemplar_cap // max(1, known["accepted_core"].nunique())), len(grp))
            parts.append(grp.head(take))
        if parts:
            ex_frame = pd.concat(parts, ignore_index=True)
            exemplars = (
                ex_frame["resolutions_text"].fillna("").astype(str).tolist()[:exemplar_cap]
            )
    der = max_sim_to_exemplars(texts, exemplars, fp)

    scored = undecided[["id"]].copy()
    scored["nn_sim"] = nn
    scored["fp_cluster_id"] = labels.astype(int)
    scored["derivative_score"] = der
    scored["fp_scored"] = True
    out = out.drop(
        columns=["nn_sim", "fp_cluster_id", "derivative_score", "fp_scored"],
        errors="ignore",
    )
    out = out.merge(scored, on="id", how="left")
    out["fp_scored"] = out["fp_scored"].fillna(False).astype(bool)

    counts = Counter(labels.tolist())
    n_clusters = len(counts)
    n_singletons = sum(1 for c in counts.values() if c == 1)
    largest = max(counts.values()) if counts else 0
    meta = {
        "fingerprint_ran": True,
        "n_undecided": int(len(undecided)),
        "fp_cut": float(fp_cut),
        "n_exemplars": len(exemplars),
        "n_clusters": int(n_clusters),
        "n_singletons": int(n_singletons),
        "share_largest_cluster": (largest / len(undecided)) if len(undecided) else None,
        "nn_sim_p50": float(np.median(nn)) if len(nn) else None,
        "nn_sim_p90": float(np.quantile(nn, 0.9)) if len(nn) else None,
        "derivative_score_p50": float(np.median(der)) if len(der) else None,
        "note": (
            "Content fingerprint on undecided only; derivative_score = "
            "max_sim to proto-blueprint exemplars. Clusters ≠ types."
        ),
    }
    return out, meta


def summarize_composition_unknown(
    frame: pd.DataFrame,
    *,
    year: int,
    min_support: int = DEFAULT_MIN_SUPPORT,
    fingerprint_meta: dict[str, Any] | None = None,
) -> dict[str, Any]:
    n = len(frame)
    motif_counts = (
        frame["motif_class"].value_counts().to_dict() if n else {}
    )
    motif = {
        k: {
            "n": int(motif_counts.get(k, 0)),
            "frac": (motif_counts.get(k, 0) / n) if n else None,
        }
        for k in (MOTIF_FILLER, MOTIF_KNOWN, MOTIF_EMPTY, MOTIF_NOVEL)
    }

    # Proto-blueprint catalogue + variation mass.
    known = frame.loc[frame["motif_class"] == MOTIF_KNOWN]
    proto_rows: list[dict[str, Any]] = []
    if len(known):
        for core, grp in known.groupby("accepted_core", sort=True):
            bag_counts = Counter(grp["present_bag"].tolist())
            top_n = bag_counts.most_common(1)[0][1] if bag_counts else 0
            proto_rows.append(
                {
                    "accepted_core": list(core),
                    "support": int(len(grp)),
                    "n_unique_exact_bags": int(len(bag_counts)),
                    "dominant_bag_frac": (top_n / len(grp)) if len(grp) else None,
                }
            )
        proto_rows.sort(key=lambda r: -r["support"])

    n_undecided = int(frame["composition_unknown"].sum()) if n else 0
    n_unique_bags = int(frame["present_bag"].nunique()) if n else 0
    n_unique_cores = int(frame["accepted_core"].nunique()) if n else 0

    # Optional STEPT1h crosstab
    crosstab = None
    try:
        unk = pd.DataFrame(load("resolution_unknown_scores"))
        unk["id"] = unk["id"].astype(str)
        if "high_unknown" in unk.columns and "year" in unk.columns:
            unk["year"] = pd.to_numeric(unk["year"], errors="coerce")
            slice_ = unk.loc[unk["year"] == int(year), ["id", "high_unknown"]]
            merged = frame[["id", "motif_class", "composition_unknown"]].merge(
                slice_, on="id", how="left"
            )
            if merged["high_unknown"].notna().any():
                crosstab = {
                    "n_joined": int(merged["high_unknown"].notna().sum()),
                    "n_composition_unknown_and_high_unknown": int(
                        (
                            merged["composition_unknown"]
                            & merged["high_unknown"].fillna(False).astype(bool)
                        ).sum()
                    ),
                    "note": "Diagnostic only — STEPT1h cover-unknown ≠ composition-unknown",
                }
    except Exception:
        crosstab = {"note": "resolution_unknown_scores not available"}

    return {
        "step": "STEPT1i",
        "method": "composition_unknown_graph_fingerprint",
        "year": int(year),
        "min_support": int(min_support),
        "accepted_types": sorted(ACCEPTED_TYPE_IDS),
        "composition_root": COMPOSITION_ROOT,
        "constraint": "blueprint_derivative_novel_via_graph_and_fingerprint",
        "n_universe": n,
        "n_unique_exact_bags": n_unique_bags,
        "n_unique_accepted_cores": n_unique_cores,
        "n_proto_blueprints": len(proto_rows),
        "n_undecided": n_undecided,
        "frac_undecided": (n_undecided / n) if n else None,
        "motif_class": motif,
        "proto_blueprints": proto_rows,
        "stept1h_crosstab": crosstab,
        "fingerprint": fingerprint_meta or {"fingerprint_ran": False},
        "notes": (
            "Proto-blueprints = accepted_cores with support>=min. "
            "Within-core exact bags = derivatives. "
            "Undecided = empty|novel_tail; fingerprints score derivative-vs-novel "
            "candidates. Do not mint types from clusters or bag n."
        ),
    }


def draw_undecided_sample(
    frame: pd.DataFrame,
    *,
    per_stratum: int = DEFAULT_SAMPLE_PER_STRATUM,
    seed: int = DEFAULT_SAMPLE_SEED,
) -> pd.DataFrame:
    """Sample undecided texts; prefer fp_cluster strata when present."""
    undecided = frame.loc[frame["composition_unknown"]].copy()
    if undecided.empty:
        return undecided.head(0)

    if "resolutions_text" not in undecided.columns:
        undecided = _attach_texts(undecided)

    if "fp_cluster_id" in undecided.columns and undecided["fp_cluster_id"].notna().any():
        stratum_col = "fp_cluster_id"
    else:
        stratum_col = "motif_class"

    parts: list[pd.DataFrame] = []
    rng = seed
    for key, group in undecided.groupby(stratum_col, sort=True):
        take = min(int(per_stratum), len(group))
        if take <= 0:
            continue
        sampled = group.sample(n=take, random_state=rng).copy()
        rng += 1
        sampled["sample_stratum"] = str(key)
        parts.append(sampled)

    if not parts:
        return undecided.head(0)
    out = pd.concat(parts, ignore_index=True)
    keep = [
        "id",
        "year",
        "motif_class",
        "present_bag",
        "accepted_core",
        "bag_support",
        "core_support",
        "nn_sim",
        "derivative_score",
        "fp_cluster_id",
        "sample_stratum",
        "resolutions_text",
    ]
    cols = [c for c in keep if c in out.columns]
    result = out[cols].copy()
    if "present_bag" in result.columns:
        result["present_bag"] = result["present_bag"].map(list)
    if "accepted_core" in result.columns:
        result["accepted_core"] = result["accepted_core"].map(list)
    if "resolutions_text" in result.columns:
        result["resolutions_text"] = (
            result["resolutions_text"].fillna("").astype(str).str.slice(0, 1200)
        )
    return result


def fixture_composition_frame() -> pd.DataFrame:
    """Tiny in-memory frame (no parquet)."""
    rows = [
        # filler
        {
            "id": "r1",
            "year": 1780,
            "present_bag": (COMPOSITION_ROOT,),
        },
        {
            "id": "r2",
            "year": 1780,
            "present_bag": (COMPOSITION_ROOT,),
        },
        # known sparse appointment (± ontfangen) — same core
        {
            "id": "r3",
            "year": 1780,
            "present_bag": (APPOINTMENT_ID, COMPOSITION_ROOT),
        },
        {
            "id": "r4",
            "year": 1780,
            "present_bag": (APPOINTMENT_ID,),
        },
        {
            "id": "r5",
            "year": 1780,
            "present_bag": (APPOINTMENT_ID, COMPOSITION_ROOT),
        },
        {
            "id": "r6",
            "year": 1780,
            "present_bag": (APPOINTMENT_ID, COMPOSITION_ROOT),
        },
        {
            "id": "r7",
            "year": 1780,
            "present_bag": (APPOINTMENT_ID, COMPOSITION_ROOT),
        },
        # advies core (support 5)
        {
            "id": "r8",
            "year": 1780,
            "present_bag": (ADVIES_ID, COMPOSITION_ROOT),
        },
        {
            "id": "r9",
            "year": 1780,
            "present_bag": (ADVIES_ID, COMPOSITION_ROOT),
        },
        {
            "id": "r10",
            "year": 1780,
            "present_bag": (ADVIES_ID,),
        },
        {
            "id": "r11",
            "year": 1780,
            "present_bag": (ADVIES_ID, COMPOSITION_ROOT),
        },
        {
            "id": "r12",
            "year": 1780,
            "present_bag": (ADVIES_ID, COMPOSITION_ROOT),
        },
        # empty
        {"id": "r13", "year": 1780, "present_bag": ()},
        {"id": "r14", "year": 1780, "present_bag": ()},
        # novel: rare provisional-only non-filler (e.g. requeste alone) — use fake type
        {
            "id": "r15",
            "year": 1780,
            "present_bag": ("requeste_start",),
        },
    ]
    return build_composition_frame(pd.DataFrame(rows), min_support=5)
