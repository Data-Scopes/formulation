# STEPT1ae — Wire overlap-cue prove into family fold

**Goal:** Call STEPT1ad prove helpers from `fold_phrases` when `--overlap` / `--overlap-fixture` is set; rewrite `formula_family_candidates` + skim; no auto-mint.
**Done when:** fixture `--overlap-fixture` unites gedelibereert chain; default fold without flag unchanged; NOTES filled; `PLAN.md` updated.

**Prerequisite:** STEPT1ad accepted; `phrases_5gram_overlap` in local.toml for full `--overlap`.

## Constraint (locked)

- Default path (no flag) = STEPT1ab behavior.
- Overlap pass: union + paradigm + F1b annotate from `overlap_cue_prove`; then existing variant_fold.
- `human_role` empty; no `formula_templates` write; no F1b lookahead.
- `overlap_freq` = merge weight only (not written as typology prevalence).

## You do

```bash
uv run pytest tests/test_formula_family_fold.py tests/test_overlap_cue_prove.py -q
uv run python scripts/run_formula_family_fold.py --fixture-only --overlap-fixture
# full re-fold (user; streams ~7M edges filtered to profile norms):
# uv run python scripts/run_formula_family_fold.py --overlap
uv run python -m data_io.check
```

Fill: [`docs/proofs/multi-template-registry/STEPT1ae-overlap-cue-fold-wire.md`](../../docs/proofs/multi-template-registry/STEPT1ae-overlap-cue-fold-wire.md).

## Eval gates (NOTES)

1. Without `--overlap`: same family count class as STEPT1ab fixture.
2. With `--overlap-fixture`: gedelibereert skim chain → 1 family, `overlap_cue=waar_op`.
3. Every family still has null `human_role`.

## After this step

Human skim refreshed xlsx (cue/place columns) → typology map. Clear the chat before the next step.
