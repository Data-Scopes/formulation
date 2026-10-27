# STEPT1aa — 5-gram high-freq inventory + rare sidecar (NOTES)

**Status:** implemented (awaiting full dump run).  
**Guide:** [`plans/steps/STEPT1aa-phrases-5gram-profile.md`](../../../plans/steps/STEPT1aa-phrases-5gram-profile.md)

```bash
uv run pytest tests/test_phrases_5gram_profile.py -q
uv run python scripts/run_phrases_5gram_profile.py --fixture-only
uv run python scripts/run_phrases_5gram_profile.py          # full dump
uv run python scripts/run_phrases_5gram_profile.py --year 1780
uv run python -m data_io.check
```

## Deliverables

| Logical name | Role |
|--------------|------|
| `phrases_5gram_18th` | Frozen occurrence dump (local.toml → Extreme SSD) |
| `phrases_5gram_profile_metrics` | Stream summary (`n_high_freq`, `n_protected_below_gate`, …) |
| `phrases_5gram_high_freq` | Pass A unique phrases ≥ `MIN_FREQ` |
| `phrases_5gram_rare_sidecar` | Protected below-gate + mid-body rare top-N |
| `output/phrases_5gram_profile.xlsx` | Human skim (not a manifest dataset) |

## Gates

1. Fixture: high_freq + protected sidecar present — **PASS** (unit).
2. Full-run numbers — **pending** user terminal.
3. No fold / mint this step — **PASS**.

## Caveats

- Pass A is scaffolding-biased; sidecar is recovery, not a full rare census.
- `MIN_FREQ` is a size adaptation; legacy notebooks did not gate on `phrase_freq` at load.

## Next

STEPT1ab fold → human skim → **impact on `formula_sequence_matrix`** (replace noisy harvest surfaces with folded family exemplars).
