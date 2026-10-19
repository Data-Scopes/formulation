# Data layout and manifest

Decouple code from disk layout using `data_manifest.toml` and `data_io`.

## Tiers (edit in `data_manifest.toml`)

| Tier | Typical role |
|------|----------------|
| **hot** | Code repos, tiny local inputs |
| **warm** | Canonical parsed datasets (parquet, annotation JSON) |
| **scratch** | Ephemeral exports, semi-structured JSONL (in-repo `./output` by default) |
| **cold** | Raw archives (zip, XML dumps) |
| **collab** | SurfDrive / Nextcloud shared data |

**Scratch:** committed default is `./output`. Override `[tiers.scratch]` in `data_manifest.local.toml` if you want an external drive (see `output/README.md`). Pipeline writes still go through `data_io` — not ad-hoc files in `notebooks/`.

## Workspaces

| Directory | Role |
|-----------|------|
| `notebooks/` | Ad-hoc `.ipynb` explore work (Jupyter default root) |
| `output/` | Scratch-tier root (gitignored; see `output/README.md`) |

## Day-zero checklist

1. Committed `data_manifest.toml` already uses in-repo tier roots (`.` / `./data/warm` / `./output` / `./data/cold`).
2. Optional: `data_manifest.local.toml` (gitignored) — per-machine overrides (external drives, full S4 file). **Track R requires it:** absolute paths for `resolutions_flat` and `delegates_resolutie_refs` (see `data_manifest.local.toml.example`).
3. `uv sync` (already run by bootstrap; re-run if you change dependencies)
4. `uv run python -m data_io.check` — the data registry view (declared datasets + on-disk status)
5. Add `[datasets.*]` entries before writing scripts that read/write data.

## Registered datasets (this repo)

| Logical name | Phase | Notes |
|--------------|-------|--------|
| `formula_documents` | frozen | republic_clean `documents.parquet`: boolean formula-family flags per `doc_id` (1705–1796); path override in `data_manifest.local.toml` |
| `formula_templates` | explore | Multi-template registry stub (framing / doc_flag / appointment_subtype / residual) |
| `resolutions_flat` | frozen | Shared REPUBLIC resolutions; Track R + formula text; often needs absolute path in `local.toml` |
| `delegates_resolutie_refs` | frozen | rc5 delegate resolutie refs (labels, not full text) |

Full list: `uv run python -m data_io.check`.

## Data registry view

`uv run python -m data_io.check` is the fastest way to answer “what datasets do I know about, and which of them are currently available on disk?” without doing broad filesystem searches.

It lists:

- each configured `tier` and whether its `mount_check` path exists
- each `[datasets.<logical_name>]` entry from `data_manifest.toml`, including the resolved path and whether it currently exists

Limits:

- it only shows datasets that are declared in `data_manifest.toml`
- it does not discover “extra” files that you forgot to register; for legacy/orphan files you use the `llm_archivist` workflow (`archive-inventory` / `archive-scan`) on `output/_inbox/`

## Three-phase pipeline

| Phase | Format | Save via |
|-------|--------|----------|
| explore | jsonl, pkl, xlsx | `save_jsonl(..., phase="explore")` |
| semi | jsonl + `.meta.toml` | `save_semi_structured(...)` |
| frozen | parquet + `.meta.json` | `save_parquet(...)` |

Promote to Parquet only after schema review.

## Provenance sidecars

`data_io` writes deterministic provenance sidecars for pipeline outputs:

- Phase 1–2: `*.meta.toml`
- Phase 3: `*.meta.json` (and embedded Parquet metadata)
- Also: `*.provenance.json` (stable JSON provenance, for spec compatibility)

## API

```python
from data_io import resolve, load, save_semi_structured, save_parquet

path = resolve("my_dataset")
rows = load("my_dataset")

save_semi_structured(records, logical_name="my_output", script=__file__)
```

## GNB-style example

```toml
[datasets.gnb_passport_sessions]
tier = "scratch"
path = "gnb_passport_sessions.jsonl"
phase = "semi"
parent = "gnb_raw_resolutions"
description = "Sessions with passport agenda items"
```

```python
save_semi_structured(
    sessions,
    logical_name="gnb_passport_sessions",
    parent_sources=["gnb_raw_resolutions"],
    description="Ready for entity extraction.",
    script=__file__,
)
```

## Legacy files — `llm_archivist` (optional)

Bootstrap with `--with-archivist` to install `llm_archivist` and inbox helper scripts. For files **not** created by `data_io` (inbox dumps, old exports):

```bash
# Fast — no Ollama (columns, coverage, row counts)
uv run archive-inventory ./output/_inbox
# → INVENTORY.md + inventory_report.toml at scan root

# LLM — rich description (Ollama on localhost:11434)
uv run archive-scan ./output/_inbox --model qwen2.5-coder:latest
```

**Do not** run on `data_io` outputs — they already have provenance sidecars.

| Tool | Use case | LLM? |
|------|----------|------|
| `data_io.save_*` | New pipeline writes | No |
| `archive-inventory` | Fast orphan triage | No |
| `archive-scan` | Inferred research context | Yes |

Shortcuts: `./scripts/inventory_inbox.sh` (fast), `./scripts/archive_inbox.sh` (LLM)

