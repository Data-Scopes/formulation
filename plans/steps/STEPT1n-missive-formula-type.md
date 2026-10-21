# STEPT1n — Missive opener formula-type measure (STEPT1k-style)

**Goal:** Accept **missive opener** (*Ontfangen een Missive van ...*) as a formula type (A) by alignment (slot-cloud + DAG), mirroring STEPT1k's requeste opener exactly. Same metric schema as STEPT1a2/STEPT1k. Gold = ES `proposition_type == missive` joined to `resolutions_flat` — **not** `formula_documents.ontfangen_start` (wording-only; STEPT1e explicitly declined to accept that wording flag as a formula type, but a measured slot-cloud/DAG eval against ES gold is the same upgrade path already used for advies and requeste).
**Done when:** provenanced `formula_type_missive_metrics` + `_scores` written; NOTES pass/fail; `data_io.check` clean.

**Prerequisite:** STEPT1m done (3-core accepted: appointment/advies/requeste). Empirical canonic for the opener is already established from `formula_period_bins.OPENING_FAMILIES["ontfangen_start"]`: `"Ontfangen een missive van"`.

## You do

```bash
uv run pytest tests/test_missive_formula_type.py -q

# First run: refresh ES gold → write missive_es_gold, then measure
uv run python scripts/eval_missive_formula_type.py --refresh-gold

# Later re-measure from frozen gold (no ES)
uv run python scripts/eval_missive_formula_type.py

# Smoke (no parquet / ES)
uv run python scripts/eval_missive_formula_type.py --fixture-only

uv run python -m data_io.check
```

Fill / judge: [`docs/proofs/multi-template-registry/STEPT1n-missive-formula-type.md`](../../docs/proofs/multi-template-registry/STEPT1n-missive-formula-type.md).

## Measurements (required)

| Metric | What |
|--------|------|
| Recall vs ES missive gold | Overall + pre/post-1731 |
| Baseline delta | Wording matcher `missive`/`missiue`/`brief`/`brieff` |
| FP rate | N=500 stratified negatives (exclude gold + bootstrap ids) |
| Align quality | Score distribution gold vs neg; operating cut = p20 holdout |
| Popularity | IDF-style weight from neg hit rate at cut |
| Cloud learning | Cue-window bootstrap accepts ≫ 0 |

## Eval gates (NOTES)

1. Overall model recall **≥ 0.70** on ES missive gold.
2. FP rate on N=500 **recorded and judged** (prefer ≤ 0.05; not ignored — STEPT1e already found ontfangen+ is only P(missive\|ont+)=0.928, so some FP against non-missive ontfangen+ resolutions is expected and should be read against that prior, not treated as a surprise).
3. Cue-window cloud `n_hits_accepted` ≫ 0.
4. Pass/fail written in proof NOTES.

## Do not

- Define the type by `formula_documents.ontfangen_start` or substring alone.
- Mix appointment / advies / requeste clouds or Track R/L gold into this eval.
- Mint subtypes or run missive+ characterisation in this session.

## After this step

Mark STEPT1n in `PLAN.md`. **Next:** mirror STEPT1m — wire `missive_ontfangen` into `composition_unknown.ACCEPTED_TYPE_IDS` + `formula_type_presence.py`, re-run the 1780 comparison (3-core → 4-core), and promote if low-noise (see STEPT1o below, same session per explicit user direction).
