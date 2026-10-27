# STEPT1ah — Seed hinge archetype ledger

**Goal:** Hand-seed a small **`formula_hinge_candidates`** ledger (~15–25 hinge-sized archetypes) under the locked formula-in-effect ontology. Decision scaffolding first; L2 of the six blueprints; pockets unnamed.
**Done when:** fixture + provenanced seed written; unit tests pass; `data_io.check` clean; NOTES + `PLAN.md` updated.

**Prerequisite:** Redesign pause locked ([`docs/DECISIONS.md`](../../docs/DECISIONS.md) 2026-10-26 formula-in-effect; [`docs/formula-conceptual-overview.md`](../../docs/formula-conceptual-overview.md)). STEPT1aa–ag parked as archaeology.

## Constraint (locked)

- Archetypes first — **no** witness TF-IDF, no fold, no residual skim, no auto-mint to `formula_templates`.
- Omit standalone `gedelibereert`; person/office strings; fold exemplars; residual-review rows.
- Statuses: `candidate` (scaffolding), `from_blueprint` (L2 of accepted openers), `pocket` (canonic may be null).
- Human fields blank (`human_keep`, `human_note`).

## You do

```bash
uv run pytest tests/test_formula_hinge_ledger.py -q
uv run python scripts/seed_formula_hinge_ledger.py --fixture-only
uv run python scripts/seed_formula_hinge_ledger.py
uv run python -m data_io.check
```

Fill: [`docs/proofs/multi-template-registry/STEPT1ah-hinge-archetype-seed.md`](../../docs/proofs/multi-template-registry/STEPT1ah-hinge-archetype-seed.md).

## After this step

Human glance the ledger. Clear the chat before witness adjudicate (char TF-IDF near/mid/far).
