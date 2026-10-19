# STEPL2 — Character n-gram TF-IDF + logistic regression (missive receipt)

**Goal:** Fit the same cheap document-level baseline as STEPR2 on `missive_receipt_labelled` and record holdout recall, precision, and F1.  
**Done when:** provenanced holdout + metrics exist; metrics recorded in `svz.py`; model not tuned on the test split.

## Closed gate (this session)

STEPL2 is a **metric gate only**. Record holdout recall / precision / F1. Do **not** open STEPL3 harvest or build `missive_receipt_selected` unless a later written decision says so.

Full R1-shaped ladder (L3→L4→selected list) stays available but **parked** to avoid a second retrieval rabbit hole. Cue-defined `missive_receipt_labelled` remains the working type definition.

## Prerequisites

STEPL1 labelled table (`missive_receipt_labelled`). Read [`plans/milestones/L1-missive-receipt-retrieval.md`](../milestones/L1-missive-receipt-retrieval.md). Mirror [STEPR2](STEPR2-tfidf-baseline.md). Do **not** harvest the remainder (STEPL3) or mix Track R / S scripts.

## You do

```bash
uv run python -m data_io.check
uv run pytest tests/test_missive_receipt_tfidf.py -q
uv run python scripts/run_missive_receipt_tfidf.py
uv run python scripts/svz.py metric L1 recall <value>
uv run python scripts/svz.py metric L1 precision <value>
uv run python scripts/svz.py metric L1 f1 <value>
```

## Cursor guides

- Vectorizer: `char_wb` n-grams 3–5; classifier: logistic regression (`liblinear`). Same frozen hyperparameters as R1 unless metrics force a rethink.
- Stratified 80/20 on labelled rows (`missive_receipt` vs `overig`). Never tune on the test split.
- Headline metric is **recall**; also precision and F1. Accuracy is not the headline.
- Package: `formulation/missive_receipt_tfidf.py` (reuses pipeline factory from `aanstelling_tfidf`). Script: `scripts/run_missive_receipt_tfidf.py`.
- Outputs: `missive_receipt_tfidf_holdout` (parquet), `missive_receipt_tfidf_metrics` (JSONL).
- Do not run GysBERT / e5 / SetFit in this step. Do not score the unlabelled remainder (STEPL3).

## Next step

**Stop Track L** after metrics are recorded (park L3+). Resume formula work: wire boundary→registry, or period-keyed `institution_patterns`. Clear the chat before the next step. Open STEPL3 only with an explicit decision.
