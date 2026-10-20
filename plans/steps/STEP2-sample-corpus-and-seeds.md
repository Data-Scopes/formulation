# Step 2 — Sample corpus and S4 seeds

**Goal:** Register an ES-free sample of resolutions plus an S4 opening-phrase seed list.  
**Done when:** logical names `sample_resolutions` and `s4_opening_phrase_candidates` resolve; `uv run python -m data_io.check` shows them; a seed reader loads the fixture.

## Prerequisites

STEP1. S4 shape: [`formulator-project-docs/internal-context/s4-opening-phrases-sample.md`](../../formulator-project-docs/internal-context/s4-opening-phrases-sample.md).

Registered reference matrix: `formula_documents` (`load("formula_documents")`) — date-based `doc_id` values such as `session-1735-11-26-num-1-resolution-2`. **`resolutions_flat.id` uses numeric session ids** (`session-3788-num-1-resolution-1`). There is **no direct `doc_id` join** between the two without an explicit session bridge (date ↔ session number / URN from `republic_clean` or session index). Before any evaluation that needs both paragraph text and notebook formula flags, document or implement that bridge; do not assume `merge(on="doc_id")` works.

## You do

After the agent adds manifest entries and files:

```bash
uv run python -m data_io.check
uv run python -c "from data_io import resolve; print(resolve('sample_resolutions')); print(resolve('s4_opening_phrase_candidates'))"
```

## Cursor guides

- Warm sample: `data/warm/datasets/corpus/sample_resolutions.jsonl`. Each record needs enough structure to recover **position** (`section` and/or character/token offsets) as well as text/tokens.
- S4: trimmed fixture under `data/warm/datasets/seeds/` (offline envelope; a handful of candidates is enough). Optional `data_manifest.local.toml` override to the full 271-candidate file on disk — do not hardcode that path in Python.
- Reader e.g. `formulation/seeds.py` (`load_s4_opening_seeds`). Envelope is **one JSON object** with `candidates[]` of `phrase`, `count`, `word_count` — not one-record-per-line JSONL.
- Register `[datasets.*]` **before** code references the names. Keep S4 metadata (`minimum_frequency`, envelope counts) — do not drop archival fields.
- Notebook gold CSVs stay unregistered until path-cleaned and licensable.

## Next step

[STEP3-formula-search-script.md](STEP3-formula-search-script.md)
