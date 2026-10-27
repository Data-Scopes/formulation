# STEPT1v2 — Formula reduction L1→L2 hard-drop (`requeste_geleesen`)

**Goal:** Finish Doc B’s L1→L2 after STEPT1v’s soft `optional_slots` pass proved a no-op. **Hard-drop** each slot from the cloud (`variant_lists` without slot *i*), recalibrate p20 per config, name hinge vs scaffolding.  
**Done when:** provenanced `formula_reduction_hard_drop_metrics` (+ scores) written; NOTES name hinge / safe / L2 guess; `data_io.check` clean; `PLAN.md` updated.

**Prerequisite:** STEPT1v done ([NOTES](../../docs/proofs/multi-template-registry/STEPT1v-formula-reduction-l2.md)): soft optional identical on long-head; call = hard-drop next. Doctrine: [`docs/formula-abstraction-design.md`](../../docs/formula-abstraction-design.md).

## Constraint (locked)

- Object = **one formula** (`requeste_geleesen`), long-head gold only (`is_long_requeste_head`).
- Bootstrap cloud **once**; configs differ only by **which slots remain** in `variant_lists` + per-config `calibrate_cut` (p20). Do **not** retrain clouds per drop.
- Hard-drop = remove the slot entirely (forced absence). Do **not** re-run soft `optional_slots` ablation.
- Measurement only — do **not** change frozen cut 4.5, `ACCEPTED_TYPE_IDS`, or `formula_templates`.
- No new opener mint; no L3 recurrence harvest this step.

## You do

```bash
uv run pytest tests/test_formula_reduction_hard_drop.py -q

uv run python scripts/eval_formula_reduction_hard_drop.py --fixture-only

# POC (advised first)
uv run python scripts/eval_formula_reduction_hard_drop.py --limit-gold 2000 --neg-n 500

# Full long-head gold
uv run python scripts/eval_formula_reduction_hard_drop.py

uv run python -m data_io.check
```

Fill: [`docs/proofs/multi-template-registry/STEPT1v2-formula-reduction-hard-drop.md`](../../docs/proofs/multi-template-registry/STEPT1v2-formula-reduction-hard-drop.md).

## Design locks

| Piece | Rule |
|-------|------|
| Canonic | `IS ter Vergaderinge geleesen de Requeste` (6 slots) |
| Configs (required) | `full` (all 6 slots, `optional_slots=[]`); `drop_<i>` / `drop_<token>` for each slot *i* removed alone |
| Cut | p20 of **holdout** positive scores **per config** (`calibrate_cut`) — scores shrink with fewer slots |
| Localisation | recall on long-head gold + FP on negatives; span IoU vs `full` on gold hits |
| Optional | `--leave-k N` = all subsets of size N kept (only with `--limit-gold` or explicit OK) |

## Eval gates (NOTES)

1. **Hinge:** which single hard-drop collapses recall (≥0.10 drop vs `full`) or blows FP?
2. **Scaffolding:** which slots stay droppable (recall/FP within ε of baseline)?
3. **Call:** name the reduced L2 skeleton (required slot indices/tokens) — or “no reduction safe” / “every slot hinge.” Do **not** deploy the reduced cut into presence this step.
4. If single drops are flat again, record that; do **not** invent leave-k as a rescue without signal.

## Do not

- Soft-optional re-ablate (STEPT1v already closed that arm)
- Change frozen cut / blueprints / composition wiring
- Ablate short opener or other families
- Mix empty-band / rapport / letter work into the table
- Treat ES `evidence` as span gold

## Datasets to register first

| Logical name | Tier | Contents |
|--------------|------|----------|
| `formula_reduction_hard_drop_metrics` | semi | Per-config recall/FP/cut + deltas vs full + slot labels |
| `formula_reduction_hard_drop_scores` | explore | Per-id × config score/pred/span (no full text) |

## After this step

Mark STEPT1v2 in `PLAN.md` + Doc B status line. Follow NOTES call (accept L2 skeleton / no-reduction / leave-k next / another family). Clear the chat before the next step.
