# STEPS2 — Slot-cloud bootstrap

**Goal:** Aggregate STEPS1 candidate windows into a frequency-weighted **slot-cloud** for the 18c opening template via Smith-Waterman (no MSA).  
**Done when:** `formula_slot_cloud` + `formula_slot_cloud_metrics` are registered and written via `data_io`; `uv run python -m data_io.check` is clean; pytest smoke passes; cloud is usable by `align_sw_cloud`.

## Prerequisites

STEPS0–1. Read [`plans/milestones/S1-formula-boundary-evolution.md`](../milestones/S1-formula-boundary-evolution.md) and [`docs/formula-boundary-evolution.md`](../../docs/formula-boundary-evolution.md). Do **not** run DAG span harvest on real data (STEPS3), GysBERT, FormulaSearch, or calibrate the STEPS1 cosine cut in this session.

## You do

Smoke (no year slice):

```bash
uv run python -m data_io.check
uv run python scripts/run_slot_cloud_bootstrap.py --fixture-only
uv run pytest tests/test_slot_cloud.py -q
```

From existing STEPS1 candidates (if present):

```bash
uv run python scripts/run_slot_cloud_bootstrap.py --from-windows
```

Year-slice POC (user terminal; optional `--limit`):

```bash
uv run python scripts/run_slot_cloud_bootstrap.py --year 1780 --limit 200
uv run python -m data_io.check
```

## Cursor guides

- Package: `formulation/boundary/slot_cloud.py`. Script: `scripts/run_slot_cloud_bootstrap.py`.
- Method: SW single alignment per hit → collect OCR tokens per template slot → frequency-weighted variants. **No MSA.**
- Template: same 18c `opening_requeste_18c` as STEPS1. 17c period clouds remain deferred.
- Output schema: ordered `slots[]` with `canonical`, `optional`, `variants[{token,count}]`, plus `variant_lists` for `align_sw_cloud`.
- Optional slots: hypothesis from skip rate (default **0.25**); record as hypothesis, do not freeze.
- Accept hits when matched-slot ratio ≥ **0.5** (hypothesis).
- Period filter: `--period` label + `--year` / `--year-min` / `--year-max` metadata (single-year framing for now).
- Do not mix L1/R1 harvest or FormulaSearch. Do not calibrate STEPS1 thresholds here.

## Next step

STEPS3 — provenanced DAG/SW spans on real STEPS1 windows using this cloud.
