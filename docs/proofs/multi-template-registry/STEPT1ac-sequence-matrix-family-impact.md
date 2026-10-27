# STEPT1ac — Sequence-matrix family impact (NOTES)

**Status:** implemented (catalog path); full year matrix optional user run.  
**Guide:** [`plans/steps/STEPT1ac-sequence-matrix-family-impact.md`](../../../plans/steps/STEPT1ac-sequence-matrix-family-impact.md)  
**Decision:** [`docs/DECISIONS.md`](../../DECISIONS.md) 2026-10-26 *Do science on a canonical form*.

```bash
uv run pytest tests/test_formula_family_skim.py tests/test_formula_sequence_family_impact.py -q
uv run python scripts/run_formula_family_fold.py --skim-xlsx-only
uv run python scripts/run_formula_sequence_family_impact.py --catalog-only
# Optional full 1780 rebuild on exemplars (preserves STEPT1z jsonl):
uv run python scripts/run_formula_sequence_family_impact.py --year 1780
```

## Principle

**Do science on a canonical form.** Family exemplar = matrix/harvest join key; members for skim only.

## Deliverables

| Artifact | Role |
|----------|------|
| `formula_family_skim.xlsx` | Blank `keep` / `human_role` / `variant_of` |
| `formula_sequence_family_harvest` | Exemplar (+ pocket) harvest shortlist |
| `formula_sequence_family_impact_metrics` | Hard catalog stats + soft containment (+ year deltas if run) |

## Soft vs hard

- **Hard:** harvest surface count / family collapse ratio; year empty/nodes/edges when `--year` run.
- **Soft:** STEPT1z harvest strings contained under family exemplars/members.

## Catalog result (1780 families on disk, 2026-10-26)

- families **1978**; member surfaces **3273** (collapse ≈1.65 members/family)
- STEPT1z harvest **28** → exemplar harvest cap **40** (pockets + stratified exemplars)
- soft containment **15/28 (0.536)** — misses are mostly scheme OCR variants / short stubs not in the 5-gram fold (`goetgervonden`, `remons`, `conform…`, welkom scheme canonic, …)

## Next

Human fills `formula_family_skim.xlsx` → typology map. Optional: `--year 1780` for empty/node deltas vs STEPT1z.
