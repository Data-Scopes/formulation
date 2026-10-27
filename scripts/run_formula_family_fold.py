#!/usr/bin/env python3
"""STEPT1af: overlap-first fold; type from place (profile roles ignored).

    uv run python scripts/run_formula_family_fold.py --fixture-only --overlap-fixture
    uv run python scripts/run_formula_family_fold.py --overlap
    uv run python scripts/run_formula_family_fold.py --skim-xlsx-only
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from data_io import load, resolve, save_semi_structured
from formulation.formula_family_fold import DEFAULT_VARIANT_RATIO, fixture_fold, fold_phrases
from formulation.formula_family_skim import write_family_skim_xlsx
from formulation.overlap_cue_prove import (
    DEFAULT_MIN_FRAC,
    DEFAULT_MIN_OVERLAP_N,
    collect_edges_for_norms,
)
from formulation.phrases_5gram_profile import fixture_profile, normalize_phrase

ROOT = Path(__file__).resolve().parents[1]
FIXTURE_EDGES = ROOT / "tests/fixtures/overlap_cue_prove_edges.jsonl"


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--fixture-only", action="store_true")
    p.add_argument("--variant-ratio", type=float, default=DEFAULT_VARIANT_RATIO)
    p.add_argument("--no-write", action="store_true")
    p.add_argument(
        "--no-skim-xlsx",
        action="store_true",
        help="Skip formula_family_skim.xlsx",
    )
    p.add_argument(
        "--skim-xlsx-only",
        action="store_true",
        help="Rebuild skim xlsx from disk families; no re-fold",
    )
    p.add_argument(
        "--overlap",
        action="store_true",
        help="STEPT1ae: stream phrases_5gram_overlap into fold",
    )
    p.add_argument(
        "--overlap-fixture",
        action="store_true",
        help="STEPT1ae: use tests/fixtures/overlap_cue_prove_edges.jsonl",
    )
    p.add_argument("--overlap-min-n", type=int, default=DEFAULT_MIN_OVERLAP_N)
    p.add_argument("--overlap-min-frac", type=float, default=DEFAULT_MIN_FRAC)
    return p.parse_args(argv)


def _load_fixture_edges() -> list[dict]:
    return [
        json.loads(line)
        for line in FIXTURE_EDGES.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def _rows_fixture() -> list[dict]:
    prof = fixture_profile()
    rows = list(prof["high_freq"]) + list(prof["rare_sidecar"])
    rows.append(
        {
            "phrase": "Ontfangen een missive van den",
            "phrase_norm": "ontfangen een missive van den",
            "phrase_freq": 88000,
            "zone": "opening",
            "lcats": "small",
            "suggested_role": "scaffolding_opener",
            "protected": False,
            "source": "high_freq",
        }
    )
    return rows


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)
    write_skim = not args.no_skim_xlsx

    if args.skim_xlsx_only:
        families = load("formula_family_candidates")
        try:
            metrics = load("formula_family_metrics")[0]
        except Exception:
            metrics = {"step": "STEPT1ab", "n_families": len(families)}
        path = Path(resolve("formula_family_skim_xlsx"))
        write_family_skim_xlsx(path, families, metrics=metrics)
        print(f"wrote family skim → {path}")
        return

    overlap_edges = None
    if args.overlap_fixture:
        overlap_edges = _load_fixture_edges()
    elif args.overlap:
        if args.fixture_only:
            rows_pre = _rows_fixture()
        else:
            high = load("phrases_5gram_high_freq")
            try:
                rare = load("phrases_5gram_rare_sidecar")
            except FileNotFoundError:
                rare = []
            rows_pre = list(high) + list(rare)
        norms = {
            normalize_phrase(str(r.get("phrase") or r.get("phrase_norm") or ""))
            for r in rows_pre
        }
        print(
            f"STEPT1ae: streaming overlap for {len(norms)} norms "
            f"(min_n={args.overlap_min_n}, min_frac={args.overlap_min_frac})…"
        )
        overlap_edges = collect_edges_for_norms(
            resolve("phrases_5gram_overlap"),
            norms,
            min_n=args.overlap_min_n,
            min_frac=args.overlap_min_frac,
        )
        print(f"STEPT1ae: kept {len(overlap_edges)} edges")

    if args.fixture_only:
        if overlap_edges is None:
            result = fixture_fold()
        else:
            result = fold_phrases(
                _rows_fixture(),
                variant_ratio=args.variant_ratio,
                overlap_edges=overlap_edges,
                overlap_min_n=args.overlap_min_n,
                overlap_min_frac=args.overlap_min_frac,
            )
    else:
        high = load("phrases_5gram_high_freq")
        try:
            rare = load("phrases_5gram_rare_sidecar")
        except FileNotFoundError:
            rare = []
        rows = list(high) + list(rare)
        result = fold_phrases(
            rows,
            variant_ratio=args.variant_ratio,
            overlap_edges=overlap_edges,
            overlap_min_n=args.overlap_min_n,
            overlap_min_frac=args.overlap_min_frac,
        )

    metrics = result["metrics"]
    families = result["families"]
    step = metrics.get("step", "STEPT1ab")
    extra = ""
    if metrics.get("overlap_enabled"):
        extra = f" overlap_merges={metrics.get('n_overlap_merges', 0)}"
    print(
        f"{step}: input={metrics['n_input_phrases']} "
        f"after_nest={metrics['n_after_nest']} "
        f"families={metrics['n_families']} "
        f"nested_dropped={metrics['n_nested_dropped']} "
        f"variant_merges={metrics['n_variant_merges']}{extra}"
    )

    if args.no_write:
        return

    save_semi_structured(
        [metrics],
        logical_name="formula_family_metrics",
        script=__file__,
        description=f"{step} fold metrics",
    )
    save_semi_structured(
        families,
        logical_name="formula_family_candidates",
        script=__file__,
        description=f"{step} family candidates (human_role empty)",
    )
    if write_skim:
        path = Path(resolve("formula_family_skim_xlsx"))
        write_family_skim_xlsx(path, families, metrics=metrics)
        print(f"wrote family skim → {path}")


if __name__ == "__main__":
    main()
