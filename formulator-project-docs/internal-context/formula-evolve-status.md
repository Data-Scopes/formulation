---
cursor:
  subagentId: "bc-b1f5b1a0-2045-5d68-bfb4-d6f8ac9cb2c6"
---

# Formula evolve status

Updated: 2026-09-21 (complete)

| Todo | Status | Notes |
|------|--------|-------|
| survey-merge | completed | `internal/formula-port-list.md` (+ S4 seed inventory path) |
| retarget-bootstrap | completed | `dighum-project` → `republic-formulas` |
| wire-formula-lib | completed | `formula_detection` + adapters + S4 seed reader/fixture/manifest |
| lift-notebooks | completed | `search_workflow.py`, script, demo notebook |
| first-slice | completed | Sample → FormulaSearch → provenanced candidates; 15 tests pass |

Working branch: `cursor/republic-formulas-evolve-b2c6` (pushed)

## How to run

```bash
uv sync
uv run python -m data_io.check
uv run python scripts/run_formula_search.py
uv run pytest tests/ -q
```

## PR

**Blocked:** `repoKind="agent_temp"` — Origin only supports PRs for standard repos. After Create repo, open a draft PR from `cursor/republic-formulas-evolve-b2c6` → `main`.

## Key paths

- `republic_formulas/adapters.py`, `seeds.py`, `search_workflow.py`
- `scripts/run_formula_search.py`
- `data/warm/datasets/corpus/sample_resolutions.jsonl`
- `data/warm/datasets/seeds/s4_opening_phrase_candidates.jsonl`
- `tests/test_adapters.py`, `tests/test_seeds.py`
- `notebooks/01_formula_search_demo.ipynb`
