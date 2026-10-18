"""Build missive-receipt labelled rows for Track L (STEPL1).

Positives = open+close cue both-hits (minus aanstelling_selected) plus hand seeds.
Overig = 10× sample in the same year window. Whole-resolution labels only.
"""

from __future__ import annotations

import re
from collections.abc import Sequence

import pandas as pd

from formulation.aanstelling import (
    OVERIG_PER_POSITIVE,
    RANDOM_STATE,
    inventory_from_id,
    sample_overig,
)

LABEL_MISSIVE = "missive_receipt"
LABEL_OVERIG = "overig"

OPEN_CUE = re.compile(
    r"ontfangen\s+een(?:en)?\s+(?:missive|missiue|brief|brieff)",
    re.I,
)
CLOSE_CUE = re.compile(
    r"geen\s+resolutie\s+(?:is\s+)?gevallen|"
    r"geen\s+resolutie\s+vere[iy]sch",
    re.I,
)

REQUIRED_FLAT_COLS = ("id", "date", "year", "resolutions_text")
LABEL_COLS = ("label", "inventory", "positive_source")
SOURCE_CUE_BOTH = "cue_both"
SOURCE_HAND_SEED = "hand_seed"


def normalize_text(value: object) -> str:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return ""
    return re.sub(r"\s+", " ", str(value).casefold()).strip()


def open_close_mask(text: pd.Series) -> pd.Series:
    """Vectorized open∧close cue hits on resolution text."""
    filled = text.fillna("").astype(str)
    return filled.str.contains(OPEN_CUE) & filled.str.contains(CLOSE_CUE)


def cue_both_positives(
    resolutions: pd.DataFrame,
    *,
    year_min: int,
    year_max: int,
    exclude_ids: Sequence[str] | None = None,
) -> pd.DataFrame:
    """Rows in the year window that match open+close cues, minus exclusions."""
    _require_flat(resolutions)
    excluded = set(map(str, exclude_ids or ()))
    in_years = resolutions["year"].between(year_min, year_max)
    both = open_close_mask(resolutions["resolutions_text"])
    keep = in_years & both & ~resolutions["id"].astype(str).isin(excluded)
    keep &= resolutions["resolutions_text"].fillna("").astype(str).str.strip().ne("")
    out = resolutions.loc[keep].copy()
    out["positive_source"] = SOURCE_CUE_BOTH
    return out


def match_hand_seeds(
    resolutions: pd.DataFrame,
    seeds: Sequence[dict] | pd.DataFrame,
    *,
    exclude_ids: Sequence[str] | None = None,
) -> tuple[pd.DataFrame, list[dict]]:
    """Exact normalized-text matches for hand seeds; return (hits, unmatched seeds)."""
    _require_flat(resolutions)
    seed_rows = _seeds_frame(seeds)
    if seed_rows.empty:
        return resolutions.iloc[0:0].copy(), []

    excluded = set(map(str, exclude_ids or ()))
    flat = resolutions.loc[
        ~resolutions["id"].astype(str).isin(excluded)
        & resolutions["resolutions_text"].fillna("").astype(str).str.strip().ne("")
    ].copy()
    flat["_norm"] = flat["resolutions_text"].map(normalize_text)
    by_norm = flat.drop_duplicates(subset=["_norm"], keep="first").set_index("_norm")

    hits: list[pd.DataFrame] = []
    unmatched: list[dict] = []
    for _, seed in seed_rows.iterrows():
        norm = normalize_text(seed.get("text", ""))
        if not norm:
            continue
        if norm in by_norm.index:
            row = by_norm.loc[[norm]].copy()
            row["positive_source"] = SOURCE_HAND_SEED
            row["seed_note"] = seed.get("note", "")
            hits.append(row.drop(columns=["_norm"], errors="ignore"))
        else:
            unmatched.append(
                {
                    "text": str(seed.get("text", "")),
                    "note": str(seed.get("note", "")),
                    "source": str(seed.get("source", "hand")),
                }
            )
    if not hits:
        return resolutions.iloc[0:0].copy(), unmatched
    matched = pd.concat(hits, ignore_index=True)
    matched = matched.drop_duplicates(subset=["id"], keep="first")
    return matched, unmatched


def unmatched_seed_rows(unmatched: Sequence[dict]) -> pd.DataFrame:
    """Synthetic positive rows for hand seeds with no corpus text match."""
    if not unmatched:
        return pd.DataFrame(
            columns=list(REQUIRED_FLAT_COLS) + ["type", "weekday", "paragraph_texts", "positive_source", "seed_note"]
        )
    rows = []
    for i, seed in enumerate(unmatched):
        rows.append(
            {
                "id": f"hand_seed:{i}",
                "type": "",
                "date": "",
                "year": pd.NA,
                "weekday": "",
                "paragraph_texts": "",
                "resolutions_text": seed["text"],
                "positive_source": SOURCE_HAND_SEED,
                "seed_note": seed.get("note", ""),
            }
        )
    return pd.DataFrame(rows)


def merge_positives(cue_hits: pd.DataFrame, seed_hits: pd.DataFrame) -> pd.DataFrame:
    """Union cue and seed positives; combine ``positive_source`` on id overlap."""
    if cue_hits.empty and seed_hits.empty:
        raise ValueError("No missive-receipt positives (cue both-hits or seeds)")
    if cue_hits.empty:
        return seed_hits.copy()
    if seed_hits.empty:
        return cue_hits.copy()

    cue = cue_hits.copy()
    seed = seed_hits.copy()
    cue_ids = set(cue["id"].astype(str))
    seed_ids = set(seed["id"].astype(str))
    both_ids = cue_ids & seed_ids

    cue.loc[cue["id"].astype(str).isin(both_ids), "positive_source"] = (
        f"{SOURCE_CUE_BOTH};{SOURCE_HAND_SEED}"
    )
    seed_only = seed.loc[~seed["id"].astype(str).isin(cue_ids)]
    return pd.concat([cue, seed_only], ignore_index=True)


def build_labelled_table(
    resolutions: pd.DataFrame,
    seeds: Sequence[dict] | pd.DataFrame,
    *,
    exclude_ids: Sequence[str] | None = None,
    year_min: int,
    year_max: int,
    overig_per_positive: int = OVERIG_PER_POSITIVE,
    random_state: int = RANDOM_STATE,
    include_unmatched_seeds: bool = True,
) -> pd.DataFrame:
    """Missive-receipt positives + 10× overig in ``[year_min, year_max]``.

    Excludes ``exclude_ids`` (typically ``aanstelling_selected``) from positives only.
    """
    _require_flat(resolutions)
    if year_min > year_max:
        raise ValueError(f"year_min ({year_min}) > year_max ({year_max})")

    cue = cue_both_positives(
        resolutions,
        year_min=year_min,
        year_max=year_max,
        exclude_ids=exclude_ids,
    )
    seed_hits, unmatched = match_hand_seeds(
        resolutions, seeds, exclude_ids=exclude_ids
    )
    # Keep seed matches even outside the year window (true exemplars).
    positives = merge_positives(cue, seed_hits)
    if include_unmatched_seeds and unmatched:
        positives = pd.concat(
            [positives, unmatched_seed_rows(unmatched)], ignore_index=True
        )

    corpus_pos = positives.loc[~positives["id"].astype(str).str.startswith("hand_seed:")]
    if corpus_pos.empty:
        # Only synthetic seeds — still need an overig year window from args.
        overig_year_min, overig_year_max = year_min, year_max
    else:
        years = pd.to_numeric(corpus_pos["year"], errors="coerce").dropna()
        overig_year_min = int(years.min()) if not years.empty else year_min
        overig_year_max = int(years.max()) if not years.empty else year_max
        # Stay inside the requested window for overig sampling.
        overig_year_min = max(overig_year_min, year_min)
        overig_year_max = min(overig_year_max, year_max)

    n_overig = overig_per_positive * len(positives)
    overig = sample_overig(
        resolutions,
        positives["id"].astype(str),
        n=n_overig,
        year_min=overig_year_min,
        year_max=overig_year_max,
        random_state=random_state,
    )

    positive_out = _with_label_fields(positives, label=LABEL_MISSIVE)
    overig_out = _with_label_fields(overig.assign(positive_source=""), label=LABEL_OVERIG)
    labelled = pd.concat([positive_out, overig_out], ignore_index=True)

    overlap = labelled.loc[labelled["label"].eq(LABEL_OVERIG), "id"].isin(
        labelled.loc[labelled["label"].eq(LABEL_MISSIVE), "id"]
    )
    if overlap.any():
        raise ValueError("Overig sample leaked missive-receipt positive ids")

    excluded = set(map(str, exclude_ids or ()))
    leaked = labelled.loc[
        labelled["label"].eq(LABEL_MISSIVE)
        & labelled["id"].astype(str).isin(excluded)
        & ~labelled["id"].astype(str).str.startswith("hand_seed:")
    ]
    if not leaked.empty:
        raise ValueError(
            "Positives include excluded aanstelling ids: "
            f"{leaked['id'].astype(str).head(3).tolist()}"
        )
    return labelled


def _seeds_frame(seeds: Sequence[dict] | pd.DataFrame) -> pd.DataFrame:
    if isinstance(seeds, pd.DataFrame):
        frame = seeds.copy()
    else:
        frame = pd.DataFrame(list(seeds))
    if frame.empty:
        return pd.DataFrame(columns=["text", "note", "source"])
    if "text" not in frame.columns:
        raise ValueError("Seeds need a text column")
    return frame


def _require_flat(resolutions: pd.DataFrame) -> None:
    missing = [c for c in REQUIRED_FLAT_COLS if c not in resolutions.columns]
    if missing:
        raise ValueError(f"resolutions_flat missing columns: {missing}")


def _with_label_fields(frame: pd.DataFrame, *, label: str) -> pd.DataFrame:
    out = frame.copy()
    from_id = out["id"].map(inventory_from_id)
    if "inventory" in out.columns:
        existing = out["inventory"].astype("string").str.strip()
        out["inventory"] = existing.where(existing.notna() & existing.ne(""), from_id)
    else:
        out["inventory"] = from_id
    for col in LABEL_COLS:
        if col == "label":
            continue
        if col not in out.columns:
            out[col] = ""
        else:
            out[col] = out[col].fillna("")
    out["label"] = label
    parquet_cols = [c for c in frame.columns if c not in LABEL_COLS]
    ordered = [c for c in parquet_cols if c in out.columns] + [c for c in LABEL_COLS]
    extra = [c for c in out.columns if c not in ordered]
    return out.loc[:, ordered + extra]
