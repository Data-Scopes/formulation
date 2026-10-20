"""Match delegates in resolution text via unique-table OCR patterns.

Uses semicolon-separated ``patterns`` / ``pattern`` strings from the 1705–1795
unique delegates file (attendance OCR variants). Exact casefold substring
match, year-gated, scored by sum of matched pattern lengths squared. Prefers
hits inside aanstelling cue windows (*op den heer*, *committeren*, …).
"""

from __future__ import annotations

import json
import math
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

import pandas as pd

from data_io import resolve
from formulation.attendance_activity import (
    AttendanceSpan,
    is_active_on,
    new_seat_boost,
    parse_resolution_date,
)

LOGICAL_UNIQUE = "delegates_unique_1705_1795"
MIN_PATTERN_LEN = 10
YEAR_SLACK = 2

# Province / formula tokens that appear as false-friend patterns.
_GEO_BLACKLIST = frozenset(
    {
        "holland",
        "hollandt",
        "zeeland",
        "zeelandt",
        "gelderland",
        "gelderlandt",
        "utrecht",
        "friesland",
        "vriesland",
        "vrieslandt",
        "overyssel",
        "overijssel",
        "groningen",
        "stadt en lande",
        "stad en lande",
        "brabant",
        "generaliteit",
        "westvriesland",
        "west-vriesland",
        "west vriesland",
        "den hage",
        "van holland",
        "van zeeland",
        "van gelderland",
        "van utrecht",
        "van vriesland",
        "van friesland",
    }
)

_CUE_WINDOW = re.compile(
    r"(?:"
    r"op\s+den\s+hee(?:re|r)"
    r"|jonckh[a-z]*\.?"
    r"|committ[a-z]*"
    r"|commissie.{0,100}?op"
    r").{0,140}",
    re.IGNORECASE | re.DOTALL,
)


@dataclass(frozen=True)
class PatternEntry:
    pattern_cf: str
    length: int
    delegate_id: str
    fullname: str
    min_year: int | None
    max_year: int | None


@dataclass(frozen=True)
class DelegateMatch:
    delegate_id: str
    fullname: str
    score: float
    patterns: tuple[str, ...]
    in_cue_window: bool


def _split_patterns(*cells: object) -> list[str]:
    out: list[str] = []
    for cell in cells:
        if cell is None or (isinstance(cell, float) and pd.isna(cell)):
            continue
        out.extend(str(cell).split(";"))
    return [p.strip() for p in out if p.strip()]


def _is_blacklisted(pattern_cf: str) -> bool:
    if pattern_cf in _GEO_BLACKLIST:
        return True
    tokens = [t for t in re.split(r"[\s\-']+", pattern_cf) if t]
    if tokens and all(t in _GEO_BLACKLIST or len(t) < 3 for t in tokens):
        return True
    return False


def _year_int(value: object) -> int | None:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return None


def load_unique_delegates(path: Path | None = None) -> pd.DataFrame:
    """Load the unique delegates JSON (list of objects)."""
    resolved = Path(path) if path is not None else Path(resolve(LOGICAL_UNIQUE))
    raw = json.loads(resolved.read_text(encoding="utf-8"))
    if not isinstance(raw, list):
        raise ValueError(f"Expected a JSON list in {resolved}")
    return pd.DataFrame(raw)


def build_pattern_index(
    delegates: pd.DataFrame,
    *,
    min_len: int = MIN_PATTERN_LEN,
) -> list[PatternEntry]:
    """Flatten ``patterns`` + ``pattern`` into longest-first lookup entries."""
    entries: list[PatternEntry] = []
    for _, row in delegates.iterrows():
        did = str(row.get("delegate_id") or row.get("cons_id_str") or "").strip()
        if not did:
            continue
        fullname = str(row.get("fullname") or "").strip()
        min_y = _year_int(row.get("minjaar"))
        max_y = _year_int(row.get("maxjaar"))
        seen: set[str] = set()
        for phrase in _split_patterns(row.get("patterns"), row.get("pattern")):
            if len(phrase) < int(min_len):
                continue
            cf = phrase.casefold()
            if cf in seen or _is_blacklisted(cf):
                continue
            seen.add(cf)
            entries.append(
                PatternEntry(
                    pattern_cf=cf,
                    length=len(cf),
                    delegate_id=did,
                    fullname=fullname,
                    min_year=min_y,
                    max_year=max_y,
                )
            )
    entries.sort(key=lambda e: (-e.length, e.delegate_id))
    return entries


def _cue_windows(text: str) -> list[str]:
    return [m.group(0).casefold() for m in _CUE_WINDOW.finditer(text)]


def match_delegates_in_text(
    text: str,
    year: int | None,
    index: list[PatternEntry],
    *,
    year_slack: int = YEAR_SLACK,
    top_k: int = 3,
    resolution_date: object | None = None,
    attendance: dict[str, AttendanceSpan] | None = None,
    require_attendance_active: bool = False,
) -> list[DelegateMatch]:
    """Return top-k delegates by pattern score for one resolution text.

    Attendance dates (when provided) re-rank candidates:

    - active on resolution date → mild boost (+ new-seat boost if first
      sitting is near the resolution)
    - has attendance but inactive that day → demote (unless
      ``require_attendance_active``, which drops them)
    - no attendance row → unique-table year gate only
    """
    if not text or not index:
        return []
    full_cf = str(text).casefold()
    windows = _cue_windows(str(text))
    res_date = parse_resolution_date(resolution_date)
    scores: dict[str, float] = {}
    names: dict[str, str] = {}
    pats: dict[str, list[str]] = {}
    cue_hit: dict[str, bool] = {}

    for entry in index:
        if year is not None:
            if entry.min_year is not None and year < entry.min_year - year_slack:
                continue
            if entry.max_year is not None and year > entry.max_year + year_slack:
                continue
        span = attendance.get(entry.delegate_id) if attendance else None
        active = (
            span is not None
            and res_date is not None
            and is_active_on(res_date, span)
        )
        if require_attendance_active and span is not None and res_date is not None and not active:
            continue
        in_cue = any(entry.pattern_cf in w for w in windows) if windows else False
        in_full = entry.pattern_cf in full_cf
        if not (in_cue or in_full):
            continue
        weight = float(entry.length * entry.length)
        if in_cue:
            weight *= 2.0
        if span is not None and res_date is not None:
            if active:
                weight *= 1.25
                weight *= new_seat_boost(res_date, span)
            else:
                weight *= 0.25
        scores[entry.delegate_id] = scores.get(entry.delegate_id, 0.0) + weight
        names[entry.delegate_id] = entry.fullname
        pats.setdefault(entry.delegate_id, []).append(entry.pattern_cf)
        cue_hit[entry.delegate_id] = cue_hit.get(entry.delegate_id, False) or in_cue

    ranked = sorted(scores.items(), key=lambda kv: (-kv[1], kv[0]))
    out: list[DelegateMatch] = []
    for did, score in ranked[: max(int(top_k), 1)]:
        out.append(
            DelegateMatch(
                delegate_id=did,
                fullname=names[did],
                score=float(score),
                patterns=tuple(pats[did][:5]),
                in_cue_window=bool(cue_hit.get(did)),
            )
        )
    return out


def add_delegate_matches(
    frame: pd.DataFrame,
    index: list[PatternEntry],
    *,
    text_col: str = "resolutions_text",
    year_col: str = "year",
    date_col: str = "date",
    only_non_suspect: bool = True,
    top_k: int = 3,
    attendance: dict[str, AttendanceSpan] | None = None,
    require_attendance_active: bool = False,
) -> pd.DataFrame:
    """Add best / runner-up delegate match columns.

    When ``only_non_suspect`` and a ``suspect`` column exists, suspects get empty
    match fields (still keep the row).
    """
    if text_col not in frame.columns:
        raise ValueError(f"Frame missing {text_col!r}")
    out = frame.copy()
    best_id: list[str] = []
    best_name: list[str] = []
    best_score: list[float] = []
    best_pats: list[str] = []
    best_cue: list[bool] = []
    alt: list[str] = []
    n_matches: list[int] = []

    has_suspect = "suspect" in out.columns
    for _, row in out.iterrows():
        if only_non_suspect and has_suspect and bool(row["suspect"]):
            best_id.append("")
            best_name.append("")
            best_score.append(math.nan)
            best_pats.append("")
            best_cue.append(False)
            alt.append("")
            n_matches.append(0)
            continue
        year = _year_int(row[year_col]) if year_col in out.columns else None
        res_date = row[date_col] if date_col in out.columns else None
        matches = match_delegates_in_text(
            str(row[text_col] or ""),
            year,
            index,
            top_k=top_k,
            resolution_date=res_date,
            attendance=attendance,
            require_attendance_active=require_attendance_active,
        )
        if not matches:
            best_id.append("")
            best_name.append("")
            best_score.append(math.nan)
            best_pats.append("")
            best_cue.append(False)
            alt.append("")
            n_matches.append(0)
            continue
        top = matches[0]
        best_id.append(top.delegate_id)
        best_name.append(top.fullname)
        best_score.append(top.score)
        best_pats.append("; ".join(top.patterns))
        best_cue.append(top.in_cue_window)
        rest = matches[1:]
        alt.append(
            "; ".join(f"{m.fullname} [{m.delegate_id}] ({m.score:.0f})" for m in rest)
        )
        n_matches.append(len(matches))

    out["matched_delegate_id"] = best_id
    out["matched_fullname"] = best_name
    out["match_score"] = best_score
    out["match_patterns"] = best_pats
    out["match_in_cue"] = best_cue
    out["match_alternates"] = alt
    out["n_delegate_matches"] = n_matches
    return out


def match_summary(frame: pd.DataFrame) -> list[dict[str, Any]]:
    if "matched_delegate_id" not in frame.columns:
        return []
    has = frame["matched_delegate_id"].astype(str).str.len() > 0
    eligible = ~frame["suspect"] if "suspect" in frame.columns else pd.Series(True, index=frame.index)
    return [
        {"item": "delegate_match_eligible", "value": int(eligible.sum())},
        {"item": "delegate_match_hit", "value": int((eligible & has).sum())},
        {
            "item": "delegate_match_rate",
            "value": round(float((eligible & has).sum() / eligible.sum()), 4)
            if int(eligible.sum())
            else 0.0,
        },
    ]
