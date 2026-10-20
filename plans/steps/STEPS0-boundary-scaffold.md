# STEPS0 — Boundary scaffold (metrics + SW + DAG)

**Goal:** Register a tiny span-gold fixture and a comparative runner for Smith-Waterman (single / slot-cloud) and DAG alignment.  
**Done when:** `formula_boundary_cases` and `formula_boundary_benchmark_metrics` are in the manifest; `uv run python -m data_io.check` is clean; `uv run python scripts/run_boundary_benchmark.py` prints IoU / delta / ms; pytest smoke passes.

## Prerequisites

Read [`plans/milestones/S1-formula-boundary-evolution.md`](../milestones/S1-formula-boundary-evolution.md) and [`docs/formula-boundary-evolution.md`](../../docs/formula-boundary-evolution.md). Do **not** run full-corpus TF-IDF, GysBERT, or FormulaSearch in this session.

## You do

```bash
uv sync
uv run python -m data_io.check
uv run python scripts/run_boundary_benchmark.py
uv run pytest tests/test_boundary_metrics.py -q
```

## Cursor guides

- Package: `formulation/boundary/` — `metrics`, `align_sw`, `align_dag`, `benchmark`
- Fixture: `tests/fixtures/formula_boundary_cases.jsonl` — half-open `[gt_start, gt_end)` token spans
- Script writes metrics with `save_semi_structured(..., logical_name="formula_boundary_benchmark_metrics")`
- Dep: `rapidfuzz` for word-level Levenshtein; reuse R1 `char_wb` family only from STEPS1 onward

## Next step

[STEPS1-tfidf-window-framing.md](STEPS1-tfidf-window-framing.md)
