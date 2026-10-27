# STEPT1ab — Fold phrases into formula family candidates

**Goal:** Nest-collapse + variant-fold STEPT1aa survivors into `formula_family_candidates` (exemplar + members + zone×lcats + suggested_role). Human roles empty for write-back.
**Done when:** provenanced families + metrics; fixture tests pass; NOTES filled; no auto-mint; `PLAN.md` updated.

**Prerequisite:** STEPT1aa outputs on disk (`phrases_5gram_high_freq`, `phrases_5gram_rare_sidecar`) or `--fixture-only`.

## Constraint (locked)

- Freq alone does **not** decide merges.
- Pass B nest collapse; Pass C variant fold within hinge buckets (edit ratio + zone guard).
- `human_role` / `variant_of` stay null until human skim.
- No blueprint promote.

## You do

```bash
uv run pytest tests/test_formula_family_fold.py -q
uv run python scripts/run_formula_family_fold.py --fixture-only
uv run python scripts/run_formula_family_fold.py
uv run python -m data_io.check
```

Fill: [`docs/proofs/multi-template-registry/STEPT1ab-formula-family-fold.md`](../../docs/proofs/multi-template-registry/STEPT1ab-formula-family-fold.md).

## Eval gates (NOTES)

1. `n_families` < `n_input_phrases` when nests/variants exist.
2. Every family has empty `human_role`.
3. Metrics report nested_dropped + variant_merges.

## After this step

Human skim → typology map (STEPT1ac). **Impact check:** rebuild / compare [`STEPT1z formula_sequence_matrix`](STEPT1z-formula-sequence-matrix.md) using folded family exemplars as harvest nodes (vs nested-surface noise). Clear the chat before the next step.
