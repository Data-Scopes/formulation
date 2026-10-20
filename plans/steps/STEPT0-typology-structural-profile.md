# STEPT0 — Provisional 18c proposition-type structural profile

**Goal:** Describe, per `proposition_type`, how 18c resolutions are structured — evidence-label zones, length, closing-formula flag rates — as a provisional typology, not a model.
**Done when:** `typology_structural_profile` is registered and written via `data_io`; composition (full population) and the characterisation sample (floored, per-type) are kept separate in the output; `uv run python -m data_io.check` is clean.

## Prerequisites

None (new track). Reuses `RepublicEsClient` (`formulation/republic_es.py`) and `formula_documents` (recovered this step from `notebook-archive`, see `docs/DECISIONS.md` 2026-10-19). Do **not** train anything on this profile in this step; do not classify outcomes as decisions (see scope guards below).

## You do

Cheap check first (agent-safe, no sample draw):

```bash
uv run python scripts/run_typology_profile.py --composition-only
```

Full pass (user terminal — draws a live ES sample):

```bash
uv run python scripts/run_typology_profile.py
uv run python -m data_io.check
```

Widen later with the same script once `POC_YEAR` (1780) looks sane:

```bash
uv run python scripts/run_typology_profile.py --full-18c
uv run python scripts/run_typology_profile.py --year-min 1710 --year-max 1710   # comparison year
```

## Cursor guides

- Package: `formulation/typology_sample.py`. Script: `scripts/run_typology_profile.py`.
- **Composition vs characterisation are different questions, computed separately:** `composition_by_type()` is a full-population ES terms aggregation (zero sampling error) — the only source for population proportions. `allocate_sample_sizes()` / `draw_typed_sample()` floor rare types (`DEFAULT_FLOOR=30`) so they're analysable; this sample must **never** be read as the population mix. Every profile record carries `population_n`/`population_pct` from composition alongside the (floored) `sample_n`.
- Join key to `formula_documents` outcome flags is `(session_date, resolution_index)` — the only key present on both sides. `formula_documents.doc_id` is date-based with a constant `num=1`; `resolutions_flat`/ES key on inventory `num` instead. Unmatched rows are kept with null flags and marked via `outcome_joined`, never dropped.
- Flag columns must be cast to pandas nullable `boolean` dtype after the merge — a plain left-join silently upcasts bool columns to `object` wherever NaN is introduced, which breaks naive `dtype == bool` re-detection downstream (this broke the first run; see `docs/DECISIONS.md`).
- `evidence` entries from `full_resolutions` are `PhraseMatch` output (ngram/Levenshtein/char scores) — silver, not gold. Offsets are normalised by the max offset within a resolution's own evidence, a proxy for text length since full resolution text is deliberately not pulled.
- **Known caveat:** `praeside_start`/`praesentibus_start` in `formula_documents` mark attendance-list openers, not resolution content; small nonzero rates on resolution rows reflect upstream session-boundary parsing leakage, not signal.
- Do not classify outcomes as decisions — report closing boilerplate as formula, never as "no decision was made" (REPUBLIC deliberately has no outcome label, for this reason).
- Do not widen past `POC_YEAR` (1780) or add modelling in this step.

## Next step

Widen to `--full-18c` and re-check the structural separation holds, or move to a follow-up track (unpark Track L using the "information resolution" structure, or mine `evidence` phrase/variant pairs as a slot-cloud seed for Track S). See STEPT0 plan follow-ups.

`onbekend`'s low outcome-join coverage (15.6% on 1780) is **not** an open question — those resolutions were already unclassifiable upstream (why ES has no `proposition_type` for them), so sparse outcome coverage is expected, not a signal to chase.
