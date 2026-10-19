"""Formula template registry loader (manifest stub).

Loads `formula_templates` via data_io. Validates schema fields from the
multi-template prove-first; does not harvest institution_patterns yet.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from typing import Any

from data_io import load

LOGICAL_NAME = "formula_templates"

ROLES = frozenset({"framing", "doc_flag", "appointment_subtype", "residual"})

REQUIRED_KEYS = (
    "template_id",
    "role",
    "period",
    "year_min",
    "year_max",
    "tokens",
    "threshold",
    "threshold_frozen",
    "zones_hypothesized",
    "function",
    "intention",
    "nlp_start_marker",
    "outcome_signal",
    "role_depends_on_place",
    "resolution_parts",
    "discriminators",
    "notes",
    "seed_refs",
)

BOOL_KEYS = (
    "threshold_frozen",
    "nlp_start_marker",
    "outcome_signal",
    "role_depends_on_place",
)


def validate_template(row: Mapping[str, Any]) -> None:
    """Raise ValueError if a registry row is missing required shape."""
    missing = [k for k in REQUIRED_KEYS if k not in row]
    if missing:
        raise ValueError(f"template missing keys {missing}: {row.get('template_id')!r}")

    tid = row["template_id"]
    if not isinstance(tid, str) or not tid.strip():
        raise ValueError(f"template_id must be non-empty str, got {tid!r}")

    role = row["role"]
    if role not in ROLES:
        raise ValueError(f"{tid}: role {role!r} not in {sorted(ROLES)}")

    if not isinstance(row["tokens"], list):
        raise ValueError(f"{tid}: tokens must be a list")
    if not isinstance(row["zones_hypothesized"], list):
        raise ValueError(f"{tid}: zones_hypothesized must be a list")
    if not isinstance(row["resolution_parts"], list):
        raise ValueError(f"{tid}: resolution_parts must be a list")
    if not isinstance(row["discriminators"], list):
        raise ValueError(f"{tid}: discriminators must be a list")
    if not isinstance(row["seed_refs"], list):
        raise ValueError(f"{tid}: seed_refs must be a list")

    for key in BOOL_KEYS:
        if not isinstance(row[key], bool):
            raise ValueError(f"{tid}: {key} must be bool")

    thr = row["threshold"]
    if thr is not None and not isinstance(thr, (int, float)):
        raise ValueError(f"{tid}: threshold must be number or null")

    if row.get("threshold_frozen") and thr is None:
        raise ValueError(f"{tid}: threshold_frozen requires a numeric threshold")

    if "institution" in row["discriminators"]:
        targets = row.get("institution_targets")
        if not isinstance(targets, list) or not targets:
            raise ValueError(
                f"{tid}: discriminators include institution but "
                "institution_targets is missing or empty"
            )


def validate_registry(rows: Sequence[Mapping[str, Any]]) -> None:
    """Validate all rows; require unique template_id."""
    seen: set[str] = set()
    for row in rows:
        validate_template(row)
        tid = str(row["template_id"])
        if tid in seen:
            raise ValueError(f"duplicate template_id: {tid!r}")
        seen.add(tid)


def load_templates(
    *,
    logical_name: str = LOGICAL_NAME,
    rows: Sequence[Mapping[str, Any]] | None = None,
    validate: bool = True,
) -> list[dict[str, Any]]:
    """Load registry rows from data_io or an in-memory sequence."""
    if rows is None:
        loaded = load(logical_name)
        if not isinstance(loaded, list):
            raise TypeError(f"{logical_name} must load as list[dict], got {type(loaded)}")
        out = [dict(r) for r in loaded]
    else:
        out = [dict(r) for r in rows]
    if validate:
        validate_registry(out)
    return out


def index_by_id(rows: Iterable[Mapping[str, Any]]) -> dict[str, dict[str, Any]]:
    """Map template_id → row (last wins if duplicates; prefer validate first)."""
    return {str(r["template_id"]): dict(r) for r in rows}


def get_template(
    template_id: str,
    *,
    logical_name: str = LOGICAL_NAME,
    rows: Sequence[Mapping[str, Any]] | None = None,
) -> dict[str, Any]:
    """Return one validated template by id."""
    by_id = index_by_id(load_templates(logical_name=logical_name, rows=rows))
    try:
        return by_id[template_id]
    except KeyError as exc:
        raise KeyError(f"unknown template_id: {template_id!r}") from exc


def templates_by_role(
    role: str,
    *,
    logical_name: str = LOGICAL_NAME,
    rows: Sequence[Mapping[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    """Filter registry by role (framing / doc_flag / appointment_subtype / residual)."""
    if role not in ROLES:
        raise ValueError(f"role {role!r} not in {sorted(ROLES)}")
    return [r for r in load_templates(logical_name=logical_name, rows=rows) if r["role"] == role]
