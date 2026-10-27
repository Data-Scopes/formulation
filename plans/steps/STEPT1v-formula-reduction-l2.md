# STEPT1v — Formula reduction L1→L2 (`requeste_geleesen`)

**Goal:** Measure Doc B’s **reduced skeleton**: which slots of the settled long requeste opener are required for localisation vs scaffolding. Ablate by making slots optional (`align_dag(optional_slots=…)`), recalibrate each config at its own p20, keep the minimal subset that still localises.  
**Done when:** provenanced `formula_reduction_l2_metrics` (+ optional per-config scores) written; NOTES name hinge vs ablatable slots; `data_io.check` clean; `PLAN.md` updated.

**Prerequisite:** STEPT1k/s/t done (long + short requeste settled); STEPT1r band call done (L2 was deferred until then). Doctrine: [`docs/formula-abstraction-design.md`](../../docs/formula-abstraction-design.md) (L1→L2). Frozen `rekest_es_gold` on disk.

## Constraint (locked)

- Object = **one formula** (`requeste_geleesen`), not resolution typing and not empty-band coverage.
- Gold = **long-head** rekest only (`is_long_requeste_head`) — short `Op de Requeste` is a sibling type, not an ablation of this canonic.
- Bootstrap cloud **once**; configs differ only in `optional_slots` + per-config `calibrate_cut` (p20). Do **not** retrain clouds per ablation.
- Measurement only — do **not** change the frozen operating cut (4.5), `ACCEPTED_TYPE_IDS`, or `formula_templates`.
- No new opener mint; no L3 recurrence harvest this step.

## You do

```bash
uv run pytest tests/test_formula_reduction_l2.py -q

uv run python scripts/eval_formula_reduction_l2.py --fixture-only

# POC (advised first)
uv run python scripts/eval_formula_reduction_l2.py --limit-gold 2000 --neg-n 500

# Full long-head gold
uv run python scripts/eval_formula_reduction_l2.py

uv run python -m data_io.check
```

Fill: [`docs/proofs/multi-template-registry/STEPT1v-formula-reduction-l2.md`](../../docs/proofs/multi-template-registry/STEPT1v-formula-reduction-l2.md).

## Design locks

| Piece | Rule |
|-------|------|
| Canonic | `IS ter Vergaderinge geleesen de Requeste` (6 slots) |
| Configs (required) | `full` (bootstrap optional_slots); `all_required` (`[]`); `ablate_<i>` / `ablate_<token>` for each slot i made optional alone |
| Cut | p20 of **holdout** positive scores **per config** (`calibrate_cut`) |
| Localisation | recall on long-head gold + FP on negatives; span IoU vs `all_required` (or `full`) on gold hits |
| Optional | `--exhaustive` = all 2^n required-subset masks (n=6 → 64; only with `--limit-gold` or explicit OK) |

## Eval gates (NOTES)

1. **Hinge:** which single-slot ablation collapses recall (≥0.10 drop vs `all_required`) or blows FP?
2. **Scaffolding:** which slots stay ablatable (recall/FP within ε of baseline)?
3. **Call:** name the reduced L2 skeleton (required slot indices/tokens) — or “no reduction safe” if every ablation hurts. Do **not** deploy the reduced cut into presence this step.

## Do not

- Ablate / recalibrate short opener or other families in this step
- Mint templates / promote blueprints / wire composition
- Mix empty-band or rapport-opener work into the ablation table
- Treat ES `evidence` as span gold
- Quote pre-re-pin gold numbers

## Datasets to register first

| Logical name | Tier | Contents |
|--------------|------|----------|
| `formula_reduction_l2_metrics` | semi | Per-config recall/FP/cut + deltas vs baseline + slot labels |
| `formula_reduction_l2_scores` | explore | Per-id × config score/pred/span (no full text) |

## After this step

Mark STEPT1v in `PLAN.md` + Doc B status line. Follow NOTES call (accept L2 skeleton / no-reduction / try another family). Clear the chat before the next step.
