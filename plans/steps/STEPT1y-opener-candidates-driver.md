# STEPT1y — Opener candidates queue + measure→wire→propose-promote driver

**Goal:** Replace twin per-opener scripts with a human-judged `opener_candidates` table and a driver that writes evidence back into it. Pipeline never auto-mints, auto-accepts A, or auto-promotes.
**Done when:** `opener_candidates` registered + seeded (6 blueprint audit rows + voordracht / conclusie_handen pockets); driver phases `measure` / `wire` / `propose-promote` write evidence and refuse without the right status/verdict; fixture-only smoke + unit tests pass; `data_io.check` clean; NOTES filled; `PLAN.md` + milestone updated.

**Prerequisite:** STEPT1x done (6 blueprints). DECISIONS 2026-10-25 (STEPT1y opened) records the write-back loop.

## Constraint (locked)

- Human writes `canonic` / `candidate_id` (pocket → named) and verdicts (`a_verdict`, `promote_verdict`).
- Driver writes evidence only (`recall`, `fp_rate`, `operating_cut`, `empty_delta`, `n_present`, timestamps, awaiting `status`).
- Do **not** mint voordracht / conclusie canonic in this step.
- Do **not** run full ES gold eval or unify the six `eval_*_formula_type.py` scripts.
- Do **not** mutate `formula_templates` / `ACCEPTED_TYPE_IDS` unless `--apply-promote` **and** `promote_verdict=accept` (default off).

## Status loop

`pocket` → `named` → `measured` (awaiting A) → `accepted_a` → `wired` (awaiting promote) → `blueprint` | `parked` | `rejected`

## You do

```bash
uv run pytest tests/test_opener_candidates.py -q

# Seed / load fixture queue (no parquet required for smoke)
uv run python scripts/run_opener_candidates_driver.py --seed-from-fixture --no-write
uv run python scripts/run_opener_candidates_driver.py --phase measure --candidate-id rapport_gehoord --fixture-only

# Human merge (collapse nested/alias surfaces into one survivor)
uv run python scripts/run_opener_candidates_driver.py \
  --merge conclusie_handen --into voordracht --canonic "…" --fixture-only

# Persist seed once (provenanced)
uv run python scripts/run_opener_candidates_driver.py --seed-from-fixture
uv run python -m data_io.check
```

Fill / judge: [`docs/proofs/multi-template-registry/STEPT1y-opener-candidates-driver.md`](../../docs/proofs/multi-template-registry/STEPT1y-opener-candidates-driver.md).

## Eval gates (NOTES)

1. Seed has six `blueprint` audit rows + two `pocket` rows (voordracht n≈80, conclusie_handen n≈41); no canonic on pockets.
2. Measure on `pocket` / unknown id **refuses**; measure on known audit id writes evidence (fixture-only).
3. Wire refuses without `a_verdict=accept` (or blueprint dry-run); propose-promote refuses without human promote verdict; `--apply-promote` default off.
4. Driver never sets `a_verdict` / `promote_verdict`.

## Do not

- Name or measure voordracht / conclusie this session
- Full ES gold / presence / composition re-score for a new type
- Auto-promote into the registry
- Re-wire the five downstream modules

## After this step

Mark STEPT1y in `PLAN.md` and `plans/milestones/T1-unknown-first.md`. Human names voordracht canonic (pocket → named) in a fresh chat; next step adds a real measure adapter. Clear the chat before the next step.
