# STEPT1af — Overlap-first fold; type from place (NOTES)

**Status:** implemented (code); full `--overlap` re-fold = user run.  
**Guide:** [`plans/steps/STEPT1af-overlap-first-type-from-place.md`](../../../plans/steps/STEPT1af-overlap-first-type-from-place.md)

```bash
uv run pytest tests/test_formula_family_fold.py tests/test_overlap_cue_prove.py tests/test_phrases_5gram_profile.py -q
uv run python scripts/run_formula_family_fold.py --overlap
```

## Pipeline

Pass A surfaces (freq only) → repair/split → nest → overlap group → name-strip → **then** `suggested_role` from place + cue.

## Gates (unit)

| Gate | Result |
|------|--------|
| Type after overlap (`type_after_overlap`) | **PASS** |
| Null wins over `waar_op` | **PASS** |
| Bare mid-`waar` split | **PASS** |
| Name strip (griffier+name) | **PASS** |
| Body ≠ opener via `opener_abs` | **PASS** |
| No `gedelibereert_*` cue seed | **PASS** |

## Next

User `--overlap` re-fold → skim cue/place/roles.
