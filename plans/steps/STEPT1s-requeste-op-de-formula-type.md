# STEPT1s — Mint + calibrate `requeste_op_de` (`Op de Requeste`)

**Goal:** Accept the STEPT1r-named short requeste opener as a measured formula type (A), same slot-cloud + DAG schema as STEPT1k. Canonic **`Op de Requeste`**, id **`requeste_op_de`**. Long type `requeste_geleesen` stays untouched this step.  
**Done when:** provenanced `formula_type_requeste_op_de_metrics` + `_scores` written; NOTES pass/fail (FP judged carefully — three-token opener is loose); `data_io.check` clean.

**Prerequisite:** STEPT1r PASS + human name confirmed (`docs/DECISIONS.md` 2026-10-22). Frozen `rekest_es_gold` on disk (no ES refresh required unless gold is missing).

## Constraint (locked)

- **Do not** promote to `role: "blueprint"` or wire into `composition_unknown.ACCEPTED_TYPE_IDS` here (that is a later STEPT1m-style step if gates PASS).
- **Do not** change `requeste_geleesen`’s frozen cut or cloud.
- **Do not** open the letter/missive short-opener parallel (parked until this type is measured).
- Gold is **short-form rekest**, not full ES rekest: filter `rekest_es_gold` to head `Op`/`OP`/`op` + `de` + requeste-surface. Full-rekest recall would fail ≥0.70 by construction (~37% short on clean gold).

## You do

```bash
uv run pytest tests/test_requeste_op_de_formula_type.py -q

# Smoke (no parquet / ES)
uv run python scripts/eval_requeste_op_de_formula_type.py --fixture-only

# Measure from frozen rekest_es_gold (needs resolutions_flat only for negatives)
uv run python scripts/eval_requeste_op_de_formula_type.py

uv run python -m data_io.check
```

Fill / judge: [`docs/proofs/multi-template-registry/STEPT1s-requeste-op-de-formula-type.md`](../../docs/proofs/multi-template-registry/STEPT1s-requeste-op-de-formula-type.md).

## Measurements (required)

| Metric | What |
|--------|------|
| Recall vs short-form rekest gold | Overall + pre/post-1731 (head-filtered ES rekest) |
| Baseline delta | Head wording `op de requeste/rekest/reqte` (surface of the name) |
| FP rate | N=500 stratified negatives (exclude full ES rekest gold + bootstrap ids) |
| Cross-fire diagnostic | Short model on a sample of long-head rekest (expect low fire rate) |
| Align quality | Score distribution gold vs neg; operating cut = p20 holdout |
| Popularity | IDF-style weight from neg hit rate at cut |
| Cloud learning | Cue-window bootstrap accepts ≫ 0 |

## Eval gates (NOTES)

1. Overall model recall **≥ 0.70** on short-form gold.  
2. FP rate on N=500 **recorded and judged** (prefer ≤ 0.05; expect higher — short canonic; do not ignore).  
3. Cue-window cloud `n_hits_accepted` ≫ 0.  
4. Pass/fail written in proof NOTES; if A accepted, next = wire/promote (separate step), not letter parallel.

## Do not

- Mint from band n without the STEPT1r name (already confirmed)  
- Redefine gold as full ES rekest  
- Recalibrate or ablate `requeste_geleesen` here  
- Run Doc B L2 slot reduction  
- Fold missive/letter short-opener work into this session  

## After this step

Mark STEPT1s in `PLAN.md`. If A: later composition-wire + promote. If FAIL on FP only: record like STEPT1k (accept-with-caveat vs reject). Clear the chat before the next step.
