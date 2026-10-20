# formulation

DH data pipeline for **formulaic language** in REPUBLIC (Dutch States General) resolutions: find and type templated openings, decisions, and related skeletons via `formula_detection`, with paths and provenance through `data_manifest.toml` + `data_io`.

Plan: [`PLAN.md`](PLAN.md). Research notions: [`docs/formula-conceptual-overview.md`](docs/formula-conceptual-overview.md).

## Setup

```bash
# Bootstrap already ran `uv sync` and installed the Jupyter kernel.
# Re-run `uv sync` if you later change dependencies.
# Committed data_manifest.toml uses in-repo tier roots.
# Optional per-machine overrides (external drives, full S4 file):
# cp data_manifest.local.toml.example data_manifest.local.toml
# Data registry view (manifest-declared datasets + on-disk status)
uv run python -m data_io.check
```

Open the workspace profile in Cursor or VS Code:

```bash
cursor formulation.code-workspace
# or: code formulation.code-workspace
```

## Layout

| Path | Role |
|------|------|
| `AGENTS.md` | Agent instructions (Cursor and VS Code Copilot) |
| `PLAN.md` | Headlines checklist and dataset table |
| `plans/` | Milestones and step guides (fill when multi-step) |
| `docs/DATA.md` | Tiers, phases, manifest workflow |
| `data_manifest.toml` | Tier roots and registered datasets |
| `notebooks/` | Jupyter workspace (explore phase) |
| `output/` | Scratch-tier root (gitignored; see `output/README.md`) |
| `data_io/` | Manifest I/O and provenance helpers |

## Agents (Cursor / VS Code)

Read **`AGENTS.md`** first. The same standards load from:

- Cursor: `.cursor/rules/project-standards.mdc`
- VS Code Copilot: `.github/copilot-instructions.md`
