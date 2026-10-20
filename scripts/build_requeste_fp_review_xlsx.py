#!/usr/bin/env python3
"""Build Excel workbook to hand-read requeste-opener false positives (STEPT1k2).

Settles whether the <=0.05 FP gate is reachable against ES-derived gold at
all: negatives are defined solely by ES label absence, so a share of the 103
false positives (role=negative, pred=true in ``formula_type_requeste_scores``)
may be genuinely requeste-opening resolutions ES did not type as ``rekest``.
Mirrors the ``aanstelling_pre1705_gold_review_xlsx`` to_score convention.

    uv run python scripts/build_requeste_fp_review_xlsx.py
    uv run python scripts/build_requeste_fp_review_xlsx.py --priority-n 30
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path

import pandas as pd

from data_io import load, resolve
from data_io.jsonl_io import save_semi_structured
from formulation.appointment_formula_type import align_tokenize
from formulation.requeste_formula_type import join_texts_from_flat, wording_flags
from formulation.review_snippet import add_review_snippet

LOGICAL_XLSX = "requeste_fp_review_xlsx"
RANDOM_STATE = 20261020
PRIORITY_N = 30
N_CALIBRATION = 6
TEXT_EXCEL_MAX = 12_000

# Decision-formula marker family from the STEPT1k FP diagnosis (scratch, not
# pipeline) — FP rate 0.340 for negatives carrying it vs 0.117 without.
_GOEDGEVONDEN_RE = re.compile(r"(?i)\b(?:goed|goet)ge(?:vonden|vondem)\b")


def _fp_rows() -> pd.DataFrame:
    """role=negative & pred=true from the frozen STEPT1k scores."""
    scores = pd.DataFrame(load("formula_type_requeste_scores"))
    return scores.loc[
        scores["role"].eq("negative") & scores["pred"].astype(bool)
    ].reset_index(drop=True)


def _calibration_rows(n: int, random_state: int) -> pd.DataFrame:
    """Known gold positives: a self-check sheet, answer not shown."""
    scores = pd.DataFrame(load("formula_type_requeste_scores"))
    gold_pred = scores.loc[scores["role"].eq("gold") & scores["pred"].astype(bool)]
    if gold_pred.empty:
        return gold_pred
    return gold_pred.sample(n=min(n, len(gold_pred)), random_state=random_state)


def _matched_span(text: str, start_idx: int, end_idx: int) -> str:
    tokens = align_tokenize(str(text or ""))
    n = len(tokens)
    if n == 0:
        return ""
    lo = max(0, min(int(start_idx), n - 1))
    hi = max(lo, min(int(end_idx), n - 1))
    return " ".join(tokens[lo : hi + 1])


def _priority_sample(frame: pd.DataFrame, n: int, random_state: int) -> set[str]:
    """Stratify the hand-read subset by score band x goedgevonden marker."""
    band = pd.cut(
        frame["score"], bins=[-1, 5.5, 7.0, 99], labels=["low", "mid", "high"]
    )
    strata = frame.assign(_band=band)
    total = len(strata)
    picked: list[pd.DataFrame] = []
    for _, grp in strata.groupby(["_band", "has_goedgevonden"], observed=True):
        take = max(1, round(n * len(grp) / total))
        picked.append(grp.sample(n=min(take, len(grp)), random_state=random_state))
    out = pd.concat(picked)
    if len(out) > n:
        out = out.sample(n=n, random_state=random_state)
    return set(out["id"].astype(str))


def _with_text_and_flags(rows: pd.DataFrame, gold_texts: dict[str, str]) -> pd.DataFrame:
    """Join resolutions_flat text, recover opener span, flag decision markers."""
    out = rows.copy()
    out["id"] = out["id"].astype(str)
    meta = [{"id": r["id"], "year": r.get("year")} for r in out.to_dict("records")]
    texts = join_texts_from_flat(meta)
    text_by_id = dict(zip(texts["id"].astype(str), texts["resolutions_text"]))
    out["resolutions_text"] = [
        gold_texts.get(rid, text_by_id.get(rid, "")) for rid in out["id"]
    ]
    out["matched_span"] = [
        _matched_span(t, s, e)
        for t, s, e in zip(out["resolutions_text"], out["start_idx"], out["end_idx"])
    ]
    out["has_goedgevonden"] = out["resolutions_text"].apply(
        lambda t: bool(_GOEDGEVONDEN_RE.search(t))
    )
    out["requeste_wording"] = out["requeste_wording"].fillna(False) | out[
        "resolutions_text"
    ].apply(lambda t: wording_flags(t)["requeste_wording"])
    return out


def _instructions(priority_n: int) -> pd.DataFrame:
    rows = [
        (
            "to_score",
            f"Read ``review_snippet``. Fill ``verdict``: bearing (genuinely opens "
            f"with a read-requeste clause — ES gold is incomplete here) | mention "
            f"(requeste named later, not the opener) | unrelated (alignment noise) "
            f"| ambiguous (can't tell). {priority_n} rows, stratified by score band "
            f"x goedgevonden marker.",
        ),
        (
            "calibration",
            "6 known ES-rekest gold positives, unmarked. Fill ``verdict`` the same "
            "way as a self-check — the expected answer is always ``bearing``; low "
            "accuracy here means re-read the to_score sheet's instructions, not "
            "the model.",
        ),
        (
            "context",
            "STEPT1k measured requeste opener FP = 0.206 (103/500) against ES "
            "``rekest`` gold. A negative is only a resolution ES did not label "
            "rekest — this workbook settles how much of that 0.206 is a gold gap "
            "vs model error.",
        ),
    ]
    return pd.DataFrame(rows, columns=["sheet", "purpose"])


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--priority-n", type=int, default=PRIORITY_N)
    p.add_argument("--calibration-n", type=int, default=N_CALIBRATION)
    p.add_argument("--random-state", type=int, default=RANDOM_STATE)
    args = p.parse_args(argv)

    gold_texts = {
        str(r["id"]): r.get("resolutions_text", "") for r in load("rekest_es_gold")
    }

    fp = _with_text_and_flags(_fp_rows(), gold_texts)
    calibration = _with_text_and_flags(
        _calibration_rows(args.calibration_n, args.random_state), gold_texts
    )

    priority_ids = _priority_sample(fp, args.priority_n, args.random_state)
    to_score = fp.loc[fp["id"].isin(priority_ids)].copy()
    to_score = to_score.sort_values(["score", "id"]).reset_index(drop=True)
    to_score["resolutions_text"] = to_score["resolutions_text"].str.slice(
        0, TEXT_EXCEL_MAX
    )
    to_score["verdict"] = ""
    to_score["notes"] = ""
    to_score = add_review_snippet(to_score, date_col="year", max_chars=TEXT_EXCEL_MAX)

    calibration = calibration.sort_values("id").reset_index(drop=True)
    calibration["resolutions_text"] = calibration["resolutions_text"].str.slice(
        0, TEXT_EXCEL_MAX
    )
    calibration["verdict"] = ""
    calibration["notes"] = ""
    calibration = add_review_snippet(
        calibration, date_col="year", max_chars=TEXT_EXCEL_MAX
    )

    to_score_cols = [
        "id",
        "year",
        "score",
        "requeste_wording",
        "has_goedgevonden",
        "matched_span",
        "verdict",
        "notes",
        "review_snippet",
    ]
    to_score = to_score[to_score_cols]
    calibration = calibration[to_score_cols]

    xlsx_path = Path(resolve(LOGICAL_XLSX))
    xlsx_path.parent.mkdir(parents=True, exist_ok=True)
    with pd.ExcelWriter(xlsx_path, engine="openpyxl") as writer:
        _instructions(len(to_score)).to_excel(
            writer, sheet_name="instructions", index=False
        )
        to_score.to_excel(writer, sheet_name="to_score", index=False)
        calibration.to_excel(writer, sheet_name="calibration", index=False)
        summary = pd.DataFrame(
            [
                {"item": "fp_total", "value": len(fp)},
                {"item": "to_score_rows", "value": len(to_score)},
                {"item": "calibration_rows", "value": len(calibration)},
                {"item": "fp_rate_measured", "value": 0.206},
                {"item": "fp_gate", "value": 0.05},
            ]
        )
        summary.to_excel(writer, sheet_name="summary", index=False)

    meta_path = save_semi_structured(
        summary.to_dict(orient="records"),
        logical_name="requeste_fp_review_meta",
        description="STEPT1k2: build stats for requeste FP review workbook",
        parent_sources=["formula_type_requeste_scores", "rekest_es_gold"],
        script=__file__,
    )
    print(f"wrote {xlsx_path}")
    print(f"meta {meta_path}")
    print(summary.to_string(index=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
