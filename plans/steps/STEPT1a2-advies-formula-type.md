# STEPT1a2 — Advies formula-type measure (STEPT1a-style)

**Goal:** Accept **advies** as a formula type by alignment (slot-cloud + DAG), not regex. Same metric schema as STEPT1a appointment.  
**Done when:** provenanced `formula_type_advies_metrics` + `_scores` written; NOTES pass/fail; `data_io.check` clean.

**Prerequisite:** STEPT1d PASS (next A family). Gold = ES `proposition_type == advies` (995 ids in 1705–1796), joined to `resolutions_flat` text — **not** the `formula_documents.advies` flag (35k; wording only).

## You do

```bash
uv run pytest tests/test_advies_formula_type.py -q

# First run: refresh ES gold → write advies_es_gold, then measure
uv run python scripts/eval_advies_formula_type.py --refresh-gold

# Later re-measure from frozen gold (no ES)
uv run python scripts/eval_advies_formula_type.py

# Smoke (no parquet / ES)
uv run python scripts/eval_advies_formula_type.py --fixture-only

uv run python -m data_io.check
```

## Measurements (required)

| Metric | What |
|--------|------|
| Recall vs ES gold | Overall + pre/post-1731 (schema parity; no known 1731 break for advies) |
| Baseline delta | Same splits for wording matcher `advi[sz]` (datasheet seed `advis`) |
| FP rate | N=500 stratified negatives (exclude gold + bootstrap ids; not flag-filtered) |
| Align quality | Score distribution gold vs neg; operating cut = p20 holdout |
| Popularity | IDF-style weight from neg hit rate at cut |
| Cloud learning | Cue-window bootstrap accepts ≫ 0 |

## Eval gates (NOTES)

1. Overall model recall **≥ 0.70** on ES gold (ballpark; wording often ~0.9 on this type).  
2. FP rate on N=500 **recorded and judged** (prefer ≤ 0.05; not ignored).  
3. Cue-window cloud `n_hits_accepted` ≫ 0 (empirical canonic, not datasheet `"..."`).  
4. Pass/fail written in `docs/proofs/multi-template-registry/STEPT1a2-advies-formula-type.md`.

## Do not

- Define the type by `formula_documents.advies` or substring alone  
- Use `praeside_start` / `praesentibus_start`  
- Mix appointment clouds or Track R gold into this eval  
- Run full presence / position / order in this session  

## After this step

Mark STEPT1a2 in `PLAN.md`. Next: wire accepted advies into presence bags (T1b-style refresh), or another A family / sieve residual. Clear the chat before the next step.
