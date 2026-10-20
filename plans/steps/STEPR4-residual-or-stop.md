# STEPR4 — Stop, or one residual neural pass

**Goal:** Decide whether the TF-IDF harvest is enough, or whether one residual embedding pass on TF-IDF negatives is warranted.  
**Done when:** a `docs/DECISIONS.md` entry records stop vs residual, with the metric that justified it.

## Prerequisites

STEPR2 metrics and STEPR3 harvest.

## You do

Read the holdout numbers and harvest. Then either:

```bash
uv run python scripts/svz.py decision "R1 stop after TF-IDF" \
  --context "..." --decision "..." --reason "..."
```

or run **one** residual pass (GysBERT mean-pool or embedding cosine vs gold centroid/k-NN) **only on TF-IDF negatives**, compare extra true aanstellingen, and write the decision.

## Cursor guides

- Default research goal is complete the historical list (Doel A), not a methods paper (Doel B).
- If holdout already meets the writeup ballpark, **stop**. Harvest; no bake-off.
- Residual only if the worry is false negatives with odd wording. Compare **only TF-IDF negatives**. If the neural model finds no extra true aanstellingen, drop it.
- Do not declare 17c HTR done from an 18c-trained model, or the reverse.
- After R1 is judged, resume formula [STEP2-sample-corpus-and-seeds.md](STEP2-sample-corpus-and-seeds.md).

## Next step

Formula STEP2, or a new Track R iteration if the residual pass was justified and still incomplete.
