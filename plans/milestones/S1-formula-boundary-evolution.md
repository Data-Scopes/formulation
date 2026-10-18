# S1 — Formula boundary evolution

**Status:** done (STEPS4: stop after SW/DAG; no GysBERT residual; calibrate STEPS1 next)  
**Steps:** STEPS0–STEPS4 under [`plans/steps/`](../steps/)  
**Notions:** [`docs/formula-boundary-evolution.md`](../../docs/formula-boundary-evolution.md), [`docs/formula-conceptual-overview.md`](../../docs/formula-conceptual-overview.md)

## Goal

Evolve formula work beyond whole-document char TF-IDF (R1) into **exact template span boundaries**: candidate windows → Smith-Waterman (single / slot-cloud) → DAG with optional skips. Output is boilerplate vs variable slots, with provenance.

This is the methodological next stage of the same research thread (templated administrative language), not a side-benchmark and not a FormulaSearch wrapper.

## Pipeline phases

1. **TF-IDF framing** (`char_wb` 3–5, later `sublinear_tf`) — candidate windows (STEPS1)
2. **SW single / slot-cloud** — exact token spans against canonical template or variant cloud (STEPS0 scaffold; STEPS2 cloud build)
3. **DAG** — skip-edges for shortened clerk variants (STEPS0 scaffold; STEPS3 on real data)
4. **Residual** — GysBERT / token classification only if alignment fails on hard cases (STEPS4)

## Done when (milestone)

- Provenanced span outputs for a defined formula family (e.g. openings) on a sample or year slice
- Comparative metrics (IoU, boundary delta, latency) recorded for SW single / cloud / DAG
- Written STEPS4 decision on residual neural pass

## Out of scope here

Live Elasticsearch; mixing L1/R1 whole-document harvest into boundary scripts; forking `formula_detection`; training GysBERT in STEPS0–3; full MSA cloud bootstrap before STEPS2.

**Deferred (registered, not active):** 17c requeste openings / period template map — [`plans/deferred/S1-17c-requeste-templates.md`](../deferred/S1-17c-requeste-templates.md). STEPS1 framing stays **18c-first**. Neural residual **comparison / eval framework** (GysBERT vs GloBERTise on shared span gold; reuse STEPS0 metrics) — [`plans/deferred/S1-neural-span-eval.md`](../deferred/S1-neural-span-eval.md); STEPS4 stays a written yes/no, not that bake-off.

## Steps

| Step | Guide | Done when |
|------|-------|-----------|
| S0 | [STEPS0-boundary-scaffold.md](../steps/STEPS0-boundary-scaffold.md) | Package + fixture + benchmark runner; metrics via `data_io` |
| S1 | [STEPS1-tfidf-window-framing.md](../steps/STEPS1-tfidf-window-framing.md) | Candidate windows from sample / slice; sharper threshold notes |
| S2 | [STEPS2-slot-cloud-bootstrap.md](../steps/STEPS2-slot-cloud-bootstrap.md) | Slot-clouds from aggregated hits; optional period filter |
| S3 | [STEPS3-dag-spans.md](../steps/STEPS3-dag-spans.md) | Provenanced span JSONL on real shortened formulas |
| S4 | [STEPS4-residual-or-stop.md](../steps/STEPS4-residual-or-stop.md) | Written GysBERT yes/no decision (done: stop) |

## Relation to other tracks

| Track | Unit | Relation |
|-------|------|----------|
| R1 | whole resolution | Supplied `char_wb` evidence; reuse vectorizer family |
| L1 | whole resolution | Parallel type-retrieval; do not mix scripts |
| F / M1 | FormulaSearch candidates | Paused; later motifs may sit beside S spans |
| **S1** | token spans | Evolution: template boundaries + slots |
