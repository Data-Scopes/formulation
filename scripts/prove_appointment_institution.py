#!/usr/bin/env python3
"""Prove-first: does institution name separate lookalike appointment types?

Compares R1 ``aanstelling_selected`` (vergadering) with harvest rows that
mention Rekenkamer *and* carry aanstelling cues. Scratch output only —
not registered in the manifest.

    uv run python scripts/prove_appointment_institution.py
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pandas as pd

from data_io import load
from formulation.aanstelling_cues import add_aanstelling_cues

OUT_DIR = Path("docs/proofs/multi-template-registry")
SAMPLE_N = 50
RNG = 0

REKENKAMER_RE = re.compile(
    r"[Rr]eken\s*kamer|[Rr]eeckenkamer|[Rr]ekenkaemer", re.IGNORECASE
)

INST_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    (
        "rekenkamer",
        re.compile(r"(?:[Dd]e\s+)?(?:[Gg]eneraliteits?\s+)?[Rr]eken\s*kamer\w*", re.I),
    ),
    (
        "gecommitteerde_raaden",
        re.compile(
            r"[Gg]ecommitteerde\s+[Rr]aa+den\s+van\s+[A-Za-zÁÉÍÓÚäëïöü\-]{2,40}",
            re.I,
        ),
    ),
    (
        "collegie",
        re.compile(
            r"[Cc]ollegie\s+van\s+(?:de\s+)?(?:[Hh]eeren\s+)?[A-Za-zÁÉÍÓÚäëïöü\s]{2,60}",
            re.I,
        ),
    ),
    (
        "admirality",
        re.compile(
            r"(?:[Cc]ollegie\s+ter\s+)?[Aa]dmiraliteit\w*(?:\s+ter\s+\w+)?", re.I
        ),
    ),
    (
        "raad_van_state",
        re.compile(r"[Rr]aa[de]{0,2}\s+[Vv]an\s+[Ss]tate\w*", re.I),
    ),
    (
        "staten_generael",
        re.compile(
            r"[Vv]ergadering(?:e)?\s+van\s+(?:haer\s+)?"
            r"(?:[Hh]oo?ge?\s*)?[Mm]ogende|[Ss]taten\s+[Gg]enera\w*",
            re.I,
        ),
    ),
    (
        "provincial_staten",
        re.compile(r"[Ss]taten\s+van\s+[A-Za-z]{3,20}", re.I),
    ),
]

_PRIMARY_ORDER = (
    "rekenkamer",
    "admirality",
    "raad_van_state",
    "gecommitteerde_raaden",
    "collegie",
    "staten_generael",
    "provincial_staten",
)


def extract_institutions(text: str) -> list[tuple[str, str]]:
    hits: list[tuple[str, str]] = []
    for label, pat in INST_PATTERNS:
        for match in pat.finditer(str(text)):
            span = re.sub(r"\s+", " ", match.group(0)).strip()[:80]
            hits.append((label, span))
    return hits


def primary_institution(hits: list[tuple[str, str]]) -> str:
    by_label = {lab: span for lab, span in hits}
    for lab in _PRIMARY_ORDER:
        if lab in by_label:
            return lab
    return "none"


def _sample(frame: pd.DataFrame, n: int) -> pd.DataFrame:
    if len(frame) <= n:
        return frame.copy()
    return frame.sample(n, random_state=RNG)


def build_rows() -> pd.DataFrame:
    selected = load("aanstelling_selected")
    if not isinstance(selected, pd.DataFrame):
        selected = pd.DataFrame(selected)
    selected = add_aanstelling_cues(selected)
    sel_s = _sample(selected, SAMPLE_N)

    harvest = load("aanstelling_tfidf_harvest")
    if not isinstance(harvest, pd.DataFrame):
        harvest = pd.DataFrame(harvest)
    rek_mask = (
        harvest["resolutions_text"]
        .fillna("")
        .astype(str)
        .str.contains(REKENKAMER_RE.pattern, regex=True, na=False)
    )
    rek = add_aanstelling_cues(harvest.loc[rek_mask].copy())
    cued_rek = rek.loc[rek["has_aanstelling_cue"]].copy()
    rek_s = _sample(cued_rek, SAMPLE_N)

    rows: list[dict] = []
    for typ, frame in (
        ("sibling_rekenkamer_cued", rek_s),
        ("vergadering_selected", sel_s),
    ):
        for record in frame.to_dict(orient="records"):
            hits = extract_institutions(str(record.get("resolutions_text") or ""))
            prim = primary_institution(hits)
            rows.append(
                {
                    "type": typ,
                    "id": record["id"],
                    "bucket": record.get("bucket", "selected"),
                    "cue_hits": record.get("cue_hits") or "",
                    "primary_institution": prim,
                    "n_inst_hits": len(hits),
                    "inst_labels": ",".join(sorted({h[0] for h in hits})),
                    "example_span": hits[0][1] if hits else "",
                }
            )
    return pd.DataFrame(rows)


def summarize(out: pd.DataFrame) -> dict:
    sibling = out[out["type"] == "sibling_rekenkamer_cued"]
    verg = out[out["type"] == "vergadering_selected"]
    n_sib = len(sibling)
    n_verg = len(verg)
    sib_rek = int((sibling["primary_institution"] == "rekenkamer").sum())
    verg_rek_fp = int((verg["primary_institution"] == "rekenkamer").sum())
    sib_none = int((sibling["primary_institution"] == "none").sum())
    verg_none = int((verg["primary_institution"] == "none").sum())
    return {
        "sample_n_per_type": SAMPLE_N,
        "n_sibling_rekenkamer_cued": n_sib,
        "n_vergadering_selected": n_verg,
        "sibling_primary_rekenkamer": sib_rek,
        "sibling_rekenkamer_rate": round(sib_rek / n_sib, 4) if n_sib else None,
        "sibling_none_rate": round(sib_none / n_sib, 4) if n_sib else None,
        "vergadering_primary_rekenkamer_fp": verg_rek_fp,
        "vergadering_none_rate": round(verg_none / n_verg, 4) if n_verg else None,
        "primary_institution_crosstab": {
            str(k): {str(t): int(v) for t, v in vals.items()}
            for k, vals in pd.crosstab(
                out["type"], out["primary_institution"]
            )
            .to_dict()
            .items()
        },
        "pass_no_fp_rekenkamer_on_selected": verg_rek_fp == 0,
        "pass_usable_rekenkamer_recall_on_cued_siblings": (
            (sib_rek / n_sib) >= 0.5 if n_sib else False
        ),
        "notes": (
            "Hypothesized discriminator=institution. "
            "Sibling pool = harvest texts matching Rekenkamer regex AND "
            "has_aanstelling_cue. Selected = R1 vergadering list."
        ),
    }


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out = build_rows()
    metrics = summarize(out)
    rows_path = OUT_DIR / "appointment_institution_sample.jsonl"
    metrics_path = OUT_DIR / "appointment_institution_metrics.jsonl"

    with rows_path.open("w", encoding="utf-8") as handle:
        for row in out.to_dict(orient="records"):
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")
    with metrics_path.open("w", encoding="utf-8") as handle:
        handle.write(json.dumps(metrics, ensure_ascii=False) + "\n")

    print(f"wrote {rows_path} ({len(out)} rows)")
    print(f"wrote {metrics_path}")
    print(json.dumps(metrics, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
