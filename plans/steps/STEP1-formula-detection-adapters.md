# Step 1 — `formula_detection` and adapters

**Goal:** Depend on the published library and expose REPUBLIC-style token streams this project owns.  
**Done when:** `formulation.adapters` yields iterables `FormulaSearch` accepts; `uv add` is in `pyproject.toml` / `uv.lock`; a smoke import works.

## Prerequisites

STEP0. Port list: [`formulator-project-docs/internal-context/formula-port-list.md`](../../formulator-project-docs/internal-context/formula-port-list.md).

## You do

```bash
uv add 'formula_detection>=0.5.0,<0.6'
# if install fails on Python 3.13+, pin requires-python to >=3.12,<3.13
uv run python -c "from formula_detection.search import FormulaSearch; print(FormulaSearch)"
```

## Cursor guides

- Add package `formulation/` (`adapters.py`; keep archival metadata on records).
- Pattern to copy *as an idea*: upstream `notebooks/resolution_iterables.py` / `ResolutionSentences` — iterable of token lists or dicts with `words`.
- Include `formulation` in setuptools package discovery (today only `data_io` and `tests`).
- Do **not** vendor the `formula_detection` tree. Do **not** import `republic.*` or talk to Elasticsearch.

## Next step

[STEP2-sample-corpus-and-seeds.md](STEP2-sample-corpus-and-seeds.md)
