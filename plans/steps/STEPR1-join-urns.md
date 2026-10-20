# STEPR1 — Join URNs to flat text

**Goal:** Turn gold `resolutie_refs` into a provenanced labelled table of resolution texts.  
**Done when:** labelled rows (aanstelling vs sample of overig) are written through `data_io` with provenance sidecars.

## Prerequisites

STEPR0. Grain and year notes in [`docs/DECISIONS.md`](../../docs/DECISIONS.md).

## You do

After the agent registers the output dataset and writes the join script:

```bash
uv run python scripts/join_aanstelling_gold.py
uv run python -m data_io.check
```

## Cursor guides

- Grain is already one row per resolution (STEPR0). Join key: parse `urn:republic:inv-{inv}-date-…-session-{num}-resolution-{k}` → `session-{inv}-num-{num}-resolution-{k}` when URN date equals parquet `date` (199/217 unique URNs). The other 18 are still **gold**: load `aanstelling_gold_relocations` (nearby `num` on the same inventory + date + resolution; one 1685 case keeps the naive id). Do not invent text. Strip trailing `;` and extract URNs from goetgevonden.nl URLs.
- Keep archival fields (URN, delegate ids, dates, inventory). Text column: `resolutions_text` (not `paragraph_texts`; that field is a JSON list of the same wording).
- Output via `save_parquet` or `save_semi_structured` with a registered logical name. Parent: `resolutions_flat` + `delegates_resolutie_refs`.
- Stratified 80/20 split is STEPR2; this step only freezes the labelled table.
- No Elasticsearch. No formula `FormulaSearch`.

## Next step

[STEPR2-tfidf-baseline.md](STEPR2-tfidf-baseline.md)
