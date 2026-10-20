# STEPT1k — Requeste opener formula-type measure (STEPT1a2-style)

**Goal:** Accept **requeste opener** as a formula type (A) by alignment (slot-cloud + DAG), not regex / provisional `requeste_start` wording. Same metric schema as STEPT1a2 advies. Closes the STEPT1j empty-band head (rekest-headed; presence missed the opener).  
**Done when:** provenanced `formula_type_requeste_metrics` + `_scores` written; NOTES pass/fail; `data_io.check` clean.

**Prerequisite:** STEPT1j2 PASS (empty ≠ R1/L1). Gold = ES `proposition_type == rekest` joined to `resolutions_flat` text — **not** `formula_documents.requeste_start` / `request_start` flags (wording-only; late bins collapsed in STEPT1-period).

## You do

```bash
uv run pytest tests/test_requeste_formula_type.py -q

# First run: refresh ES gold → write rekest_es_gold, then measure
uv run python scripts/eval_requeste_formula_type.py --refresh-gold

# Later re-measure from frozen gold (no ES)
uv run python scripts/eval_requeste_formula_type.py

# Smoke (no parquet / ES)
uv run python scripts/eval_requeste_formula_type.py --fixture-only

uv run python -m data_io.check
```

Fill / judge: [`docs/proofs/multi-template-registry/STEPT1k-requeste-formula-type.md`](../../docs/proofs/multi-template-registry/STEPT1k-requeste-formula-type.md).

## Measurements (required)

| Metric | What |
|--------|------|
| Recall vs ES rekest gold | Overall + pre/post-1731 (schema parity; no known 1731 break for requeste) |
| Baseline delta | Same splits for wording matcher `requeste`/`rekest`/`reqte` |
| FP rate | N=500 stratified negatives (exclude gold + bootstrap ids; not flag-filtered) |
| Align quality | Score distribution gold vs neg; operating cut = p20 holdout |
| Popularity | IDF-style weight from neg hit rate at cut |
| Cloud learning | Cue-window bootstrap accepts ≫ 0 |

## Eval gates (NOTES)

1. Overall model recall **≥ 0.70** on ES rekest gold.  
2. FP rate on N=500 **recorded and judged** (prefer ≤ 0.05; not ignored).  
3. Cue-window cloud `n_hits_accepted` ≫ 0 (empirical canonic `IS ter Vergaderinge geleesen de Requeste`, not datasheet-only).  
4. Pass/fail written in proof NOTES.

## Do not

- Define the type by `formula_documents.requeste_start` / `request_start` or substring alone  
- Treat provisional presence `requeste_start` as already accepted  
- Mix appointment / advies clouds or Track R/L gold into this eval  
- Mint subtypes or run requeste+ characterisation in this session  
- Expand 17c requeste period map (deferred track S)

## After this step

Mark STEPT1k in `PLAN.md`. **Next:** subtype characterisation under **requeste+** (STEPT1l — mirror STEPT1f under ontfangen+). Clear the chat before the next step.
