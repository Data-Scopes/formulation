#!/usr/bin/env python3
"""STEPT1z / STEPT1z2: probabilistic sequence matrix + archetypal examples.

    uv run python scripts/run_formula_sequence_matrix.py --fixture-only
    uv run python scripts/run_formula_sequence_matrix.py --year 1780
    uv run python scripts/run_formula_sequence_matrix.py --xlsx-from-disk --year 1780
"""

from __future__ import annotations

import argparse
import json
from typing import Any

from data_io import load, save_semi_structured
from formulation.formula_sequence_matrix import (
    DEFAULT_YEAR,
    MIN_EDGE_N_ADJACENT,
    build_archetypal_examples,
    fixture_matrix,
    fixture_sequences,
    fixture_texts_by_id,
    harvest_catalog,
    harvest_records,
    matrix_edges_records,
    matrix_nodes_records,
    run_year_matrix,
    sequence_score_records,
    write_human_xlsx,
)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--fixture-only", action="store_true")
    p.add_argument("--year", type=int, default=DEFAULT_YEAR)
    p.add_argument("--limit", type=int, default=None)
    p.add_argument(
        "--max-harvest",
        type=int,
        default=40,
        help="Cap scheme harvest surfaces (pocket surfaces always kept)",
    )
    p.add_argument(
        "--xlsx-from-disk",
        action="store_true",
        help="Rebuild Excel from metrics jsonl; with --year also rebuild examples",
    )
    p.add_argument("--no-write", action="store_true")
    p.add_argument(
        "--no-xlsx",
        action="store_true",
        help="Skip human Excel workbook (jsonl only)",
    )
    p.add_argument(
        "--no-examples",
        action="store_true",
        help="Skip archetypal example sheets / jsonl",
    )
    return p.parse_args(argv)


def _metrics_row(matrix: dict[str, Any]) -> dict[str, Any]:
    """Compact metrics record (no full wide P dump — edges carry that)."""
    keep = {
        "year",
        "n_resolutions",
        "n_empty",
        "frac_empty",
        "primary",
        "row_sum_ok",
        "n_edges",
        "n_nodes",
        "n_harvest_surfaces",
        "limit",
        "columns",
        "row_sums",
    }
    out = {k: matrix.get(k) for k in keep if k in matrix}
    edges = [
        e
        for e in matrix.get("edges") or []
        if e.get("to_id") != "END" and float(e.get("p_adjacent") or 0) > 0
    ]
    edges.sort(key=lambda e: (-float(e["p_adjacent"]), -int(e["n_adjacent"])))
    out["top_p_adjacent"] = edges[:15]
    out["P_adjacent"] = matrix.get("P_adjacent")
    out["N_adjacent"] = matrix.get("N_adjacent")
    return out


def _matrix_from_disk() -> tuple[dict[str, Any], list[dict[str, Any]]]:
    metrics = load("formula_sequence_matrix_metrics")[0]
    edges = load("formula_sequence_matrix")
    nodes = load("formula_sequence_nodes")
    try:
        harvest = load("formula_sequence_harvest")
    except FileNotFoundError:
        harvest = []
    matrix = dict(metrics)
    matrix["edges"] = edges
    matrix["nodes"] = nodes
    return matrix, harvest


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    node_examples: list[dict[str, Any]] = []
    edge_examples: list[dict[str, Any]] = []

    if args.xlsx_from_disk:
        matrix, harvest_out = _matrix_from_disk()
        if not args.no_examples:
            # Re-score sequences for hits + texts (P matrix kept from disk)
            _m, sequences, harvest, texts_by_id = run_year_matrix(
                year=args.year,
                limit=args.limit,
                max_harvest=args.max_harvest,
            )
            del _m
            node_examples, edge_examples = build_archetypal_examples(
                sequences, texts_by_id, matrix
            )
            if not args.no_write:
                save_semi_structured(
                    node_examples + edge_examples,
                    logical_name="formula_sequence_examples",
                    parent_sources=["formula_sequence_matrix_metrics"],
                    script=__file__,
                )
        path = write_human_xlsx(
            matrix,
            harvest=harvest_out,
            node_examples=node_examples,
            edge_examples=edge_examples,
        )
        print(
            f"wrote human workbook → {path} "
            f"(examples nodes={len(node_examples)} edges={len(edge_examples)})"
        )
        return 0

    if args.fixture_only:
        matrix = fixture_matrix()
        sequences = fixture_sequences()
        harvest = harvest_catalog()
        texts_by_id = fixture_texts_by_id()
        matrix["n_harvest_surfaces"] = len(harvest)
    else:
        matrix, sequences, harvest, texts_by_id = run_year_matrix(
            year=args.year,
            limit=args.limit,
            max_harvest=args.max_harvest,
        )

    metrics = _metrics_row(matrix)
    edges = matrix_edges_records(matrix)
    nodes = matrix_nodes_records(matrix)
    scores = sequence_score_records(sequences)
    harvest_out = harvest_records(harvest, matrix)

    if not args.no_examples:
        min_edge = 1 if args.fixture_only else MIN_EDGE_N_ADJACENT
        node_examples, edge_examples = build_archetypal_examples(
            sequences,
            texts_by_id,
            matrix,
            min_edge_n=min_edge,
        )

    print(
        json.dumps(
            {
                "year": metrics.get("year"),
                "n_resolutions": metrics.get("n_resolutions"),
                "n_empty": metrics.get("n_empty"),
                "frac_empty": metrics.get("frac_empty"),
                "row_sum_ok": metrics.get("row_sum_ok"),
                "n_nodes": metrics.get("n_nodes"),
                "n_edges": metrics.get("n_edges"),
                "n_node_examples": len(node_examples),
                "n_edge_examples": len(edge_examples),
                "top_p_adjacent": metrics.get("top_p_adjacent"),
            },
            ensure_ascii=False,
            indent=2,
        )
    )

    if args.no_write:
        if not args.no_xlsx:
            path = write_human_xlsx(
                matrix,
                harvest=harvest_out,
                node_examples=node_examples,
                edge_examples=edge_examples,
            )
            print(f"(--no-write jsonl; xlsx → {path})")
        else:
            print("(--no-write)")
        return 0

    parents = ["formula_type_presence_scores", "resolutions_flat"]
    if args.fixture_only:
        parents = []

    save_semi_structured(
        [metrics],
        logical_name="formula_sequence_matrix_metrics",
        parent_sources=parents,
        script=__file__,
    )
    save_semi_structured(
        edges,
        logical_name="formula_sequence_matrix",
        parent_sources=["formula_sequence_matrix_metrics"],
        script=__file__,
    )
    save_semi_structured(
        nodes,
        logical_name="formula_sequence_nodes",
        parent_sources=["formula_sequence_matrix_metrics"],
        script=__file__,
    )
    save_semi_structured(
        scores,
        logical_name="formula_sequence_scores",
        parent_sources=["formula_sequence_matrix_metrics"],
        script=__file__,
    )
    save_semi_structured(
        harvest_out,
        logical_name="formula_sequence_harvest",
        parent_sources=["formula_sequence_matrix_metrics"],
        script=__file__,
    )
    if not args.no_examples:
        save_semi_structured(
            node_examples + edge_examples,
            logical_name="formula_sequence_examples",
            parent_sources=["formula_sequence_matrix_metrics"],
            script=__file__,
        )
    print(
        f"wrote metrics/edges/nodes/scores/harvest"
        f"{'/examples' if not args.no_examples else ''} "
        f"(n_edges={len(edges)}, n_harvest={len(harvest_out)}, "
        f"n_ex={len(node_examples)}+{len(edge_examples)})"
    )
    if not args.no_xlsx:
        path = write_human_xlsx(
            matrix,
            harvest=harvest_out,
            node_examples=node_examples,
            edge_examples=edge_examples,
        )
        print(f"wrote human workbook → {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
