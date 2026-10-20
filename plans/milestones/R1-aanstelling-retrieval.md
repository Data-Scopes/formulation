# R1 — Aanstelling retrieval (whole resolutions)

**Status:** done (STEPR4: stop after TF-IDF; no residual neural pass)  
**Steps:** STEPR0–STEPR4 under [`plans/steps/`](../steps/)  
**Judged.** Selection frozen; results: [`docs/r1-aanstelling-results.md`](../../docs/r1-aanstelling-results.md). Formula M1 / Track L next as chosen.

## Goal

Find *aanstellingsresoluties* missing from the hand-found gold by scoring **whole resolutions** in `resolutions_flat` against known examples. Output a ranked list of candidate resolutions, not formula spans.

Start with **character n-gram TF-IDF + logistic regression** (char_wb 3–5). Dense retrieval / GysBERT is an optional **residual** pass on TF-IDF negatives only — not the first model.

## Done when

- `resolutions_flat` and `delegates_resolutie_refs` resolve via `data_io` (STEPR0).
- Gold URNs join to flat text; a provenanced labelled table exists (STEPR1).
- Holdout recall / precision / F1 are recorded (`svz.py metric`) (STEPR2).
- Unlabelled remainder is bucketed high / grey / low (STEPR3).
- A written decision: stop, or one residual neural pass (STEPR4).

## Out of scope here

Formula `FormulaSearch` (Track F), live Elasticsearch, copying `resolutions_flat` into this repo, a methods bake-off (TF-IDF vs e5 vs GysBERT vs SetFit) unless the goal becomes a methods paper.

## Decision points

- Unique-table gold is too thin (4 delegates / 6 URNs) → use the rc5 table (~222 URNs). Do not train on four positives.
- URNs do not join to `resolutions_flat` → diagnostic first; do not invent text from the spreadsheet.
- Holdout already good enough (writeup ballpark: recall ~0.97 / precision ~0.95) → harvest; no model bake-off.
- Worry is only odd-wording false negatives → one residual GysBERT/embedding pass on TF-IDF negatives only. **STEPR4: stop.** 5/6 holdout FNs already sit in `(0.15,0.5]` review; the remaining FN is 1690 HTR (`p=0.023`). high_or_grey recall 0.977.
- `resolutions_flat` is paragraph-grained → collapse to one text per resolution before TF-IDF (STEPR1).
- 18c print gold vs 17c HTR in the parquet → domain drift; do not declare one century done from the other.

## Sources

- Gold: `resolutie_refs` URNs in `delegates_1705_1795_v1.0-rc5.xlsx` (logical name `delegates_resolutie_refs`).
- Corpus: shared REPUBLIC parquet `resolutions_flat` (same file as `republic_ner_matching`).
- Writeup: copy into `formulator-project-docs/` if still on disk (*Zoeken naar resoluties via embeddings*).
