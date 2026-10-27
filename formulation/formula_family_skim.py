"""STEPT1ac: human skim workbook for formula_family_candidates (blank keep/role)."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Sequence

import pandas as pd

from formulation.formula_family_fold import HUMAN_ROLES

SKIM_COLUMNS = (
    "keep",
    "human_role",
    "variant_of",
    "family_id",
    "exemplar",
    "n_members",
    "phrase_freq_max",
    "suggested_role",
    "zone",
    "lcats",
    "hinge_bucket",
    "overlap_cue",
    "overlap_place",
    "part_of",
    "protected_any",
    "sources",
    "member_preview",
)


def family_skim_rows(families: Sequence[dict[str, Any]]) -> list[dict[str, Any]]:
    """Flatten families for Excel skim; keep/human_role/variant_of blank."""
    out: list[dict[str, Any]] = []
    for fam in families:
        members = fam.get("members") or []
        preview = " | ".join(
            str(m.get("phrase") or "")[:60] for m in members[:5] if m.get("phrase")
        )
        sources = fam.get("sources") or []
        if isinstance(sources, list):
            sources_s = ";".join(str(s) for s in sources)
        else:
            sources_s = str(sources)
        out.append(
            {
                "keep": "",
                "human_role": fam.get("human_role") or "",
                "variant_of": fam.get("variant_of") or "",
                "family_id": fam.get("family_id"),
                "exemplar": fam.get("exemplar"),
                "n_members": int(fam.get("n_members") or 0),
                "phrase_freq_max": int(fam.get("phrase_freq_max") or 0),
                "suggested_role": fam.get("suggested_role"),
                "zone": fam.get("zone"),
                "lcats": fam.get("lcats"),
                "hinge_bucket": fam.get("hinge_bucket"),
                "overlap_cue": fam.get("overlap_cue") or "",
                "overlap_place": fam.get("overlap_place") or "",
                "part_of": fam.get("part_of") or "",
                "protected_any": bool(fam.get("protected_any")),
                "sources": sources_s,
                "member_preview": preview,
            }
        )
    out.sort(
        key=lambda r: (
            -int(r["phrase_freq_max"]),
            str(r.get("suggested_role") or ""),
            str(r.get("family_id") or ""),
        )
    )
    return out


def write_family_skim_xlsx(
    path: Path | str,
    families: Sequence[dict[str, Any]],
    *,
    metrics: dict[str, Any] | None = None,
) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    rows = family_skim_rows(families)
    df = pd.DataFrame(rows, columns=list(SKIM_COLUMNS))
    guide = pd.DataFrame(
        [
            {
                "field": "keep",
                "values": "yes | no | undecided (blank = not reviewed)",
                "note": "Import only filled keep rows later; blank-keep trifecta habit",
            },
            {
                "field": "human_role",
                "values": " | ".join(HUMAN_ROLES),
                "note": "Position/zone ≠ role; do science on exemplar, not every member",
            },
            {
                "field": "variant_of",
                "values": "family_id of survivor",
                "note": "When skim disagrees with auto-fold merge",
            },
            {
                "field": "principle",
                "values": "do science on a canonical form",
                "note": "Exemplar = join key; members = skim evidence only",
            },
        ]
    )
    meta_rows = [{"key": k, "value": str(v)} for k, v in (metrics or {}).items()]
    with pd.ExcelWriter(path, engine="openpyxl") as writer:
        df.to_excel(writer, sheet_name="families", index=False)
        guide.to_excel(writer, sheet_name="guide", index=False)
        if meta_rows:
            pd.DataFrame(meta_rows).to_excel(writer, sheet_name="metrics", index=False)
    return path
