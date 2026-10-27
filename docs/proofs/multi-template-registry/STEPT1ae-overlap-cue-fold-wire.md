# STEPT1ae — Overlap-cue fold wire (NOTES)

**Status:** implemented (code); full `--overlap` year re-fold optional user run.  
**Guide:** [`plans/steps/STEPT1ae-overlap-cue-fold-wire.md`](../../../plans/steps/STEPT1ae-overlap-cue-fold-wire.md)  
**Prior:** STEPT1ad accepted.

```bash
uv run pytest tests/test_formula_family_fold.py tests/test_overlap_cue_prove.py -q
uv run python scripts/run_formula_family_fold.py --fixture-only --overlap-fixture --no-write
# full re-fold on STEPT1aa outputs (streams overlap dump):
# uv run python scripts/run_formula_family_fold.py --overlap
```

## Gates

| Gate | Result |
|------|--------|
| Default fold unchanged without `--overlap` | **PASS** (fixture 5 families both paths on stock fixture) |
| Overlap unites gedelibereert → `waar_op` | **PASS** (unit: 4 windows → 1 family) |
| `human_role` always null | **PASS** |

## Next

```bash
uv run python scripts/run_formula_family_fold.py --overlap
```

Then skim `formula_family_skim.xlsx` (cue / place / part_of columns).
