# Deferred — Track S: neural residual comparison / evaluation framework

**Status:** deferred (do not execute in STEPS4; STEPS4 is GysBERT yes/no only)  
**Parent:** [`plans/milestones/S1-formula-boundary-evolution.md`](../milestones/S1-formula-boundary-evolution.md)

## Why deferred

STEPS4 mirrors STEPR4: a **written stop-or-one-residual** decision for hard alignment leftovers. A multi-model bake-off needs shared span gold, metrics, and harness beyond that gate. Reuse STEPS0 IoU / boundary delta / latency; do not invent a parallel eval stack in the residual session.

## Named candidates (when chosen)

| Model | Role |
|-------|------|
| **GysBERT** | Default residual named in S1 (broad historical Dutch) |
| **GloBERTise** | GLOBALISE VOC Early Modern Dutch; compare later, not STEPS4 default |
| SW single / SW cloud / DAG | Non-neural baselines already in `formula_boundary_*` |

## What to pick up later

1. Frozen span-gold set (extend `formula_boundary_cases` + sample of STEPS3 windows with human `[start, end)`).
2. Common runner: predict spans → IoU / Δstart / Δend / latency; provenanced metrics via `data_io`.
3. Protocol: residual only on **low-alignment leftovers** (mirror STEPR4 negatives), not full-corpus re-score.
4. Optional: GysBERT vs GloBERTise token-tag or span head on the same leftovers; report deltas, not a methods paper unless that becomes the goal.

## Out of scope until chosen

Training from scratch; live Elasticsearch; mixing L1/R1 harvest into the eval harness; calibrating STEPS1 cosine as part of the bake-off.
