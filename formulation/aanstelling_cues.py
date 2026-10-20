"""Aanstelling formula cues and rough name spans in resolution text.

Cue families (orthographic variants):

- *creditief* / *creditif* / *credentiael* …
- *sessie genomen* / *sessie genoomen*
- *verwelkomt* / *verwellekomt* …
- *aengenaem* / *aangenaam* … (not *aangenomen*)
- *holland_multi* — Gecommitteerde Raaden introduce several Heeren
  (*geintroduceert stonden te worden … weegens de Steeden*)

Also extracts a rough appointee string after common frames (*creditief op …*,
*op den heer …*, *verwelkomt den heer …*, Holland-multi name lists).
"""

from __future__ import annotations

import re
from typing import Any

import pandas as pd

# Distinctive aanstelling language (avoid bare *commissie* / *committeren* —
# those dominate the grey band without being appointments).
CUE_PATTERNS: dict[str, re.Pattern[str]] = {
    "creditief": re.compile(
        r"cr[eéi]?dit[ie]*[fv]|cr[eéi]?denti(?:aa?l|eel)\w*|credentyf|criditijf",
        re.IGNORECASE,
    ),
    "sessie_genomen": re.compile(
        r"sessi[eë]?\s+geno+men|"
        r"heeft\s+(?:daer\s+|daar\s+)?(?:op\s+)?sessi[eë]?",
        re.IGNORECASE,
    ),
    "verwelkom": re.compile(
        # verwellekomt / verwillecompt / verwelkomt / verwelkomst
        r"verwe+l+e?(?:ko+m|compt)\w*|verwelkomst|verwellekomst",
        re.IGNORECASE,
    ),
    "aengenaem": re.compile(
        # aangenaam / aengenaem / aengenaamen — not aangenomen
        r"a\.?e?nge?na+e?m\w*",
        re.IGNORECASE,
    ),
    "op_den_heer": re.compile(
        r"op\s+den\s+(?:hee(?:re|r)|jonckh[a-z]*\.?)\s+\S",
        re.IGNORECASE,
    ),
    "holland_multi": re.compile(
        r"geintroduc\w*\s+stonden\s+te\s+worden|"
        r"we+gens?\s+de\s+Steeden",
        re.IGNORECASE,
    ),
}

# Holland multi-appointment: names between *de Heeren …* and *weegens de Steeden*.
_HOLLAND_MULTI_SPAN = re.compile(
    r"geintroduc\w*\s+stonden\s+te\s+worden\s+"
    r"(?:de\s+)?Heeren?\s+"
    r"(.+?)"
    r"\s*,?\s*we+gens?\s+de\s+Steeden",
    re.IGNORECASE | re.DOTALL,
)
_HOLLAND_NAME_SPLIT = re.compile(r"\s*,\s*(?:en\s+)?|\s+en\s+", re.IGNORECASE)

# Prefer longer, more specific extractors first.
# Name heads use (?-i:[A-Z…]) so IGNORECASE does not let "ter" match as a name.
_NAME_HEAD = r"(?-i:[A-ZÁÉÍÓÚÄËÏÖÜ])"
_NAME_EXTRACTORS: list[tuple[str, re.Pattern[str]]] = [
    (
        "creditief_op",
        re.compile(
            r"(?:cr[eéi]?dit[ie]*[fv]|cr[eéi]?denti(?:aa?l|eel)\w*)\s+op\s*"
            r"(?:den\s+)?"
            r"(?:(?:hee(?:re|r)|raedsheer|raedtsheer|jonckh[a-z]*\.?)\s+)?"
            rf"({_NAME_HEAD}[^,;.]{{2,90}})",
            re.IGNORECASE,
        ),
    ),
    (
        "op_den_heer",
        re.compile(
            r"op\s*den\s+(?:hee(?:re|r)|jonckh[a-z]*\.?)\s+"
            rf"((?:(?:jonckh[a-z]*\.?|mr\.?)\s+)?{_NAME_HEAD}[^,;.]{{2,90}})",
            re.IGNORECASE,
        ),
    ),
    (
        "gecommitteert_den",
        re.compile(
            r"gecommitteert\s+(?:hadden\s+)?"
            r"(?:ter\s+vergaderinge\s+(?:van\s+ha\w*\s+ho:?\s*mo:?\s*)?)?"
            r"(?:(?:den|de|d[''])\s+)?"
            r"(?:hee(?:re|r)\s+)?"
            # 17c often lowercases the forename (henrick ter Culen)
            r"((?:(?:jonckh[a-z]*\.?|jr\.?|mr\.?)\s+)?"
            r"(?!(?:ter|van|den|de|om|omme|tot|tot|te)\b)"
            r"[A-Za-zÁÉÍÓÚÄËÏÖÜ][^,;.]{2,90})",
            re.IGNORECASE,
        ),
    ),
    (
        "deputeren_den",
        re.compile(
            r"(?:te\s+)?(?:authoris\w*\s*(?:ende|,)?\s*)?(?:te\s+)?deput\w*\s+"
            r"(?:(?:den|de)\s+)?"
            r"(?:hee(?:re|r)\s+)?"
            r"(?:ende\s+)?"
            rf"((?:(?:jonckh[a-z]*\.?|jr\.?|mr\.?)\s+)?{_NAME_HEAD}[^,;.]{{2,90}})",
            re.IGNORECASE,
        ),
    ),
    (
        "verwelkomt_heer",
        re.compile(
            # verwellekomt / verwillecompt / verwelkomt
            r"verwe+l+e?(?:ko+m|compt)\w*\s+(?:hier\s+)?(?:ter\s+vergaderinge\s+)?"
            r"(?:den\s+)?(?:hee(?:re|r)\s+)?"
            rf"({_NAME_HEAD}[^,;.]{{2,90}})",
            re.IGNORECASE,
        ),
    ),
    (
        "gemelten_heer",
        re.compile(
            r"(?:den|de)\s+gem(?:elten?|elde|:)\s+"
            r"(?:hee(?:re|r)\s+)?"
            rf"((?:van\s+)?{_NAME_HEAD}[^,;.]{{2,70}})",
            re.IGNORECASE,
        ),
    ),
    (
        "committeren_den",
        re.compile(
            r"te\s+committ\w*\s+(?:den\s+)?(?:hee(?:re|r)\s+)?"
            rf"({_NAME_HEAD}[^,;.]{{2,70}})",
            re.IGNORECASE,
        ),
    ),
]

_STOP_PREFIXES = re.compile(
    r"^(?:ende|en|om|omme|tot|ter|wegen|hier|aldaar|aldaer)\b",
    re.IGNORECASE,
)
_TRAIL_NOISE = re.compile(
    r"\s+(?:om|omme|van\s+wegens|ende|en\s+heeft|waarop|waerop|"
    r"verwe+l+e?(?:ko+m|compt)\w*|"
    r"ou[dt]t?\b|raedt|pensionaris|burgermr|borgmr|burgemeester)\b.*$",
    re.IGNORECASE,
)


def cue_hits(text: str) -> list[str]:
    if not text:
        return []
    return [name for name, rx in CUE_PATTERNS.items() if rx.search(text)]


def has_aanstelling_cue(text: str) -> bool:
    return bool(cue_hits(text))


def _clean_name_span(span: str) -> str:
    cleaned = re.sub(r"\s+", " ", span).strip(" ,;.-")
    cleaned = _TRAIL_NOISE.sub("", cleaned).strip(" ,;.-")
    if _STOP_PREFIXES.match(cleaned):
        return ""
    # Drop title-only captures
    if re.fullmatch(
        r"(?:jonckh[a-z]*\.?|hee(?:re|r)|mr\.?|burgermeester)",
        cleaned,
        flags=re.IGNORECASE,
    ):
        return ""
    if len(cleaned) < 4:
        return ""
    return cleaned


def extract_holland_multi_names(text: str, *, max_names: int = 8) -> list[str]:
    """Split appointees from the Holland Gecommitteerde Raaden multi frame."""
    if not text:
        return []
    found: list[str] = []
    seen: set[str] = set()
    for match in _HOLLAND_MULTI_SPAN.finditer(text):
        span = re.sub(r"\s+", " ", match.group(1)).strip(" ,;.-")
        if not span:
            continue
        parts = [p.strip(" ,;.-") for p in _HOLLAND_NAME_SPLIT.split(span) if p.strip()]
        for part in parts:
            name = _clean_name_span(part)
            if not name:
                continue
            key = name.casefold()
            if key in seen:
                continue
            seen.add(key)
            found.append(name)
            if len(found) >= max_names:
                return found
    return found


def is_holland_multi(text: str) -> bool:
    return bool(CUE_PATTERNS["holland_multi"].search(text or ""))


def extract_rough_names(text: str, *, max_names: int = 5) -> list[str]:
    """Pull rough appointee strings from formula frames (may be multi)."""
    if not text:
        return []
    found: list[str] = []
    seen: set[str] = set()

    # Prefer Holland-multi splits when the frame is present.
    for name in extract_holland_multi_names(text, max_names=max_names):
        key = name.casefold()
        if key in seen:
            continue
        seen.add(key)
        found.append(name)
        if len(found) >= max_names:
            return found

    for _label, rx in _NAME_EXTRACTORS:
        for match in rx.finditer(text):
            name = _clean_name_span(match.group(1))
            if not name:
                continue
            key = name.casefold()
            if key in seen:
                continue
            seen.add(key)
            found.append(name)
            if len(found) >= max_names:
                return found
    return found


def add_aanstelling_cues(
    frame: pd.DataFrame,
    *,
    text_col: str = "resolutions_text",
) -> pd.DataFrame:
    """Add cue boolean columns + ``has_aanstelling_cue`` / ``cue_hits``."""
    if text_col not in frame.columns:
        raise ValueError(f"Frame missing {text_col!r}")
    out = frame.copy()
    texts = out[text_col].fillna("").astype(str)
    for name, rx in CUE_PATTERNS.items():
        out[f"cue_{name}"] = texts.str.contains(rx.pattern, case=False, regex=True)
    out["cue_hits"] = texts.map(lambda t: ";".join(cue_hits(t)))
    cue_cols = [f"cue_{name}" for name in CUE_PATTERNS]
    out["has_aanstelling_cue"] = out[cue_cols].any(axis=1)
    return out


def add_rough_names(
    frame: pd.DataFrame,
    *,
    text_col: str = "resolutions_text",
) -> pd.DataFrame:
    """Add ``rough_names`` / ``holland_multi_names`` from formula frames."""
    if text_col not in frame.columns:
        raise ValueError(f"Frame missing {text_col!r}")
    out = frame.copy()
    texts = out[text_col].fillna("").astype(str)
    holland = texts.map(extract_holland_multi_names)
    names = texts.map(extract_rough_names)
    out["holland_multi_names"] = holland.map(lambda xs: "; ".join(xs))
    out["n_holland_multi_names"] = holland.map(len)
    out["rough_names"] = names.map(lambda xs: "; ".join(xs))
    out["n_rough_names"] = names.map(len)
    return out


def cue_summary(frame: pd.DataFrame) -> list[dict[str, Any]]:
    if "has_aanstelling_cue" not in frame.columns:
        return []
    rows: list[dict[str, Any]] = [
        {
            "item": "with_aanstelling_cue",
            "value": int(frame["has_aanstelling_cue"].sum()),
        },
        {
            "item": "aanstelling_cue_rate",
            "value": round(float(frame["has_aanstelling_cue"].mean()), 4)
            if len(frame)
            else 0.0,
        },
    ]
    if "cue_holland_multi" in frame.columns:
        rows.append(
            {
                "item": "holland_multi",
                "value": int(frame["cue_holland_multi"].sum()),
            }
        )
    return rows
