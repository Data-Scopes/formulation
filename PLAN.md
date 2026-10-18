# Project plan

Headlines only. Keep this file short. Full plans, milestones, and step guides live under [`plans/`](plans/) — see dighum_template wisdom [cost-sensitive-agent-workflow](../../wisdom/topics/cost-sensitive-agent-workflow.md).

Two tracks, one step per session. **Active retrieval (next): Track L STEPL1** (missive receipt labelled table). Track F STEP2 remains available; R1 judged.

Cross-cutting: [`plans/formula-pipeline.md`](plans/formula-pipeline.md). Retrieval: [`plans/milestones/R1-aanstelling-retrieval.md`](plans/milestones/R1-aanstelling-retrieval.md), [`plans/milestones/L1-missive-receipt-retrieval.md`](plans/milestones/L1-missive-receipt-retrieval.md). Research notions: [`docs/formula-conceptual-overview.md`](docs/formula-conceptual-overview.md).

**Side plans / deferred tracks (not active):** [Presence lists 1630–1704](plans/presence-lists-1630-1704-side-plan.md) — raw session JSON harvest; [R2 pre-1705 aanstelling expansion](plans/milestones/R2-pre1705-aanstelling-expansion.md) — char/vector expansion using R1’s 615 pre-1705 keeps; **do not execute** until chosen.

## Goal

- **Track R (judged):** recover missing whole *aanstellingsresoluties* from `resolutions_flat` by similarity to gold `resolutie_refs`. Stopped after char n-gram TF-IDF + logistic regression; no residual neural pass. Selection: `aanstelling_selected`.
- **Track L (next):** recover *missive/brief receipt with no substantive resolution* (*geen resolutie gevallen / vereischende*). Mirror R1 machinery; different type filters.
- **Track F:** detect, group, and type **formulaic language** in REPUBLIC resolutions as building blocks. Technical core: `formula_detection.FormulaSearch`; write through `data_io`. Resume at STEP2 when L1 pauses.

## One research thread (tracks are not sidesteps)

Same object: **templated administrative language** in States-General material (fixed skeletons, variable slots, spelling drift, position matters). Different **units and outputs**:

| Work | Unit | Question |
|------|------|----------|
| **R1** | whole resolution | Which sittings match the *aanstelling* document type? (char TF-IDF harvest) |
| **R2** (deferred) | whole resolution, `year < 1705` | Expand pre-18c recall using **615 reviewed exemplars** + char k-NN/refit; optional dense rerank; not new gold |
| **L1** | whole resolution | Which sittings are *missive/brief* receipts with *geen resolutie*? |
| **M1–M3** | spans / building blocks | What recurring skeletons exist, how do they compose, where do they sit in the resolution? |
| **Presence side plan** | session opening / presentielijst | Where is the presidium block in raw session text, across 1630–1704? (bracket: 1626–30 gold + 18c phrase seeds) |

Shared machinery recurs: **character-level tolerance**, **manifest + provenance**, **candidate-then-structure** (fuzzy or n-gram recall, then pairing/position/criteria)—not one monolithic pipeline. Side plans stay off the active checklist but feed the same typology and segmentation story as formula work.

**Publications (REPUBLIC / formulas):** [docs/research-publications.md](docs/research-publications.md) — JOCCH preexisting structures + fuzzy boundaries; incremental modelling; attendance lists across centuries; formulaicity & regularisation (1576–1796).

## Milestones

| Milestone | Doc | Status |
|-----------|-----|--------|
| R1 Aanstelling retrieval | [R1-aanstelling-retrieval.md](plans/milestones/R1-aanstelling-retrieval.md) | done (stop after TF-IDF; selection frozen) |
| R2 Pre-1705 aanstelling expansion | [R2-pre1705-aanstelling-expansion.md](plans/milestones/R2-pre1705-aanstelling-expansion.md) | **deferred** (registered; not started) |
| L1 Missive-receipt retrieval | [L1-missive-receipt-retrieval.md](plans/milestones/L1-missive-receipt-retrieval.md) | in progress (STEPL0 done; next STEPL1) |
| M1 First runnable slice | [M1-first-slice.md](plans/milestones/M1-first-slice.md) | in progress (STEP0–1 done; next STEP2) |
| M2 Building-block criteria | [M2-building-blocks.md](plans/milestones/M2-building-blocks.md) | not started |
| M3 Composition + position | [M3-composition-and-position.md](plans/milestones/M3-composition-and-position.md) | not started |

## Progress checklist

### Track R — retrieval (R1), judged

| Step | Guide | Done when | Status |
|------|-------|-----------|--------|
| R0 | [STEPR0-register-retrieval-inputs.md](plans/steps/STEPR0-register-retrieval-inputs.md) | `resolutions_flat` + `delegates_resolutie_refs`; `data_io.check`; grain/years recorded | done |
| R1 | [STEPR1-join-urns.md](plans/steps/STEPR1-join-urns.md) | Provenanced labelled table of gold URNs joined to flat text | done |
| R2 | [STEPR2-tfidf-baseline.md](plans/steps/STEPR2-tfidf-baseline.md) | Char n-gram TF-IDF + LR holdout recall/precision/F1 | done |
| R3 | [STEPR3-harvest-buckets.md](plans/steps/STEPR3-harvest-buckets.md) | Unlabelled remainder scored high / grey / low | done |
| R4 | [STEPR4-residual-or-stop.md](plans/steps/STEPR4-residual-or-stop.md) | Stop, or one residual neural pass on TF-IDF negatives | done (stop) |

### Track L — missive receipt (L1), next

| Step | Guide | Done when | Status |
|------|-------|-----------|--------|
| L0 | [STEPL0-define-missive-receipt-type.md](plans/steps/STEPL0-define-missive-receipt-type.md) | Type + seeds + cue inventory counts | done |
| L1 | (STEPL1 — labelled table) | Provenanced positives + overig; exclude aanstelling ids | not started |
| L2 | (STEPL2 — TF-IDF baseline) | Holdout recall / precision / F1 | not started |
| L3 | (STEPL3 — harvest) | Remainder high / grey / low | not started |
| L4 | (STEPL4 — residual or stop) | Written decision | not started |

### Track F — formulas (M1)

| Step | Guide | Done when | Status |
|------|-------|-----------|--------|
| 0 | [STEP0-local-data-wiring.md](plans/steps/STEP0-local-data-wiring.md) | In-repo tier roots; `data_io.check` runs | done |
| 1 | [STEP1-formula-detection-adapters.md](plans/steps/STEP1-formula-detection-adapters.md) | `formula_detection` dep + `formulation.adapters` token streams | done |
| 2 | [STEP2-sample-corpus-and-seeds.md](plans/steps/STEP2-sample-corpus-and-seeds.md) | `sample_resolutions` + `s4_opening_phrase_candidates` registered | not started |
| 3 | [STEP3-formula-search-script.md](plans/steps/STEP3-formula-search-script.md) | `scripts/run_formula_search.py` writes provenanced candidates | not started |
| 4 | [STEP4-tests-and-demo.md](plans/steps/STEP4-tests-and-demo.md) | pytest + demo notebook + README how-to-run | not started |

Survey + dighum shell: done (see pipeline plan). Do not lift the `republic_clean` notebook tree or talk to live Elasticsearch.

## Data paths

Logical names live in [`data_manifest.toml`](data_manifest.toml). Verify with `uv run python -m data_io.check`. Register **before** code references them. Track R machine paths (2TB parquet, rc5 xlsx) go in gitignored `data_manifest.local.toml`.

| Logical name | Phase | Notes |
|--------------|-------|-------|
| `resolutions_flat` | frozen | Shared REPUBLIC parquet; one row per resolution; path override in local.toml |
| `delegates_resolutie_refs` | frozen | rc5 xlsx gold (`resolutie_refs` URNs); path override in local.toml |
| `delegates_unique_1705_1795` | frozen | Unique delegates + OCR `patterns` for naming harvest hits; local.toml |
| `attendance_long_1705_1795` | frozen | Attendance-long rc6 (d/m/j per sitting); date constraints for matching |
| `aanstelling_gold_relocations` | explore | 18 drifted URNs mapped to nearby `resolutions_flat` ids; still positives |
| `aanstelling_labelled` | frozen | Gold texts + 10× overig sample (one row per resolution); STEPR1 |
| `aanstelling_tfidf_holdout` | frozen | 20% stratified test rows + TF-IDF+LR scores; STEPR2 |
| `aanstelling_tfidf_metrics` | semi | Holdout recall / precision / F1 and frozen settings; STEPR2 |
| `aanstelling_tfidf_harvest_poc` | explore | One-year remainder scores + buckets; STEPR3 POC |
| `aanstelling_tfidf_harvest_poc_metrics` | semi | Harvest-cut holdout metrics + remainder-year counts; STEPR3 POC |
| `aanstelling_tfidf_harvest` | frozen | Full unlabelled remainder high / grey / low; STEPR3 |
| `aanstelling_retrieval_xlsx` | explore | Human Excel: gold + ingest + review + ES + shape + unique-pattern delegate matches |
| `aanstelling_review_labels` | semi | keep/drop labels (human + rule) for suspect sheets |
| `aanstelling_selected` | semi | Final R1 vergadering-aanstelling id list + rough names |
| `aanstelling_pre1705_gold_review_xlsx` | explore | Early pre-1705 rows to score for new gold (`to_score` sheet) |
| `missive_receipt_seeds` | explore | Hand seed texts for L1 (*geen resolutie* missive receipts) |
| `formula_documents` | frozen | republic_clean `documents.parquet`: formula-type flags per doc_id (1705–1796); path in `local.toml` |
| `sample_resolutions` | explore | Offline sample JSONL with section/offsets; warm; formula STEP2 |
| `s4_opening_phrase_candidates` | explore | Trimmed S4 fixture; optional local.toml → full 271-candidate file |
| `formula_candidates` (name TBD in STEP3) | semi | FormulaSearch output via `save_semi_structured` |

## Outputs

| Artifact | Logical name | Path (via manifest) |
|----------|--------------|---------------------|
| Shared corpus | `resolutions_flat` | warm parquet via local.toml (do not copy) |
| Aanstelling gold | `delegates_resolutie_refs` | hot xlsx via local.toml |
| Relocated gold URNs | `aanstelling_gold_relocations` | `tests/fixtures/aanstelling_gold_relocations.jsonl` |
| Labelled aanstelling table | `aanstelling_labelled` | scratch `aanstelling_labelled.parquet` via `save_parquet` |
| TF-IDF holdout scores | `aanstelling_tfidf_holdout` | scratch `aanstelling_tfidf_holdout.parquet` via `save_parquet` |
| TF-IDF holdout metrics | `aanstelling_tfidf_metrics` | scratch `aanstelling_tfidf_metrics.jsonl` via `save_semi_structured` |
| Harvest POC remainder | `aanstelling_tfidf_harvest_poc` | scratch parquet via `save_parquet` |
| Harvest POC metrics | `aanstelling_tfidf_harvest_poc_metrics` | scratch JSONL via `save_semi_structured` |
| Harvest remainder | `aanstelling_tfidf_harvest` | scratch parquet via `save_parquet` |
| Human Excel export | `aanstelling_retrieval_xlsx` | scratch `aanstelling_retrieval.xlsx` |
| R1 selected list | `aanstelling_selected` | scratch parquet |
| R1 results writeup | — | [`docs/r1-aanstelling-results.md`](docs/r1-aanstelling-results.md) |
| Formula documents matrix | `formula_documents` | `republic_clean/.../documents.parquet` via `local.toml` |
| Sample corpus | `sample_resolutions` | `data/warm/datasets/corpus/sample_resolutions.jsonl` |
| S4 seed fixture | `s4_opening_phrase_candidates` | `data/warm/datasets/seeds/s4_opening_phrase_candidates.jsonl` |
| Formula candidates | (register in STEP3) | scratch-tier JSONL + provenance sidecars |
