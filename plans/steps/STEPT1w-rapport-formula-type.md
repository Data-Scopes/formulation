# STEPT1w — Rapport opener formula-type measure (`IS gehoord het rapport`)

**Goal:** Accept **rapport** as a measured formula type (A) by alignment (slot-cloud + DAG), not regex / `rapport_start` flag. Same metric schema as STEPT1a2 / STEPT1k / STEPT1n. Canonic from STEPT1u empty-band reading: **`IS gehoord het rapport van`**, id **`rapport_gehoord`**.  
**Done when:** provenanced `formula_type_rapport_metrics` + `_scores` written; NOTES pass/fail; `data_io.check` clean.

**Prerequisite:** STEPT1u PASS (rapport named as sharpest residual A); STEPT1v2 closed. Gold = ES `proposition_type == rapport` joined to `resolutions_flat` — **not** the `formula_documents.rapport_start` flag.

## Constraint (locked)

- **Do not** promote to `role: "blueprint"` or wire into `composition_unknown.ACCEPTED_TYPE_IDS` here (later STEPT1m-style step if gates PASS).
- **Do not** mint voordracht or conclusie+handen in this session (STEPT1u named them; park).
- **Do not** reopen requeste L2 / leave-k or Doc B L3 here.
- Existing fixture row `rapport_surface` (`role: "doc_flag"`, dual-zone illustration) stays untouched — this type is a separate measured opener id.

## You do

```bash
uv run pytest tests/test_rapport_formula_type.py -q

# First run: refresh ES gold → write rapport_es_gold, then measure
uv run python scripts/eval_rapport_formula_type.py --refresh-gold

# Later re-measure from frozen gold (no ES)
uv run python scripts/eval_rapport_formula_type.py

# Smoke (no parquet / ES)
uv run python scripts/eval_rapport_formula_type.py --fixture-only

uv run python -m data_io.check
```

Fill / judge: [`docs/proofs/multi-template-registry/STEPT1w-rapport-formula-type.md`](../../docs/proofs/multi-template-registry/STEPT1w-rapport-formula-type.md).

## Measurements (required)

| Metric | What |
|--------|------|
| Recall vs ES gold | Overall + pre/post-1731 (schema parity; no known 1731 break for rapport) |
| Baseline delta | Same splits for wording matcher `rapport` (flag surface for deltas only) |
| FP rate | N=500 stratified negatives (exclude gold + bootstrap ids; not flag-filtered) |
| Align quality | Score distribution gold vs neg; operating cut = p20 holdout |
| Popularity | IDF-style weight from neg hit rate at cut |
| Cloud learning | Cue-window bootstrap accepts ≫ 0 |

## Eval gates (NOTES)

1. Overall model recall **≥ 0.70** on ES gold.  
2. FP rate on N=500 **recorded and judged** (prefer ≤ 0.05; mid-text `rapport` under referred requeste may inflate FP — do not ignore).  
3. Cue-window cloud `n_hits_accepted` ≫ 0 (empirical canonic, not datasheet).  
4. Pass/fail written in proof NOTES; if A accepted, next = wire/promote (separate step), not voordracht mint.

## Do not

- Define the type by `formula_documents.rapport_start` or substring alone  
- Promote / add to ACCEPTED_TYPE_IDS this session  
- Mix appointment / requeste / missive clouds into this eval  
- Run full presence / composition-unknown re-score in this session  
- Open Doc B L3 or voordracht characterisation here  

## After this step

Mark STEPT1w in `PLAN.md`. If A: later composition-wire + promote. If FAIL on FP only: record like STEPT1k (accept-with-caveat vs reject). Clear the chat before the next step.
