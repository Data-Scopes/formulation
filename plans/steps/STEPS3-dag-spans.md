# STEPS3 — DAG / SW spans on real windows

**Goal:** Run SW single, SW slot-cloud, and DAG alignment on STEPS1 candidate windows using the STEPS2 slot-cloud; write provenanced span JSONL.  
**Done when:** `formula_boundary_spans` + `formula_boundary_span_metrics` are registered and written via `data_io`; `uv run python -m data_io.check` is clean; pytest smoke passes; fixture-only and `--from-windows` paths work.

## Prerequisites

STEPS0–2. Read [`plans/milestones/S1-formula-boundary-evolution.md`](../milestones/S1-formula-boundary-evolution.md) and [`docs/formula-boundary-evolution.md`](../../docs/formula-boundary-evolution.md). Do **not** calibrate the STEPS1 cosine cut, run GysBERT, FormulaSearch, or mix L1/R1 harvest in this session.

## You do

Smoke (no year slice):

```bash
uv run python -m data_io.check
uv run python scripts/run_span_harvest.py --fixture-only
uv run pytest tests/test_span_harvest.py -q
```

From existing STEPS1 candidates + STEPS2 cloud:

```bash
uv run python scripts/run_span_harvest.py --from-windows
```

Year-slice POC (user terminal; optional `--limit`):

```bash
uv run python scripts/run_span_harvest.py --year 1780 --limit 200
uv run python -m data_io.check
```

## Cursor guides

- Package: `formulation/boundary/span_harvest.py`. Script: `scripts/run_span_harvest.py`.
- Methods per window: `align_sw_single`, `align_sw_cloud`, `align_dag` (optional slots from cloud).
- Inputs: STEPS1 `formula_tfidf_windows` (or framed year slice / fixture seeds) + STEPS2 `formula_slot_cloud` (`variant_lists`, `optional_slots`).
- Align on `window_text` tokens; map local `[start, end)` to document offsets via `token_start` when present.
- Output schema: one row per window × method with local + doc spans, score, latency, matched tokens, archival `id` / TF-IDF score.
- Metrics: per-method latency / score / span-length notes + SW-cloud↔DAG agreement; IoU only when gold spans are present (fixture path).
- Do **not** freeze STEPS1 thresholds here. 17c templates stay deferred. No GysBERT (STEPS4).

## Next step

STEPS4 — written GysBERT residual yes/no decision.
