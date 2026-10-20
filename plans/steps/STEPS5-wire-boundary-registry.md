# STEPS5 — Wire boundary defaults to `formula_templates`

**Goal:** STEPS1–3 framing (`opening_requeste_18c` tokens + frozen 0.40 cosine) come from the registry, not hardcoded lists in `tfidf_windows`.  
**Done when:** `default_opening_template` / `default_framing_threshold` / slot-cloud `default_template` resolve via `resolve_framing_template`; tests green; no institution_patterns harvest.

## Prerequisites

Registry stub registered (`formula_templates` + `formulation.formula_templates`). STEPS1b cut frozen at 0.40 on the framing row.

## You do

```bash
uv run pytest tests/test_formula_templates.py tests/test_tfidf_windows.py tests/test_slot_cloud.py tests/test_span_harvest.py -q
uv run python -c "from formulation.boundary.tfidf_windows import default_opening_template, default_framing_threshold; print(default_opening_template(), default_framing_threshold())"
```

Fixture-only smoke (optional, light):

```bash
uv run python scripts/run_tfidf_window_framing.py --fixture-only
```

## Do not

- Harvest `institution_patterns` or touch republic_ner ORG files
- Change the frozen 0.40 cut or extend the template past *Requeste*
- Re-run full-year framing / span harvest unless checking a regression
- Resume FormulaSearch STEP2 or Track L harvest

## After this step

Mark STEPS5 in `PLAN.md`. Next: period-keyed `institution_patterns`, or another explicit choice. Clear the chat before the next step.
