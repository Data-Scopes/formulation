# Agent instructions — DH data project

Read this file, `docs/DATA.md`, and `PLAN.md` before writing pipeline code.

## Data paths (strict)

- **Never** hardcode absolute paths (`/Users/...`, `/Volumes/...`) in Python scripts.
- **Always** register datasets in `data_manifest.toml` first, then use:
  ```python
  from data_io import resolve, load, save_semi_structured, save_parquet
  ```
- **Always** run after manifest or tier changes:
  ```bash
  uv run python -m data_io.check
  ```

## Output writes (strict)

- Phase 1–2 (explore / semi): `save_semi_structured(..., logical_name="...", script=__file__)`
- Phase 3 (frozen): `save_parquet(df, logical_name="...", script=__file__)`
- Never write pipeline outputs without sidecar provenance (`data_io` does this automatically).

## Legacy / orphan files — `llm_archivist` (optional)

Available when the project was bootstrapped with `--with-archivist` (or `llm_archivist/` was added manually). For **existing** files without `data_io` sidecars (inbox dumps, old exports):

```bash
# Fast — no Ollama (columns, coverage, row counts)
uv run archive-inventory /path/to/folder

# LLM — rich description (requires Ollama at localhost:11434)
uv run archive-scan /path/to/folder --model qwen2.5-coder:latest
```

- Profiles `.parquet`, `.csv`, `.xlsx`, `.ipynb` → `filename.meta.toml`
- Use on `output/_inbox/` or migrated legacy data — **not** on `data_io` outputs
- After inventory, read **`INVENTORY.md`** at the scan root; add canonical files to `data_manifest.toml`

| Tool | When | Sidecar | LLM? |
|------|------|---------|------|
| `data_io.save_*` | New pipeline outputs | `.meta.toml` / `.parquet.meta.json` | No |
| `archive-inventory` | Fast orphan triage | `.meta.toml` (`inventory_mode = "fast"`) | No |
| `archive-scan` | Rich archival context | `.meta.toml` | Yes |

## Before adding a dataset

1. Add `[datasets.<logical_name>]` to `data_manifest.toml` (tier, path, phase, description, parent).
2. Run `data_io.check`.
3. Only then reference `logical_name` in code.

## Archival integrity

- Do not drop metadata fields from domain records when transforming.
- Do not mutate canonical reference files in place; write versioned outputs.
- Promote JSONL → Parquet only when schema is stable for one review cycle.

## Session workflow

1. One active step per session — never “execute the whole plan”.
2. Read `PLAN.md` first; if multi-step, follow `plans/steps/STEP*.md` (see wisdom [cost-sensitive-agent-workflow](../../wisdom/topics/cost-sensitive-agent-workflow.md)). Prefer advising commands; user runs the terminal by default.
3. Update `PLAN.md` when a step is done (checklist) and when manifest datasets change.
4. After a step: short handoff + next step; clear the chat before starting the next step.
5. (Recommended) `uv run python -m data_io.check` before new pipeline work.
6. Smoke test: `uv run python -c "from data_io import resolve; print(resolve('...'))"`

## Editors (Cursor, VS Code, Claude Code)

This file is the **canonical** agent brief. The same non-negotiables are copied into:

| Editor | File |
|--------|------|
| Cursor | `.cursor/rules/project-standards.mdc` (`alwaysApply`) |
| VS Code Copilot | `.github/copilot-instructions.md` |
| Claude Code | `CLAUDE.md` |

Do not edit those generated files by hand in a bootstrapped repo unless you keep all of them in sync. Domain extras go here (and in add-on `.cursor/rules/` + the `## Add-ons` section below).

## Optional: data_io MCP (Cursor)

When the `data-io-mcp` add-on is applied, prefer MCP tools (`check_manifest`, `list_datasets`, `preview_dataset`) over raw filesystem reads. See `docs/addons/data-io-mcp/README.md`.

## Common mistakes (avoid)

| Wrong | Right |
|-------|-------|
| `pd.read_parquet("/Volumes/...")` | `load("resolutions_flat")` |
| `open("data/out.jsonl", "w")` | `save_semi_structured(rows, logical_name="...")` |
| `archive-scan` on `data_io` outputs | Only scan legacy/orphan folders |
| New path in code only | New `[datasets.*]` entry + `data_io.check` |

## Wisdom and add-ons

- **Wisdom** (cross-project lessons): `docs/wisdom/` if bootstrapped with `--with-wisdom`, else `~/develop/dighum_template/wisdom/INDEX.md`
- **Add-ons** (domain overlays): see `docs/addons/APPLIED.md` and extra `.cursor/rules/*` (Cursor) plus this file’s `## Add-ons` section (all editors)
- Apply later: `~/develop/dighum_template/scripts/apply_addon.sh <this-repo> <name>`

## Add-ons

None applied yet.

## Domain (tracks)

- **Track R (judged):** retrieve missing whole *aanstellingsresoluties* over `resolutions_flat` + delegates `resolutie_refs`. STEPR4 stopped after TF-IDF; selection in `aanstelling_selected`. Do not mix retrieval into formula STEP2.
- **Track R2 (deferred):** pre-1705 expansion using ~615 reviewed keeps as exemplars (char k-NN/refit; optional dense rerank)—see [`plans/milestones/R2-pre1705-aanstelling-expansion.md`](plans/milestones/R2-pre1705-aanstelling-expansion.md). **Not active** until explicitly chosen.
- **Track L:** retrieve *missive/brief* receipts with *geen resolutie gevallen / vereischende* (L1). Mirror R1; exclude aanstelling ids from L positives. Seeds: `missive_receipt_seeds`.
- **Track S (judged):** formula **boundary evolution** — TF-IDF windows → Smith-Waterman (single / slot-cloud) → DAG for exact boilerplate spans. See [`plans/milestones/S1-formula-boundary-evolution.md`](plans/milestones/S1-formula-boundary-evolution.md). STEPS4: stop (no GysBERT). Next classical: STEPS1 threshold calibration; L1 STEPL1 available.
- **Track F (paused):** formulaic language via PyPI `formula_detection` / `FormulaSearch` (M1). Do not fork the library or lift the `republic_clean` notebook tree. Not the harness for Track S.

Do not mix tracks in one script. No live Elasticsearch.

Read [`PLAN.md`](PLAN.md), [`docs/formula-conceptual-overview.md`](docs/formula-conceptual-overview.md), and [`docs/formula-boundary-evolution.md`](docs/formula-boundary-evolution.md) before pipeline work. Execution: [`plans/formula-pipeline.md`](plans/formula-pipeline.md), [`plans/milestones/S1-formula-boundary-evolution.md`](plans/milestones/S1-formula-boundary-evolution.md), [`plans/milestones/R1-aanstelling-retrieval.md`](plans/milestones/R1-aanstelling-retrieval.md), [`plans/milestones/L1-missive-receipt-retrieval.md`](plans/milestones/L1-missive-receipt-retrieval.md).
