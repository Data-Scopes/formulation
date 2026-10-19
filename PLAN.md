# Project plan

Headlines only. Keep this file short. Full plans, milestones, and step guides live under [`plans/`](plans/) — see dighum_template wisdom [cost-sensitive-agent-workflow](../../wisdom/topics/cost-sensitive-agent-workflow.md).

One step per session. **Registry stub done** (`formula_templates` + `formulation.formula_templates`). Prove-first: [docs/proofs/multi-template-registry/](docs/proofs/multi-template-registry/). STEPS1b cut 0.40 frozen on `opening_requeste_18c`. Next: Track L STEPL2, or wire boundary code to load tokens/threshold from registry, or period-keyed `institution_patterns` (republic_ner ORG). Proposer slots / 17c deferred. F/M1 paused; R1 judged.

Cross-cutting: [`plans/formula-pipeline.md`](plans/formula-pipeline.md). Boundary evolution: [`plans/milestones/S1-formula-boundary-evolution.md`](plans/milestones/S1-formula-boundary-evolution.md), [`docs/formula-boundary-evolution.md`](docs/formula-boundary-evolution.md). Retrieval: [`plans/milestones/R1-aanstelling-retrieval.md`](plans/milestones/R1-aanstelling-retrieval.md), [`plans/milestones/L1-missive-receipt-retrieval.md`](plans/milestones/L1-missive-receipt-retrieval.md). Research notions: [`docs/formula-conceptual-overview.md`](docs/formula-conceptual-overview.md).

**Side plans / deferred tracks (not active):** [Presence lists 1630–1704](plans/presence-lists-1630-1704-side-plan.md) — raw session JSON harvest; [R2 pre-1705 aanstelling expansion](plans/milestones/R2-pre1705-aanstelling-expansion.md) — char/vector expansion using R1’s 615 pre-1705 keeps; [S1 17c requeste templates](plans/deferred/S1-17c-requeste-templates.md) — period map after 18c framing; [S1 neural span eval](plans/deferred/S1-neural-span-eval.md) — GysBERT vs GloBERTise (+ SW/DAG) comparison harness after STEPS4; **do not execute** until chosen.

## Goal

- **Track R (judged):** recover missing whole *aanstellingsresoluties* from `resolutions_flat` by similarity to gold `resolutie_refs`. Stopped after char n-gram TF-IDF + logistic regression; no residual neural pass. Selection: `aanstelling_selected`.
- **Track L:** recover *missive/brief receipt with no substantive resolution* (*geen resolutie gevallen / vereischende*). Mirror R1 machinery; different type filters.
- **Track S (judged):** evolve formula work to **exact template span boundaries** — TF-IDF windows → Smith-Waterman (single / slot-cloud) → DAG. See [`docs/formula-boundary-evolution.md`](docs/formula-boundary-evolution.md). STEPS0–4 + registry stub done (stop; no GysBERT).
- **Track F (paused):** `formula_detection.FormulaSearch` first slice (M1 STEP2+). Resume when S or L pauses; not the harness for S.

## One research thread (tracks are not sidesteps)

Same object: **templated administrative language** in States-General material (fixed skeletons, variable slots, spelling drift, position matters). Different **units and outputs**:

| Work | Unit | Question |
|------|------|----------|
| **R1** | whole resolution | Which sittings match the *aanstelling* document type? (char TF-IDF harvest) |
| **R2** (deferred) | whole resolution, `year < 1705` | Expand pre-18c recall using **615 reviewed exemplars** + char k-NN/refit; optional dense rerank; not new gold |
| **L1** | whole resolution | Which sittings are *missive/brief* receipts with *geen resolutie*? |
| **S1** | token spans | Where does boilerplate end and the variable slot begin? (TF-IDF → SW → DAG) |
| **M1–M3** | spans / building blocks | FormulaSearch / criteria path (paused while S runs); same typology story |
| **Presence side plan** | session opening / presentielijst | Where is the presidium block in raw session text, across 1630–1704? (bracket: 1626–30 gold + 18c phrase seeds) |

Shared machinery recurs: **character-level tolerance**, **manifest + provenance**, **candidate-then-structure** (TF-IDF or fuzzy recall, then alignment / position / criteria)—not one monolithic pipeline. Side plans stay off the active checklist but feed the same typology and segmentation story as formula work.

**Publications (REPUBLIC / formulas):** [docs/research-publications.md](docs/research-publications.md) — JOCCH preexisting structures + fuzzy boundaries; incremental modelling; attendance lists across centuries; formulaicity & regularisation (1576–1796).

## Milestones

| Milestone | Doc | Status |
|-----------|-----|--------|
| R1 Aanstelling retrieval | [R1-aanstelling-retrieval.md](plans/milestones/R1-aanstelling-retrieval.md) | done (stop after TF-IDF; selection frozen) |
| R2 Pre-1705 aanstelling expansion | [R2-pre1705-aanstelling-expansion.md](plans/milestones/R2-pre1705-aanstelling-expansion.md) | **deferred** (registered; not started) |
| L1 Missive-receipt retrieval | [L1-missive-receipt-retrieval.md](plans/milestones/L1-missive-receipt-retrieval.md) | in progress (STEPL1 done 1780; next STEPL2) |
| S1 Formula boundary evolution | [S1-formula-boundary-evolution.md](plans/milestones/S1-formula-boundary-evolution.md) | done (stop after SW/DAG; no GysBERT; STEPS1b cut 0.40; registry stub registered) |
| M1 First runnable slice | [M1-first-slice.md](plans/milestones/M1-first-slice.md) | paused (STEP0–1 done; FormulaSearch STEP2+) |
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

### Track L — missive receipt (L1)

| Step | Guide | Done when | Status |
|------|-------|-----------|--------|
| L0 | [STEPL0-define-missive-receipt-type.md](plans/steps/STEPL0-define-missive-receipt-type.md) | Type + seeds + cue inventory counts | done |
| L1 | [STEPL1-labelled-table.md](plans/steps/STEPL1-labelled-table.md) | Provenanced positives + overig; exclude aanstelling ids | done (1780: 680+2122) |
| L2 | (STEPL2 — TF-IDF baseline) | Holdout recall / precision / F1 | not started |
| L3 | (STEPL3 — harvest) | Remainder high / grey / low | not started |
| L4 | (STEPL4 — residual or stop) | Written decision | not started |

### Track S — formula boundary evolution (S1), judged

| Step | Guide | Done when | Status |
|------|-------|-----------|--------|
| S0 | [STEPS0-boundary-scaffold.md](plans/steps/STEPS0-boundary-scaffold.md) | Fixture + SW/DAG benchmark; provenanced metrics | done |
| S1 | [STEPS1-tfidf-window-framing.md](plans/steps/STEPS1-tfidf-window-framing.md) | Candidate windows; threshold notes | done |
| S1b | [STEPS1-calibrate-threshold.md](plans/steps/STEPS1-calibrate-threshold.md) | Frozen cosine cut (+ optional peak-dedup) | done (0.40, 18c only) |
| S2 | [STEPS2-slot-cloud-bootstrap.md](plans/steps/STEPS2-slot-cloud-bootstrap.md) | Slot-clouds from hits; optional period filter | done |
| S3 | [STEPS3-dag-spans.md](plans/steps/STEPS3-dag-spans.md) | Provenanced span output on real data | done |
| S4 | [STEPS4-residual-or-stop.md](plans/steps/STEPS4-residual-or-stop.md) | Written GysBERT yes/no | done (stop) |
| S5 | (registry stub — no step guide) | `formula_templates` in manifest + loader; schema smoke | done |

### Track F — formulas (M1), paused

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
| `missive_receipt_labelled` | frozen | Cue both-hits + seeds + 10× overig; STEPL1 |
| `formula_templates` | explore | Multi-template registry stub (framing / doc_flag / appointment / residual) |
| `formula_boundary_cases` | explore | Tiny span-gold OCR windows for S1 STEPS0 benchmark |
| `formula_boundary_benchmark_metrics` | semi | IoU / boundary delta / latency per method (STEPS0) |
| `formula_tfidf_windows` | explore | STEPS1 candidate windows (cosine vs opening template) |
| `formula_tfidf_window_metrics` | semi | STEPS1 threshold notes + score distribution |
| `formula_slot_cloud` | semi | STEPS2 frequency-weighted slot-cloud (`opening_requeste_18c`) |
| `formula_slot_cloud_metrics` | semi | STEPS2 bootstrap notes (accept / optional-skip hypotheses) |
| `formula_boundary_spans` | semi | STEPS3 SW/DAG token spans on STEPS1 windows |
| `formula_boundary_span_metrics` | semi | STEPS3 latency / score / cloud↔DAG agreement notes |
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
| Formula template registry | `formula_templates` | `tests/fixtures/formula_templates.jsonl` |
| Boundary span fixtures | `formula_boundary_cases` | `tests/fixtures/formula_boundary_cases.jsonl` |
| Boundary benchmark metrics | `formula_boundary_benchmark_metrics` | scratch JSONL via `save_semi_structured` |
| TF-IDF candidate windows | `formula_tfidf_windows` | scratch JSONL via `save_semi_structured` |
| TF-IDF window metrics | `formula_tfidf_window_metrics` | scratch JSONL via `save_semi_structured` |
| Slot-cloud (18c opening) | `formula_slot_cloud` | scratch JSONL via `save_semi_structured` |
| Slot-cloud metrics | `formula_slot_cloud_metrics` | scratch JSONL via `save_semi_structured` |
| Boundary spans (SW/DAG) | `formula_boundary_spans` | scratch JSONL via `save_semi_structured` |
| Boundary span metrics | `formula_boundary_span_metrics` | scratch JSONL via `save_semi_structured` |
| Formula documents matrix | `formula_documents` | `republic_clean/.../documents.parquet` via `local.toml` |
| Sample corpus | `sample_resolutions` | `data/warm/datasets/corpus/sample_resolutions.jsonl` |
| S4 seed fixture | `s4_opening_phrase_candidates` | `data/warm/datasets/seeds/s4_opening_phrase_candidates.jsonl` |
| Formula candidates | (register in STEP3) | scratch-tier JSONL + provenance sidecars |
