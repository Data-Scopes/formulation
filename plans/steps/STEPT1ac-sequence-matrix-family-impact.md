# STEPT1ac — Sequence-matrix impact (canonical exemplars)

**Goal:** Do science on a **canonical form** — rebuild sequence-matrix harvest from family **exemplars** (not nested 5-gram surfaces), skim families with blank `keep`/`human_role`, compare to STEPT1z with hard + soft metrics.
**Done when:** DECISIONS named; family skim xlsx; impact metrics (+ optional year matrix on exemplars); NOTES filled; no auto-mint.

**Prerequisite:** STEPT1aa/ab 1780 outputs on disk (`formula_family_candidates`).

## Principle (locked)

Exemplar = join key for matrix / typology / counts. Members = skim evidence only. Zone ≠ role. Blank until human decide.

## You do

```bash
uv run pytest tests/test_formula_family_skim.py tests/test_formula_sequence_family_impact.py -q
uv run python scripts/run_formula_family_fold.py --skim-xlsx-only
uv run python scripts/run_formula_sequence_family_impact.py --catalog-only
# Full year matrix on exemplars (1780; slower; does not overwrite STEPT1z):
uv run python scripts/run_formula_sequence_family_impact.py --year 1780
uv run python -m data_io.check
```

## Eval gates

1. Soft containment: most STEPT1z harvest surfaces sit under some family exemplar/member.
2. Hard: fewer harvest nodes than STEPT1z nested shortlist (after cap); empty/node deltas reported.
3. No auto-`named` / blueprint mint.

## After this step

Human fills skim `keep`/`human_role` → typology map. Clear chat before next step.
