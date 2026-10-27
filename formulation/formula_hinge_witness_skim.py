"""STEPT1aj: human skim workbook for near+mid hinge-witness adjudication.

Far band stays parked. Emit blank human_keep/human_note; ingest filled rows only.
Does not mint hinges or mutate formula_templates.
"""

from __future__ import annotations

from collections import Counter
from pathlib import Path
from typing import Any, Sequence

import pandas as pd

from formulation.formula_hinge_ledger import (
    default_seed_rows,
    load_fixture_rows as load_hinge_fixture_rows,
)
from formulation.formula_hinge_witness import (
    adjudicate_witnesses,
    default_hinge_rows,
    load_witness_fixture,
)

LOGICAL_XLSX = "formula_hinge_witness_skim_xlsx"
LOGICAL_VERDICTS = "formula_hinge_witness_verdicts"
METRICS_NAME = "formula_hinge_witness_skim_metrics"

SKIM_BANDS = frozenset({"near", "mid"})
HUMAN_KEEP_VALUES = frozenset({"variant", "split", "composition", "reject"})

SKIM_COLUMNS = (
    "human_keep",
    "human_note",
    "band",
    "best_sim",
    "best_hinge_id",
    "canonic",
    "second_hinge_id",
    "second_sim",
    "witness_id",
    "witness_text",
    "phrase_freq",
    "source",
)


def _hinge_canonic_map(hinges: Sequence[dict[str, Any]] | None = None) -> dict[str, str]:
    rows = list(hinges) if hinges is not None else default_hinge_rows()
    out: dict[str, str] = {}
    for r in rows:
        hid = str(r.get("hinge_id") or "")
        can = r.get("canonic")
        if hid and can and str(can).strip():
            out[hid] = str(can).strip()
    return out


def filter_near_mid(rows: Sequence[dict[str, Any]]) -> list[dict[str, Any]]:
    return [r for r in rows if str(r.get("band") or "") in SKIM_BANDS]


def skim_rows(
    adjudication: Sequence[dict[str, Any]],
    *,
    hinges: Sequence[dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    """Flatten near+mid adjudication for Excel; human fields blank on emit."""
    canonic = _hinge_canonic_map(hinges)
    out: list[dict[str, Any]] = []
    for r in filter_near_mid(adjudication):
        hid = str(r.get("best_hinge_id") or "")
        keep = r.get("human_keep")
        note = r.get("human_note")
        out.append(
            {
                "human_keep": "" if keep is None else str(keep),
                "human_note": "" if note is None else str(note),
                "band": str(r.get("band") or ""),
                "best_sim": float(r.get("best_sim") or 0.0),
                "best_hinge_id": hid,
                "canonic": canonic.get(hid, ""),
                "second_hinge_id": r.get("second_hinge_id"),
                "second_sim": r.get("second_sim"),
                "witness_id": str(r.get("witness_id") or ""),
                "witness_text": str(r.get("witness_text") or ""),
                "phrase_freq": int(r.get("phrase_freq") or 0),
                "source": str(r.get("source") or ""),
            }
        )
    out.sort(
        key=lambda r: (
            0 if r["band"] == "near" else 1,
            -float(r["best_sim"]),
            str(r["best_hinge_id"]),
            str(r["witness_id"]),
        )
    )
    return out


def skim_metrics(
    adjudication: Sequence[dict[str, Any]],
    skim: Sequence[dict[str, Any]],
) -> dict[str, Any]:
    by_band_all = Counter(str(r.get("band")) for r in adjudication)
    by_band_skim = Counter(str(r.get("band")) for r in skim)
    by_hinge: Counter[str] = Counter(str(r.get("best_hinge_id")) for r in skim)
    return {
        "step": "STEPT1aj",
        "n_adjudication": len(adjudication),
        "n_skim": len(skim),
        "by_band_adjudication": {
            b: int(by_band_all.get(b, 0)) for b in ("near", "mid", "far")
        },
        "by_band_skim": {b: int(by_band_skim.get(b, 0)) for b in ("near", "mid")},
        "by_hinge_skim": dict(sorted(by_hinge.items())),
        "human_keep_vocab": sorted(HUMAN_KEEP_VALUES),
        "note": (
            "Near+mid skim only; far parked. Blank human_keep until human fill. "
            "No auto-mint; templates and hinge seed untouched."
        ),
    }


def write_skim_xlsx(
    path: Path | str,
    adjudication: Sequence[dict[str, Any]],
    *,
    hinges: Sequence[dict[str, Any]] | None = None,
    metrics: dict[str, Any] | None = None,
) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    rows = skim_rows(adjudication, hinges=hinges)
    df = pd.DataFrame(rows, columns=list(SKIM_COLUMNS))
    # Keep human columns as strings so blank emit does not round-trip as float NaN.
    df["human_keep"] = df["human_keep"].astype("string")
    df["human_note"] = df["human_note"].astype("string")
    guide = pd.DataFrame(
        [
            {
                "field": "human_keep",
                "values": " | ".join(sorted(HUMAN_KEEP_VALUES)) + " | (blank)",
                "note": "near: variant|reject; mid: split|composition|reject|rare variant",
            },
            {
                "field": "human_note",
                "values": "free text",
                "note": "For split: proposed hinge_id; for composition: name the parts",
            },
            {
                "field": "band",
                "values": "near | mid",
                "note": "Far excluded from this workbook (STEPT1ai noise mass)",
            },
            {
                "field": "principle",
                "values": "archetypes first; mid does not auto-mint",
                "note": "DECISIONS 2026-10-26 formula-in-effect witness adjudication",
            },
            {
                "field": "watchwords",
                "values": (
                    "afgewezen | naar Y gestuurt voor advies | afgehandeld te worden | "
                    "resolutie commissoriaal | hebben … geexamineerd | op advies van"
                ),
                "note": (
                    "Post-goedgevonden referral + commissorial/advice chain → composition; "
                    "exposition citing these / earlier resoluties → composition"
                ),
            },
        ]
    )
    meta_rows = [{"key": k, "value": str(v)} for k, v in (metrics or {}).items()]
    with pd.ExcelWriter(path, engine="openpyxl") as writer:
        df.to_excel(writer, sheet_name="near_mid", index=False)
        guide.to_excel(writer, sheet_name="guide", index=False)
        if meta_rows:
            pd.DataFrame(meta_rows).to_excel(writer, sheet_name="metrics", index=False)
    return path


def parse_filled_keep(value: Any) -> str | None:
    """Return normalised human_keep or None if blank. Raise on unknown."""
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    s = str(value).strip().lower()
    if not s:
        return None
    if s not in HUMAN_KEEP_VALUES:
        raise ValueError(f"Unrecognised human_keep value: {s!r}")
    return s


def ingest_skim_xlsx(path: Path | str) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Read filled near_mid sheet; return judged rows + summary metrics."""
    path = Path(path)
    book = pd.read_excel(path, sheet_name=None)
    if "near_mid" not in book:
        raise ValueError(f"{path}: missing sheet 'near_mid'")
    frame = book["near_mid"]
    judged: list[dict[str, Any]] = []
    for raw in frame.to_dict(orient="records"):
        keep = parse_filled_keep(raw.get("human_keep"))
        if keep is None:
            continue
        note_raw = raw.get("human_note")
        if note_raw is None or (isinstance(note_raw, float) and pd.isna(note_raw)):
            note = ""
        else:
            note = str(note_raw).strip()
        judged.append(
            {
                "witness_id": str(raw.get("witness_id") or ""),
                "band": str(raw.get("band") or ""),
                "best_hinge_id": str(raw.get("best_hinge_id") or ""),
                "best_sim": float(raw["best_sim"])
                if raw.get("best_sim") is not None and not pd.isna(raw.get("best_sim"))
                else None,
                "witness_text": str(raw.get("witness_text") or ""),
                "human_keep": keep,
                "human_note": note,
                "source_workbook": path.name,
            }
        )
    counts = Counter(r["human_keep"] for r in judged)
    by_band = Counter(r["band"] for r in judged)
    summary = {
        "step": "STEPT1aj",
        "n_judged": len(judged),
        "by_human_keep": {k: int(counts.get(k, 0)) for k in sorted(HUMAN_KEEP_VALUES)},
        "by_band_judged": {b: int(by_band.get(b, 0)) for b in ("near", "mid")},
        "source_workbook": path.name,
        "note": "Ingested human fill only; templates and hinge seed untouched.",
    }
    return judged, summary


def fixture_adjudication_for_skim() -> list[dict[str, Any]]:
    """CI smoke: adjudicate fixture witnesses (includes near/mid/far)."""
    return adjudicate_witnesses(default_seed_rows(), load_witness_fixture())


def load_hinge_rows_for_skim() -> list[dict[str, Any]]:
    from formulation.formula_hinge_ledger import FIXTURE_PATH

    if FIXTURE_PATH.is_file():
        return load_hinge_fixture_rows()
    return default_seed_rows()
