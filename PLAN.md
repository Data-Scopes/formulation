# Project plan

Headlines only. Keep this file short. Full plans, milestones, and step guides live under [`plans/`](plans/) — see dighum_template wisdom [cost-sensitive-agent-workflow](../../wisdom/topics/cost-sensitive-agent-workflow.md).

One step per session. **STEPT1k done** — requeste opener accepted (A) on recall (0.898); FP (0.206) accepted as a known decision-type confound, not fixed (see proof NOTES). **STEPT1k2 done** — hand-read settled the open "is the gate reachable?" question: corrected FP 0.121 (CI 0.084–0.153), gate not rescued even crediting ES label gaps. **STEPT1l done** — requeste+ routing subtypes (referred 0.194 / granted_direct 0.709 / routing_unclear 0.050) separate structurally (length +93 words referred vs granted); stop, no new A. STEPT1e1 parked. Track L **parked**. F/M1 paused; R1 judged.

Cross-cutting: [`plans/formula-pipeline.md`](plans/formula-pipeline.md). Boundary evolution: [`plans/milestones/S1-formula-boundary-evolution.md`](plans/milestones/S1-formula-boundary-evolution.md), [`docs/formula-boundary-evolution.md`](docs/formula-boundary-evolution.md). Retrieval: [`plans/milestones/R1-aanstelling-retrieval.md`](plans/milestones/R1-aanstelling-retrieval.md), [`plans/milestones/L1-missive-receipt-retrieval.md`](plans/milestones/L1-missive-receipt-retrieval.md). Research notions: [`docs/formula-conceptual-overview.md`](docs/formula-conceptual-overview.md). Template **design questions** (north star, not a checklist): [`docs/template-design-questions.md`](docs/template-design-questions.md).

**Side plans / deferred tracks (not active):** [Presence lists 1630–1704](plans/presence-lists-1630-1704-side-plan.md) — raw session JSON harvest; [R2 pre-1705 aanstelling expansion](plans/milestones/R2-pre1705-aanstelling-expansion.md) — char/vector expansion using R1’s 615 pre-1705 keeps; [S1 17c requeste templates](plans/deferred/S1-17c-requeste-templates.md) — period map after 18c framing; [S1 neural span eval](plans/deferred/S1-neural-span-eval.md) — GysBERT vs GloBERTise (+ SW/DAG) comparison harness after STEPS4; **do not execute** until chosen.

## Goal

- **Track R (judged):** recover missing whole *aanstellingsresoluties* from `resolutions_flat` by similarity to gold `resolutie_refs`. Stopped after char n-gram TF-IDF + logistic regression; no residual neural pass. Selection: `aanstelling_selected`.
- **Track L (parked after STEPL2):** recover *missive/brief receipt with no substantive resolution*. Labelled + holdout metrics done; L3 harvest not opened.
- **Track S (judged):** evolve formula work to **exact template span boundaries** — TF-IDF windows → Smith-Waterman (single / slot-cloud) → DAG. See [`docs/formula-boundary-evolution.md`](docs/formula-boundary-evolution.md). STEPS0–4 + registry stub done (stop; no GysBERT).
- **Track F (paused):** `formula_detection.FormulaSearch` first slice (M1 STEP2+). Resume when S or L pauses; not the harness for S.
- **Track T (new, one step done):** provisional multi-class **resolution typology** by `proposition_type` — structural profile (evidence-label zones, length, `formula_documents` outcome-flag rates), composition kept separate from a floored characterisation sample. See [`plans/steps/STEPT0-typology-structural-profile.md`](plans/steps/STEPT0-typology-structural-profile.md).

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
| **T0** | whole resolution, by `proposition_type` | How many major resolution types are there, and how does each look structurally? (ES composition + floored sample → evidence zones, length, outcome flags) |

Shared machinery recurs: **character-level tolerance**, **manifest + provenance**, **candidate-then-structure** (TF-IDF or fuzzy recall, then alignment / position / criteria)—not one monolithic pipeline. Side plans stay off the active checklist but feed the same typology and segmentation story as formula work.

**Publications (REPUBLIC / formulas):** [docs/research-publications.md](docs/research-publications.md) — JOCCH preexisting structures + fuzzy boundaries; incremental modelling; attendance lists across centuries; formulaicity & regularisation (1576–1796).

## Milestones

| Milestone | Doc | Status |
|-----------|-----|--------|
| R1 Aanstelling retrieval | [R1-aanstelling-retrieval.md](plans/milestones/R1-aanstelling-retrieval.md) | done (stop after TF-IDF; selection frozen) |
| R2 Pre-1705 aanstelling expansion | [R2-pre1705-aanstelling-expansion.md](plans/milestones/R2-pre1705-aanstelling-expansion.md) | **deferred** (registered; not started) |
| L1 Missive-receipt retrieval | [L1-missive-receipt-retrieval.md](plans/milestones/L1-missive-receipt-retrieval.md) | STEPL2 done (closed gate); L3+ parked |
| S1 Formula boundary evolution | [S1-formula-boundary-evolution.md](plans/milestones/S1-formula-boundary-evolution.md) | done (stop after SW/DAG; no GysBERT; STEPS1b cut 0.40; registry stub registered) |
| M1 First runnable slice | [M1-first-slice.md](plans/milestones/M1-first-slice.md) | paused (STEP0–1 done; FormulaSearch STEP2+) |
| M2 Building-block criteria | [M2-building-blocks.md](plans/milestones/M2-building-blocks.md) | not started |
| M3 Composition + position | [M3-composition-and-position.md](plans/milestones/M3-composition-and-position.md) | not started |
| T0 Typology structural profile | [STEPT0-typology-structural-profile.md](plans/steps/STEPT0-typology-structural-profile.md) | done (1780 provisional) |
| T1 Unknown-first typology | [T1-unknown-first.md](plans/milestones/T1-unknown-first.md) | **active** (STEPT1k done: requeste opener A; STEPT1l done: routing subtypes separate, stop; STEPT1m opened: blueprint promotion not started) |

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
| L2 | [STEPL2-tfidf-baseline.md](plans/steps/STEPL2-tfidf-baseline.md) | Holdout recall / precision / F1 | done (closed gate; R 0.934 P 0.907 F1 0.920) |
| L3 | (STEPL3 — harvest) | Remainder high / grey / low | **parked** |
| L4 | (STEPL4 — residual or stop) | Written decision | **parked** |

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
| S5b | [STEPS5-wire-boundary-registry.md](plans/steps/STEPS5-wire-boundary-registry.md) | STEPS1–3 defaults via `resolve_framing_template` | done |
| S6 | [STEPS6-institution-patterns.md](plans/steps/STEPS6-institution-patterns.md) | Manifest + fixture + loader for period-keyed patterns (no full ORG harvest) | done (bookkeeping) |
| S6b | (prove wire-up — no step guide) | Prove script uses `institution_patterns`; templates keep targets only | done |
| S6c | [STEPS6c-org-pattern-harvest.md](plans/steps/STEPS6c-org-pattern-harvest.md) | Stream-harvest ORG annotations → provenanced `institution_patterns` | done (script; user runs full harvest) |
| S6d | (prove A/B — no step guide) | Seeds vs harvest on locked sample; compare metrics in proof dir | done (harvest +1 FP; tighten min-n next) |

### Track F — formulas (M1), paused

| Step | Guide | Done when | Status |
|------|-------|-----------|--------|
| 0 | [STEP0-local-data-wiring.md](plans/steps/STEP0-local-data-wiring.md) | In-repo tier roots; `data_io.check` runs | done |
| 1 | [STEP1-formula-detection-adapters.md](plans/steps/STEP1-formula-detection-adapters.md) | `formula_detection` dep + `formulation.adapters` token streams | done |
| 2 | [STEP2-sample-corpus-and-seeds.md](plans/steps/STEP2-sample-corpus-and-seeds.md) | `sample_resolutions` + `s4_opening_phrase_candidates` registered | not started |
| 3 | [STEP3-formula-search-script.md](plans/steps/STEP3-formula-search-script.md) | `scripts/run_formula_search.py` writes provenanced candidates | not started |
| 4 | [STEP4-tests-and-demo.md](plans/steps/STEP4-tests-and-demo.md) | pytest + demo notebook + README how-to-run | not started |

Survey + dighum shell: done (see pipeline plan). Do not lift the `republic_clean` notebook tree or talk to live Elasticsearch.

### Track T — typology (T0), new

| Step | Guide | Done when | Status |
|------|-------|-----------|--------|
| T0 | [STEPT0-typology-structural-profile.md](plans/steps/STEPT0-typology-structural-profile.md) | `typology_structural_profile` registered + written; composition and floored sample kept distinct in output; `data_io.check` clean | done (1780 provisional profile) |
| T1a | [STEPT1-lift-segmentation-and-formula-types.md](plans/steps/STEPT1-lift-segmentation-and-formula-types.md) | Measured appointment formula-type metrics (recall pre/post-1731, baselines, FP, popularity) | done (PASS; welkom 0-accept caveat) |
| T1a-fix | (no step guide — follow NOTES) | Welkom cloud learns variants: cue windows + empirical canonic; `n_hits_accepted` ≫ 0; re-measure pre-1731 | **done** (2251/2313; gates hold; cut=6.0 side-effect) |
| T1-period | [STEPT1-period-bins.md](plans/steps/STEPT1-period-bins.md) | Family × 25y cross-bin matrix + recalibrate signals | done (script; user runs eval) |
| T1b | [STEPT1b-presence-scoring.md](plans/steps/STEPT1b-presence-scoring.md) | Year-slice presence + popularity weights + bag summary | done (1780; bags=fragments → T1c) |
| T1b-refresh | [STEPT1b-presence-scoring.md](plans/steps/STEPT1b-presence-scoring.md) | Re-score 1780 with accepted `advies_geleesen` in bags | **done** (PASS; advies 2.7%; bags still fragments) |
| T1c | [STEPT1c-position-zones.md](plans/steps/STEPT1c-position-zones.md) | DAG mid-span → opening/body/close + zone-tagged bags | done (1780; zone separates; bags still fragments) |
| T1c-refresh | [STEPT1c-position-zones.md](plans/steps/STEPT1c-position-zones.md) | Re-score 1780 zones with accepted `advies_geleesen` | **done** (PASS; advies mostly opening, soft; still fragments) |
| T1d order | [STEPT1d-order-composition.md](plans/steps/STEPT1d-order-composition.md) | Ordered sequences by start_idx (soft constraint) | done / **parked** (1780; not the composition definition) |
| T1d graph | [STEPT1d-composition-graph.md](plans/steps/STEPT1d-composition-graph.md) | Type co-presence graph + 1780 smoke; period matrix only if needed | **done** (PASS; star; skip period bins) |
| T1e0 | [STEPT1e0-ontfangen-inventory.md](plans/steps/STEPT1e0-ontfangen-inventory.md) | Inventory ontfangen+ from existing metrics + known-set overlaps; typology gaps | **done** (call → STEPT1e probe) |
| T1e | [STEPT1e-partition-probe.md](plans/steps/STEPT1e-partition-probe.md) | ES type mix + flags on ontfangen±; residual not-L1; typology NOTES | **done** (PASS; discourse-stage call → e1) |
| T1-map | [STEPT1-typology-formula-map.md](plans/steps/STEPT1-typology-formula-map.md) | Layers + schemes×STEPT0×measured crosswalk + inventory; typology-before-classify call | **done** (docs; e1 parked) |
| T1e1 | [STEPT1e1-residual-flag-sieve.md](plans/steps/STEPT1e1-residual-flag-sieve.md) | Bucket ontfangen+ by discourse flags (null / decision / defer / other) | **parked** (until map names a kind-gap) |
| T1a2 | [STEPT1a2-advies-formula-type.md](plans/steps/STEPT1a2-advies-formula-type.md) | Measured advies formula-type vs ES gold (recall / wording / FP / cloud accepts) | **done** (PASS; recall 0.762 / FP 0.034) |
| T1f | [STEPT1f-missive-subtype-characterisation.md](plans/steps/STEPT1f-missive-subtype-characterisation.md) | Missive subtypes under ontfangen+: info vs decisionful (length + flags) | **done** (PASS w/ circular L1 caveat) |
| T1g | [STEPT1g-residual-structure-probe.md](plans/steps/STEPT1g-residual-structure-probe.md) | Decisionful residual structure: pockets + catalogue + sample shapes | **done** (PASS; sparse ≠ filler) |
| T1h | [STEPT1h-unknown-likeliness.md](plans/steps/STEPT1h-unknown-likeliness.md) | Unknown-likeliness under accepted cover; 1780 scores + high-unknown sample | **done** (PASS; high-unk 0.72) |
| T1i | [STEPT1i-composition-unknown.md](plans/steps/STEPT1i-composition-unknown.md) | Proto-blueprints / derivatives / undecided + fingerprints | **done** (PASS; empty=1329; fp one mass) |
| T1j | [STEPT1j-empty-band-characterisation.md](plans/steps/STEPT1j-empty-band-characterisation.md) | Empty-band type/length/flags + fp_cut sweep + sample | **done** (PASS; rekest-headed; fp@0.45 sample-only) |
| T1j2 | [STEPT1j2-empty-band-retrieval-probe.md](plans/steps/STEPT1j2-empty-band-retrieval-probe.md) | Empty × frozen R1/L1 P-bands × ES type | **done** (PASS; both ~low; L1 soft on empty missive grey) |
| T1k | [STEPT1k-requeste-formula-type.md](plans/steps/STEPT1k-requeste-formula-type.md) | Measured requeste opener vs ES rekest (recall / wording / FP / cloud) | **done** (A accepted; recall 0.898 PASS, FP 0.206 accepted not fixed — decision-type confound) |
| T1k2 | (proof addendum, no separate step guide) | Hand-read FP adjudication xlsx: is the 0.05 FP gate reachable against ES gold at all? | **done** (not_rescued; corrected FP 0.121, CI 0.084–0.153) |
| T1l | [STEPT1l-requeste-subtype-characterisation.md](plans/steps/STEPT1l-requeste-subtype-characterisation.md) | Subtypes under requeste+ (mirror STEPT1f) | **done** (PASS; referred 0.194 / granted_direct 0.709 / routing_unclear 0.050; length +93 words referred vs granted) |
| T1m | [STEPT1m-blueprint-promotion.md](plans/steps/STEPT1m-blueprint-promotion.md) | Requeste joins accepted core; 3-way composition-unknown re-run; promote if low-noise | **not started** |

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
| `missive_receipt_tfidf_holdout` | frozen | STEPL2 20% holdout scores |
| `missive_receipt_tfidf_metrics` | semi | STEPL2 recall / precision / F1 + settings |
| `formula_templates` | explore | Multi-template registry stub (framing / doc_flag / appointment / residual) |
| `formula_type_composition_graph_metrics` | semi | STEPT1d: co-presence graph + shape (1780 or period matrix) |
| `formula_type_composition_graph_scores` | explore | STEPT1d: per-id bags ordered by mid_norm |
| `ontfangen_partition_metrics` | semi | STEPT1e: ontfangen± ES mix + flags + known sets |
| `ontfangen_partition_scores` | explore | STEPT1e: per-id partition tags + ES type |
| `missive_subtype_metrics` | semi | STEPT1f: missive subtype characterisation (info vs decisionful) |
| `missive_subtype_scores` | explore | STEPT1f: per-id subtype + n_words |
| `residual_structure_metrics` | semi | STEPT1g: residual pockets + combo catalogue + bags |
| `residual_structure_scores` | explore | STEPT1g: per-id residual + pockets |
| `residual_structure_sample` | explore | STEPT1g: stratified text sample for NOTES |
| `resolution_unknown_metrics` | semi | STEPT1h: unknown-likeliness band + cover hits |
| `resolution_unknown_scores` | explore | STEPT1h: per-id cover + unknown_score |
| `resolution_unknown_sample` | explore | STEPT1h: high-unknown text sample (truncated) |
| `composition_unknown_metrics` | semi | STEPT1i: proto-blueprints + motif fracs + fingerprint summary |
| `composition_unknown_scores` | explore | STEPT1i: per-id bag/core/motif (+ fp fields) |
| `composition_unknown_sample` | explore | STEPT1i: undecided stratified sample (truncated) |
| `empty_band_metrics` | semi | STEPT1j: empty type/length/flags + fp_cut sweep |
| `empty_band_scores` | explore | STEPT1j: per-id empty characterisation (+ fp cluster) |
| `empty_band_sample` | explore | STEPT1j: stratified empty text sample (truncated) |
| `empty_band_retrieval_metrics` | semi | STEPT1j2: empty R1/L1 P-bands × ES type |
| `empty_band_retrieval_scores` | explore | STEPT1j2: per-id empty R1/L1 proba+bucket |
| `rekest_es_gold` | explore | STEPT1k: ES rekest ids + flat text |
| `formula_type_requeste_metrics` | semi | STEPT1k: requeste opener recall / FP / cloud |
| `formula_type_requeste_scores` | explore | STEPT1k: per-id align scores |
| `requeste_fp_review_xlsx` | explore | STEPT1k2: hand-read workbook (30 FP + 6 calibration) |
| `requeste_fp_review_meta` | semi | STEPT1k2: build stats for the review workbook |
| `requeste_fp_verdicts` | semi | STEPT1k2: ingested verdicts + corrected-FP-rate summary |
| `requeste_subtype_metrics` | semi | STEPT1l: requeste+ routing subtype characterisation |
| `requeste_subtype_scores` | semi | STEPT1l: per-id requeste+ routing subtype + flags |
| `org_annotations` | frozen | republic_ner ORG NER mentions (`tag_text`+`inv`); path in local.toml → 2TB |
| `org_entities` | frozen | Canonical ORG ids/names; path in local.toml → republic_ner data.bak |
| `inventory_metadata` | frozen | inventory_num → year_start/year_end; local.toml → republic_ner data.bak |
| `institution_patterns_seeds` | explore | Hand fixture seeds (CI + optional merge into harvest) |
| `institution_patterns` | explore | Period-/inventory-keyed surfaces; scratch harvest from ORG annotations |
| `institution_patterns_metrics` | semi | Harvest summary counts |
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
| Missive labelled table | `missive_receipt_labelled` | scratch parquet |
| Missive TF-IDF holdout | `missive_receipt_tfidf_holdout` | scratch parquet |
| Missive TF-IDF metrics | `missive_receipt_tfidf_metrics` | scratch JSONL |
| Formula template registry | `formula_templates` | `tests/fixtures/formula_templates.jsonl` |
| Institution pattern seeds | `institution_patterns_seeds` | `tests/fixtures/institution_patterns.jsonl` |
| Institution patterns (harvest) | `institution_patterns` | scratch JSONL via `save_semi_structured` |
| Institution harvest metrics | `institution_patterns_metrics` | scratch JSONL via `save_semi_structured` |
| Boundary span fixtures | `formula_boundary_cases` | `tests/fixtures/formula_boundary_cases.jsonl` |
| Boundary benchmark metrics | `formula_boundary_benchmark_metrics` | scratch JSONL via `save_semi_structured` |
| TF-IDF candidate windows | `formula_tfidf_windows` | scratch JSONL via `save_semi_structured` |
| TF-IDF window metrics | `formula_tfidf_window_metrics` | scratch JSONL via `save_semi_structured` |
| Slot-cloud (18c opening) | `formula_slot_cloud` | scratch JSONL via `save_semi_structured` |
| Slot-cloud metrics | `formula_slot_cloud_metrics` | scratch JSONL via `save_semi_structured` |
| Boundary spans (SW/DAG) | `formula_boundary_spans` | scratch JSONL via `save_semi_structured` |
| Boundary span metrics | `formula_boundary_span_metrics` | scratch JSONL via `save_semi_structured` |
| Advies ES gold | `advies_es_gold` | scratch JSONL (`--refresh-gold`) |
| Advies type metrics / scores | `formula_type_advies_metrics` / `_scores` | scratch JSONL |
| Rekest ES gold | `rekest_es_gold` | scratch JSONL (`--refresh-gold`) |
| Requeste type metrics / scores | `formula_type_requeste_metrics` / `_scores` | scratch JSONL |
| Formula documents matrix | `formula_documents` | `republic_clean/.../documents.parquet` via `local.toml` |
| Sample corpus | `sample_resolutions` | `data/warm/datasets/corpus/sample_resolutions.jsonl` |
| S4 seed fixture | `s4_opening_phrase_candidates` | `data/warm/datasets/seeds/s4_opening_phrase_candidates.jsonl` |
| Formula candidates | (register in STEP3) | scratch-tier JSONL + provenance sidecars |
