# M1 — First runnable formula slice

**Status:** in progress (STEP0–1 done; next STEP2)  
**Plan:** [`plans/formula-pipeline.md`](../formula-pipeline.md)  
**Steps:** STEP0–STEP4 under [`plans/steps/`](../steps/)

## Goal

Ship an ES-free path: **sample tokenized resolutions → `FormulaSearch` → provenanced candidate formulas**, with a README how-to-run and adapter tests. Reflect the conceptual model lightly (section/offsets on docs and candidates; gappy extract knobs available) without building a criteria engine.

## Done when

- Manifest tiers are local/in-repo and `uv run python -m data_io.check` is clean for registered datasets.
- `formula_detection` is a project dependency; `formulation.adapters` yields token streams `FormulaSearch` can consume.
- `sample_resolutions` and `s4_opening_phrase_candidates` are registered and loadable via `data_io`.
- `uv run python scripts/run_formula_search.py` writes candidates through `save_semi_structured`.
- Adapter/seed tests pass; `notebooks/01_formula_search_demo.ipynb` demonstrates the slice.

## Out of scope here

Full corpus ETL, live Elasticsearch, forking `formula_detection`, building-block criteria, hoedanigheden linking, Flair models, a web UI.

## Sources to read before implementing

- [`formulator-project-docs/internal-context/formula-port-list.md`](../../formulator-project-docs/internal-context/formula-port-list.md)
- [`docs/formula-conceptual-overview.md`](../../docs/formula-conceptual-overview.md) (keep / leave table)
- Package pattern: `formula_detection` `notebooks/resolution_iterables.py` (after the dependency is added)
