# STEPT1h — Unknown-likeliness POC (1780)

**Goal:** Score every resolution in the year-slice presence universe by how little the **accepted cover set** explains it; write provenanced scores + high-unknown sample. No new types; no characterisation yet.  
**Done when:** `resolution_unknown_metrics` / `_scores` / `_sample` registered + written; NOTES record band sizes; `data_io.check` clean; `PLAN.md` updated.

**Prerequisite:** Doctrine locked in [`plans/milestones/T1-unknown-first.md`](../milestones/T1-unknown-first.md). Presence scores + known sets on disk for 1780 (STEPT1b/e).

## Constraint (locked)

**Unknown-first:** do not classify the corpus from incomplete expert inventories. Cover = accepted evidence only. High unknown = triage for later content characterisation — not a residual subtype id.

Not STEPT1e1. Not STEPT1g again (that inventoried missive residual structure). Not promoting templates.

## You do

```bash
uv run pytest tests/test_unknown_likeliness.py -q

uv run python scripts/run_unknown_likeliness.py --fixture-only

# Full 1780 (reuse presence + known sets; optional word counts for sample strata)
uv run python scripts/run_unknown_likeliness.py --year 1780

uv run python -m data_io.check
```

Fill: [`docs/proofs/multi-template-registry/STEPT1h-unknown-likeliness.md`](../../docs/proofs/multi-template-registry/STEPT1h-unknown-likeliness.md) — band counts only; reading waits for characterisation.

## Design locks

| Piece | Rule |
|-------|------|
| Universe | Presence-score year slice (1780 first) |
| Cover axes | L1 labelled · R1 selected · appointment present · advies present ∨ advies gold |
| Score | `unknown_score = 1 − (n_cover_hits / n_axes)` |
| High-unknown | `unknown_score == 1.0` (no cover hit) |
| Sample | Stratified high-unknown texts for later characterisation (not labelling here) |
| Not cover | Solo ontfangen, flag rates, ES proposition_type alone |

## Measurements (required)

| Piece | Where |
|-------|--------|
| `n_universe`, `n_high_unknown`, `frac_high_unknown` | metrics |
| Per-axis cover hit counts | metrics.cover |
| Score histogram / share at 1.0 | metrics |
| Per-id cover flags + score | `resolution_unknown_scores` |
| High-unknown stratified sample | `resolution_unknown_sample` |

## Eval gates (NOTES)

1. High-unknown band is large enough to triage, not empty / not “everything”.
2. Cover axes behave sensibly (L1/R1/appointment/advies hit where expected).
3. Call: next = fingerprints bridge **or** characterise high-unknown — not a new A from band size alone.

## Do not

- Mint subtype ids from unknown scores
- Use flag rates or ontfangen-alone as cover
- Run content characterisation or template promotion in this step
- Widen past `POC_YEAR` unless the 1780 band looks sane
