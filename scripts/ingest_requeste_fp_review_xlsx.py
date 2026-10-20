#!/usr/bin/env python3
"""Ingest hand-filled ``to_score``/``calibration`` verdicts (STEPT1k2).

Reads back ``requeste_fp_review_xlsx``, reports calibration accuracy (6 known
rekest-gold rows — expected verdict is always ``bearing``), and computes the
FP rate corrected for cases judged ``bearing`` (genuinely requeste-opening,
ES label gap) vs the measured 0.206, with a Wilson 95% CI on whether the
<=0.05 FP gate becomes reachable.

    uv run python scripts/ingest_requeste_fp_review_xlsx.py
"""

from __future__ import annotations

import math

import pandas as pd

from data_io import resolve
from data_io.jsonl_io import save_semi_structured

LOGICAL_XLSX = "requeste_fp_review_xlsx"
LOGICAL_OUT = "requeste_fp_verdicts"
FP_RATE_MEASURED = 0.206
FP_GATE = 0.05
VALID_VERDICTS = {"bearing", "mention", "unrelated", "ambiguous"}


def _judged(frame: pd.DataFrame) -> pd.DataFrame:
    verdict = frame["verdict"].fillna("").astype(str).str.strip().str.lower()
    bad = set(verdict[verdict.ne("")]) - VALID_VERDICTS
    if bad:
        raise ValueError(f"Unrecognised verdict value(s): {sorted(bad)}")
    out = frame.copy()
    out["verdict"] = verdict
    return out.loc[out["verdict"].ne("")]


def _wilson(k: int, n: int) -> tuple[float, float]:
    if not n:
        return (0.0, 1.0)
    z = 1.96
    p = k / n
    denom = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / denom
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / denom
    return (max(0.0, centre - half), min(1.0, centre + half))


def main() -> int:
    path = resolve(LOGICAL_XLSX)
    book = pd.read_excel(path, sheet_name=None)
    to_score = _judged(book["to_score"])
    calibration = _judged(book["calibration"])

    cal_n = len(calibration)
    cal_right = int(calibration["verdict"].eq("bearing").sum())
    cal_acc = cal_right / cal_n if cal_n else None

    counts = to_score["verdict"].value_counts().to_dict()
    decided = int(to_score["verdict"].ne("ambiguous").sum())
    bearing = int(counts.get("bearing", 0))
    p = bearing / decided if decided else None
    corrected = FP_RATE_MEASURED * (1 - p) if p is not None else None
    ci = _wilson(bearing, decided) if decided else (None, None)
    corrected_lo = FP_RATE_MEASURED * (1 - ci[1]) if ci[1] is not None else None
    corrected_hi = FP_RATE_MEASURED * (1 - ci[0]) if ci[0] is not None else None

    if corrected_hi is not None and corrected_hi <= FP_GATE:
        gate_verdict = "reachable"
    elif corrected_lo is not None and corrected_lo > FP_GATE:
        gate_verdict = "not_rescued"
    else:
        gate_verdict = "inconclusive"

    records = [
        {
            "id": str(r["id"]),
            "year": int(r["year"]) if pd.notna(r.get("year")) else None,
            "score": float(r["score"]) if pd.notna(r.get("score")) else None,
            "requeste_wording": bool(r.get("requeste_wording")),
            "has_goedgevonden": bool(r.get("has_goedgevonden")),
            "matched_span": str(r.get("matched_span", "")),
            "verdict": r["verdict"],
            "notes": str(r.get("notes", "") or ""),
            "source_workbook": str(path.name),
            "source_sheet": "to_score",
        }
        for r in to_score.to_dict(orient="records")
    ]

    summary = {
        "n_to_score_judged": len(to_score),
        "n_calibration_judged": cal_n,
        "calibration_accuracy": cal_acc,
        "verdict_counts": {k: int(v) for k, v in counts.items()},
        "decided_n": decided,
        "fp_rate_measured": FP_RATE_MEASURED,
        "fp_gate": FP_GATE,
        "bearing_share": p,
        "fp_rate_corrected": corrected,
        "fp_rate_corrected_ci95": [corrected_lo, corrected_hi],
        "gate_verdict": gate_verdict,
    }
    records.append({**summary, "id": "__summary__", "source_sheet": "to_score"})

    out = save_semi_structured(
        records,
        logical_name=LOGICAL_OUT,
        description=(
            "STEPT1k2: human verdicts + corrected-FP-rate summary from "
            "requeste_fp_review_xlsx"
        ),
        parent_sources=["requeste_fp_review_xlsx"],
        script=__file__,
    )

    print(f"wrote {len(records)} rows -> {out}")
    print(f"calibration: {cal_right}/{cal_n} bearing" + (
        f" ({cal_acc:.0%})" if cal_acc is not None else " (no calibration rows judged)"
    ))
    print(f"to_score verdicts: {counts}")
    if corrected is not None:
        print(
            f"corrected FP rate: {corrected:.3f} "
            f"(95% CI {corrected_lo:.3f}-{corrected_hi:.3f}) "
            f"vs measured {FP_RATE_MEASURED} and gate {FP_GATE} -> {gate_verdict}"
        )
    else:
        print("no to_score rows judged yet")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
