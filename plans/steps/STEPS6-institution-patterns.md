# STEPS6 — Period-keyed `institution_patterns` (bookkeeping)

**Goal:** Register republic_ner ORG inputs and a period-/inventory-keyed `institution_patterns` schema so appointment `discriminators: ["institution"]` can consume harvested surfaces later — without a full 650MB harvest in this session.  
**Done when:** `org_annotations` / `org_entities` / `institution_patterns` are in the manifest; fixture loads via `formulation.institution_patterns`; `data_io.check` + unit tests green; local.toml example documents the 2TB / data.bak overrides.

## Prerequisites

STEPS5 done. Read [`docs/DECISIONS.md`](../../docs/DECISIONS.md) (ORG harvest decision) and [`docs/proofs/multi-template-registry/NOTES.md`](../../docs/proofs/multi-template-registry/NOTES.md) § “Next pattern source”.

## You do

```bash
# Point local overrides at republic_ner paths (do not commit local.toml)
# See data_manifest.local.toml.example — org_annotations / org_entities blocks.

uv run python -m data_io.check
uv run pytest tests/test_institution_patterns.py tests/test_formula_templates.py -q
uv run python -c "
from formulation.institution_patterns import load_patterns, patterns_for_target
rows = load_patterns()
print('n', len(rows))
print(patterns_for_target('rekenkamer', year=1780)[:3])
"
```

Optional resolve smoke (needs local.toml + mounted 2TB):

```bash
uv run python -c "from data_io import resolve; print(resolve('org_annotations')); print(resolve('org_entities'))"
```

## Do not

- Stream / aggregate full `ORG-annotations.json` (650MB) in this step
- Treat NER committee labels as `formula_templates` classification
- Rewire `scripts/prove_appointment_institution.py` or freeze new discriminators
- Open Track L harvest or FormulaSearch STEP2

## After this step

Mark STEPS6 bookkeeping in `PLAN.md`. Next (explicit choice): stream-harvest ORG surfaces into provenanced `institution_patterns`, or wire patterns into the prove script. Clear the chat before the next step.
