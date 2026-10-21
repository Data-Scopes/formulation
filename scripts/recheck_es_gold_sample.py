#!/usr/bin/env python3
"""Re-measure accepted formula types on a CLEAN stratified gold sample.

After the 2026-10-21 ES re-pin (resolution ids are not stable across index
generations), every ``*_es_gold`` set has ~31% of rows labelled from the wrong
resolution. Rather than re-fetch and re-score 74k-177k rows per type, this
samples: k ES-labelled ids per year from the *pinned* index, joins flat text
(same generation, so the join is exact), and re-measures recall / FP with
Wilson intervals against the recorded stale numbers.

Negatives are verified individually against the pinned index, so a "negative"
is a resolution the pinned index really does not label as the target type.

    uv run python scripts/recheck_es_gold_sample.py --type missive
    uv run python scripts/recheck_es_gold_sample.py --type all --per-year 25
"""

from __future__ import annotations

import argparse
import json
from typing import Any

import pandas as pd

from data_io import load, save_semi_structured
from formulation.appointment_formula_type import YEAR_MAX, YEAR_MIN
from formulation.es_gold_sample import (
    flat_texts,
    stratified_gold_ids,
    verified_negatives,
    wilson,
)
from formulation.republic_es import RepublicEsClient

# type key -> (ES proposition_type, metrics logical name, cloud builder, scorer)
TYPES = {
    "requeste": {
        "proposition_type": "rekest",
        "metrics": "formula_type_requeste_metrics",
        "gold": "rekest_es_gold",
    },
    "advies": {
        "proposition_type": "advies",
        "metrics": "formula_type_advies_metrics",
        "gold": "advies_es_gold",
    },
    "missive": {
        "proposition_type": "missive",
        "metrics": "formula_type_missive_metrics",
        "gold": "missive_es_gold",
    },
}


def build_scorer(type_key: str):
    """(cloud, cut, score_fn) reusing the type's existing frozen model."""
    if type_key == "requeste":
        from formulation.formula_type_presence import fit_requeste_presence_model
        from formulation.requeste_formula_type import score_text

        m = fit_requeste_presence_model()
        return m["cloud"], float(m["operating_cut"]), score_text
    if type_key == "advies":
        from formulation.advies_formula_type import score_text
        from formulation.formula_type_presence import fit_advies_presence_model

        m = fit_advies_presence_model()
        return m["cloud"], float(m["operating_cut"]), score_text
    from formulation.formula_type_presence import fit_missive_presence_model
    from formulation.missive_formula_type import score_text

    m = fit_missive_presence_model()
    return m["cloud"], float(m["operating_cut"]), score_text


def stale_metrics(logical: str) -> dict[str, Any]:
    try:
        rows = load(logical)
        rows = rows if isinstance(rows, list) else rows.to_dict("records")
        return rows[-1] if rows else {}
    except Exception:
        return {}


def recheck(
    type_key: str,
    *,
    per_year: int,
    neg_n: int,
    random_state: int,
    random_within_year: bool = False,
) -> dict[str, Any]:
    spec = TYPES[type_key]
    client = RepublicEsClient()
    pt = spec["proposition_type"]

    gold_ids = stratified_gold_ids(
        client,
        pt,
        per_year=per_year,
        random_within_year=random_within_year,
        random_seed=random_state,
    )
    gold = flat_texts(gold_ids)
    n_requested, n_joined = len(gold_ids), len(gold)

    neg, n_dropped = verified_negatives(
        client,
        exclude={r["id"] for r in gold_ids},
        n=neg_n,
        proposition_type=pt,
        random_state=random_state,
    )

    cloud, cut, score_text = build_scorer(type_key)
    g_hits = sum(1 for t in gold["resolutions_text"] if score_text(t, cloud)["score"] >= cut)
    n_hits = sum(1 for t in neg["resolutions_text"] if score_text(t, cloud)["score"] >= cut)

    recall = g_hits / len(gold) if len(gold) else None
    fp = n_hits / len(neg) if len(neg) else None
    old = stale_metrics(spec["metrics"])
    old_recall = ((old.get("overall") or {}).get("recall_model")) if old else None
    old_fp = old.get("fp_rate") if old else None
    sampling_mode = "random_within_year" if random_within_year else "systematic_id_asc"

    return {
        "type": type_key,
        "proposition_type": pt,
        "index": client.config.resolutions_index,
        "sampling": f"stratified {per_year}/year {YEAR_MIN}-{YEAR_MAX} ({sampling_mode})",
        "sampling_mode": sampling_mode,
        "n_gold_requested": n_requested,
        "n_gold_joined": n_joined,
        "gold_join_rate": round(n_joined / n_requested, 4) if n_requested else None,
        "operating_cut": cut,
        "recall_clean": round(recall, 4) if recall is not None else None,
        "recall_clean_ci95": [round(x, 4) for x in wilson(g_hits, len(gold))],
        "recall_stale": old_recall,
        "n_negatives": int(len(neg)),
        "n_negatives_dropped_as_target_type": int(n_dropped),
        "fp_clean": round(fp, 4) if fp is not None else None,
        "fp_clean_ci95": [round(x, 4) for x in wilson(n_hits, len(neg))],
        "fp_stale": old_fp,
        "note": (
            "Clean = ES labels and flat text from the same (pinned) generation. "
            "Stale = recorded metric built across generations (~31% mismatch). "
            "Cloud is the existing frozen model, so this isolates the gold "
            "contamination effect, not a retrained pipeline."
        ),
    }


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--type", default="all", choices=[*TYPES, "all"])
    p.add_argument("--per-year", type=int, default=25)
    p.add_argument("--neg-n", type=int, default=500)
    p.add_argument("--random-state", type=int, default=20261021)
    p.add_argument("--no-write", action="store_true")
    p.add_argument(
        "--random-within-year",
        action="store_true",
        help=(
            "sample gold randomly within each year instead of taking the "
            "lowest ids (default: systematic, comparable to the recorded "
            "recheck numbers)"
        ),
    )
    args = p.parse_args(argv)

    keys = list(TYPES) if args.type == "all" else [args.type]
    out = []
    for k in keys:
        print(f"--- {k} ---", flush=True)
        r = recheck(
            k,
            per_year=args.per_year,
            neg_n=args.neg_n,
            random_state=args.random_state,
            random_within_year=args.random_within_year,
        )
        out.append(r)
        print(json.dumps(r, indent=2), flush=True)

    if not args.no_write:
        save_semi_structured(
            out,
            logical_name="es_gold_recheck_metrics",
            script=__file__,
            parent_sources=["resolutions_flat"],
            description=(
                "Clean stratified re-measurement of accepted formula types "
                "after the 2026-10-21 ES index re-pin"
            ),
        )
    print("\n=== summary ===")
    print(
        pd.DataFrame(out)[
            ["type", "n_gold_joined", "recall_clean", "recall_stale", "fp_clean", "fp_stale"]
        ].to_string(index=False)
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
