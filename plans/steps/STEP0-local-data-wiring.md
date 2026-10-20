# Step 0 — Local data wiring

**Goal:** Point `data_io` at in-repo tiers so it resolves without placeholder `/Volumes` paths.  
**Done when:** `data_manifest.toml` uses relative roots; `uv run python -m data_io.check` runs; example datasets may still be `MISSING`.

## Prerequisites

Read [`docs/DATA.md`](../../docs/DATA.md) and [`formulator-project-docs/internal-context/tiers-vs-drives.md`](../../formulator-project-docs/internal-context/tiers-vs-drives.md).

## You do

Committed default (do **not** require external drives):

| Tier | Root |
|------|------|
| hot | `.` |
| warm | `./data/warm` |
| scratch | `./output` |
| cold | `./data/cold` |

Optional: `cp data_manifest.local.toml.example data_manifest.local.toml` only if you need a scratch or S4 override. **Do not commit** `data_manifest.local.toml`.

```bash
uv sync
uv run python -m data_io.check
```

Full S4 file (later steps, via local.toml or a registered cold/warm path — never hardcoded in Python):

`~/develop/republic_ner_matching/output/s4_opening_phrase_candidates.jsonl`

## Cursor guides

Edit `data_manifest.toml` tier roots and `[manifest].project` if needed. Do not register first-slice datasets yet (that is STEP2). Do not invent `/Volumes/...` names.

## Next step

[STEP1-formula-detection-adapters.md](STEP1-formula-detection-adapters.md)
