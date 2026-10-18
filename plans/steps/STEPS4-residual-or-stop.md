# STEPS4 — Stop, or one GysBERT residual pass

**Goal:** Decide whether SW / slot-cloud / DAG span harvest is enough for the 18c opening family, or whether one residual neural referee (GysBERT) on low-alignment leftovers is warranted.  
**Done when:** a `docs/DECISIONS.md` entry records stop vs residual, with the metric that justified it.

## Prerequisites

STEPS0 fixture IoU, STEPS1 windows + metrics, STEPS2 slot-cloud, STEPS3 `formula_boundary_spans` / `formula_boundary_span_metrics`. Read [`plans/milestones/S1-formula-boundary-evolution.md`](../milestones/S1-formula-boundary-evolution.md) and [`docs/formula-boundary-evolution.md`](../../docs/formula-boundary-evolution.md). Do **not** run the deferred GysBERT vs GloBERTise bake-off ([`plans/deferred/S1-neural-span-eval.md`](../deferred/S1-neural-span-eval.md)) in this session.

## You do

Read STEPS0–3 metrics. Then either:

```bash
uv run python scripts/svz.py decision "S1 stop after SW/DAG" \
  --context "..." --decision "..." --reason "..."
```

or run **one** residual pass (GysBERT token-tag or span head) **only on low-alignment leftovers**, compare span quality vs SW/DAG, and write the decision.

## Cursor guides

- Mirror STEPR4: default research goal is usable boilerplate spans (Doel A), not a methods paper (Doel B).
- If fixture IoU is already perfect and real-window failures are mostly TF-IDF neighbours / uncalibrated cuts, **stop**. No neural bake-off.
- Residual only if the worry is hard OCR / reordered leftovers where classical alignment returns empty or wrong spans on true formulas. Compare **only low-alignment leftovers**, not full-corpus re-score.
- GysBERT is the named residual; GloBERTise comparison stays deferred.
- Do not freeze STEPS1 cosine here unless the decision explicitly says to calibrate next.
- Do not declare 17c templates done from an 18c cloud.

## Next step

Calibrate STEPS1 thresholds (framework now in place), or resume Track L STEPL1 / deferred S sides when chosen. Clear the chat before the next step.
