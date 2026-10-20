# STEPT1g — Decisionful residual structure probe

**Goal:** Probe what is inside **missive ∩ ontfangen+ ∩ residual_not_l1** as structure and inventory — known formula pockets, surface-combination catalogue, accepted-formula bags, stratified text sample for reading.  
**Done when:** provenanced metrics + scores + sample written; NOTES name **shapes** (not probability subtypes); `data_io.check` clean; `PLAN.md` updated.

**Prerequisite:** STEPT1e scores on disk; STEPT1f ran (circular L1 half noted — open question was always this residual).

## Constraint (locked)

**Probability is not typology.** Do not invent residual subtypes from `P(flag)`, frac tables, length cuts, or rate contrasts. Formula types *may* carry a hit rate; that number does **not** make them more or less useful. Near-universal surfaces are filler (no signal) — same lesson as popularity weights / “too many, no signal.” Most of the residual will look trivial; **interesting structure is sparse**.

Counts and inventories are catalogue / pocket evidence. NOTES name readable skeletons and known detectors — especially **sparse** pockets — not classes defined by a probability cut or by topping the combo chart.

Not STEPT1e1 (flag sieve). Not another pass over L1 / `info_receipt`.

## You do

```bash
uv run pytest tests/test_residual_structure.py -q

uv run python scripts/run_residual_structure_probe.py --fixture-only

# Full 1780 (reuse partition + presence + formula_documents + flat text)
uv run python scripts/run_residual_structure_probe.py --year 1780

uv run python -m data_io.check
```

Fill / judge: [`docs/proofs/multi-template-registry/STEPT1g-residual-structure-probe.md`](../../docs/proofs/multi-template-registry/STEPT1g-residual-structure-probe.md) — **by reading the sample**, not by crowning top flag rates as types.

## Design locks

| Piece | Rule |
|-------|------|
| Universe | missive ∩ ontfangen+ ∩ `residual_not_l1` (1780 first) |
| Pockets | Accepted formula evidence only (appointment / advies present at operating cut) |
| Catalogue | Distinct flag *sets* with n + long-tail summary — not subtype ids |
| Bags | Present accepted / provisional types per id (inventory) |
| Sample | Stratified text from `resolutions_flat` for NOTES reading |
| Flags | Surfaces in a catalogue, not archival outcomes |

## Measurements (required)

| Piece | Where |
|-------|--------|
| `n_residual_missive` + non-missive leakage side count | metrics |
| Appointment / advies pocket sizes | metrics.pockets |
| Combo catalogue: top-K, `n_unique`, share top 5/20 | metrics.combo_catalogue |
| Bag shapes (solo opener / +appointment / multi) | metrics.bags |
| Stratified sample rows | `residual_structure_sample` |

## Eval gates (NOTES — not probability gates)

1. Is residual **one** readable shape or several distinct skeletons/composites? (Expect: much filler + sparse interesting pockets.)
2. Which **sparse** shapes are covered by accepted formula evidence (appointment) vs unexplained?
3. Call: next kind-support / characterisation from a named *sparse* shape, or park. Not e1; not a new A from bag density / high-n combos alone.

## Do not

- Subtype labels from flag rates / length cuts / logistic scores
- Implement STEPT1e1
- Re-characterise L1
- Accept residual shapes as formula types in this step
- ES live text remget

## After this step

Mark STEPT1g in `PLAN.md`. Follow NOTES call. Clear the chat before the next step.
