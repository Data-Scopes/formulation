"""STEPT1y: human-judged opener_candidates queue + driver write-back.

Pipeline writes evidence only. Human writes names and verdicts.
No auto-mint, no auto-A, no auto-promote.
"""

from __future__ import annotations

import copy
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from data_io import load, load_jsonl, save_semi_structured

LOGICAL_NAME = "opener_candidates"
FIXTURE_PATH = (
    Path(__file__).resolve().parents[1] / "tests" / "fixtures" / "opener_candidates.jsonl"
)

STATUSES = frozenset(
    {
        "pocket",
        "named",
        "measured",
        "accepted_a",
        "wired",
        "blueprint",
        "parked",
        "rejected",
        "merged",
    }
)
VERDICTS = frozenset({"accept", "reject", "park", "hold", ""})
HUMAN_VERDICT_FIELDS = frozenset({"a_verdict", "promote_verdict"})
# Statuses that may be absorbed into another candidate (human merge).
MERGEABLE_FROM = frozenset({"pocket", "named", "parked", "measured"})
# Statuses allowed as merge target (survivor).
MERGEABLE_INTO = frozenset({"pocket", "named", "parked", "measured", "accepted_a"})

# Audit evidence for the six accepted openers (NOTES / frozen cuts).
# Used by fixture-only measure/wire/propose-promote write-back — not a live eval.
AUDIT_EVIDENCE: dict[str, dict[str, Any]] = {
    "appointment_installation": {
        "operating_cut": 6.0,
        "recall": None,
        "fp_rate": None,
        "n_cloud_accepted": None,
        "n_present": None,
        "empty_delta": None,
        "n_proto_cores": None,
    },
    "advies_geleesen": {
        "operating_cut": 4.12,
        "recall": 0.762,
        "fp_rate": 0.034,
        "n_cloud_accepted": None,
        "n_present": None,
        "empty_delta": None,
        "n_proto_cores": None,
    },
    "requeste_geleesen": {
        "operating_cut": 4.5,
        "recall": 0.898,
        "fp_rate": 0.206,
        "n_cloud_accepted": None,
        "n_present": None,
        "empty_delta": -0.335,
        "n_proto_cores": None,
    },
    "missive_ontfangen": {
        "operating_cut": 6.0,
        "recall": 0.887,
        "fp_rate": 0.11,
        "n_cloud_accepted": None,
        "n_present": None,
        "empty_delta": -0.018,
        "n_proto_cores": None,
    },
    "requeste_op_de": {
        "operating_cut": 4.5,
        "recall": 1.0,
        "fp_rate": 0.064,
        "n_cloud_accepted": None,
        "n_present": None,
        "empty_delta": 0.0,
        "n_proto_cores": 3,
    },
    "rapport_gehoord": {
        "operating_cut": 7.5,
        "recall": 0.895,
        "fp_rate": 0.006,
        "n_cloud_accepted": 10642,
        "n_present": 63,
        "empty_delta": -0.015,
        "n_proto_cores": 3,
    },
}

REQUIRED_COLUMNS = (
    "candidate_id",
    "canonic",
    "es_proposition_type",
    "source",
    "status",
    "operating_cut",
    "recall",
    "fp_rate",
    "n_cloud_accepted",
    "n_empty_support",
    "empty_delta",
    "n_present",
    "n_proto_cores",
    "a_verdict",
    "promote_verdict",
    "comparison_year",
    "measured_at",
    "wired_at",
    "proposed_promote_at",
    "seed_refs",
    "notes",
)


class OpenerCandidatesError(ValueError):
    """Driver refused a phase or human helper."""


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _blank(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, float) and value != value:  # NaN
        return True
    if isinstance(value, str) and not value.strip():
        return True
    return False


def _norm_verdict(value: Any) -> str:
    if _blank(value):
        return ""
    return str(value).strip().lower()


def load_fixture_candidates(path: Path | None = None) -> list[dict[str, Any]]:
    rows = load_jsonl(path or FIXTURE_PATH)
    return [dict(r) for r in rows]


def load_candidates(*, from_fixture: bool = False) -> list[dict[str, Any]]:
    if from_fixture:
        return load_fixture_candidates()
    try:
        rows = load(LOGICAL_NAME)
    except FileNotFoundError:
        return load_fixture_candidates()
    if isinstance(rows, list):
        return [dict(r) for r in rows]
    raise OpenerCandidatesError(f"unexpected load type for {LOGICAL_NAME}: {type(rows)}")


def save_candidates(
    rows: list[dict[str, Any]],
    *,
    script: str | None = None,
    description: str = "",
) -> Path:
    validate_rows(rows)
    return save_semi_structured(
        rows,
        logical_name=LOGICAL_NAME,
        parent_sources=[],
        description=description
        or "STEPT1y opener_candidates queue (human verdicts + driver evidence)",
        script=script,
    )


def validate_rows(rows: list[dict[str, Any]]) -> None:
    if not rows:
        raise OpenerCandidatesError("opener_candidates is empty")
    ids: set[str] = set()
    for i, row in enumerate(rows):
        cid = row.get("candidate_id")
        if _blank(cid):
            raise OpenerCandidatesError(f"row {i}: missing candidate_id")
        cid_s = str(cid)
        if cid_s in ids:
            raise OpenerCandidatesError(f"duplicate candidate_id: {cid_s}")
        ids.add(cid_s)
        status = row.get("status")
        if status not in STATUSES:
            raise OpenerCandidatesError(f"{cid_s}: bad status {status!r}")
        for field in HUMAN_VERDICT_FIELDS:
            v = _norm_verdict(row.get(field))
            if v and v not in VERDICTS:
                raise OpenerCandidatesError(f"{cid_s}: bad {field}={v!r}")
        if status == "named" and _blank(row.get("canonic")):
            raise OpenerCandidatesError(f"{cid_s}: named requires canonic")
        if status == "pocket" and not _blank(row.get("canonic")):
            # allow draft canonic on pocket, but prefer empty until human names
            pass


def find_row(rows: list[dict[str, Any]], candidate_id: str) -> dict[str, Any]:
    for row in rows:
        if row.get("candidate_id") == candidate_id:
            return row
    raise OpenerCandidatesError(f"unknown candidate_id: {candidate_id}")


def index_of(rows: list[dict[str, Any]], candidate_id: str) -> int:
    for i, row in enumerate(rows):
        if row.get("candidate_id") == candidate_id:
            return i
    raise OpenerCandidatesError(f"unknown candidate_id: {candidate_id}")


def _as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return list(value)
    if isinstance(value, tuple):
        return list(value)
    return [value]


def _surfaces_of(row: dict[str, Any]) -> list[str]:
    """Unique surface strings: explicit surfaces + canonic if set."""
    out: list[str] = []
    seen: set[str] = set()
    for item in _as_list(row.get("surfaces")) + (
        [row["canonic"]] if not _blank(row.get("canonic")) else []
    ):
        s = str(item).strip()
        if not s:
            continue
        key = s.casefold()
        if key in seen:
            continue
        seen.add(key)
        out.append(s)
    return out


def name_candidate(
    rows: list[dict[str, Any]],
    candidate_id: str,
    *,
    canonic: str,
    es_proposition_type: str | None = None,
) -> list[dict[str, Any]]:
    """Human helper: pocket → named. Driver never calls this."""
    out = copy.deepcopy(rows)
    row = find_row(out, candidate_id)
    if row["status"] not in {"pocket", "named"}:
        raise OpenerCandidatesError(
            f"{candidate_id}: name_candidate only from pocket/named, got {row['status']}"
        )
    if _blank(canonic):
        raise OpenerCandidatesError(f"{candidate_id}: canonic required")
    row["canonic"] = canonic
    surfaces = _surfaces_of(row)
    if canonic.casefold() not in {x.casefold() for x in surfaces}:
        surfaces.append(canonic)
    row["surfaces"] = surfaces
    if es_proposition_type is not None:
        row["es_proposition_type"] = es_proposition_type
    row["status"] = "named"
    validate_rows(out)
    return out


def active_candidates(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Rows still in play (exclude merged-away / rejected)."""
    return [
        r
        for r in rows
        if r.get("status") not in {"merged", "rejected"}
    ]


def merge_candidates(
    rows: list[dict[str, Any]],
    *,
    into_id: str,
    from_ids: list[str],
    canonic: str | None = None,
    notes: str | None = None,
) -> list[dict[str, Any]]:
    """Human helper: absorb ``from_ids`` into ``into_id``.

    Survivor keeps ``into_id``. Absorbed rows get ``status=merged`` and
    ``merged_into``. Surfaces / seed_refs / n_empty_support accumulate on the
    survivor. Does not invent a_verdict / promote_verdict. Refuses to absorb
    or overwrite ``blueprint`` rows.
    """
    if not from_ids:
        raise OpenerCandidatesError("merge requires at least one from_id")
    if into_id in from_ids:
        raise OpenerCandidatesError("into_id must not appear in from_ids")

    out = copy.deepcopy(rows)
    target = find_row(out, into_id)
    if target["status"] == "blueprint":
        raise OpenerCandidatesError(
            f"{into_id}: refuse merge into blueprint — open a new named row instead"
        )
    if target["status"] == "merged":
        raise OpenerCandidatesError(
            f"{into_id}: already merged into {target.get('merged_into')!r}"
        )
    if target["status"] not in MERGEABLE_INTO:
        raise OpenerCandidatesError(
            f"{into_id}: cannot merge into status {target['status']!r}"
        )

    surfaces = _surfaces_of(target)
    merged_from = [str(x) for x in _as_list(target.get("merged_from"))]
    seed_refs = [str(x) for x in _as_list(target.get("seed_refs"))]
    n_empty = target.get("n_empty_support")
    n_empty_sum = int(n_empty) if n_empty is not None and not _blank(n_empty) else 0
    saw_empty = n_empty is not None and not _blank(n_empty)

    for fid in from_ids:
        src = find_row(out, fid)
        if src["status"] == "blueprint":
            raise OpenerCandidatesError(f"{fid}: refuse to absorb a blueprint")
        if src["status"] == "merged":
            raise OpenerCandidatesError(
                f"{fid}: already merged into {src.get('merged_into')!r}"
            )
        if src["status"] not in MERGEABLE_FROM:
            raise OpenerCandidatesError(
                f"{fid}: merge-from status {src['status']!r} not allowed "
                "(use pocket/named/parked/measured only)"
            )
        for s in _surfaces_of(src):
            if s.casefold() not in {x.casefold() for x in surfaces}:
                surfaces.append(s)
        merged_from.append(str(fid))
        for ref in _as_list(src.get("seed_refs")):
            r = str(ref)
            if r and r not in seed_refs:
                seed_refs.append(r)
        src_n = src.get("n_empty_support")
        if src_n is not None and not _blank(src_n):
            n_empty_sum += int(src_n)
            saw_empty = True
        src["status"] = "merged"
        src["merged_into"] = into_id
        src["merged_at"] = _now_iso()

    target["surfaces"] = surfaces
    target["merged_from"] = merged_from
    target["seed_refs"] = seed_refs
    if saw_empty:
        target["n_empty_support"] = n_empty_sum
    if canonic is not None:
        if _blank(canonic):
            raise OpenerCandidatesError("canonic must be non-empty when provided")
        target["canonic"] = canonic
        if target["status"] == "pocket":
            target["status"] = "named"
        # keep canonic in surfaces
        if canonic.casefold() not in {x.casefold() for x in surfaces}:
            surfaces.append(canonic)
            target["surfaces"] = surfaces
    if notes is not None:
        prev = str(target.get("notes") or "").strip()
        target["notes"] = f"{prev}; {notes}".strip("; ") if prev else notes
    else:
        prev = str(target.get("notes") or "").strip()
        merge_note = f"merged ← {', '.join(from_ids)}"
        target["notes"] = f"{prev}; {merge_note}".strip("; ") if prev else merge_note
    target["merged_at"] = _now_iso()
    validate_rows(out)
    return out


def set_a_verdict(
    rows: list[dict[str, Any]],
    candidate_id: str,
    verdict: str,
) -> list[dict[str, Any]]:
    """Human helper after measure. Driver never calls this."""
    out = copy.deepcopy(rows)
    row = find_row(out, candidate_id)
    v = _norm_verdict(verdict)
    if v not in {"accept", "reject", "park"}:
        raise OpenerCandidatesError(f"a_verdict must be accept|reject|park, got {verdict!r}")
    if row["status"] not in {"measured", "accepted_a", "parked", "rejected"}:
        raise OpenerCandidatesError(
            f"{candidate_id}: a_verdict expects status measured (got {row['status']})"
        )
    row["a_verdict"] = v
    if v == "accept":
        row["status"] = "accepted_a"
    elif v == "reject":
        row["status"] = "rejected"
    else:
        row["status"] = "parked"
    validate_rows(out)
    return out


def set_promote_verdict(
    rows: list[dict[str, Any]],
    candidate_id: str,
    verdict: str,
) -> list[dict[str, Any]]:
    """Human helper after wire. Driver never sets this field itself."""
    out = copy.deepcopy(rows)
    row = find_row(out, candidate_id)
    v = _norm_verdict(verdict)
    if v not in {"accept", "hold", "park", "reject"}:
        raise OpenerCandidatesError(
            f"promote_verdict must be accept|hold|park|reject, got {verdict!r}"
        )
    if row["status"] not in {"wired", "blueprint", "parked", "rejected"}:
        raise OpenerCandidatesError(
            f"{candidate_id}: promote_verdict expects status wired (got {row['status']})"
        )
    row["promote_verdict"] = v
    # Status advances only via propose_promote (or park/reject here for hold-outs).
    if v in {"park", "reject"}:
        row["status"] = "parked" if v == "park" else "rejected"
    validate_rows(out)
    return out


def has_measure_adapter(candidate_id: str) -> bool:
    return candidate_id in AUDIT_EVIDENCE


def phase_measure(
    rows: list[dict[str, Any]],
    candidate_id: str,
    *,
    fixture_only: bool = True,
) -> list[dict[str, Any]]:
    """Write measure evidence. Never sets a_verdict.

    STEPT1y: audit adapters only (known blueprints). New types refuse until
    a later step adds a real eval adapter.
    """
    del fixture_only  # reserved; STEPT1y never hits live ES
    out = copy.deepcopy(rows)
    row = find_row(out, candidate_id)
    status = row["status"]
    if status == "merged":
        raise OpenerCandidatesError(
            f"{candidate_id}: merged into {row.get('merged_into')!r} — measure the survivor"
        )
    if status == "pocket":
        raise OpenerCandidatesError(
            f"{candidate_id}: refuse measure on pocket — human must name canonic first"
        )
    if status not in {"named", "measured", "blueprint", "accepted_a"}:
        raise OpenerCandidatesError(
            f"{candidate_id}: measure expects named/measured/blueprint, got {status}"
        )
    if _blank(row.get("canonic")):
        raise OpenerCandidatesError(f"{candidate_id}: canonic required before measure")
    if not has_measure_adapter(candidate_id):
        raise OpenerCandidatesError(
            f"{candidate_id}: no measure adapter yet — add eval adapter after naming "
            "(STEPT1y scaffolds audit adapters for the six blueprints only)"
        )
    evidence = AUDIT_EVIDENCE[candidate_id]
    for key, value in evidence.items():
        if key in {
            "operating_cut",
            "recall",
            "fp_rate",
            "n_cloud_accepted",
            "n_present",
            "empty_delta",
            "n_proto_cores",
        }:
            # measure phase fills score metrics; composition fields may stay for wire
            if key in {"operating_cut", "recall", "fp_rate", "n_cloud_accepted"}:
                row[key] = value
    row["measured_at"] = _now_iso()
    if status == "named":
        row["status"] = "measured"
    # blueprint / accepted_a / measured: keep status; refresh evidence only
    validate_rows(out)
    return out


def phase_wire(
    rows: list[dict[str, Any]],
    candidate_id: str,
    *,
    fixture_only: bool = True,
) -> list[dict[str, Any]]:
    """Write wire/presence evidence. Requires human a_verdict=accept (or blueprint audit)."""
    del fixture_only
    out = copy.deepcopy(rows)
    row = find_row(out, candidate_id)
    status = row["status"]
    a_v = _norm_verdict(row.get("a_verdict"))
    if status == "blueprint":
        # dry-run write-back of known composition numbers
        pass
    elif status == "accepted_a" and a_v == "accept":
        pass
    else:
        raise OpenerCandidatesError(
            f"{candidate_id}: wire requires status accepted_a with a_verdict=accept "
            f"(or blueprint audit); got status={status} a_verdict={a_v!r}"
        )
    if not has_measure_adapter(candidate_id):
        raise OpenerCandidatesError(
            f"{candidate_id}: no wire adapter — presence wiring is a later step"
        )
    evidence = AUDIT_EVIDENCE[candidate_id]
    if evidence.get("n_present") is not None:
        row["n_present"] = evidence["n_present"]
    if evidence.get("empty_delta") is not None:
        row["empty_delta"] = evidence["empty_delta"]
    if evidence.get("n_proto_cores") is not None:
        row["n_proto_cores"] = evidence["n_proto_cores"]
    row["wired_at"] = _now_iso()
    if status == "accepted_a":
        row["status"] = "wired"
    validate_rows(out)
    return out


def phase_propose_promote(
    rows: list[dict[str, Any]],
    candidate_id: str,
    *,
    apply_promote: bool = False,
    fixture_only: bool = True,
) -> list[dict[str, Any]]:
    """Write promote proposal evidence. Never auto-promotes without human + flag.

    Default: fill proposed_promote_at + composition evidence; leave status as wired
    (or blueprint). Only if promote_verdict=accept AND apply_promote: status→blueprint.
    Does not mutate formula_templates / ACCEPTED_TYPE_IDS in STEPT1y.
    """
    del fixture_only
    out = copy.deepcopy(rows)
    row = find_row(out, candidate_id)
    status = row["status"]
    p_v = _norm_verdict(row.get("promote_verdict"))
    if status == "blueprint":
        pass
    elif status == "wired":
        # may propose before verdict; advancing to blueprint needs verdict+flag
        pass
    else:
        raise OpenerCandidatesError(
            f"{candidate_id}: propose-promote expects wired or blueprint, got {status}"
        )
    if not has_measure_adapter(candidate_id):
        raise OpenerCandidatesError(f"{candidate_id}: no promote adapter yet")
    evidence = AUDIT_EVIDENCE[candidate_id]
    if evidence.get("empty_delta") is not None:
        row["empty_delta"] = evidence["empty_delta"]
    if evidence.get("n_proto_cores") is not None:
        row["n_proto_cores"] = evidence["n_proto_cores"]
    row["proposed_promote_at"] = _now_iso()
    if apply_promote:
        if p_v != "accept":
            raise OpenerCandidatesError(
                f"{candidate_id}: --apply-promote requires promote_verdict=accept "
                f"(got {p_v!r}); driver never invents the verdict"
            )
        if status == "wired":
            row["status"] = "blueprint"
        # STEPT1y: do not touch formula_templates / ACCEPTED_TYPE_IDS here
    validate_rows(out)
    return out


def seed_rows_from_fixture() -> list[dict[str, Any]]:
    rows = load_fixture_candidates()
    validate_rows(rows)
    return rows


__all__ = (
    "AUDIT_EVIDENCE",
    "FIXTURE_PATH",
    "HUMAN_VERDICT_FIELDS",
    "LOGICAL_NAME",
    "MERGEABLE_FROM",
    "MERGEABLE_INTO",
    "OpenerCandidatesError",
    "REQUIRED_COLUMNS",
    "STATUSES",
    "VERDICTS",
    "active_candidates",
    "find_row",
    "has_measure_adapter",
    "index_of",
    "load_candidates",
    "load_fixture_candidates",
    "merge_candidates",
    "name_candidate",
    "phase_measure",
    "phase_propose_promote",
    "phase_wire",
    "save_candidates",
    "seed_rows_from_fixture",
    "set_a_verdict",
    "set_promote_verdict",
    "validate_rows",
)
