#!/usr/bin/env python3
"""Prove-first: does institution name separate lookalike appointment types?

Compares R1 ``aanstelling_selected`` (vergadering) with harvest rows that
mention Rekenkamer *and* carry aanstelling cues. Surfaces come from
``institution_patterns`` (not ``formula_templates``). Scratch output only —
not registered in the manifest.

Sibling-pool sampling always uses fixture seeds (stable sample). Classification
can use seeds, harvest, or both (A/B):

    uv run python scripts/prove_appointment_institution.py --source compare
    uv run python scripts/prove_appointment_institution.py --source seeds
    uv run python scripts/prove_appointment_institution.py --source harvest
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

import pandas as pd

from data_io import load
from formulation.aanstelling_cues import add_aanstelling_cues
from formulation.institution_patterns import (
    LOGICAL_NAME,
    SEEDS_LOGICAL_NAME,
    dedupe_pattern_rows,
    extract_institutions,
    load_patterns,
    pattern_to_regex,
    primary_institution,
)

OUT_DIR = Path("docs/proofs/multi-template-registry")
SAMPLE_N = 50
RNG = 0

DELTA_KEYS = (
    "sibling_rekenkamer_rate",
    "sibling_none_rate",
    "vergadering_primary_rekenkamer_fp",
    "vergadering_none_rate",
)


def _rekenkamer_pool_regex(seed_rows: list[dict[str, Any]]) -> re.Pattern[str]:
    """Union of *seed* rekenkamer surfaces for sibling-pool sampling."""
    parts = [
        pattern_to_regex(str(r["pattern"])).pattern
        for r in seed_rows
        if r["institution_target"] == "rekenkamer"
    ]
    if not parts:
        raise ValueError("no rekenkamer patterns in institution_patterns_seeds")
    return re.compile("|".join(f"(?:{p})" for p in parts), re.IGNORECASE)


def _sample(frame: pd.DataFrame, n: int) -> pd.DataFrame:
    if len(frame) <= n:
        return frame.copy()
    return frame.sample(n, random_state=RNG)


def _year_from_record(record: dict[str, Any]) -> int | None:
    raw = record.get("year")
    if raw is None or (isinstance(raw, float) and pd.isna(raw)):
        return None
    try:
        return int(raw)
    except (TypeError, ValueError):
        return None


def build_sample() -> pd.DataFrame:
    """Lock N=50 sibling + N=50 selected using seed rekenkamer pool only."""
    seeds = load_patterns(logical_name=SEEDS_LOGICAL_NAME)
    rek_pool = _rekenkamer_pool_regex(seeds)

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
        .str.contains(rek_pool.pattern, regex=True, na=False)
    )
    rek = add_aanstelling_cues(harvest.loc[rek_mask].copy())
    cued_rek = rek.loc[rek["has_aanstelling_cue"]].copy()
    rek_s = _sample(cued_rek, SAMPLE_N)

    rows: list[dict[str, Any]] = []
    for typ, frame in (
        ("sibling_rekenkamer_cued", rek_s),
        ("vergadering_selected", sel_s),
    ):
        for record in frame.to_dict(orient="records"):
            rows.append(
                {
                    "type": typ,
                    "id": record["id"],
                    "bucket": record.get("bucket", "selected"),
                    "cue_hits": record.get("cue_hits") or "",
                    "year": _year_from_record(record),
                    "resolutions_text": str(record.get("resolutions_text") or ""),
                }
            )
    return pd.DataFrame(rows)


def score_sample(
    sample: pd.DataFrame,
    patterns: list[dict[str, Any]],
    *,
    year_scoped: bool,
) -> pd.DataFrame:
    """Classify locked sample texts with the given pattern rows."""
    rows: list[dict[str, Any]] = []
    for record in sample.to_dict(orient="records"):
        year = _year_from_record(record) if year_scoped else None
        hits = extract_institutions(
            str(record.get("resolutions_text") or ""),
            year=year,
            rows=patterns,
        )
        prim = primary_institution(hits)
        rows.append(
            {
                "type": record["type"],
                "id": record["id"],
                "bucket": record.get("bucket", "selected"),
                "cue_hits": record.get("cue_hits") or "",
                "year": record.get("year"),
                "primary_institution": prim,
                "n_inst_hits": len(hits),
                "inst_labels": ",".join(sorted({h[0] for h in hits})),
                "example_span": hits[0][1] if hits else "",
            }
        )
    return pd.DataFrame(rows)


def summarize(
    out: pd.DataFrame,
    *,
    pattern_source: str,
    n_patterns: int,
    n_unique_surfaces: int,
) -> dict[str, Any]:
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
        "pattern_source": pattern_source,
        "n_patterns": n_patterns,
        "n_unique_surfaces": n_unique_surfaces,
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
            "Surfaces from institution_patterns (not formula_templates). "
            "Sibling pool locked to seed rekenkamer surfaces AND "
            "has_aanstelling_cue. Selected = R1 vergadering list."
        ),
    }


def _write_jsonl(path: Path, rows: list[dict[str, Any]] | dict[str, Any]) -> None:
    with path.open("w", encoding="utf-8") as handle:
        if isinstance(rows, dict):
            handle.write(json.dumps(rows, ensure_ascii=False) + "\n")
            return
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def _arm_patterns(source: str) -> tuple[list[dict[str, Any]], str, bool]:
    if source == "seeds":
        rows = load_patterns(logical_name=SEEDS_LOGICAL_NAME)
        return rows, SEEDS_LOGICAL_NAME, False
    if source == "harvest":
        rows = load_patterns(logical_name=LOGICAL_NAME)
        return rows, LOGICAL_NAME, True
    raise ValueError(f"unknown arm source {source!r}")


def _run_arm(
    sample: pd.DataFrame,
    source: str,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    patterns, logical, year_scoped = _arm_patterns(source)
    scored = score_sample(sample, patterns, year_scoped=year_scoped)
    metrics = summarize(
        scored,
        pattern_source=logical,
        n_patterns=len(patterns),
        n_unique_surfaces=len(dedupe_pattern_rows(patterns)),
    )
    return scored, metrics


def _delta(seeds: dict[str, Any], harvest: dict[str, Any]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for key in DELTA_KEYS:
        s_val = seeds.get(key)
        h_val = harvest.get(key)
        if isinstance(s_val, (int, float)) and isinstance(h_val, (int, float)):
            out[key] = round(float(h_val) - float(s_val), 4)
        else:
            out[key] = None
    out["pass_no_fp_rekenkamer_on_selected"] = {
        "seeds": seeds.get("pass_no_fp_rekenkamer_on_selected"),
        "harvest": harvest.get("pass_no_fp_rekenkamer_on_selected"),
    }
    out["pass_usable_rekenkamer_recall_on_cued_siblings"] = {
        "seeds": seeds.get("pass_usable_rekenkamer_recall_on_cued_siblings"),
        "harvest": harvest.get("pass_usable_rekenkamer_recall_on_cued_siblings"),
    }
    return out


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Prove appointment institution discrimination (seeds vs harvest)."
    )
    parser.add_argument(
        "--source",
        choices=("seeds", "harvest", "compare"),
        default="compare",
        help="Pattern arm to score (default: compare both on one locked sample)",
    )
    args = parser.parse_args()

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    sample = build_sample()

    if args.source == "compare":
        seeds_out, seeds_m = _run_arm(sample, "seeds")
        harvest_out, harvest_m = _run_arm(sample, "harvest")
        compare = {
            "sample_n_per_type": SAMPLE_N,
            "sibling_pool": "institution_patterns_seeds rekenkamer union",
            "seeds": seeds_m,
            "harvest": harvest_m,
            "deltas_harvest_minus_seeds": _delta(seeds_m, harvest_m),
        }
        seeds_path = OUT_DIR / "appointment_institution_sample_seeds.jsonl"
        harvest_path = OUT_DIR / "appointment_institution_sample_harvest.jsonl"
        compare_path = OUT_DIR / "appointment_institution_metrics_compare.jsonl"
        _write_jsonl(seeds_path, seeds_out.to_dict(orient="records"))
        _write_jsonl(harvest_path, harvest_out.to_dict(orient="records"))
        _write_jsonl(compare_path, compare)
        print(f"wrote {seeds_path} ({len(seeds_out)} rows)")
        print(f"wrote {harvest_path} ({len(harvest_out)} rows)")
        print(f"wrote {compare_path}")
        print(json.dumps(compare, indent=2, ensure_ascii=False))
        return

    scored, metrics = _run_arm(sample, args.source)
    rows_path = OUT_DIR / "appointment_institution_sample.jsonl"
    metrics_path = OUT_DIR / "appointment_institution_metrics.jsonl"
    _write_jsonl(rows_path, scored.to_dict(orient="records"))
    _write_jsonl(metrics_path, metrics)
    print(f"wrote {rows_path} ({len(scored)} rows)")
    print(f"wrote {metrics_path}")
    print(json.dumps(metrics, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
