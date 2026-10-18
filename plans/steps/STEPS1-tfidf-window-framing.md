# STEPS1 — TF-IDF window framing

**Goal:** Score sliding token windows against an opening-formula template with sharpened char TF-IDF; emit candidate windows and threshold notes on a year slice.  
**Done when:** `formula_tfidf_windows` + `formula_tfidf_window_metrics` are registered and written via `data_io`; `uv run python -m data_io.check` is clean; pytest smoke passes; threshold notes record the score distribution (0.35 is a hypothesis, not frozen).

## Prerequisites

STEPS0. Read [`plans/milestones/S1-formula-boundary-evolution.md`](../milestones/S1-formula-boundary-evolution.md) and [`docs/formula-boundary-evolution.md`](../../docs/formula-boundary-evolution.md). Do **not** run SW/DAG harvest, GysBERT, FormulaSearch, or full-corpus overnight in this session.

## You do

Smoke on fixtures (no year slice):

```bash
uv run python -m data_io.check
uv run python scripts/run_tfidf_window_framing.py --fixture-only
uv run pytest tests/test_tfidf_windows.py -q
```

Year-slice POC (user terminal; optional `--limit`):

```bash
uv run python scripts/run_tfidf_window_framing.py --year 1780 --limit 200
uv run python -m data_io.check
```

## Cursor guides

- Vectorizer: `TfidfVectorizer(analyzer="char_wb", ngram_range=(3, 5), sublinear_tf=True, min_df=2)`. Same family as R1; **no** logistic regression, stopword list, binary/BM25, or `strip_accents` in this step.
- Fit IDF on the **window corpus** of the slice (not templates alone). Score cosine vs the **18c** opening `IS ter Vergaderinge geleesen de Requeste` (`opening_requeste_18c`). Do **not** use the STEPS0 fixture template (*Gepraesenteert…*) for framing.
- **Scope now:** 18th-century requeste openings. 17c variants are deferred — see [`plans/deferred/S1-17c-requeste-templates.md`](../deferred/S1-17c-requeste-templates.md); expand later with a period map, not in this cut.
- Score windows ~12–24 tokens (default 16), stride 2–4 (default 2). Record a separate align-pad (default 8 tokens) for later SW — do not score on 150-word bags.
- Default cosine cut **0.35** is a hypothesis; metrics must include score percentiles / hit counts so the cut can move after inspection.
- Source: `resolutions_flat` year slice (default 1780). Do not block on Track F `sample_resolutions`.
- Package: `formulation/boundary/tfidf_windows.py`. Script: `scripts/run_tfidf_window_framing.py`.
- Do not mix L1/R1 harvest scripts or FormulaSearch.

## Calibration (now available)

Framework (STEPS2–4) is done. Freeze the cut in [STEPS1-calibrate-threshold.md](STEPS1-calibrate-threshold.md). Do not add proposer / variable-slot gaps until after that cut.

## Next step

[STEPS1-calibrate-threshold.md](STEPS1-calibrate-threshold.md) — or STEPS2 if re-running the original framing path.
