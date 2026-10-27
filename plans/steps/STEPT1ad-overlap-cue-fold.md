# STEPT1ad — Prove overlap-cue fold (separate module)

**Goal:** Demonstrate overlap-chain + cue + place + paradigm + cardinal corpus-test principles in a **prove module** before wiring into production `formula_family_fold`.
**Done when:** fixture prove + unit tests green; NOTES filled with scenario PASS/FAIL; `houdende dat` not a cardinal; `formula_family_fold.py` untouched; no auto-mint.

**Prerequisite:** none for `--fixture-only`. Optional: `phrases_5gram_overlap` path in `data_manifest.local.toml` for `--overlap` stream smoke.

## Constraint (locked)

- Prove-first — do **not** change `fold_phrases` this step.
- `overlap_freq` = merge weight only; corpus prevalence = `corpus_hit_rate`.
- Place bands hard-gate merges; lexicon is bottom-up (bootstrap + induced hubs).
- Paradigm mask = cardinals + same-noun plural only (`brief`/`brieven`; not `missive`↔`brief`).
- Short tails (`houdende dat`) = F1b: never cardinal; `part_of` best-effort; no lookahead.
- No auto-mint / no `human_role` / no `formula_templates` write.

## You do

```bash
uv run pytest tests/test_overlap_cue_prove.py -q
uv run python scripts/prove_overlap_cue_fold.py --fixture-only
uv run python -m data_io.check
# optional:
# uv run python scripts/prove_overlap_cue_fold.py --overlap --skim-top 60
```

Fill: [`docs/proofs/multi-template-registry/STEPT1ad-overlap-cue-fold.md`](../../docs/proofs/multi-template-registry/STEPT1ad-overlap-cue-fold.md).

## Eval gates (NOTES)

1. Overlap chain merges; no-edge split holds.
2. Place / straddle / paradigm / dominant-cue scenarios PASS.
3. Cardinal shortlist capped; short tails suppressed; zero-hit → `review`.
4. F1b link documented as best-effort (PASS if suppressed + optional `part_of`).

## After this step

Accept NOTES → **STEPT1ae** wire prove helpers into fold (fresh chat). Later: F1a→F1b lookahead. Clear the chat before the next step.
