#!/usr/bin/env python3
"""STEPT1y: opener_candidates queue driver (measure → wire → propose-promote).

Human merge (collapse nested/alias surfaces into one candidate):

    uv run python scripts/run_opener_candidates_driver.py \\
        --merge harvest_conclusie_handen_bare \\
        --into harvest_conclusie_handen

    uv run python scripts/run_opener_candidates_driver.py --seed-from-fixture --no-write
    uv run python scripts/run_opener_candidates_driver.py --phase measure \\
        --candidate-id rapport_gehoord --fixture-only
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any

from formulation.opener_candidates import (
    OpenerCandidatesError,
    find_row,
    load_candidates,
    merge_candidates,
    phase_measure,
    phase_propose_promote,
    phase_wire,
    save_candidates,
    seed_rows_from_fixture,
)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument(
        "--phase",
        choices=("measure", "wire", "propose-promote"),
        default=None,
        help="Driver phase (requires --candidate-id)",
    )
    p.add_argument("--candidate-id", default=None)
    p.add_argument(
        "--merge",
        nargs="+",
        default=None,
        metavar="FROM_ID",
        help="Absorb these candidate_ids into --into (human merge)",
    )
    p.add_argument(
        "--into",
        default=None,
        help="Survivor candidate_id for --merge",
    )
    p.add_argument(
        "--canonic",
        default=None,
        help="Optional canonic for merge survivor (pocket→named if set)",
    )
    p.add_argument(
        "--seed-from-fixture",
        action="store_true",
        help="Load tests/fixtures/opener_candidates.jsonl as the queue",
    )
    p.add_argument(
        "--fixture-only",
        action="store_true",
        help="Operate on fixture rows only (no disk load); implies no live ES",
    )
    p.add_argument(
        "--apply-promote",
        action="store_true",
        help="Only with propose-promote + human promote_verdict=accept; "
        "advances status to blueprint (does not edit formula_templates)",
    )
    p.add_argument("--no-write", action="store_true")
    p.add_argument("--list", action="store_true", help="Print candidate_id + status")
    return p.parse_args(argv)


def _print_row(row: dict[str, Any]) -> None:
    keep = {
        "candidate_id": row.get("candidate_id"),
        "status": row.get("status"),
        "canonic": row.get("canonic"),
        "surfaces": row.get("surfaces"),
        "merged_from": row.get("merged_from"),
        "merged_into": row.get("merged_into"),
        "operating_cut": row.get("operating_cut"),
        "recall": row.get("recall"),
        "fp_rate": row.get("fp_rate"),
        "empty_delta": row.get("empty_delta"),
        "n_present": row.get("n_present"),
        "n_empty_support": row.get("n_empty_support"),
        "a_verdict": row.get("a_verdict"),
        "promote_verdict": row.get("promote_verdict"),
        "measured_at": row.get("measured_at"),
        "wired_at": row.get("wired_at"),
        "proposed_promote_at": row.get("proposed_promote_at"),
        "notes": row.get("notes"),
    }
    print(json.dumps(keep, ensure_ascii=False, indent=2))


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        if args.fixture_only or (args.seed_from_fixture and args.merge):
            rows = load_candidates(from_fixture=True)
        elif args.seed_from_fixture and not args.phase and not args.merge:
            rows = seed_rows_from_fixture()
        elif args.fixture_only:
            rows = load_candidates(from_fixture=True)
        else:
            rows = load_candidates(from_fixture=False)

        if args.list:
            for row in rows:
                print(
                    f"{row.get('candidate_id')}\t{row.get('status')}\t"
                    f"{row.get('canonic')}\tmerged_into={row.get('merged_into')}"
                )
            return 0

        if args.merge is not None:
            if not args.into:
                print("--merge requires --into", file=sys.stderr)
                return 2
            rows = merge_candidates(
                rows,
                into_id=args.into,
                from_ids=list(args.merge),
                canonic=args.canonic,
            )
            _print_row(find_row(rows, args.into))
            if not args.no_write and not args.fixture_only:
                path = save_candidates(rows, script=__file__)
                print(f"wrote {len(rows)} rows → {path}")
            elif args.fixture_only:
                print("(fixture-only; not written)")
            else:
                print("(--no-write)")
            return 0

        if args.phase is None:
            if args.seed_from_fixture:
                if not args.no_write:
                    path = save_candidates(rows, script=__file__)
                    print(f"wrote {len(rows)} seed rows → {path}")
                else:
                    print(f"seed ok ({len(rows)} rows); --no-write")
                return 0
            print(
                "pass --phase, --merge/--into, --seed-from-fixture, or --list",
                file=sys.stderr,
            )
            return 2

        if not args.candidate_id:
            print("--phase requires --candidate-id", file=sys.stderr)
            return 2

        if args.phase == "measure":
            rows = phase_measure(rows, args.candidate_id, fixture_only=True)
        elif args.phase == "wire":
            rows = phase_wire(rows, args.candidate_id, fixture_only=True)
        else:
            rows = phase_propose_promote(
                rows,
                args.candidate_id,
                apply_promote=args.apply_promote,
                fixture_only=True,
            )

        _print_row(find_row(rows, args.candidate_id))

        if not args.no_write and not args.fixture_only:
            path = save_candidates(rows, script=__file__)
            print(f"wrote {len(rows)} rows → {path}")
        elif args.fixture_only:
            print("(fixture-only; not written)")
        else:
            print("(--no-write)")
        return 0
    except OpenerCandidatesError as exc:
        print(f"refused: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
