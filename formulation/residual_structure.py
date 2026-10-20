"""STEPT1g: decisionful residual structure probe (ontfangen+ \\ L1).

Universe = missive ∩ ontfangen+ ∩ residual_not_l1. Inventory + pockets +
stratified text sample for reading. **Probability is not typology** — do not
mint subtype ids from flag rates, fracs, or length cuts.
"""

from __future__ import annotations

from collections import Counter
from typing import Any

import pandas as pd

from data_io import load
from formulation.advies_formula_type import FORMULA_TYPE_ID as ADVIES_ID
from formulation.appointment_formula_type import FORMULA_TYPE_ID as APPOINTMENT_ID
from formulation.boundary.tfidf_windows import POC_YEAR
from formulation.formula_type_composition_graph import COMPOSITION_ROOT
from formulation.missive_subtype_profile import (
    attach_word_counts,
    load_partition_scores,
)
from formulation.ontfangen_partition import fixture_partition_frame
from formulation.typology_sample import (
    _resolution_index_from_id,
    join_outcome_flags,
)

DEFAULT_YEAR = POC_YEAR
DEFAULT_SAMPLE_SEED = 20261020
DEFAULT_SAMPLE_PER_STRATUM = 5
CATALOGUE_TOP_K = 20

ACCEPTED_TYPES = (APPOINTMENT_ID, ADVIES_ID)

__all__ = (
    "ACCEPTED_TYPES",
    "CATALOGUE_TOP_K",
    "DEFAULT_SAMPLE_PER_STRATUM",
    "DEFAULT_SAMPLE_SEED",
    "DEFAULT_YEAR",
    "attach_presence_pockets",
    "build_residual_frame",
    "draw_stratified_sample",
    "fixture_residual_frame",
    "load_residual_universe",
    "summarize_residual_structure",
)


def load_residual_universe(*, year: int = DEFAULT_YEAR) -> pd.DataFrame:
    """Ontfangen+ rows; caller filters missive residual for primary tables."""
    scores = load_partition_scores(year=year)
    return scores.loc[scores["ontfangen_present"]].copy()


def attach_presence_pockets(
    frame: pd.DataFrame,
    *,
    year: int = DEFAULT_YEAR,
) -> pd.DataFrame:
    """Tag accepted formula-type present flags from presence scores."""
    out = frame.copy()
    out["id"] = out["id"].astype(str)
    presence = pd.DataFrame(load("formula_type_presence_scores"))
    presence["id"] = presence["id"].astype(str)
    presence["year"] = pd.to_numeric(presence["year"], errors="coerce")
    slice_ = presence.loc[presence["year"] == int(year)].copy()
    slice_["present"] = slice_["present"].astype(bool)

    for ft, col in (
        (APPOINTMENT_ID, "appointment_present"),
        (ADVIES_ID, "advies_present"),
        (COMPOSITION_ROOT, "ontfangen_presence_present"),
    ):
        hits = set(
            slice_.loc[
                (slice_["formula_type_id"] == ft) & slice_["present"],
                "id",
            ].astype(str)
        )
        out[col] = out["id"].isin(hits)

    # Bag = sorted present type ids (accepted + provisional openings in scores).
    present_rows = slice_.loc[slice_["present"], ["id", "formula_type_id"]]
    bags = (
        present_rows.groupby("id")["formula_type_id"]
        .apply(lambda s: tuple(sorted(str(x) for x in s)))
        .to_dict()
    )
    out["present_bag"] = out["id"].map(lambda i: bags.get(str(i), ()))
    return out


def _combo_counter(
    group: pd.DataFrame,
    flag_cols: list[str],
) -> Counter[tuple[str, ...]]:
    known = group[group["outcome_joined"]] if "outcome_joined" in group else group
    if known.empty or not flag_cols:
        return Counter()
    patterns: Counter[tuple[str, ...]] = Counter()
    for row in known[flag_cols].itertuples(index=False):
        combo = tuple(sorted(col for col, val in zip(flag_cols, row) if val))
        patterns[combo] += 1
    return patterns


def combo_catalogue(
    group: pd.DataFrame,
    flag_cols: list[str],
    *,
    top_k: int = CATALOGUE_TOP_K,
) -> dict[str, Any]:
    """Distinct flag-set inventory with concentration summary (not subtypes)."""
    known = group[group["outcome_joined"]] if "outcome_joined" in group else group
    known_n = len(known)
    counts = _combo_counter(group, flag_cols)
    ranked = counts.most_common()
    top = ranked[:top_k]
    n_unique = len(counts)
    top5_n = sum(n for _, n in ranked[:5])
    top20_n = sum(n for _, n in ranked[:20])
    return {
        "n_outcome_joined": known_n,
        "n_unique_combos": n_unique,
        "share_top_5": (top5_n / known_n) if known_n else None,
        "share_top_20": (top20_n / known_n) if known_n else None,
        "top_combos": [
            {"flags": list(combo), "n": int(n)}
            for combo, n in top
        ],
        "note": (
            "Catalogue of distinct boilerplate flag sets — inventory only; "
            "do not promote high-n combos to subtype ids. High-n is usually "
            "filler (no signal); interesting shapes are sparse."
        ),
    }


def _bag_inventory(frame: pd.DataFrame) -> list[dict[str, Any]]:
    bags = frame["present_bag"].tolist() if "present_bag" in frame.columns else []
    counts = Counter(bags)
    rows = []
    for bag, n in counts.most_common(30):
        label = "+".join(bag) if bag else "(empty)"
        rows.append({"bag": list(bag), "bag_label": label, "n": int(n)})
    return rows


def build_residual_frame(
    ontfangen_plus: pd.DataFrame,
    *,
    year: int = DEFAULT_YEAR,
    join_flags: bool = True,
    join_text_length: bool = True,
    join_presence: bool = True,
) -> pd.DataFrame:
    """Full ontfangen+ with joins; primary analysis filters missive residual."""
    frame = ontfangen_plus.copy()
    frame["id"] = frame["id"].astype(str)
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

    if join_presence:
        frame = attach_presence_pockets(frame, year=year)
    else:
        frame["appointment_present"] = False
        frame["advies_present"] = False
        frame["ontfangen_presence_present"] = (
            frame["ontfangen_present"]
            if "ontfangen_present" in frame.columns
            else False
        )
        frame["present_bag"] = [() for _ in range(len(frame))]

    frame.attrs["flag_columns"] = flag_cols
    return frame


def _length_tercile(series: pd.Series) -> pd.Series:
    """Label short / mid / long from tertile cuts (sample strata only)."""
    valid = series.dropna()
    if valid.empty:
        return pd.Series(["unknown"] * len(series), index=series.index)
    q1, q2 = valid.quantile([1 / 3, 2 / 3])
    out = pd.Series(["mid"] * len(series), index=series.index, dtype=object)
    out.loc[series.isna()] = "unknown"
    out.loc[series <= q1] = "short"
    out.loc[series > q2] = "long"
    # between q1 and q2 stays mid; equalities: <=q1 short, >q2 long
    mid_mask = series.notna() & (series > q1) & (series <= q2)
    out.loc[mid_mask] = "mid"
    return out


def draw_stratified_sample(
    residual: pd.DataFrame,
    *,
    per_stratum: int = DEFAULT_SAMPLE_PER_STRATUM,
    seed: int = DEFAULT_SAMPLE_SEED,
) -> pd.DataFrame:
    """Length tercile × appointment± sample of residual texts for NOTES reading."""
    frame = residual.copy()
    if "n_words" not in frame.columns:
        frame["n_words"] = pd.NA
    if "appointment_present" not in frame.columns:
        frame["appointment_present"] = False
    frame["length_stratum"] = _length_tercile(frame["n_words"])
    frame["appointment_stratum"] = frame["appointment_present"].map(
        lambda x: "appointment" if bool(x) else "no_appointment"
    )

    # Join text
    ids = set(frame["id"].astype(str))
    flat = load("resolutions_flat")
    sub = flat.loc[flat["id"].astype(str).isin(ids), ["id", "resolutions_text"]].copy()
    sub["id"] = sub["id"].astype(str)
    frame = frame.merge(sub, on="id", how="left")

    parts: list[pd.DataFrame] = []
    rng = seed
    for (length_s, appt_s), group in frame.groupby(
        ["length_stratum", "appointment_stratum"], sort=True
    ):
        if length_s == "unknown":
            continue
        take = min(int(per_stratum), len(group))
        if take <= 0:
            continue
        sampled = group.sample(n=take, random_state=rng)
        rng += 1
        sampled = sampled.copy()
        sampled["sample_stratum"] = f"{length_s}|{appt_s}"
        parts.append(sampled)

    if not parts:
        return frame.head(0)
    out = pd.concat(parts, ignore_index=True)
    keep = [
        "id",
        "year",
        "proposition_type",
        "n_words",
        "length_stratum",
        "appointment_present",
        "advies_present",
        "is_r1",
        "present_bag",
        "sample_stratum",
        "resolutions_text",
    ]
    cols = [c for c in keep if c in out.columns]
    result = out[cols].copy()
    # Truncate text for JSONL readability (full text still in flat if needed).
    if "resolutions_text" in result.columns:
        result["resolutions_text"] = (
            result["resolutions_text"]
            .fillna("")
            .astype(str)
            .str.slice(0, 1200)
        )
    if "present_bag" in result.columns:
        result["present_bag"] = result["present_bag"].map(
            lambda b: list(b) if isinstance(b, tuple) else b
        )
    return result


def summarize_residual_structure(
    frame: pd.DataFrame,
    *,
    year: int,
) -> dict[str, Any]:
    """Provenanced metrics: pockets + catalogue + bags (no subtype ids)."""
    flag_cols: list[str] = list(frame.attrs.get("flag_columns") or [])
    # Preserve flag attrs through presence join: recover from boolean cols if needed.
    if not flag_cols:
        flag_cols = [
            c
            for c in frame.columns
            if str(frame[c].dtype) == "boolean"
            and c
            not in {
                "ontfangen_present",
                "is_l1",
                "is_r1",
                "is_advies_gold",
                "residual_not_l1",
                "es_joined",
                "outcome_joined",
                "text_joined",
                "appointment_present",
                "advies_present",
                "ontfangen_presence_present",
            }
        ]

    residual_all = frame.loc[frame["residual_not_l1"]].copy()
    residual = residual_all.loc[
        residual_all["proposition_type"].astype(str) == "missive"
    ].copy()
    leakage = residual_all.loc[
        residual_all["proposition_type"].astype(str) != "missive"
    ]

    residual.attrs["flag_columns"] = flag_cols
    catalogue = combo_catalogue(residual, flag_cols)

    n = len(residual)
    pockets = {
        "n_appointment_present": int(residual["appointment_present"].sum())
        if n and "appointment_present" in residual.columns
        else 0,
        "n_advies_present": int(residual["advies_present"].sum())
        if n and "advies_present" in residual.columns
        else 0,
        "n_r1_selected": int(residual["is_r1"].sum()) if n else 0,
        "n_appointment_and_r1": int(
            (residual["appointment_present"] & residual["is_r1"]).sum()
        )
        if n and "appointment_present" in residual.columns
        else 0,
    }

    return {
        "step": "STEPT1g",
        "method": "residual_structure_probe",
        "year": int(year),
        "composition_root": COMPOSITION_ROOT,
        "universe": "missive ∩ ontfangen+ ∩ residual_not_l1",
        "constraint": "probability_is_not_typology",
        "n_ontfangen_plus": int(frame["ontfangen_present"].sum())
        if "ontfangen_present" in frame.columns
        else len(frame),
        "n_residual_all": len(residual_all),
        "n_residual_missive": n,
        "n_non_missive_residual_leakage": len(leakage),
        "pockets": pockets,
        "combo_catalogue": catalogue,
        "bags": {
            "n_distinct_bags": len({tuple(b) for b in residual["present_bag"]})
            if n and "present_bag" in residual.columns
            else 0,
            "top_bags": _bag_inventory(residual) if n else [],
            "note": (
                "Present formula-type bags on residual ids — inventory; "
                "star-vs-multi is descriptive, not a type system."
            ),
        },
        "notes": (
            "Decisionful residual structure probe. Catalogue and pockets are "
            "inventory; NOTES must name readable (esp. sparse) shapes from the "
            "stratified sample — not subtypes from rates. Hit rate ≠ usefulness; "
            "ubiquitous filler is no signal. Not STEPT1e1."
        ),
    }


def fixture_residual_frame() -> pd.DataFrame:
    """Tiny in-memory residual-oriented frame (no parquet)."""
    base = fixture_partition_frame()
    # Keep ontfangen+ rows; mark residual ones.
    frame = base.loc[base["ontfangen_present"]].copy()
    frame["appointment_present"] = frame["is_r1"]
    frame["advies_present"] = False
    frame["ontfangen_presence_present"] = True
    frame["n_words"] = [40, 180, 90]
    frame["text_joined"] = True
    frame["present_bag"] = [
        (COMPOSITION_ROOT,),
        (COMPOSITION_ROOT, APPOINTMENT_ID),
        (COMPOSITION_ROOT,),
    ]
    if "gedelibereert_start" not in frame.columns:
        frame["gedelibereert_start"] = pd.array(
            [False, True, False], dtype="boolean"
        )
    flag_cols = [
        c
        for c in (
            "geen_resolutie",
            "advertentie",
            "goedgevonden",
            "rapport_start",
            "ontfangen_start",
            "advies",
            "requeste_start",
            "handen",
            "in handen",
            "gedelibereert_start",
        )
        if c in frame.columns
    ]
    frame.attrs["flag_columns"] = flag_cols
    return frame
