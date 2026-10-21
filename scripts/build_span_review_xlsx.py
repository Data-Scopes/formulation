#!/usr/bin/env python3
"""STEPT1q2: build the hand-read span workbook from STEPT1q arm spans.

STEPT1q measures where each retrieval arm *thinks* the formula is; nothing in
the repo says where it actually is (``formula_boundary_cases`` has 3 synthetic
cases, and ES ``evidence`` is an upstream point anchor). This workbook asks a
human which arm's span is the formula, stratified by whether the arms agreed.

Text is re-joined from ``resolutions_flat`` by id+year rather than carried in
``formula_retrieval_arms_scores`` (an explore-tier score table keeps no text).

    uv run python scripts/build_span_review_xlsx.py --type missive
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import pandas as pd

from data_io import load, resolve, save_semi_structured
from formulation.es_gold_sample import flat_texts
from formulation.formula_retrieval_arms import (
    ANCHOR_ARMS,
    SPAN_ARMS,
    TYPES,
    contained,
    normalized_tokens,
)
from formulation.review_snippet import add_review_snippet

LOGICAL_SCORES = "formula_retrieval_arms_scores"
LOGICAL_XLSX = "formula_span_review_xlsx"
LOGICAL_META = "formula_span_review_meta"
TEXT_EXCEL_MAX = 3000
DEFAULT_N = 30
RANDOM_STATE = 20261021


def render_span(tokens: list[str], start: Any, end: Any) -> str:
    """The span itself, with 6 tokens of context either side, span in «»."""
    if start is None or end is None or pd.isna(start) or pd.isna(end):
        return ""
    s, e = int(start), int(end)
    lead = " ".join(tokens[max(0, s - 6) : s])
    span = " ".join(tokens[s:e])
    trail = " ".join(tokens[e : e + 6])
    return f"{lead} «{span}» {trail}".strip()


def agreement_stratum(row: dict[str, Any]) -> str:
    """How the arms related on this row — the sampling stratum."""
    fired = [a for a in SPAN_ARMS if row.get(f"{a}_fire")]
    if not fired:
        return "no_span_arm_fired"
    if len(fired) == 1:
        return f"only_{fired[0]}"

    def _span(arm: str) -> tuple[int, int] | None:
        s, e = row.get(f"{arm}_start"), row.get(f"{arm}_end")
        if s is None or e is None or pd.isna(s) or pd.isna(e):
            return None
        return (int(s), int(e))

    dags = [a for a in fired if a.startswith("dag_")]
    if "tfidf_window" in fired and dags:
        if not all(contained(_span(d), _span("tfidf_window")) for d in dags):
            return "window_misses_dag"
    if len(dags) == 2:
        a, b = _span(dags[0]), _span(dags[1])
        if a != b:
            return "dags_disagree"
    anchors_in = [
        contained(_span(an), _span(dags[0]))
        for an in ANCHOR_ARMS
        if row.get(f"{an}_fire") and dags
    ]
    if anchors_in and not all(anchors_in):
        return "anchor_outside_dag"
    return "arms_agree"


def _instructions(n_rows: int, type_key: str) -> pd.DataFrame:
    return pd.DataFrame(
        [
            (
                "to_score",
                "Each row shows the same resolution as located by each arm, "
                "span marked «like this». Fill ``verdict`` with the arm whose "
                "span is the formula: tfidf_window | dag_frozen | "
                "dag_clean_boot | all_correct | none_correct. Fill "
                "``correct_span`` only when the answer is none_correct — give "
                "the formula's first and last words.",
            ),
            (
                "strata",
                "Rows are sampled per agreement stratum, not uniformly: "
                "disagreement rows are where span gold actually decides "
                "something, so they are deliberately over-represented. Do not "
                "read sheet proportions as corpus rates.",
            ),
            (
                "context",
                f"STEPT1q compared retrieval arms for {type_key} on clean "
                f"post-re-pin gold ({n_rows} rows here). The repo has no "
                "corpus-scale human span gold; this sheet is it.",
            ),
        ],
        columns=["sheet", "purpose"],
    )


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--type", default="missive", choices=list(TYPES))
    p.add_argument(
        "--sampling-mode",
        default="systematic_id_asc",
        help="which STEPT1q run to read rows from (default: systematic_id_asc)",
    )
    p.add_argument("--n", type=int, default=DEFAULT_N)
    p.add_argument("--random-state", type=int, default=RANDOM_STATE)
    args = p.parse_args(argv)

    rows = load(LOGICAL_SCORES)
    scores = pd.DataFrame(rows if isinstance(rows, list) else rows)
    if scores.empty:
        raise SystemExit(f"{LOGICAL_SCORES} is empty - run STEPT1q first")

    # Runs accumulate in this dataset keyed by (type, sampling_mode); filter
    # before any stratum/sampling logic so the workbook can never mix types.
    type_col = scores["type"] if "type" in scores.columns else pd.Series(
        [None] * len(scores), index=scores.index
    )
    mode_col = scores["sampling_mode"] if "sampling_mode" in scores.columns else pd.Series(
        [None] * len(scores), index=scores.index
    )
    available = sorted(set(zip(type_col.fillna(""), mode_col.fillna(""))))
    scores = scores.loc[
        (type_col == args.type) & (mode_col == args.sampling_mode)
    ].reset_index(drop=True)
    if scores.empty:
        raise SystemExit(
            f"no rows for (type={args.type!r}, sampling_mode={args.sampling_mode!r}) "
            f"in {LOGICAL_SCORES}; (type, sampling_mode) pairs present: {available}"
        )

    scores["stratum"] = [agreement_stratum(r) for r in scores.to_dict("records")]

    # Over-sample disagreement: that is where span gold changes a conclusion.
    per_stratum = max(1, int(args.n) // max(1, scores["stratum"].nunique()))
    picked = (
        scores.groupby("stratum", group_keys=False)
        .apply(
            lambda g: g.sample(
                min(len(g), per_stratum), random_state=int(args.random_state)
            ),
            include_groups=True,
        )
        .reset_index(drop=True)
    )

    texts = flat_texts(
        [
            {"id": str(r["id"]), "year": int(r["year"])}
            for r in picked.to_dict("records")
            if r.get("year") is not None
        ]
    )
    if texts.empty:
        raise SystemExit("no text re-joined from resolutions_flat")
    sheet = picked.merge(texts.drop(columns=["year"]), on="id", how="inner")

    rendered: list[dict[str, Any]] = []
    for rec in sheet.to_dict("records"):
        tokens = normalized_tokens(str(rec.get("resolutions_text") or ""))
        out = {
            "id": rec["id"],
            "year": rec.get("year"),
            "role": rec.get("role"),
            "stratum": rec.get("stratum"),
        }
        for arm in (*SPAN_ARMS, *ANCHOR_ARMS):
            out[f"{arm}_span"] = (
                render_span(tokens, rec.get(f"{arm}_start"), rec.get(f"{arm}_end"))
                if rec.get(f"{arm}_fire")
                else ""
            )
        out["verdict"] = ""
        out["correct_span"] = ""
        out["notes"] = ""
        out["resolutions_text"] = str(rec.get("resolutions_text") or "")[
            :TEXT_EXCEL_MAX
        ]
        rendered.append(out)

    to_score = add_review_snippet(
        pd.DataFrame(rendered), date_col="year", max_chars=TEXT_EXCEL_MAX
    ).drop(columns=["resolutions_text"])

    summary = pd.DataFrame(
        [
            {"item": "type", "value": args.type},
            {"item": "sampling_mode", "value": args.sampling_mode},
            {"item": "score_rows_available", "value": int(len(scores))},
            {"item": "to_score_rows", "value": int(len(to_score))},
            {"item": "per_stratum_cap", "value": per_stratum},
            {"item": "random_state", "value": int(args.random_state)},
        ]
        + [
            {"item": f"stratum_{k}", "value": int(v)}
            for k, v in scores["stratum"].value_counts().items()
        ]
    )

    xlsx_path = Path(resolve(LOGICAL_XLSX))
    xlsx_path.parent.mkdir(parents=True, exist_ok=True)
    with pd.ExcelWriter(xlsx_path, engine="openpyxl") as writer:
        _instructions(len(to_score), args.type).to_excel(
            writer, sheet_name="instructions", index=False
        )
        to_score.to_excel(writer, sheet_name="to_score", index=False)
        summary.to_excel(writer, sheet_name="summary", index=False)

    meta_path = save_semi_structured(
        summary.to_dict(orient="records"),
        logical_name=LOGICAL_META,
        description=(
            f"STEPT1q2: build stats for the {args.type} "
            f"({args.sampling_mode}) span review workbook"
        ),
        parent_sources=[LOGICAL_SCORES, "resolutions_flat"],
        script=__file__,
    )
    print(f"wrote {xlsx_path}")
    print(f"meta {meta_path}")
    print(summary.to_string(index=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
