# Formula boundary evolution

Methodological next stage after whole-document char TF-IDF (R1). Milestone: [`plans/milestones/S1-formula-boundary-evolution.md`](../plans/milestones/S1-formula-boundary-evolution.md).

## Why evolve

R1 showed that rare administrative n-grams survive OCR noise under `char_wb` TF-IDF. That localises *where* formulaic language sits at document or window scale. Research notions (building blocks, gappy templates, position) need **exact start/end of boilerplate** and isolation of variable slots (names, places, body). Coarse cosine alone does not cut those boundaries.

## Phased pipeline

1. **Coarse filter (TF-IDF)** — sliding or document windows; `analyzer="char_wb"`, `ngram_range=(3, 5)`, later `sublinear_tf=True`. Same family as R1. Output: candidate windows above a raised threshold (target ~0.30–0.40 after char n-grams, not the soft 0.15 word-level band).
2. **Local alignment** — word-level Smith-Waterman inside each window, with Levenshtein-based token similarity (OCR-tolerant). Score against a single canonical template or a **slot-cloud** of observed variants per position.
3. **DAG / skip paths** — when clerks omit optional words (`ende`, `sijnde`), follow skip-edges instead of burning gap penalty.
4. **Optional referee** — GysBERT / token tags only on low-alignment leftovers (mirror STEPR4 residual logic). Not required for early S steps.

## Representations

- **Slot-cloud JSON** — ordered slots with `canonical`, `optional`, and frequency-weighted `variants` (good for spelling/OCR drift with fixed word order).
- **DAG** — layered nodes + skip-edges (good when tokens are dropped or inserted).

Later: period-filtered clouds (diachronic style), change-point analysis — after span detection works on a fixed family.

## Metrics (comparative setup)

| Metric | Meaning |
|--------|---------|
| Token IoU | Overlap of predicted vs gold half-open `[start, end)` spans |
| Boundary delta | Absolute token distance on start and end |
| Latency | ms per window / case |

## Relation to FormulaSearch

`formula_detection.FormulaSearch` remains useful for motif / co-occurrence discovery later. It is **not** the harness for S1 STEPS0–3. Track F / M1 stays paused while boundary evolution runs.

## Source note

Ideas distilled from an internal design thread (`formula_transfomrer.pdf`, 2026-10-18). Project docs carry the durable design; do not treat the PDF chat as code of record.
