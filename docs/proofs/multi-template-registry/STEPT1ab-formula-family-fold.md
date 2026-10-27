# STEPT1ab — Formula family fold (NOTES)

**Status:** implemented (awaiting STEPT1aa full outputs or fixture-only).  
**Guide:** [`plans/steps/STEPT1ab-formula-family-fold.md`](../../../plans/steps/STEPT1ab-formula-family-fold.md)

```bash
uv run pytest tests/test_formula_family_fold.py -q
uv run python scripts/run_formula_family_fold.py --fixture-only
uv run python scripts/run_formula_family_fold.py
```

## Deliverables

| Logical name | Role |
|--------------|------|
| `formula_family_metrics` | Nest/variant fold summary |
| `formula_family_candidates` | Families: exemplar, members, zone×lcats, suggested_role; `human_role` empty |

## Gates

1. Fixture fold produces ≥1 family with null `human_role` — **PASS** (unit).
2. Zone-guard blocks merge of high-freq different-zone near-dupes — **PASS** (unit).
3. Full fold on aa outputs — **pending**.

## Matcher

Variant test (within hinge bucket + zone guard), any of:

1. `rapidfuzz.fuzz.ratio` ≥ **88**
2. `rapidfuzz.fuzz.token_set_ratio` ≥ **88**
3. contiguous shared token span ≥ **4** (sliding 5-gram windows of one formula)

Match against **any** cluster member (not only the exemplar) so windows chain. Plain ratio alone missed `op geen resolutie is gevallen` / `… <END>` / `WAAR op geen resolutie is` (ratios 85 / 74 / 60).

`<START>` / `<END>` are NLP parse artefacts — stripped in `normalize_phrase` before fold similarity (not counted as tokens).

## Next

Human role write-back → STEPT1ac typology map. **Then:** rebuild STEPT1z `formula_sequence_matrix` harvest from family exemplars and compare P / empty / nested-surface noise vs the pre-fold harvest.
