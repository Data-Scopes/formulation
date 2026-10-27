# STEPT1z — Probabilistic formula sequence matrix + harvest shortlist

**Goal:** Primary product = **row-stochastic transition matrix** P(next=B \| current=A) over formulas (before/after), plus a first harvest shortlist from the big formula frame. Companion table carries support `n` (and optional precedes / gap). Compute proposes; human still names into `opener_candidates`.
**Done when:** provenanced probabilistic matrix (+ n companion + harvest + per-id sequences) for year 1780; fixture smoke + tests pass; NOTES filled; no auto-mint; `data_io.check` clean; `PLAN.md` updated.

**Prerequisite:** STEPT1y done. `formula_type_presence_scores` for 1780 on disk.

## Constraint (locked)

- Comparison year **1780**.
- **Primary:** adjacent P(to|from), rows sum to 1 (include `END`).
- **Companion:** `n_adjacent`, `n_from`; optional precedes P and median token gap.
- Order = token `start_idx` from canonic/substring among presence-present blueprints + harvest substring hits — not a full DAG re-fit.
- Harvest stays shortlist; do **not** set `named` / `a_verdict`.

## You do

```bash
uv run pytest tests/test_formula_sequence_matrix.py -q
uv run python scripts/run_formula_sequence_matrix.py --fixture-only
uv run python scripts/run_formula_sequence_matrix.py --year 1780
# Rebuild Excel only (from existing jsonl):
uv run python scripts/run_formula_sequence_matrix.py --xlsx-from-disk
uv run python -m data_io.check
```

**Human read:** open `formula_sequence_matrix.xlsx` — sheet `P_adjacent` (probabilities); sheets `examples` / `edge_examples` (archetypal snippets, STEPT1z2).

Fill / judge: [`docs/proofs/multi-template-registry/STEPT1z-formula-sequence-matrix.md`](../../docs/proofs/multi-template-registry/STEPT1z-formula-sequence-matrix.md).

## Eval gates (NOTES)

1. Probabilistic matrix rows for blueprints sum ≈ 1.0 (within ε); `END` column present.
2. Six blueprints + ≥1 harvest node in the node set.
3. Companion `n` available for every positive-P cell; harvest includes voordracht/conclusie pocket surfaces.
4. No auto-`named` / blueprint mint.

## Do not

- Hand-lock one voordracht canonic as the step product
- Full ES gold measure for every harvest string
- Treat joint P(A,B) as the headline (co-presence again)
- Period matrix / full 18c

## After this step

Human reads P-matrix + harvest; picks canonics into `opener_candidates`. Clear the chat before the next step.
