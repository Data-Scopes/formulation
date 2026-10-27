# T1 — Emergent medoid + relative-gap cliff (limited POC)

**Status:** **next** after GitHub upload — limited POC for human steer (not full EM/DAG).  
**Source:** `republic_ner_matching` detour residue + 2026-10-27 bubble-up decision.  
**Decision:** [`docs/DECISIONS.md`](../../docs/DECISIONS.md) 2026-10-27 growth edge = bubble-up.

## Goal (POC)

Show a **small** emergent medoid set from scoped formula-ish windows + `char_wb` TF-IDF clustering + **cliff/relative-gap** freq sieve — enough for the human to steer merge/split/scope — **without** minting blueprints or building a transition DAG.

Hand hinge catalogue = **later comparison only** (optional overlap table), not the scoring target.

## POC scope (keep small)

- Population: openings / unique-start heads already in-repo (or a capped 1780 onset sample) — **not** full HTR 5-gram dump.
- Cluster → medoid labels; print ranked freq + proposed cliff cut.
- Output: provenanced medoid list + metrics JSONL; optional skim xlsx (blank human fields).
- Optional one-pager: overlap vs `formula_hinge_candidates` (comparison only).

## Out of POC

- EM refinement loop, transition matrix, `[SLOT]`, Viterbi formula-DAG
- Auto-mint to `formula_templates` / hinge ledger
- Port of matching underparse cutter / PINNED_TO

## Done when

Fixture or small real run + NOTES with cliff cut + medoid sample; human steer call recorded; `data_io.check` clean.

## Do not

- Treat STEPT1ah–aj seeds as ground truth types
- Reopen STEPT1aa–ag fold as typology growth without cliff sieve
