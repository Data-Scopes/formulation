#!/usr/bin/env python3
"""STEPT1aj: near+mid hinge-witness skim workbook + ingest.

    uv run python scripts/run_formula_hinge_witness_skim.py --fixture-only
    uv run python scripts/run_formula_hinge_witness_skim.py
    uv run python scripts/run_formula_hinge_witness_skim.py --ingest
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from data_io import load, resolve, save_semi_structured
from formulation.formula_hinge_witness import LOGICAL_NAME as ADJUDICATION_NAME
from formulation.formula_hinge_witness_skim import (
    LOGICAL_VERDICTS,
    LOGICAL_XLSX,
    METRICS_NAME,
    fixture_adjudication_for_skim,
    ingest_skim_xlsx,
    load_hinge_rows_for_skim,
    skim_metrics,
    skim_rows,
    write_skim_xlsx,
)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument(
        "--fixture-only",
        action="store_true",
        help="Build skim from fixture adjudication; print metrics; do not write",
    )
    p.add_argument(
        "--ingest",
        action="store_true",
        help="Ingest filled human_keep from skim xlsx → verdicts",
    )
    p.add_argument("--no-write", action="store_true")
    return p.parse_args(argv)


def _build(args: argparse.Namespace) -> int:
    hinges = load_hinge_rows_for_skim()
    if args.fixture_only:
        adjudication = fixture_adjudication_for_skim()
    else:
        adjudication = list(load(ADJUDICATION_NAME))

    skim = skim_rows(adjudication, hinges=hinges)
    m = skim_metrics(adjudication, skim)
    print(
        f"STEPT1aj: n_adjudication={m['n_adjudication']} n_skim={m['n_skim']} "
        f"by_band_skim={m['by_band_skim']} "
        f"(far parked={m['by_band_adjudication'].get('far', 0)})"
    )
    for r in skim[:6]:
        print(
            f"  {r['band']:4} {r['best_sim']:.3f} → {r['best_hinge_id']:20} "
            f"| {str(r['witness_text'])[:50]}"
        )

    if args.fixture_only or args.no_write:
        # Still exercise xlsx write to a temp path under fixture-only? No — dry.
        if args.fixture_only:
            tmp = Path("/tmp/formula_hinge_witness_skim_fixture.xlsx")
            write_skim_xlsx(tmp, adjudication, hinges=hinges, metrics=m)
            print(f"  fixture xlsx smoke → {tmp}")
        return 0

    path = Path(resolve(LOGICAL_XLSX))
    write_skim_xlsx(path, adjudication, hinges=hinges, metrics=m)
    save_semi_structured(
        [m],
        logical_name=METRICS_NAME,
        script=__file__,
        description="STEPT1aj near+mid skim emit metrics (far parked)",
    )
    # Touch provenance for xlsx via a tiny sidecar metrics already; also register path.
    print(f"STEPT1aj: wrote skim → {path}")
    return 0


def _ingest(args: argparse.Namespace) -> int:
    path = Path(resolve(LOGICAL_XLSX))
    if not path.is_file():
        print(f"STEPT1aj: skim xlsx missing: {path}", file=sys.stderr)
        return 1
    judged, summary = ingest_skim_xlsx(path)
    print(
        f"STEPT1aj ingest: n_judged={summary['n_judged']} "
        f"by_keep={summary['by_human_keep']} by_band={summary['by_band_judged']}"
    )
    if args.no_write:
        return 0
    save_semi_structured(
        judged,
        logical_name=LOGICAL_VERDICTS,
        script=__file__,
        description="STEPT1aj human near+mid skim verdicts (filled human_keep only)",
    )
    save_semi_structured(
        [summary],
        logical_name=METRICS_NAME,
        script=__file__,
        description="STEPT1aj near+mid skim ingest summary",
    )
    return 0


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if args.ingest and args.fixture_only:
        print("STEPT1aj: use --ingest or --fixture-only, not both", file=sys.stderr)
        return 1
    if args.ingest:
        return _ingest(args)
    return _build(args)


if __name__ == "__main__":
    raise SystemExit(main())
