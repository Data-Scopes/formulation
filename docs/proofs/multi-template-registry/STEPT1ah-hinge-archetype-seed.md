# STEPT1ah — Hinge archetype seed (NOTES)

**Status:** done — fixture + provenanced `formula_hinge_candidates` / `_metrics` on disk (**n=20** after polarity addendum).  
**Guide:** [`plans/steps/STEPT1ah-hinge-archetype-seed.md`](../../../plans/steps/STEPT1ah-hinge-archetype-seed.md)  
**Ontology:** DECISIONS 2026-10-26 formula-in-effect + decision-polarity pockets.

```bash
uv run pytest tests/test_formula_hinge_ledger.py -q
uv run python scripts/seed_formula_hinge_ledger.py --fixture-only
uv run python scripts/seed_formula_hinge_ledger.py
```

## Deliverables

| Logical name | Role |
|--------------|------|
| `formula_hinge_candidates` | Seeded hinge archetypes (human fields blank) |
| `formula_hinge_metrics` | Counts by layer / status / place_band |

## Gates

| Gate | Result |
|------|--------|
| n in ~15–25 | **PASS** (n=20) |
| No `gedelibereert` hinge_id | **PASS** |
| Decision scaffolds present | **PASS** |
| Six blueprints linked as `from_blueprint` | **PASS** |
| Decision polarity pockets (null canonic) | **PASS** (`decision_positive` / `_negative` / `_conditional` / `_deferred`) |
| No auto-mint / templates untouched | **PASS** |

## Next

Re-seed provenanced ledger (`seed_formula_hinge_ledger.py`) → STEPT1ai witness adjudicate.
