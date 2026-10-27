# STEPT1af — Overlap-first fold; type from place

**Goal:** Reorder fold so overlap + place grouping + name-strip happen **before** `suggested_role`; drop pre-overlap typology authority; fix null/`waar_op`, WAAR split, gedelibereert cue.
**Done when:** unit tests green; NOTES filled; user re-runs `--overlap`; `PLAN.md` updated.

**Prerequisite:** STEPT1ae wired; STEPT1ad accepted.

## Constraint (locked)

1. Overlap before type — ignore inbound profile `suggested_role`.
2. Group by likeness + place; place hard-gates.
3. Drop `gedelibereert_*` cue; chain under `waar_op` via edges.
4. Null wins when `geen resolutie` present.
5. Split mid-window at `waar op` **or** bare mid-phrase `waar`.
6. Strip person/office fillers before exemplar/hinge.
7. Type from place + cue; never `opener_abs`/`opener_rel` OR → opener.

## You do

```bash
uv run pytest tests/test_formula_family_fold.py tests/test_overlap_cue_prove.py tests/test_phrases_5gram_profile.py -q
uv run python scripts/run_formula_family_fold.py --fixture-only --overlap-fixture --no-write
# full re-fold:
uv run python scripts/run_formula_family_fold.py --overlap
uv run python -m data_io.check
```

Fill: [`docs/proofs/multi-template-registry/STEPT1af-overlap-first-type-from-place.md`](../../docs/proofs/multi-template-registry/STEPT1af-overlap-first-type-from-place.md).

## After this step

Human skim refreshed xlsx. Clear the chat before the next step.
