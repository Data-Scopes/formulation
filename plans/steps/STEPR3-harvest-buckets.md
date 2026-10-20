# STEPR3 — Harvest high / grey / low

**Goal:** Score the unlabelled remainder of `resolutions_flat` (after any collapse) into probability buckets.  
**Done when:** a provenanced harvest table exists with high / grey / low labels.

## Prerequisites

STEPR2 fitted baseline.

## You do

POC first (harvest-cut metrics on the frozen holdout, then one year of remainder):

```bash
uv run python scripts/harvest_aanstelling_scores.py --poc
uv run python -m data_io.check
```

Full remainder after the POC looks sane (overnight; do not overlap with `s6b_anchor_harvest`):

```bash
uv run python scripts/harvest_aanstelling_scores.py
uv run python -m data_io.check
```

## Cursor guides

- Buckets (starting cuts; adjust only with a written reason):
  - high (e.g. > 0.85) — candidates to ingest
  - grey (between) — manual review (atypical wording / OCR)
  - low (e.g. < 0.15) — ignore
- Score units are **whole resolutions**, same grain as STEPR1.
- Register the harvest dataset before writing. `save_semi_structured` or `save_parquet` with provenance.
- Do not change the holdout metrics from STEPR2 in this step. POC writes `aanstelling_tfidf_harvest_poc_metrics` (0.5 vs high-cut recall/precision/F1 on the frozen holdout).
- `--year` / `--limit` require `--poc` so a slice cannot overwrite `aanstelling_tfidf_harvest`.

## Next step

[STEPR4-residual-or-stop.md](STEPR4-residual-or-stop.md)
