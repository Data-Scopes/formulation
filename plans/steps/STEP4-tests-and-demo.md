# Step 4 — Tests, demo notebook, README

**Goal:** Make the first slice reproducible for a later session.  
**Done when:** adapter/seed tests pass; demo notebook runs the slice; README documents the three commands below.

## Prerequisites

STEP3.

## You do

```bash
uv run pytest tests/ -q
# then open notebooks/01_formula_search_demo.ipynb
```

## Cursor guides

- Tests around **this project’s** adapters and seed reader, not an exhaustive re-test of upstream `formula_detection`.
- Demo notebook only: `notebooks/01_formula_search_demo.ipynb`. No mega output notebooks; pipeline writes still go through `data_io`.
- README: `uv sync` → `data_io.check` → `scripts/run_formula_search.py` → pytest. Domain one-liner: formulaic language in REPUBLIC resolutions.
- After this step: tick M1 in `PLAN.md`; next milestone is [M2-building-blocks.md](../milestones/M2-building-blocks.md). Clear the chat before starting M2.

## Next step

Stop. M2 is a new session: [M2-building-blocks.md](../milestones/M2-building-blocks.md).
