---
cursor:
  subagentId: "bc-b33674e7-d9b0-5658-bdd2-545cb6b2fb61"
---

# dighum_template derivation

## Template

[HoekR/dighum_template](https://github.com/HoekR/dighum_template) bootstraps **digital humanities data pipeline** projects (not a web app). New projects are created with `scripts/bootstrap.sh`, which copies `template/`, vendors `packages/data_io/`, substitutes `PROJECT_NAME`, syncs editor rules, optionally copies wisdom / add-ons / archivist, then runs `uv sync`.

Stack: Python ≥3.12, **uv**, pandas/pyarrow, Jupyter (`ipykernel`), pytest. Convention: `data_manifest.toml` + `data_io` for paths and provenance.

## What landed in this Project

Branch: `cursor/dighum-template-derive-fb61`  
Placeholder package name: **`dighum-project`**

Derived instance (bootstrap-equivalent, `--with-wisdom`; no domain add-on):

| Included | Omitted (template-only / optional) |
|----------|-------------------------------------|
| `data_io/`, `tests/test_data_io.py` | Template repo `scripts/`, `addons/`, `wisdom/` journal |
| `data_manifest.toml` (+ `.example`) | `--with-archivist` / `llm_archivist` |
| Agent profile (`AGENTS.md`, `.cursor/`, `.github/`, `.vscode/`, workspace) | Domain overlays (`rpp`, `trifecta`, …) |
| `docs/DATA.md`, `docs/wisdom/` (11 topics) | `dighum_web_template` web surface |
| `notebooks/`, `output/`, `PLAN.md`, `README.md`, `pyproject.toml`, `uv.lock` | |

Tier roots in `data_manifest.toml` were set to local-friendly paths (`.` / `./data/warm` / `./output` / `./data/cold`) so the checkout runs without Rik’s external drives.

## How to run

```bash
# requires uv (https://docs.astral.sh/uv/)
uv sync
uv run python -m data_io.check
uv run pytest tests/ -q
```

Verified here: `data_io.check` OK (example datasets `MISSING` until real data is registered); **5 tests passed**. No web/dev server — this is a pipeline repo.

## PR

Draft PR **not created**: Origin reported `repoKind="agent_temp"` — pull requests are only supported for standard Origin repos. After Rik creates a real repo (Create repo), reopen a draft PR from `cursor/dighum-template-derive-fb61`.

## Blockers / Rik input

1. **Final project name** — replace `dighum-project` in `pyproject.toml`, README, workspace file, `[manifest].project`, kernel name.
2. **Domain add-on?** — `rpp`, `trifecta`, `paper-figures`, and/or `data-io-mcp` once the research domain is known.
3. **Real git remote / PR** — need a non-`agent_temp` repo to open the draft PR.
4. Optional: `--with-archivist` if legacy inbox inventory is needed (sibling `llm-archivist`).
