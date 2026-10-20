# Step 3 — FormulaSearch script and provenance

**Goal:** Run the first slice end to end and write candidates through `data_io`.  
**Done when:** `uv run python scripts/run_formula_search.py` produces a registered semi-structured dataset with provenance sidecars.

## Prerequisites

STEP2. Conceptual light-touch: [`docs/formula-conceptual-overview.md`](../../docs/formula-conceptual-overview.md) (mental-model steps 1–2 and 6 only).

## You do

```bash
uv run python scripts/run_formula_search.py
uv run python -m data_io.check
```

## Cursor guides

- Script: `scripts/run_formula_search.py` using `formulation` adapters + `FormulaSearch` / `extract_phrases`.
- Output via `save_semi_structured(..., logical_name="...", script=__file__)`. Register the output dataset first.
- Wire S4 seeds as `seed_phrases` and annotate candidates that match seeds (seeds are **not** ground truth).
- Retain `section` / offsets on candidate records. Allow gappy extraction knobs (`max_variables` / `max_skips`) even if the sample is small.
- Comments may name building-block / position notions; do **not** implement the M2 criteria engine here.

## Next step

[STEP4-tests-and-demo.md](STEP4-tests-and-demo.md)
