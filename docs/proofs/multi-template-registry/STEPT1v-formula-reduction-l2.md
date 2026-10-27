# STEPT1v — Formula reduction L1→L2 (`requeste_geleesen`) (NOTES)

**Status:** done (2026-10-23). Soft single-slot ablation is a **methodological no-op** on long-head gold — not a hinge finding.  
**Guide:** [`plans/steps/STEPT1v-formula-reduction-l2.md`](../../../plans/steps/STEPT1v-formula-reduction-l2.md)  
**Metrics:** `formula_reduction_l2_metrics` / `_scores`.

```bash
uv run pytest tests/test_formula_reduction_l2.py -q
uv run python scripts/eval_formula_reduction_l2.py --limit-gold 2000 --neg-n 500   # POC (same flat result)
uv run python scripts/eval_formula_reduction_l2.py                                 # full
uv run python -m data_io.check
```

## Results (full long-head)

| Piece | Value |
|-------|------:|
| n_gold (long-head) | 47,237 |
| bootstrap / holdout | 37,790 / 9,447 |
| cloud optional_slots | `[]` |
| slot labels | IS · ter · Vergaderinge · geleesen · de · Requeste |

Every config identical:

| config | optional | cut | recall | FP | span IoU vs all_required |
|--------|----------|----:|-------:|---:|-------------------------:|
| full / all_required | [] | 9.0 | 0.9766 | 0.022 | 1.0 |
| ablate_0…5 (each alone) | [i] | 9.0 | 0.9766 | 0.022 | 1.0 |

- **hinge_slots:** none  
- **safe_ablate_slots:** all six (drop/rise = 0)  
- **l2_required_tokens_guess:** `[]` (vacuous — every slot looks “safe”)

POC (`--limit-gold 2000`) showed the same flat pattern (recall 0.9575 / FP 0.16 at cut 9.0 — different sample, same invariance).

## Why this is a no-op (not “no hinge”)

Doc B’s first sketch used `align_dag(optional_slots=…)`. Making a slot **optional allows skip**; it does **not force** drop. On long-head gold the full six-slot path is still available and preferred, so:

- gold scores stay at the perfect ceiling → p20 cut stays **9.0**
- recall / FP / spans unchanged (IoU median 1.0)

So soft ablation cannot distinguish hinge from scaffolding on a population that already matches the full canonic. The empty `l2_required_tokens_guess` is an artifact of that design, not evidence that the formula has no required slots.

## Call

1. **STEPT1v soft ablation: inconclusive** — do not treat “all slots safe” as an L2 skeleton.
2. **Next (STEPT1v2):** **hard drop** — remove slot *i* from `variant_lists` (or score a reduced canonic template), recalibrate p20, compare recall/FP/span. That measures “identity without this token.” Optional: leave-k-in minimal subsets once single hard-drops show signal.
3. Do **not** change frozen cut 4.5 / blueprints from this run.
4. Exhaustive soft masks (`--exhaustive`) would inherit the same no-op; skip until hard-drop exists.

Clear the chat before the next step.
