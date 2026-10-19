# Decision Log

Record durable methodological and architectural decisions here. Keep entries short enough to scan.

## Template

### YYYY-MM-DD: Decision title

- **Context:** What changed or what result forced a choice?
- **Decision:** What did we decide?
- **Reason:** Why is this the right tradeoff now?

## 2026-09-21: Two tracks; retrieval first

- **Context:** Formula M1 (STEP0–1) is wired, but the next useful inventory work is recovering missing whole aanstellingsresoluties, not formula spans.
- **Decision:** Split **Track R** (`STEPR0`–`STEPR4`, milestone R1) from **Track F** (`STEP0`–`STEP4`, M1 paused). Active focus is R1 until judged. Do not mix retrieval into formula STEP2.
- **Reason:** Same *why* (resolutions are formulematig), different *what they return*. One-step-per-session stays unambiguous if the prefix is `STEPR*`.

## 2026-09-21: Gold is `resolutie_refs` URNs (rc5), not a text column

- **Context:** The unique-table `delegates_1705_1795_extended` release fills `resolutie_refs` for only ~4 delegates / 6 URNs. There is no `resolutions` text field.
- **Decision:** Register `delegates_resolutie_refs` pointing at `delegates_1705_1795_v1.0-rc5.xlsx` (~196/1051 rows, ~222 URNs). Bodies come from joining those URNs onto `resolutions_flat` in STEPR1. Do not train on four unique-table positives.
- **Reason:** The spreadsheet is a label list. Inventing text from it would skip the corpus join and hide coverage failures.

## 2026-09-21: `resolutions_flat` is one row per resolution; 18c is present

- **Context:** The shared parquet is described as “paragraphs”. Track R needs whole resolutions. Gold URNs are 1685–1791; sibling NER work often slices 1626–1630.
- **Decision:** Treat each parquet row as one resolution (`type=resolution`, unique `id` `session-{inv}-num-{n}-resolution-{k}`, 692,156 rows). Do **not** collapse paragraphs before TF-IDF. Score `resolutions_text`: `paragraph_texts` is the same wording as a JSON list (`["…"]`), never exact-equal (median +4 chars). 18c coverage is adequate (322,125 rows in 1705–1795). Naive constructed ids with matching dates are gold (199/217 unique URNs). The other **18 stay gold**: they are the same aanstellingen under a drifted session `num`. Relocate by same inventory + URN date + resolution index (17 unique hits → `aanstelling_gold_relocations`). The remaining 1685-09-23 URN has no parquet row that day; keep naive `session-3312-num-82-resolution-2` (parquet date 1685-09-25). Do not invent text. Strip trailing `;` and parse URNs out of goetgevonden.nl URLs.
- **Reason:** Session numbering in `resolutions_flat` has drifted from REPUBLIC URNs (already seen in `republic_ner_matching`). Dropping the 18 would throw away known positives.

## 2026-09-21: Labelled table is one row per resolution; 10× overig

- **Context:** Several delegates can share one URN; STEPR2 needs a stratified 80/20 on labelled rows. Scoring text is whole-resolution `resolutions_text`.
- **Decision:** Freeze `aanstelling_labelled` as one row per `resolutions_flat` id. Positives keep aggregated `gold_urns` / `delegate_ids` / `delegate_fullnames`. Missing `delegate_id` falls back to `cons_id_str`. Overig is a reproducible 10× sample (`random_state=42`) from the gold year window, excluding gold ids. Missing recovered ids or naive date mismatches raise; do not invent text.
- **Reason:** Duplicate resolution texts would leak across the STEPR2 split. 10× keeps the table small enough for char n-gram TF-IDF without scoring the full 18c remainder (that is STEPR3).

## 2026-09-21: In-repo warm stays; Track R paths in local.toml

- **Context:** `resolutions_flat` lives on the 2TB warm drive used by `republic_ner_matching`. Formulation’s committed warm root is in-repo `data/warm` (formula samples).
- **Decision:** Keep `[tiers.warm] = data/warm`. Override only the `resolutions_flat` and `delegates_resolutie_refs` **dataset paths** in gitignored `data_manifest.local.toml` (absolute paths). Do not remount the whole warm tier onto `/Volumes`.
- **Reason:** Remounting warm would hide in-repo formula datasets. `data_io.resolve` already returns absolute dataset paths as-is.

## 2026-09-21: TF-IDF+LR hyperparameters frozen; no test-split tuning

- **Context:** STEPR2 needs a cheap whole-resolution baseline. Holdout on `aanstelling_labelled` (213 aanstelling / 2130 overig; 80/20 stratified, `random_state=42`) is recall **0.860** / precision **0.974** / F1 **0.914** (43 test positives; 6 FN, 1 FP). Writeup ballpark was recall ~0.97 / precision ~0.95.
- **Decision:** Keep `TfidfVectorizer(analyzer="char_wb", ngram_range=(3, 5))` + `LogisticRegression(solver="liblinear", max_iter=1000, random_state=42)`. Do **not** add `class_weight`, n-gram search, or a threshold sweep after seeing holdout numbers. STEPR3 harvests with this architecture refit on all labelled rows. STEPR4 judges a residual pass: the six FNs are mostly missive / commissie / requeste openings, not the typical *is goedgevonden … committeren* wording.
- **Reason:** Headline cost is missed aanstellingen, but retuning on the test split would invalidate the metric. A methods bake-off is out of scope unless STEPR4 chooses one residual neural pass on TF-IDF negatives.

## 2026-09-21: STEPR3 harvest cuts kept; completeness is p>0.5

- **Context:** Full remainder 691943: high/grey/low 1012/6008/684923. Holdout gold median p=0.81, so the 0.85 ingest cut demoted 24/43 gold TPs into grey. Remainder bands: 1012 >0.85, 1871 in (0.5,0.85], 4137 in (0.15,0.5], 684923 <=0.15. Almost all high (1010/1012) and most p>0.5 (2711/2883) are in 1705-1795.
- **Decision:** Keep the 0.85/0.15 bucket labels on aanstelling_tfidf_harvest. Do not rescore. Completeness list is p>0.5 (2883). Post-harvest review is (0.15,0.5] (4137), not all grey. STEPR4 residual, if any, runs only on TF-IDF negatives (p<=0.5 / odd wording), not on (0.5,0.85]. Do not treat 17c HTR as done from this 18c-trained model (160 p>0.5 before 1705).
- **Reason:** Grey mixed a threshold artifact with genuine uncertainty. Stored proba is enough to re-bucket. Headline goal is complete the historical list, so ingest-quality high is not the harvest.

## 2026-09-21: R1 stop after TF-IDF

- **Context:** Holdout@0.5 is recall 0.860 (37/43; 6 FN) / precision 0.974 / F1 0.914, below writeup ~0.97 recall. Remainder 691943: p>0.5 completeness 2883, (0.15,0.5] review 4137, p<=0.15 low 684923. Of 6 FNs, 5 sit in review; 1 is 1690 HTR at p=0.023. high_or_grey recall 0.977 (42/43). Goal is complete the historical list (Doel A).
- **Decision:** Stop after TF-IDF. No residual GysBERT or embedding pass on the 689060 TF-IDF negatives (p<=0.5). Ingest p>0.5 (2883; 2711 in 1705-1795). Human review is (0.15,0.5] (4137; 3353 in 1705-1795). Do not treat 17c HTR as done.
- **Reason:** Odd-wording FNs that residual would target are already in the review band except one 17c miss, which an 18c-trained neural model must not declare done. high_or_grey recall 0.977 meets the writeup recall ballpark once review is included. Scoring 685k lows would be a methods bake-off (Doel B), not completing the list.

## 2026-09-23: Sibling appointments out of R1, kept for later

- **Context:** Harvest review surfaces true appointments that are not *aanstelling ter Vergadering* (e.g. *commissie* into the Generaliteits Rekenkamer with oath + introduction; Zeeland multi-credential batches; Gelre *om te resideren* templates). Same missive/commissie envelope, different office or formula.
- **Decision:** Track R completeness = vergadering admissions only. In Excel `review`, use `keep` / `drop` / **`other_appointment`** (optional note: `rekenkamer`, `zeeland_multi_cred`, …). Do **not** delete `other_appointment` rows from the harvest Excel or harvest parquet. Export id+label to a sidecar when review stabilizes; later track may promote them.
- **Reason:** Throwing them away would force a second full harvest. Collapsing them into R1 gold would mix document types and hurt the vergadering list.

## 2026-09-23: R1 selection finalized with review rules + names

- **Context:** Human review covered ingest_suspect (33/33) and most review_suspect; cue rules are stable (`sessie_genomen`±`aengenaem`→keep; bare `verwelkom`→drop).
- **Decision:** Freeze `aanstelling_selected` (gold + ingest_cued + suspect keeps + review shape-ok + review_suspect keeps) and `aanstelling_review_labels`. Bulk-fill remaining sessie±aengenaem / bare verwelkom blanks by rule. Refresh rough names (17c *gecommitteert* / *opden heer* / *verwillecompt*). Leave non-rule blanks unlabeled.
- **Reason:** Completes Doel A list without re-reading the whole grey band; names support delegate matching later.

## 2026-09-24: Track R2 — pre-1705 aanstelling expansion (deferred)

- **Context:** R1 `aanstelling_selected` includes **615** pre-1705 keeps (mostly review-band, **13** overlap hand gold). Early-period resolution separation is **≤ ~70% at best**; 18c-trained scores are weak on 17c, but reviewed keeps are useful exemplars.
- **Decision:** Register **Track R2** in [`plans/milestones/R2-pre1705-aanstelling-expansion.md`](../plans/milestones/R2-pre1705-aanstelling-expansion.md). Planned method: char `char_wb` k-NN/refit on pre-1705 remainder using 615 as **soft positives / seeds**; cue + Levenshtein rerank; optional dense rerank on top-K only. **Do not execute** until explicitly chosen (active: L1, F STEP2).
- **Reason:** Separates period-specific expansion from judged R1; avoids treating 615 as gold or completeness proof; keeps vector experiments scoped without blocking current tracks.

## 2026-09-23: Track L — missive receipt (parallel to R1)

- **Context:** Need a second whole-resolution type: *Ontfangen een missive/brief …* ending in *geen resolutie is gevallen* / *vereischende* (advertentie), distinct from aanstellingen that share the opening.
- **Decision:** Start **Track L / L1** mirroring R1 (char TF-IDF + LR on `resolutions_flat`). Positives require receipt + null-decision close, not opening alone. Exclude `aanstelling_selected` ids from L positives. Seeds in `missive_receipt_seeds`. Next step STEPL0.
- **Reason:** Opening-only harvest would drown in aanstellingen and referrals; R1 machinery transfers; type filter is the new work.

## 2026-10-18: Track S — formula boundary evolution (after TF-IDF)

- **Context:** R1 char `char_wb` TF-IDF works well for whole-resolution type recovery. Formula research needs exact boilerplate boundaries and variable slots; `FormulaSearch` (Track F / M1) is not the right first harness for that cut.
- **Decision:** Register **Track S / S1** — phased TF-IDF windows → Smith-Waterman (single / slot-cloud) → DAG. GysBERT only as optional STEPS4 residual. Pause M1 FormulaSearch STEP2+ while S runs. Do not mix S scripts with L1/R1 harvest.
- **Reason:** Same research object (templated language); evolution from coarse localisation to span structure. Keeps one-step-per-session clear via `STEPS*` prefix.

## 2026-10-18: STEPS1 — TF-IDF window framing knobs

- **Context:** PDF / design thread suggested char_wb 3–5 + `sublinear_tf`, threshold ~0.35–0.40, and optional stopwords / binary cosine / `strip_accents`.
- **Decision:** STEPS1 uses `char_wb` 3–5 + `sublinear_tf=True` + `min_df=2`, cosine to the openings template from `formula_boundary_cases`, score windows of ~16 tokens (stride 2), separate align-pad for later SW. Fit IDF on the window corpus of a `resolutions_flat` year slice (default 1780). Default cut **0.35** is recorded as a **hypothesis** with score percentiles — not frozen. No stopword list, binary/BM25, `strip_accents`, or logistic regression in this step.
- **Reason:** One sharpening change on the proven R1 vectorizer family; short windows match opening formulas; Track F sample corpus is not a gate; histogram before freezing the cut.

## 2026-10-18: STEPS1 — 18c template first (17c later)

- **Context:** Fixture template *Gepraesenteert ende gelesen sijnde de Requeste* barely appears in year slices; ≥0.35 hits on 1780 were mid-doc *gepraesenteert* noise. Real 18c openings are *IS ter Vergaderinge gele(e)sen de Requeste*. 17c also has *Op de Requeste* / *Is gelesen de requeste*, but that is a later expansion.
- **Decision:** STEPS1 default query = `opening_requeste_18c` (`IS ter Vergaderinge geleesen de Requeste`). Scope framing POCs to **18th century** first. Defer 17c period templates / cloud. Keep STEPS0 `formula_boundary_cases` unchanged for SW/DAG gold.
- **Reason:** One formula family + one period; avoid mixing diachronic variants into the first threshold pass.

## 2026-10-18: STEPS1 — calibrate after framework

- **Context:** With the 18c template, 1780 framing already yields real openings at high scores, but 0.35 still pulls provincial *ter Vergaderinge … leesen* neighbours; peak dedup / cut tuning is tempting.
- **Decision:** **Do not calibrate** the cosine threshold (or related ranking knobs) until the Track S **framework** is in place: STEPS2 slot-cloud bootstrap → STEPS3 provenanced spans on real windows (SW/DAG on STEPS1 candidates). Keep 0.35 labelled hypothesis. 17c templates stay deferred.
- **Reason:** Thresholds without cloud + span output optimize the wrong stage; finish the pipeline skeleton first.

## 2026-10-18: STEPS2 — SW aggregate cloud (no MSA)

- **Context:** Slot-clouds need observed OCR/spelling variants per template position; full MSA is heavy and out of scope for the S1 scaffold.
- **Decision:** Bootstrap `formula_slot_cloud` by Smith-Waterman against the 18c canonical template on STEPS1 hits (or fixture seeds); frequency-weighted `variants` per slot; optional slots from skip-rate hypothesis (0.25). Record period/`year_*` as metadata. No MSA; no STEPS1 threshold calibration; 17c clouds still deferred.
- **Reason:** Reuses STEPS0 SW; produces `variant_lists` for `align_sw_cloud`; keeps one formula family until span harvest (STEPS3) works.

## 2026-10-18: STEPS3 — provenanced SW/DAG spans

- **Context:** STEPS1 windows + STEPS2 cloud are ready; research needs exact boilerplate `[start, end)` on real (and shortened) openings before threshold tuning or a neural residual.
- **Decision:** Harvest `formula_boundary_spans` with SW single, SW cloud, and DAG per window; map local spans to doc offsets via `token_start`; record latency / score / cloud↔DAG agreement in `formula_boundary_span_metrics`. Still **no** STEPS1 cosine calibration and **no** GysBERT (STEPS4). 18c `opening_requeste_18c` only.
- **Reason:** Completes the TF-IDF → SW → DAG skeleton on real candidates; comparative span rows enable later cut tuning and residual decision.

## 2026-10-18: STEPS4 residual named GysBERT; bake-off deferred

- **Context:** Optional neural referee for hard formula spans could be GysBERT (plan default) or GloBERTise (VOC Early Modern). A fair comparison needs shared span gold and a harness beyond the residual gate.
- **Decision:** STEPS4 remains a **written GysBERT yes/no** (mirror STEPR4). Register a later comparison/eval framework — GysBERT vs GloBERTise (+ SW/DAG baselines), IoU / boundary delta / latency on frozen gold leftovers — as [`plans/deferred/S1-neural-span-eval.md`](../plans/deferred/S1-neural-span-eval.md). Do not run that bake-off inside STEPS4.
- **Reason:** Keep the residual decision cheap; methods comparison is Doel B and reuses STEPS0 metrics when chosen.

## 2026-09-23: STEPL0 — missive-receipt cue inventory (1780)

- **Context:** Seeds registered (`missive_receipt_seeds`, 6 hand texts). Cue POC on `resolutions_flat` year 1780 via `pd.read_parquet(..., columns=[id, date, resolutions_text])`.
- **Decision:** Keep open+close conjunction as the high-precision cue. Inventory: n=2796, open=1401, close=741, both=674. Open-only (~727) is large enough that opening alone is unusable; both≈close suggests most null-decision closes co-occur with the receipt open in this year.
- **Reason:** Matches L1 type definition; STEPL1 can seed from both-hits (then exclude `aanstelling_selected`) plus hand seeds.

## 2026-10-18: S1 stop after SW/DAG — no GysBERT residual

- **Context:** STEPS0 fixture IoU=1.0 for SW single/cloud/DAG. STEPS3 on 1780 (181 windows): zero empty spans; 30 full 6-token openings at align=9; among align>=6 cloud↔DAG spans agree. Overall cloud↔DAG equal-rate 0.33 (60/181) is driven by short partial matches (mostly 'ter Vergaderinge' / single-token) on STEPS1 0.35 neighbours — not failed true openings. STEPS1 cosine still uncalibrated; neural bake-off stays deferred.
- **Decision:** Stop after TF-IDF → SW/DAG. No residual GysBERT (or other neural) pass on low-alignment leftovers. Keep deferred S1-neural-span-eval for a later GysBERT vs GloBERTise harness if chosen. Next classical work: calibrate STEPS1 threshold now that the span framework exists.
- **Reason:** Classical alignment already recovers exact boilerplate on true 18c openings; leftovers look like framing false positives. A residual neural pass would be a methods bake-off (Doel B), not completing usable spans (Doel A). Mirror STEPR4.

## 2026-10-18: S1 variable slots (proposer) after STEPS1 calibration

- **Context:** Requeste openings leave the proposer (and similar fills) after the boilerplate span ending at Requeste. Longer gappy templates or post-span rules can extract those later.
- **Decision:** Defer named variable-slot extraction (proposer, place, body) until after STEPS1 cosine threshold calibration. Keep opening_requeste_18c ending at Requeste for calibration; do not extend the template with semantic gaps in this phase.
- **Reason:** Calibration needs a stable fixed skeleton + span metrics; slot semantics are a separate cut and would mix framing noise with extraction design.

## 2026-10-19: STEPS1 freeze cosine threshold (18c)

- **Context:** STEPS3 on 1780 at hypothesis 0.35: 181 windows, cloud↔dag agree 0.33, driven by provincial ter Vergaderinge neighbours (align≈3). Re-frame + re-harvest at 0.40: 59 windows, align_mean≈7.12, cloud↔dag agree 0.61; 52/59 align≥6; 7 residual ter-only. Template opening_requeste_18c only; 1715/1670 slices barely fire this skeleton.
- **Decision:** Freeze DEFAULT_THRESHOLD at 0.40 for opening_requeste_18c (18c). Mark HYPOTHESIS_THRESHOLD=False. No peak-dedup rule. Do not treat 0.40 as a cross-century cut; 17c requeste templates stay deferred with their own calibration later.
- **Reason:** Cut removes most STEPS1 neighbour noise while keeping true IS ter Vergaderinge geleesen de Requeste openings. Earlier centuries need different templates, not this threshold.

## 2026-10-19: Multi-template registry prove-first gate

- **Context:** Scratch registry records in docs/proofs/multi-template-registry/ (opening_requeste_18c framing; dual-zone requeste/rapport; goedgevonden with outcome_signal=false; nlp_start_marker for <START> artefact; appointment_vergadering vs appointment_rekenkamer with discriminators=[institution]). Institution proof: 50 selected vs 50 harvest Rekenkamer+cue — sibling primary rekenkamer 28/50 (56%), selected FP 0/50, selected none 86%.
- **Decision:** PASS prove-first. Keep proposed formula_templates schema (including nlp_start_marker, outcome_signal, role_depends_on_place, discriminators). Appointment lookalikes: use institution/college as primary discriminator before separate TF-IDF per sibling. Schedule manifest+loader implementation as a later step; do not register scratch JSONL yet. Improve vergadering-target institution patterns before production subtype tagging.
- **Reason:** Schema encodes caveats without baking <START> or goedgevonden-as-approval into framing. Institution separates Rekenkamer siblings from R1 vergadering list with zero FP on the sample; incomplete recall/none-rate means discriminator is necessary but not yet sufficient alone.

## 2026-10-19: Formula template registry stub registered

- **Context:** Prove-first passed; next chosen step was manifest + loader stub (not STEPL2).
- **Decision:** Register `formula_templates` → `tests/fixtures/formula_templates.jsonl` (hot / explore). Loader: `formulation.formula_templates` (`load_templates`, `get_template`, role filter, schema validation). Include `unknown_residual` row. Do **not** register docs/proofs scratch JSONL. Do not harvest `institution_patterns` or rewire STEPS1 constants in this step.
- **Reason:** Promotes the gated schema into data_io without closing the catalogue or baking ORG pattern harvest into the stub.

## 2026-10-19: Appointment institution patterns from republic_ner ORG

- **Context:** Prove-first institution discriminator used hand regex. republic_ner_matching already has ORG-annotations (tag_text+inv) and ORG-entities; surfaces shift by period (e.g. 1626 Gecommitteerde Raden ter Admirt. vs 1780 Collegie ter Admiraliteit).
- **Decision:** When implementing appointment institution_patterns, harvest period/inventory-keyed variants from republic_ner ORG-annotations (+ link ORG-entities / instituten_lookup), not a single timeless regex. Keep discriminators=[institution] on appointment subtype registry rows.
- **Reason:** Same college changes wording across centuries; static patterns will miss 17c or 18c and inflate none-rate on selected.

## 2026-10-19: Registry: wide-to-narrow, recall first; open problems

- **Context:** Prove-first gate passed. User confirmed appointment discriminators=[institution] (later institution_patterns), not per-sibling TF-IDF yet. Further constraints: many templates unknown/rare; limited opening phrases branch into different templates (same for formulas); 18c known vs 17c thinner (republic_ner has some); imperfect resolution parsing especially 17c — templates may help re-separate later.
- **Decision:** Implement registry progressively: wide categories first, then finer subtypes; prioritise recall over precision. Keep unknown/residual slots. Represent branching (shared opener → subtypes by zone/institution/period). Defer 17c period map and using templates to fix misparsed resolutions to a later stage.
- **Reason:** Matches R1 sibling lesson and STEPS 18c-first cut; avoids closing the catalogue prematurely or baking precision models before coverage.

## 2026-10-19: NER committees are content subject, not template class

- **Context:** republic_ner ORG layer also covers committees/colleges. Useful for subject category of resolutions or hits. Risk of mixing that into formula_templates ids or treating committee label as template classification.
- **Decision:** Treat NER committee/ORG mentions as content/subject specification (optional later subject_hints or doc facets). Do not use them as formula-template classification. Institution discriminator for appointment siblings remains a structural subtype gate, distinct from general subject tagging.
- **Reason:** Template asks how language is shaped; committee asks what the business refers to. Collapsing them closes the catalogue wrongly and confuses framing with topic.
