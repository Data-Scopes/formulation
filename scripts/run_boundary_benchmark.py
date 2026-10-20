#!/usr/bin/env python3
"""STEPS0: compare SW single / SW cloud / DAG on formula_boundary_cases.

Does not run TF-IDF framing (STEPS1) or GysBERT (STEPS4).
"""

from __future__ import annotations

from data_io import load, save_semi_structured
from formulation.boundary.benchmark import format_table, run_benchmark


def main() -> None:
    cases = load("formula_boundary_cases")
    rows = run_benchmark(cases)
    metrics_path = save_semi_structured(
        rows,
        logical_name="formula_boundary_benchmark_metrics",
        parent_sources=["formula_boundary_cases"],
        script=__file__,
    )
    print(format_table(rows))
    print(f"wrote {metrics_path}")
    print(f"cases {len(cases)} method_rows {len(rows)}")


if __name__ == "__main__":
    main()
