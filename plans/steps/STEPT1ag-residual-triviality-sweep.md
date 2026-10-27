# STEPT1ag — Residual triviality sieve + capped review

**Goal:** After fold, park thin-family trivia; emit a **capped** absorb/truncate review shortlist (no auto-merge).
**Done when:** provenanced trivial + review + metrics; fixture tests pass; NOTES filled; `PLAN.md` updated.

**Prerequisite:** `formula_family_candidates` on disk (prefer STEPT1af `--overlap` re-fold).

## Constraint (locked)

- Pass 0 trivial sieve: token≤3, `tok:` hinge without cue/keyword, closed-class/place/office only, substring of multi exemplar, short-tail F1b, no-signal leftovers.
- Pass 1 review only if cue / formula keyword / absorb or truncate signal; **`phrase_freq_max >= 500`** (Pass A floor; `--min-freq`); then **cap ~60**.
- Below floor → park (`freq_below_min`). Cap overflow → park (`review_cap_overflow`). Cap is count-only; not a substitute for the freq floor.
- `human_keep` blank; no merge into candidates this step.

## You do

```bash
uv run pytest tests/test_formula_family_residual_sweep.py -q
uv run python scripts/run_formula_family_residual_sweep.py --fixture-only
uv run python scripts/run_formula_family_residual_sweep.py
uv run python -m data_io.check
```

Fill: [`docs/proofs/multi-template-registry/STEPT1ag-residual-triviality-sweep.md`](../../docs/proofs/multi-template-registry/STEPT1ag-residual-triviality-sweep.md).

## After this step

Human skim `formula_family_residual_review` only. Clear the chat before the next step.
