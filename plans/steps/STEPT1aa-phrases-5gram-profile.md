# STEPT1aa — 5-gram high-freq inventory + rare sidecar

**Goal:** Register the huge `phrases_5gram_18th` dump and produce a skim-sized Pass A profile: high-`phrase_freq` phrases with zone×`lcats` tags, plus a protected/rare sidecar so type-carriers are not silently dropped.
**Done when:** provenanced metrics + high_freq + rare_sidecar (+ optional xlsx); fixture tests pass; NOTES filled; no fold / no auto-mint; `data_io.check` clean; `PLAN.md` updated.

**Prerequisite:** dump on disk via `data_manifest.local.toml` (`phrases_5gram_18th`).

## Constraint (locked)

- Stream only — never load ~26.7M rows as one frame.
- `phrase_freq` gate is scaffolding-biased; sidecar = named seeds below gate + mid-body low-freq top-N.
- Legacy length bins + Track T / notebook zone cuts (`lcats`, `pos_start < 20`, thirds).
- No nest/variant fold (that is STEPT1ab).

## You do

```bash
uv run pytest tests/test_phrases_5gram_profile.py -q
uv run python scripts/run_phrases_5gram_profile.py --fixture-only
# Full dump (slow; Extreme SSD mounted):
uv run python scripts/run_phrases_5gram_profile.py
# Faster smoke / year slice:
uv run python scripts/run_phrases_5gram_profile.py --max-rows 500000
uv run python scripts/run_phrases_5gram_profile.py --year 1780
uv run python -m data_io.check
```

Skim: `output/phrases_5gram_profile.xlsx` (high_freq / rare_sidecar / metrics).

Fill: [`docs/proofs/multi-template-registry/STEPT1aa-phrases-5gram-profile.md`](../../docs/proofs/multi-template-registry/STEPT1aa-phrases-5gram-profile.md).

## Eval gates (NOTES)

1. `n_high_freq` > 0 after Pass A; metrics report `n_protected_below_gate`.
2. Sidecar non-empty when protected seeds hit below gate (or rare mid-body top-N).
3. No family fold / no blueprint mint in this step.

## Do not

- Full unique-phrase catalogue
- Parquet rewrite of the dump
- Auto-mint types
- Live Google Sheet fetch

## After this step

Run STEPT1ab fold on the profile outputs → human skim families → then **revisit `formula_sequence_matrix`** with folded family nodes. Clear the chat before the next step.
