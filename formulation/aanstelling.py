"""Join gold aanstelling URNs onto resolutions_flat (Track R).

Whole-resolution labels only. Does not call FormulaSearch or Elasticsearch.
"""

from __future__ import annotations

import re
from collections.abc import Sequence
from typing import Any

import pandas as pd

# Full token (findall) vs named parts (id construction). Groups would make
# findall return tuples instead of URN strings.
URN_TOKEN = re.compile(
    r"urn:republic:inv-\d+-date-\d{4}-\d{2}-\d{2}-session-\d+-resolution-\d+"
)
URN_PARTS = re.compile(
    r"urn:republic:inv-(?P<inv>\d+)-date-(?P<date>\d{4}-\d{2}-\d{2})"
    r"-session-(?P<session>\d+)-resolution-(?P<resolution>\d+)$"
)
ID_INVENTORY = re.compile(r"^session-(?P<inv>\d+)-num-")

OVERIG_PER_POSITIVE = 10
RANDOM_STATE = 42
LABEL_AANSTELLING = "aanstelling"
LABEL_OVERIG = "overig"
RECOVERY_NAIVE = "naive_date_match"
RECOVERY_KEEP_NAIVE = "urn_date_absent_keep_naive_id"

REQUIRED_FLAT_COLS = ("id", "date", "year", "resolutions_text")
LABEL_COLS = (
    "label",
    "inventory",
    "gold_urns",
    "delegate_ids",
    "delegate_fullnames",
    "naive_id",
    "urn_date",
    "join_recovery",
)


def extract_urns(cell: object) -> list[str]:
    """Pull well-formed republic URNs out of a spreadsheet cell.

    Handles trailing ``;``, semicolon-separated lists (with or without spaces),
    and goetgevonden.nl URLs with query strings. Does not invent URNs.
    """
    if cell is None or (isinstance(cell, float) and pd.isna(cell)):
        return []
    return URN_TOKEN.findall(str(cell))


def naive_id_from_urn(urn: str) -> str:
    """Map ``urn:republic:inv-{inv}-date-…-session-{num}-resolution-{k}`` to parquet id."""
    match = URN_PARTS.match(urn.strip())
    if match is None:
        raise ValueError(f"Not a well-formed republic resolution URN: {urn!r}")
    return (
        f"session-{match.group('inv')}-num-{match.group('session')}"
        f"-resolution-{match.group('resolution')}"
    )


def urn_date(urn: str) -> str:
    match = URN_PARTS.match(urn.strip())
    if match is None:
        raise ValueError(f"Not a well-formed republic resolution URN: {urn!r}")
    return match.group("date")


def inventory_from_id(resolution_id: object) -> str:
    if resolution_id is None or (isinstance(resolution_id, float) and pd.isna(resolution_id)):
        return ""
    match = ID_INVENTORY.match(str(resolution_id))
    return match.group("inv") if match else ""


def _join_unique(series: pd.Series) -> str:
    values: list[str] = []
    seen: set[str] = set()
    for raw in series:
        if raw is None or (isinstance(raw, float) and pd.isna(raw)):
            continue
        text = str(raw).strip()
        if not text or text == "nan":
            continue
        if text not in seen:
            seen.add(text)
            values.append(text)
    return "; ".join(sorted(values))


def _relocations_frame(relocations: Sequence[dict[str, Any]] | pd.DataFrame) -> pd.DataFrame:
    reloc = pd.DataFrame(relocations)
    if reloc.empty:
        return pd.DataFrame(columns=["urn", "recovered_id", "recovery", "naive_id"])
    missing = {"urn", "recovered_id", "recovery"} - set(reloc.columns)
    if missing:
        raise ValueError(f"Relocations missing columns: {sorted(missing)}")
    return reloc.loc[:, [c for c in ("urn", "recovered_id", "recovery", "naive_id") if c in reloc.columns]]


def gold_urn_rows(gold: pd.DataFrame) -> pd.DataFrame:
    """One row per (delegate, URN) from ``resolutie_refs``. Vectorized explode."""
    if "resolutie_refs" not in gold.columns:
        raise ValueError("Gold table needs a resolutie_refs column")

    refs = gold["resolutie_refs"].fillna("").astype(str)
    has_republic = refs.str.contains("urn:republic:", regex=False)
    extracted = refs.str.findall(URN_TOKEN.pattern)
    unparsed = has_republic & extracted.str.len().eq(0)
    if unparsed.any():
        samples = refs.loc[unparsed].head(3).tolist()
        raise ValueError(
            "resolutie_refs cell contains urn:republic: but no well-formed "
            f"resolution URN (examples: {samples})"
        )

    delegate = gold["delegate_id"].astype("string") if "delegate_id" in gold.columns else pd.Series(pd.NA, index=gold.index, dtype="string")
    if "cons_id_str" in gold.columns:
        delegate = delegate.fillna(gold["cons_id_str"].astype("string"))
    fullname = gold["fullname"].astype("string") if "fullname" in gold.columns else pd.Series(pd.NA, index=gold.index, dtype="string")

    rows = gold.assign(
        gold_urn=extracted,
        delegate_id=delegate,
        fullname=fullname,
    ).explode("gold_urn", ignore_index=True)
    rows = rows.loc[rows["gold_urn"].notna() & rows["gold_urn"].astype(str).str.strip().ne("")]
    if rows.empty:
        raise ValueError("No well-formed republic URNs in resolutie_refs")

    parts = rows["gold_urn"].str.extract(URN_PARTS.pattern)
    if parts.isna().any().any():
        bad = rows.loc[parts.isna().any(axis=1), "gold_urn"].head(3).tolist()
        raise ValueError(f"URN extract failed for {bad}")
    rows = rows.assign(
        naive_id=(
            "session-"
            + parts["inv"]
            + "-num-"
            + parts["session"]
            + "-resolution-"
            + parts["resolution"]
        ),
        urn_date=parts["date"],
        inventory=parts["inv"],
    )
    return rows


def assign_recovered_ids(
    urn_rows: pd.DataFrame,
    relocations: Sequence[dict[str, Any]] | pd.DataFrame,
) -> pd.DataFrame:
    """Naive parquet id, overridden by ``aanstelling_gold_relocations`` when present."""
    reloc = _relocations_frame(relocations)
    reloc_keep = reloc.loc[:, ["urn", "recovered_id", "recovery"]].rename(
        columns={"recovered_id": "reloc_recovered_id", "recovery": "reloc_recovery"}
    )
    merged = urn_rows.merge(reloc_keep, how="left", left_on="gold_urn", right_on="urn")
    recovered_id = merged["reloc_recovered_id"].astype("string")
    recovered_id = recovered_id.where(recovered_id.notna(), merged["naive_id"].astype("string"))
    join_recovery = merged["reloc_recovery"].astype("string")
    join_recovery = join_recovery.where(join_recovery.notna(), RECOVERY_NAIVE)
    return merged.assign(recovered_id=recovered_id, join_recovery=join_recovery).drop(
        columns=["urn", "reloc_recovered_id", "reloc_recovery"],
        errors="ignore",
    )


def aggregate_gold_resolutions(assigned: pd.DataFrame) -> pd.DataFrame:
    """One labelled-positive row per recovered parquet id; keep all URNs and delegates."""
    grouped = assigned.groupby("recovered_id", sort=True, dropna=False)
    out = grouped.agg(
        gold_urns=("gold_urn", _join_unique),
        delegate_ids=("delegate_id", _join_unique),
        delegate_fullnames=("fullname", _join_unique),
        naive_id=("naive_id", _join_unique),
        urn_date=("urn_date", "first"),
        inventory=("inventory", "first"),
        join_recovery=("join_recovery", "first"),
    ).reset_index()
    return out


def _require_flat(resolutions: pd.DataFrame) -> None:
    missing = [c for c in REQUIRED_FLAT_COLS if c not in resolutions.columns]
    if missing:
        raise ValueError(f"resolutions_flat missing columns: {missing}")


def join_gold_text(
    resolutions: pd.DataFrame,
    gold_resolutions: pd.DataFrame,
) -> pd.DataFrame:
    """Attach parquet text to gold recovered ids. Raises if a gold id has no row."""
    _require_flat(resolutions)
    joined = gold_resolutions.merge(
        resolutions,
        how="left",
        left_on="recovered_id",
        right_on="id",
        suffixes=("_gold", ""),
    )
    missing = joined["id"].isna()
    if missing.any():
        ids = joined.loc[missing, "recovered_id"].tolist()
        raise ValueError(
            "Gold recovered_id not in resolutions_flat; do not invent text. "
            f"Missing ({len(ids)}): {ids[:5]}"
        )
    empty_text = joined["resolutions_text"].fillna("").astype(str).str.strip().eq("")
    if empty_text.any():
        ids = joined.loc[empty_text, "id"].tolist()
        raise ValueError(
            "Gold resolution has empty resolutions_text; do not invent text. "
            f"Ids ({len(ids)}): {ids[:5]}"
        )
    return joined


def assert_naive_dates_match(positives: pd.DataFrame) -> None:
    """URN date must equal parquet ``date``, except the one keep-naive 1685 case."""
    check = positives["join_recovery"].ne(RECOVERY_KEEP_NAIVE)
    parquet_date = positives["date"].astype(str)
    urn_dates = positives["urn_date"].astype(str)
    mismatch = check & parquet_date.ne(urn_dates)
    if mismatch.any():
        sample = positives.loc[mismatch, ["id", "date", "urn_date", "gold_urns"]].head(3)
        raise ValueError(
            "Gold id has parquet date ≠ URN date; relocate instead of inventing "
            f"text. Examples:\n{sample.to_string(index=False)}"
        )


def sample_overig(
    resolutions: pd.DataFrame,
    gold_ids: Sequence[str],
    *,
    n: int,
    year_min: int,
    year_max: int,
    random_state: int = RANDOM_STATE,
) -> pd.DataFrame:
    """Random overig sample in the gold year window, excluding gold ids."""
    _require_flat(resolutions)
    gold_id_set = set(map(str, gold_ids))
    pool = resolutions.loc[
        ~resolutions["id"].astype(str).isin(gold_id_set)
        & resolutions["year"].between(year_min, year_max)
        & resolutions["resolutions_text"].fillna("").astype(str).str.strip().ne("")
    ]
    if pool.empty:
        raise ValueError("No overig rows left in the gold year window")
    take = min(int(n), len(pool))
    return pool.sample(n=take, random_state=random_state)


def _with_label_fields(frame: pd.DataFrame, *, label: str) -> pd.DataFrame:
    out = frame.drop(columns=["recovered_id"], errors="ignore").copy()
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
    parquet_cols = [c for c in frame.columns if c not in LABEL_COLS and c != "recovered_id"]
    ordered = [c for c in parquet_cols if c in out.columns] + [c for c in LABEL_COLS]
    extra = [c for c in out.columns if c not in ordered]
    return out.loc[:, ordered + extra]


def build_labelled_table(
    resolutions: pd.DataFrame,
    gold: pd.DataFrame,
    relocations: Sequence[dict[str, Any]] | pd.DataFrame,
    *,
    overig_per_positive: int = OVERIG_PER_POSITIVE,
    random_state: int = RANDOM_STATE,
) -> pd.DataFrame:
    """Aanstelling positives (all gold URNs) plus a sample of overig.

    One row per ``resolutions_flat`` id. Scoring text is ``resolutions_text``.
    """
    _require_flat(resolutions)
    urn_rows = gold_urn_rows(gold)
    assigned = assign_recovered_ids(urn_rows, relocations)
    gold_resolutions = aggregate_gold_resolutions(assigned)
    positives = join_gold_text(resolutions, gold_resolutions)
    assert_naive_dates_match(positives)

    year_min = int(positives["year"].min())
    year_max = int(positives["year"].max())
    n_overig = overig_per_positive * len(positives)
    overig = sample_overig(
        resolutions,
        positives["id"].astype(str),
        n=n_overig,
        year_min=year_min,
        year_max=year_max,
        random_state=random_state,
    )

    positive_out = _with_label_fields(positives, label=LABEL_AANSTELLING)
    overig_out = _with_label_fields(overig, label=LABEL_OVERIG)
    labelled = pd.concat([positive_out, overig_out], ignore_index=True)

    overlap = labelled.loc[labelled["label"].eq(LABEL_OVERIG), "id"].isin(
        labelled.loc[labelled["label"].eq(LABEL_AANSTELLING), "id"]
    )
    if overlap.any():
        raise ValueError("Overig sample leaked gold resolution ids")
    return labelled
