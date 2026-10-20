"""Stream-aggregate republic_ner ORG annotations into institution_patterns rows.

Does not load the full ~650MB annotations JSON into memory. Filters to
``TARGET_ORG_ENTITIES`` ids; period keys come from inventory metadata.
"""

from __future__ import annotations

import json
from collections import Counter
from collections.abc import Iterable, Iterator, Mapping, Sequence
from pathlib import Path
from typing import Any

from data_io import load, resolve
from formulation.institution_patterns import (
    TARGET_ORG_ENTITIES,
    validate_patterns,
)

ANNOTATIONS_LOGICAL = "org_annotations"
ENTITIES_LOGICAL = "org_entities"
INVENTORY_LOGICAL = "inventory_metadata"
SEEDS_LOGICAL = "institution_patterns_seeds"
SOURCE_HARVEST = "org_annotations"


def entity_to_targets() -> dict[str, str]:
    """Reverse map: ORG-entity id → registry institution_target (first wins)."""
    out: dict[str, str] = {}
    for target, eids in TARGET_ORG_ENTITIES.items():
        for eid in eids:
            out.setdefault(str(eid), target)
    return out


def normalize_tag_text(text: str) -> str:
    return " ".join(str(text or "").split())


def normalize_entity_id(raw: Any) -> str:
    """Accept bare ``O0000072`` or ``urn:republic:entity:O0000072``."""
    s = str(raw or "").strip()
    if not s:
        return ""
    if "entity:" in s:
        return s.rsplit(":", 1)[-1].strip()
    return s


def iter_json_array(path: Path | str) -> Iterator[Any]:
    """Yield values from a top-level JSON array without full-file load."""
    decoder = json.JSONDecoder()
    path = Path(path)
    with path.open("r", encoding="utf-8") as handle:
        buf = ""
        while True:
            chunk = handle.read(65536)
            if not chunk:
                raise ValueError(f"{path}: expected JSON array, got EOF")
            buf += chunk
            i = 0
            while i < len(buf) and buf[i].isspace():
                i += 1
            if i >= len(buf):
                continue
            if buf[i] != "[":
                raise ValueError(f"{path}: expected '[', got {buf[i]!r}")
            buf = buf[i + 1 :]
            break

        while True:
            while True:
                j = 0
                while j < len(buf) and buf[j].isspace():
                    j += 1
                if j < len(buf):
                    if buf[j] == "]":
                        return
                    if buf[j] == ",":
                        buf = buf[j + 1 :]
                        continue
                    buf = buf[j:]
                    break
                chunk = handle.read(65536)
                if not chunk:
                    return
                buf += chunk

            while True:
                try:
                    obj, idx = decoder.raw_decode(buf)
                    yield obj
                    buf = buf[idx:]
                    break
                except json.JSONDecodeError:
                    chunk = handle.read(65536)
                    if not chunk:
                        raise ValueError(f"{path}: truncated JSON array") from None
                    buf += chunk


def load_entity_names(
    *,
    logical_name: str = ENTITIES_LOGICAL,
    rows: Sequence[Mapping[str, Any]] | None = None,
) -> dict[str, str]:
    if rows is None:
        loaded = load(logical_name)
        if not isinstance(loaded, list):
            raise TypeError(f"{logical_name} must be list, got {type(loaded)}")
        rows = loaded
    out: dict[str, str] = {}
    for row in rows:
        eid = normalize_entity_id(row.get("id"))
        name = str(row.get("name") or "").strip()
        if eid and name:
            out[eid] = name
    return out


def load_inventory_years(
    *,
    logical_name: str = INVENTORY_LOGICAL,
    rows: Sequence[Mapping[str, Any]] | None = None,
) -> dict[int, tuple[int | None, int | None]]:
    """Map inventory_num → (year_min, year_max)."""
    if rows is None:
        loaded = load(logical_name)
        if not isinstance(loaded, list):
            raise TypeError(f"{logical_name} must be list, got {type(loaded)}")
        rows = loaded
    out: dict[int, tuple[int | None, int | None]] = {}
    for row in rows:
        raw_inv = row.get("inventory_num", row.get("inv"))
        try:
            inv = int(raw_inv)
        except (TypeError, ValueError):
            continue
        y0 = row.get("year_start", row.get("year"))
        y1 = row.get("year_end", row.get("year"))
        try:
            lo = int(y0) if y0 is not None else None
        except (TypeError, ValueError):
            lo = None
        try:
            hi = int(y1) if y1 is not None else None
        except (TypeError, ValueError):
            hi = None
        out[inv] = (lo, hi)
    return out


def _parse_inv(raw: Any) -> int | None:
    if raw is None or str(raw).strip() == "":
        return None
    try:
        return int(raw)
    except (TypeError, ValueError):
        return None


def stream_target_mentions(
    annotations_path: Path | str,
    *,
    entity_targets: Mapping[str, str] | None = None,
    limit: int | None = None,
) -> Iterator[tuple[str, str, int | None, str]]:
    """Yield ``(institution_target, org_entity_id, inv, tag_text)`` for mapped entities."""
    mapping = dict(entity_targets) if entity_targets is not None else entity_to_targets()
    n = 0
    for obj in iter_json_array(annotations_path):
        if limit is not None and n >= limit:
            return
        n += 1
        if not isinstance(obj, dict):
            continue
        eid = normalize_entity_id(obj.get("entity"))
        target = mapping.get(eid)
        if target is None:
            continue
        ref = obj.get("reference") or {}
        if not isinstance(ref, dict):
            continue
        tag = normalize_tag_text(str(ref.get("tag_text") or ""))
        if not tag:
            continue
        yield target, eid, _parse_inv(ref.get("inv")), tag


def aggregate_mentions(
    mentions: Iterable[tuple[str, str, int | None, str]],
    *,
    entity_names: Mapping[str, str],
    inventory_years: Mapping[int, tuple[int | None, int | None]],
    min_n: int = 1,
) -> list[dict[str, Any]]:
    """Collapse mentions to pattern rows keyed by target × entity × inv × surface."""
    counts: Counter[tuple[str, str, int | None, str]] = Counter()
    for target, eid, inv, tag in mentions:
        counts[(target, eid, inv, tag)] += 1

    rows: list[dict[str, Any]] = []
    for (target, eid, inv, tag), n in sorted(
        counts.items(),
        key=lambda item: (-item[1], item[0][0], item[0][2] or 0, item[0][3]),
    ):
        if n < min_n:
            continue
        y0 = y1 = None
        if inv is not None and inv in inventory_years:
            y0, y1 = inventory_years[inv]
        rows.append(
            {
                "institution_target": target,
                "org_entity_id": eid,
                "org_entity_name": entity_names.get(eid),
                "pattern": tag,
                "inv": inv,
                "year_min": y0,
                "year_max": y1,
                "n": int(n),
                "source": SOURCE_HARVEST,
                "notes": None,
            }
        )
    validate_patterns(rows)
    return rows


def load_seed_rows(
    *,
    logical_name: str = SEEDS_LOGICAL,
) -> list[dict[str, Any]]:
    loaded = load(logical_name)
    if not isinstance(loaded, list):
        raise TypeError(f"{logical_name} must be list, got {type(loaded)}")
    return [dict(r) for r in loaded]


def merge_with_seeds(
    harvest_rows: Sequence[Mapping[str, Any]],
    seed_rows: Sequence[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    """Append seed rows whose (target, pattern, inv) is not already harvested."""
    seen = {
        (
            str(r["institution_target"]),
            normalize_tag_text(str(r["pattern"])),
            r.get("inv"),
        )
        for r in harvest_rows
    }
    out = [dict(r) for r in harvest_rows]
    for seed in seed_rows:
        key = (
            str(seed["institution_target"]),
            normalize_tag_text(str(seed["pattern"])),
            seed.get("inv"),
        )
        if key in seen:
            continue
        out.append(dict(seed))
        seen.add(key)
    validate_patterns(out)
    return out


def harvest_institution_patterns(
    *,
    annotations_path: Path | str | None = None,
    entity_names: Mapping[str, str] | None = None,
    inventory_years: Mapping[int, tuple[int | None, int | None]] | None = None,
    min_n: int = 1,
    limit: int | None = None,
    with_seeds: bool = True,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Stream ORG annotations → pattern rows + summary metrics."""
    path = Path(annotations_path) if annotations_path else resolve(ANNOTATIONS_LOGICAL)
    names = dict(entity_names) if entity_names is not None else load_entity_names()
    years = (
        dict(inventory_years)
        if inventory_years is not None
        else load_inventory_years()
    )
    mapping = entity_to_targets()
    mentions = stream_target_mentions(
        path,
        entity_targets=mapping,
        limit=limit,
    )
    harvest_rows = aggregate_mentions(
        mentions,
        entity_names=names,
        inventory_years=years,
        min_n=min_n,
    )
    if with_seeds:
        rows = merge_with_seeds(harvest_rows, load_seed_rows())
    else:
        rows = harvest_rows

    by_target: Counter[str] = Counter(str(r["institution_target"]) for r in harvest_rows)
    metrics: dict[str, Any] = {
        "n_harvest_rows": len(harvest_rows),
        "n_rows_with_seeds": len(rows),
        "n_targets": len(by_target),
        "rows_per_target": dict(sorted(by_target.items())),
        "min_n": min_n,
        "limit": limit,
        "with_seeds": with_seeds,
        "annotations_path": str(path),
        "entity_ids": sorted(mapping),
        "source": SOURCE_HARVEST,
    }
    return rows, metrics
