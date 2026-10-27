# STEPT1v2 — Formula reduction L1→L2 hard-drop (`requeste_geleesen`) (NOTES)

**Status:** done (2026-10-23). Hard-drop **moves** metrics (unlike STEPT1v soft optional). No recall hinge; **Requeste** is a specificity / FP hinge.  
**Guide:** [`plans/steps/STEPT1v2-formula-reduction-hard-drop.md`](../../../plans/steps/STEPT1v2-formula-reduction-hard-drop.md)  
**Metrics:** `formula_reduction_hard_drop_metrics` / `_scores`.

```bash
uv run pytest tests/test_formula_reduction_hard_drop.py -q
uv run python scripts/eval_formula_reduction_hard_drop.py --limit-gold 2000 --neg-n 500   # POC
uv run python scripts/eval_formula_reduction_hard_drop.py                                 # full
uv run python -m data_io.check
```

## Results (full long-head)

| Piece | Value |
|-------|------:|
| n_gold (long-head) | 47,237 |
| bootstrap / holdout | 37,790 / 9,447 |
| cloud accepted | 37,245 |
| slot labels | IS · ter · Vergaderinge · geleesen · de · Requeste |

| config | drop | cut | recall | FP | span IoU vs full |
|--------|------|----:|-------:|---:|-----------------:|
| full | — | 9.0 | 0.9766 | 0.022 | 1.0 |
| drop_0 | IS | 7.5 | 0.9766 | 0.024 | 0.833 |
| drop_1 | ter | 6.5 | 0.9766 | 0.022 | 1.0 |
| drop_2 | Vergaderinge | 6.5 | 0.9769 | 0.024 | 1.0 |
| drop_3 | geleesen | 6.5 | 0.9773 | 0.022 | 1.0 |
| drop_4 | de | 6.5 | 0.9769 | 0.022 | 1.0 |
| drop_5 | Requeste | 7.5 | **0.9978** | **0.054** | 0.833 |

- **hinge_slots (recall ≥0.10 drop):** none  
- **safe_drop_slots (ε):** IS, ter, Vergaderinge, geleesen, de  
- **l2_required_tokens_guess:** `Requeste` (fails safe via FP rise +0.032; recall *rises*)

## Reading

1. **Method works.** Cuts and span IoU move under hard-drop; STEPT1v’s soft optional was the wrong instrument, not “no hinges exist.”
2. **No recall hinge.** Any single five-slot remnant still localises long-head gold (R ≈ 0.977). The phrase is redundant for FN control.
3. **Requeste = specificity hinge.** Dropping it raises recall (0.977→0.998) and roughly doubles FP (0.022→0.054). Identity *against negatives* needs that token; identity *on gold* does not.
4. **Scaffolding for recall:** the other five slots. Span shortens when IS or Requeste is dropped (IoU 0.833); middle drops keep median IoU 1.0 (interior skip).

Do **not** treat `l2_required_tokens_guess = [Requeste]` as a deployable one-token skeleton — that config is the FP-worst. L2 claim: **keep Requeste for specificity; other slots are singly ablatable for recall.**

## Call

1. **STEPT1v2 PASS (method + naming).** Soft optional closed; hard-drop named the hinge as FP/specificity (`Requeste`), not recall.
2. Do **not** change frozen cut 4.5 / blueprints from this run. Do **not** deploy a reduced presence cut.
3. **Skip leave-k** unless a later step needs a minimal FP-preserving multi-drop subset — single-drop already answers Doc B’s L1→L2 question for this formula.
4. **Next:** park further requeste reduction; resume STEPT1u’s parked A probe (**rapport opener**) — or Doc B L3 recurrence if preferring abstraction over coverage.

Clear the chat before the next step.
