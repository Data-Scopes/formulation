# STEPR2 — Character n-gram TF-IDF + logistic regression

**Goal:** Fit a cheap document-level baseline and record holdout recall, precision, and F1.  
**Done when:** metrics are in `svz.py metric`; the model is not tuned on the test split.

## Prerequisites

STEPR1 labelled table.

## You do

```bash
uv run python scripts/run_aanstelling_tfidf.py
uv run python scripts/svz.py metric R1 recall <value>
uv run python scripts/svz.py metric R1 precision <value>
uv run python scripts/svz.py metric R1 f1 <value>
```

## Cursor guides

- Vectorizer: `char_wb` n-grams 3–5; classifier: logistic regression. No GPU.
- Stratified 80/20 on labelled rows (aanstelling vs sample of overig). Never tune on the test split.
- Headline metric is **recall** (missed aanstellingen are the historical cost); also precision and F1. Accuracy is not the headline.
- Writeup ballpark “good enough”: recall ~0.97 / precision ~0.95. If already there, skip a methods bake-off (that is STEPR4).
- Do not run GysBERT / e5 / SetFit in this step.

## Next step

[STEPR3-harvest-buckets.md](STEPR3-harvest-buckets.md)
