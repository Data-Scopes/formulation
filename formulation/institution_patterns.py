"""Period-/inventory-keyed institution surface patterns.

Loads ``institution_patterns`` via data_io (ORG harvest scratch, or fixture
seeds when harvest is absent). Appointment subtype rows keep
``discriminators: [\"institution\"]`` + ``institution_targets``; this module
supplies empirical spellings. Streaming harvest lives in
``formulation.institution_pattern_harvest``.
Pattern surfaces live here, not in ``formula_templates``.
"""

from __future__ import annotations

import re
from collections.abc import Iterable, Mapping, Sequence
from typing import Any

from data_io import load

LOGICAL_NAME = "institution_patterns"
SEEDS_LOGICAL_NAME = "institution_patterns_seeds"

# Soft map: registry institution_target → preferred ORG-entity id(s).
# gecommitteerde_raaden has no dedicated entity in ORG-entities yet.
TARGET_ORG_ENTITIES: dict[str, tuple[str, ...]] = {
    "rekenkamer": ("O0000072",),
    "staten_generael_vergadering": ("O0012259",),
    "raad_van_state": ("O0000167",),
    "admirality": (
        "O0000003",
        "O0000004",
        "O0000005",
        "O0000006",
        "O0000007",
        "O0000073",
    ),
    "gecommitteerde_raaden": (),
}

# First match in this order wins as primary institution (appointment gate).
PRIMARY_ORDER = (
    "rekenkamer",
    "admirality",
    "raad_van_state",
    "gecommitteerde_raaden",
    "staten_generael_vergadering",
)

REQUIRED_KEYS = (
    "institution_target",
    "pattern",
    "inv",
    "year_min",
    "year_max",
    "n",
    "source",
)


def validate_pattern(row: Mapping[str, Any]) -> None:
    """Raise ValueError if a pattern row is missing required shape."""
    missing = [k for k in REQUIRED_KEYS if k not in row]
    if missing:
        raise ValueError(f"institution_pattern missing keys {missing}")

    target = row["institution_target"]
    if not isinstance(target, str) or not target.strip():
        raise ValueError(f"institution_target must be non-empty str, got {target!r}")

    pattern = row["pattern"]
    if not isinstance(pattern, str) or not pattern.strip():
        raise ValueError(f"{target}: pattern must be non-empty str")

    inv = row["inv"]
    if inv is not None and not isinstance(inv, int):
        raise ValueError(f"{target}: inv must be int or null, got {inv!r}")

    for key in ("year_min", "year_max"):
        val = row[key]
        if val is not None and not isinstance(val, int):
            raise ValueError(f"{target}: {key} must be int or null, got {val!r}")

    n = row["n"]
    if not isinstance(n, int) or n < 1:
        raise ValueError(f"{target}: n must be positive int, got {n!r}")

    if not isinstance(row["source"], str) or not row["source"].strip():
        raise ValueError(f"{target}: source must be non-empty str")

    eid = row.get("org_entity_id")
    if eid is not None and (not isinstance(eid, str) or not eid.strip()):
        raise ValueError(f"{target}: org_entity_id must be str or null")


def validate_patterns(rows: Sequence[Mapping[str, Any]]) -> None:
    for row in rows:
        validate_pattern(row)


def load_patterns(
    *,
    logical_name: str = LOGICAL_NAME,
    rows: Sequence[Mapping[str, Any]] | None = None,
    validate: bool = True,
) -> list[dict[str, Any]]:
    """Load pattern rows from data_io or an in-memory sequence.

    When ``logical_name`` is the default harvest dataset and the scratch file
    is missing, fall back to ``institution_patterns_seeds`` (fixture).
    """
    if rows is None:
        try:
            loaded = load(logical_name)
        except FileNotFoundError:
            if logical_name != LOGICAL_NAME:
                raise
            loaded = load(SEEDS_LOGICAL_NAME)
        if not isinstance(loaded, list):
            raise TypeError(f"{logical_name} must load as list[dict], got {type(loaded)}")
        out = [dict(r) for r in loaded]
    else:
        out = [dict(r) for r in rows]
    if validate:
        validate_patterns(out)
    return out


def _year_overlaps(
    row: Mapping[str, Any],
    *,
    year: int | None,
) -> bool:
    if year is None:
        return True
    y0 = row.get("year_min")
    y1 = row.get("year_max")
    if y0 is None and y1 is None:
        return True
    lo = y0 if y0 is not None else y1
    hi = y1 if y1 is not None else y0
    assert lo is not None and hi is not None
    return int(lo) <= year <= int(hi)


def patterns_for_target(
    institution_target: str,
    *,
    year: int | None = None,
    inv: int | None = None,
    logical_name: str = LOGICAL_NAME,
    rows: Sequence[Mapping[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    """Return patterns for one registry target, optionally filtered by year/inv."""
    out: list[dict[str, Any]] = []
    for row in load_patterns(logical_name=logical_name, rows=rows):
        if row["institution_target"] != institution_target:
            continue
        if inv is not None and row.get("inv") is not None and int(row["inv"]) != inv:
            continue
        if not _year_overlaps(row, year=year):
            continue
        out.append(row)
    return out


def org_entity_ids_for_target(institution_target: str) -> tuple[str, ...]:
    """Known ORG-entity ids for a registry institution_target (may be empty)."""
    return TARGET_ORG_ENTITIES.get(institution_target, ())


def index_by_target(
    rows: Iterable[Mapping[str, Any]] | None = None,
    *,
    logical_name: str = LOGICAL_NAME,
) -> dict[str, list[dict[str, Any]]]:
    """Group pattern rows by institution_target."""
    loaded = load_patterns(logical_name=logical_name, rows=rows)
    by: dict[str, list[dict[str, Any]]] = {}
    for row in loaded:
        by.setdefault(str(row["institution_target"]), []).append(row)
    return by


def pattern_to_regex(pattern: str) -> re.Pattern[str]:
    """Compile a surface string: case-insensitive, flexible whitespace."""
    parts = [p for p in re.split(r"\s+", pattern.strip()) if p]
    if not parts:
        raise ValueError("empty pattern")
    body = r"\s+".join(re.escape(p) for p in parts)
    return re.compile(body, re.IGNORECASE)


def dedupe_pattern_rows(
    rows: Sequence[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    """Collapse inv-duplicates to one row per ``(target, pattern)`` (casefold).

    Keeps the row with the highest ``n``; ties keep the first seen.
    """
    best: dict[tuple[str, str], dict[str, Any]] = {}
    order: list[tuple[str, str]] = []
    for row in rows:
        key = (
            str(row["institution_target"]),
            str(row["pattern"]).casefold(),
        )
        prev = best.get(key)
        if prev is None:
            best[key] = dict(row)
            order.append(key)
            continue
        if int(row.get("n") or 0) > int(prev.get("n") or 0):
            best[key] = dict(row)
    return [best[k] for k in order]


def _rows_in_scope(
    rows: Sequence[Mapping[str, Any]],
    *,
    year: int | None,
    inv: int | None,
) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for row in rows:
        if inv is not None and row.get("inv") is not None and int(row["inv"]) != inv:
            continue
        if not _year_overlaps(row, year=year):
            continue
        out.append(dict(row))
    return out


def extract_institutions(
    text: str,
    *,
    year: int | None = None,
    inv: int | None = None,
    logical_name: str = LOGICAL_NAME,
    rows: Sequence[Mapping[str, Any]] | None = None,
) -> list[tuple[str, str]]:
    """Return ``(institution_target, matched_span)`` hits in text order.

    Uses period-/inventory-filtered surfaces from ``institution_patterns``.
    Dedupes unique surfaces after scoping. Does not read ``formula_templates``.
    """
    loaded = load_patterns(logical_name=logical_name, rows=rows)
    scoped = dedupe_pattern_rows(_rows_in_scope(loaded, year=year, inv=inv))
    hits: list[tuple[str, str]] = []
    blob = str(text or "")
    for row in scoped:
        pat = pattern_to_regex(str(row["pattern"]))
        target = str(row["institution_target"])
        for match in pat.finditer(blob):
            span = re.sub(r"\s+", " ", match.group(0)).strip()[:80]
            hits.append((target, span))
    return hits


def primary_institution(hits: Sequence[tuple[str, str]]) -> str:
    """Pick one primary target from hits using ``PRIMARY_ORDER``."""
    by_label = {lab: span for lab, span in hits}
    for lab in PRIMARY_ORDER:
        if lab in by_label:
            return lab
    if by_label:
        return next(iter(by_label))
    return "none"
