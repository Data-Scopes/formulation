# STEPS6c — Stream-harvest ORG annotations → provenanced `institution_patterns`

**Goal:** Aggregate republic_ner `ORG-annotations` (`tag_text` + `inv`) for appointment `TARGET_ORG_ENTITIES` into period-/inventory-keyed pattern rows, written via `save_semi_structured`.  
**Done when:** `inventory_metadata` + `institution_patterns_seeds` registered; harvest script + unit tests green; user-run full harvest writes scratch `institution_patterns` (+ metrics); `data_io.check` passes.

## Prerequisites

STEPS6 bookkeeping + S6b prove wire-up done. Local.toml points at `org_annotations`, `org_entities`, and `inventory_metadata` (see `data_manifest.local.toml.example`).

## You do

```bash
# Optional smoke (first N annotation objects)
uv run python scripts/harvest_institution_patterns.py --limit 50000

# Full stream (~650MB annotations; streams, does not json.load)
uv run python scripts/harvest_institution_patterns.py

uv run python -m data_io.check
uv run pytest tests/test_institution_patterns.py tests/test_institution_pattern_harvest.py -q
uv run python -c "
from formulation.institution_patterns import load_patterns, patterns_for_target
rows = load_patterns()
print('n', len(rows), 'sources', {r['source'] for r in rows})
print('rekenkamer@1780', len(patterns_for_target('rekenkamer', year=1780)))
"
```

## Do not

- `json.load` the full annotations file
- Put org surface strings into `formula_templates`
- Treat NER committees as template classification
- Open Track L harvest or FormulaSearch STEP2
- Change STEPS1 cosine cut

## After this step

Mark S6c in `PLAN.md`. Next (explicit choice): re-run prove against harvested surfaces, tighten `--min-n`, or link `gecommitteerde_raaden` entities. Clear the chat before the next step.
