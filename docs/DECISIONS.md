# Decision Log

Record durable methodological and architectural decisions here. Keep entries short enough to scan.

## Template

### YYYY-MM-DD: Decision title

- **Context:** What changed or what result forced a choice?
- **Decision:** What did we decide?
- **Reason:** Why is this the right tradeoff now?

## 2026-10-20: STEPT1o — missive joins the accepted core; four openers promoted to blueprint

- **Context:** STEPT1n accepted `missive_ontfangen` (frozen cut 6.0), mirroring STEPT1m's requeste wiring gap: `composition_unknown.ACCEPTED_TYPE_IDS` still only held the three prior openers, so STEPT1i/T1m's proto-blueprint measurement never saw missive.
- **Decision:** Wired `missive_ontfangen` into `formula_type_presence.py` (`fit_missive_presence_model`, mirrors requeste wiring) and `composition_unknown.ACCEPTED_TYPE_IDS`; re-ran the STEPT1m 1780 comparison (3-core → 4-core). Empty/undecided mass dropped only modestly (0.140→0.122), but `filler_star` (bag = bare `ontfangen_start` root only, no accepted type — 42.5% of the universe) **collapsed to 0.000** — that mass reclassifies to `known_sparse` now that the opener firing on it has a real accepted-type home. Five new/growing accepted_cores cleared support≥5 (`missive_ontfangen` alone 1239; `missive+requeste` 182; `appointment+missive+requeste` 20; `advies+missive` 7; `appointment+missive` 7), dominant_bag_frac 0.714–1.000 — same or better than the 3-core baseline's 0.706–0.982. **Promoted** `missive_ontfangen` to `role: "blueprint"` in `formula_templates`, joining the other three. Same five downstream modules (order/position/residual/graph-zone/cover-set) left untouched, per STEPT1m precedent — now a doubled follow-up item (requeste + missive).
- **Reason:** The filler_star collapse is the real typology finding here: a large share of the corpus that looked like "unexplained boilerplate" under the 3-core accepted set was actually missive-opened all along, just invisible because missive had no accepted-type home yet. Composition-level low-noise behavior (this step's gates) is independent of STEPT1n's own recall/FP judgment and isn't relitigated here.

## 2026-10-20: STEPT1n — missive opener as A family (STEPT1k-style, full ES gold)

- **Context:** STEPT1m closed with three accepted openers; user directed a missive track following the same measured-formula-type pattern as requeste (STEPT1k), not the parked Track L TF-IDF document-retrieval harvest (STEPL3, never opened).
- **Decision:** STEPT1n mirrors STEPT1k exactly: gold = ES `proposition_type=missive` + flat text (177,045 rows, 1705–1796 — 2.4× rekest's 74,205); formula type `missive_ontfangen` with empirical canonic `Ontfangen een missive van` (already established in `formula_period_bins.OPENING_FAMILIES`); cue-window slot-cloud + DAG; wording baseline for deltas only. Recall 0.887 **PASS** (≥0.70); FP 0.11 **FAIL but accepted** — smaller than requeste's 0.206, and expected given STEPT1e's own finding that ontfangen+ and ES-missive are strongly aligned but not identical (P(missive\|ont+)=0.928, P(ont+\|missive)=0.880 on 1780). New caveat vs requeste: model recall trails the naive wording baseline by 2.7–5.3 points across slices (real opener variation — plural `missiven`, reordered preambles — costs the DAG some gold that a bare substring still catches). No STEPT1k2-style hand-read FP adjudication run — the FP magnitude is smaller and the step guide's own gate anticipated the STEPT1e prior.
- **Reason:** Keeps formula-type acceptance on one consistent method (slot-cloud/DAG measuring span presence) across all four openers rather than switching definitions per type; records the wording-baseline shortfall honestly instead of only reporting the gates that passed.

## 2026-10-20: STEPT1m — requeste joins the accepted core; three openers promoted to blueprint

- **Context:** STEPT1k accepted `requeste_geleesen` (frozen cut 4.5), but it was never wired into the shared accepted-core machinery — `composition_unknown.ACCEPTED_TYPE_IDS` still only held `appointment_installation` + `advies_geleesen`, so STEPT1i's proto-blueprint/undecided measurement never saw it. `formula_templates` also had no rows at all for the three accepted formula types themselves (only boundary-span framing, doc_flag surface markers, and appointment institution siblings).
- **Decision:** Wired `requeste_geleesen` into `formula_type_presence.py` (new `fit_requeste_presence_model`, mirrors the advies wiring) and `composition_unknown.ACCEPTED_TYPE_IDS`; re-ran STEPT1i's composition-unknown measurement on the same comparison year (1780). Undecided/empty mass dropped from 0.475 to 0.140 (confirms STEPT1j's "empty is rekest-headed" finding quantitatively); two new accepted_cores cleared the support≥5 floor (`requeste_geleesen` alone, support 1113; `advies+requeste`, 57; `appointment+requeste`, 21), each with dominant_bag_frac 0.84–0.98 — same low-noise range as STEPT1i's 2-core baseline (0.71–0.93), and the 3-core split exactly partitions the 2-core totals (74 = 17+57 for advies; 28 = 7+21 for appointment). **Promoted** all three opener types (`appointment_installation`, `advies_geleesen`, `requeste_geleesen`) to a new `role: "blueprint"` in `formula_templates`. Left `formula_type_composition_graph.py` / `formula_type_order.py` / `formula_type_position.py` / `residual_structure.py` / `unknown_likeliness.py` untouched — each encodes its own already-closed step's zone/order/cover-set design call on top of a same-named but independent constant, not a shared one; wiring requeste into those is a separate follow-up per type, not mechanical.
- **Reason:** Closes the gap between "accepted formula type" (measured, frozen cut) and "in the registry / counted in composition measurement" that STEPT1k left open; confirms the promotion is safe (no bag proliferation) before treating these three as the typology's settled building-block inventory. Routing subtypes (STEPT1l) are explicitly excluded from promotion — they stay characteristics of `requeste_geleesen`, not new catalogue rows.

## 2026-10-20: STEPT1l — requeste+ routing subtypes separate structurally, stop

- **Context:** STEPT1k accepted `requeste_geleesen` as A. `docs/template-design-questions.md` named a structural outcome/routing lever ("goedgevonden vs handen/in handen vs advies co-occurrence") as "answerable now" for rekest sub-typology, in contrast to requester-identity sub-typology (civilian/institution/ambassador), which stays blocked because ES `proposer`/`proposer_role`/`proposition_organisation` are null corpus-wide. STEPT1l tested the answerable lever, mirroring STEPT1f's missive-subtype method.
- **Decision:** Universe = requeste+ model-detected (`formula_type_requeste_scores` `role=="gold"` & `pred` True — ES rekest gold where STEPT1k's opener score clears the accepted cut), full 1705–1796 (n=66,657; recall-miss 7,548 reported as a count only, not characterised). Three routing cuts: `referred` (`handen`/`in handen`, n=12,930, 19.4%), `granted_direct` (`goedgevonden`, not referred, n=47,274, 70.9%), `routing_unclear` (outcome joined, neither flag, n=3,335, 5.0%). **referred vs granted_direct separate structurally** on length (+93 words median, not circular with the defining flags) though only modestly on `advies` co-occurrence (0.199 vs 0.156). `routing_unclear` + outcome-unjoined together are only 9.7% — routing is effectively binary, not three-way. **Call: stop** — no new accepted formula type from routing density; `referred`/`granted_direct` stay characteristics cuts, same status as STEPT1f's `info_receipt`/`decisionful_residual`. Caveat recorded: `goedgevonden` fires at near-identical high rate inside `referred` (0.975) as inside `granted_direct` (1.0 by definition) — it marks "a resolution was taken," not specifically that the request's substance was approved, so `granted_direct` is a routing-absence label, not a "request succeeded" claim.
- **Reason:** Settles the one lever template-design-questions.md flagged as tractable without opening a new NER-frequency probe (requester identity) or re-running ES/model work; keeps the decision-type-vs-proposition_type caution from STEPT1k explicit rather than silently reading `goedgevonden` as approval.

## 2026-10-20: STEPT1k2 — requeste FP hand-read settles the gate-vs-gold-gap question

- **Context:** STEPT1k left an open question: is the ≤0.05 FP gate reachable at all against ES-derived gold, or does it partly measure ES label incompleteness (negatives are defined solely by `proposition_type` label absence)? Cheapest test, per the diagnosis note: hand-read ~20–30 of the 103 requeste-opener false positives rather than more compute.
- **Decision:** `scripts/build_requeste_fp_review_xlsx.py` wrote a workbook (`requeste_fp_review_xlsx`) stratifying 30 of the 103 FPs by score band × `goedgevonden` marker, plus 6 blind ES-rekest gold positives as a calibration self-check. Hand verdicts: calibration **6/6 (100%)** bearing — reviewer judgment reliable. to_score: 12/29 `bearing` (genuine ES gold gap), 17/29 `unrelated` (alignment noise). `scripts/ingest_requeste_fp_review_xlsx.py` computes the FP rate corrected for the `bearing` share with a Wilson 95% CI: **0.121 (CI 0.084–0.153)** vs measured 0.206 and gate 0.05 → **not_rescued**, even at the most favorable CI bound. **The gate is not reachable by crediting label gaps alone** for this type; the majority of FPs (59%) are real model imprecision on the decision-type confound already diagnosed in STEPT1k, not ES mislabeling. Keep STEPT1k's acceptance as-is; do not fold the 0.121 figure into pipeline metrics (29-case hand-read, not a recomputed gate). Full result in the STEPT1k proof NOTES addendum.
- **Reason:** Settles the open question empirically rather than deferring it to typology work; a real but minority (41%) label-gap share means future FP-gate failures should get a hand-read check like this one rather than defaulting to "probably unmeasurable," but should also not assume the gap explains most of the floor.

## 2026-10-20: STEPT1k — requeste opener as A family (then requeste+ subtypes)

- **Context:** STEPT1j empty band is rekest-headed (~half); provisional `requeste_start` presence only ~0.19 on that mass; STEPT1j2 confirmed empty ≠ R1/L1. User asked to measure/accept the requeste opener (A), then subtype characterisation under requeste+.
- **Decision:** STEPT1k mirrors STEPT1a2: gold = ES `proposition_type=rekest` + flat text; formula type `requeste_geleesen` with empirical canonic `IS ter Vergaderinge geleesen de Requeste`; cue-window slot-cloud + DAG; wording baseline `requeste`/`rekest`/`reqte` for deltas only. Provenanced `rekest_es_gold` / `formula_type_requeste_*`. Do **not** accept via `formula_documents` flags or provisional presence. After gates PASS, next = STEPT1l subtype characterisation under requeste+ (STEPT1f mirror) — not blueprint minting, not 17c period map.
- **Reason:** Closes the largest unexplained empty skeleton with the same acceptance bar as advies/appointment; keeps opener acceptance separate from later kind-shape characterisation.

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

## 2026-10-19: STEPL2 closed gate — park L3+ harvest

- **Context:** Risk of a second R1-sized retrieval campaign (remainder score → review → selected list) with little gain for formula typology. User chose finish STEPL2 as a closed metric gate only.
- **Decision:** Run STEPL2 holdout on `missive_receipt_labelled` (char_wb 3–5 + LR, same as R1). Record metrics; **do not** open STEPL3 harvest or freeze `missive_receipt_selected` unless a later explicit decision. Track L parked after L2. Working type definition remains cue+seeds labelled table. Next sessions: registry wiring or institution_patterns.
- **Reason:** Holdout answers “is the cheap model usable?” without committing to full-corpus review. Cue-defined positives already carry the type; a completeness list is optional Doel A, not required for typology work.

## 2026-10-19: Template design questions as research north star

- **Context:** Limited catalogue coverage; user priority is how far templates get us (power/period, discrimination, formulas↔templates, harvest speed, further discrimination, detection feasibility) — with more questions expected.
- **Decision:** Keep durable list as **design questions** in [`docs/template-design-questions.md`](template-design-questions.md), not as a pipeline checklist. Prefer small empirical probes that answer a few questions; record settled answers here; leave unresolved items in that doc.
- **Reason:** Separates research framing from step execution so Track L/R ladders do not displace typology learning.

## 2026-10-19: Boundary STEPS1–3 defaults from formula_templates

- **Context:** Registry stub held `opening_requeste_18c` tokens + frozen 0.40, while `tfidf_windows` still hardcoded the same list. STEPL2 parked; user chose wire boundary→registry over institution_patterns.
- **Decision:** `resolve_framing_template` is the source for STEPS1–3 framing id/tokens/threshold (`default_opening_template`, `default_framing_threshold`, slot-cloud `default_template`). Module snapshots (`OPENING_TEMPLATE_18C`, `DEFAULT_THRESHOLD`) load from the registry at import. Do **not** harvest `institution_patterns` in this step; do not change the 0.40 cut.
- **Reason:** One edit to the framing row updates framing/scripts; avoids drift between fixture JSONL and boundary constants.

## 2026-10-19: STEPS6 institution_patterns bookkeeping (no full ORG harvest)

- **Context:** Next work after STEPS5 is period-keyed patterns from republic_ner ORG; full `ORG-annotations.json` is ~650MB on the 2TB warm drive. Session constrained to bookkeeping.
- **Decision:** Register `org_annotations`, `org_entities`, `institution_patterns` (fixture seeds + loader `formulation.institution_patterns` with year/inv filter and target→ORG-entity map). Do **not** stream-aggregate annotations or rewire the prove script in this step. Committees remain content/subject, not template ids.
- **Reason:** Unblocks schema/manifest/tests without a heavy harvest; harvest or prove-script wire-up is an explicit follow-up.

## 2026-10-19: Prove script uses institution_patterns (not templates)

- **Context:** STEPS6 registered fixture seeds; prove script still had inline regexes. User chose wire-up over full ORG stream-harvest.
- **Decision:** `scripts/prove_appointment_institution.py` loads surfaces via `formulation.institution_patterns` (`extract_institutions` / `primary_institution`). Appointment `formula_templates` keep `discriminators: ["institution"]` + `institution_targets` only — no org pattern strings in the template registry. Broad null-dated seeds added for prove recall until harvest period-keys them.
- **Reason:** One pattern store for the discriminator; templates stay structural ids, not NER surface lexicons.

## 2026-10-19: S6c stream-harvest ORG → institution_patterns

- **Context:** Full `ORG-annotations.json` (~650MB) must not be `json.load`ed; appointment targets already map to ORG-entity ids; inv needs year from inventory metadata.
- **Decision:** Stream the annotations array (`raw_decode`), filter to `TARGET_ORG_ENTITIES`, aggregate `(target, entity, inv, tag_text)` → `n`, attach `year_min`/`year_max` from `inventory_metadata`, write provenanced scratch `institution_patterns` (+ metrics) via `save_semi_structured`. Keep fixture as `institution_patterns_seeds`; merge unmapped seeds (e.g. `gecommitteerde_raaden`) by default. `load_patterns` falls back to seeds when scratch is absent. Do not put surfaces in `formula_templates`.
- **Reason:** Period-/inventory-keyed empirical spellings without memory blow-up; CI stays seed-backed; prove recall keeps seed-only targets until entity ids exist.

## 2026-10-19: S6d prove harvest vs seeds (appointment institution)

- **Context:** Locked sample (50 sibling + 50 selected; sibling pool = seed rekenkamer union). Seeds: 14 surfaces; harvest: 43 581 rows / 17 838 unique, year-scoped extract. Sibling `rekenkamer` rate 1.0 both arms (pool bias). Selected `none` 0.82 → 0.80. Harvest introduces 1 selected FP (`session-3812-num-136-resolution-10`, *Generaliteyts Reekenkaamer*); `pass_no_fp_rekenkamer_on_selected` fails on harvest.
- **Decision:** Keep harvest as default `institution_patterns` loader source. Do **not** use the unfiltered lexicon as the appointment discriminator gate. Next: tighten harvest with `--min-n` (or frequency cut) and re-run `--source compare` before changing prove defaults. Seeds stay the no-FP baseline.
- **Reason:** Lexicon size alone does not improve sibling discrimination; one OCR-ish rekenkamer surface breaks the FP gate for negligible `none` gain.

## 2026-10-19: STEPT1-period `--family all` + previous-period borrow

- **Context:** Full period-bin run for appointment, `ontfangen_start`, `requeste_start`. Ontfangen stable (diag 0.93–1.0, no recalibrate signals). Requeste early bins fine; **1750–74 n=2 / 1775–99 n=24** under `min_bin_n` and had **no later donor**, so borrow recorded `no_later_donor`.
- **Decision:** Prefer borrow from nearest **later** self-fit model; if none, fall back to nearest **earlier** (`borrowed_previous_period`). Re-run requeste/all to measure `recall_on_sparse`. Separately, widen requeste seed surfaces (`request_start` etc.) — late collapse is largely a candidate-harvest problem, not only borrow.
- **Reason:** User’s “use the period after” covers early thin bins; late opening collapse needs the symmetric previous-period donor plus better seeds.

## 2026-10-19: STEPT1a2 — advies formula type (STEPT1a-style)

- **Context:** STEPT1d left bags as fragments; next cheap step is another sharp A family. STEPT0 priors list `advies` first. Datasheet canonic is `"..."`; corpus/ES majority opener is **`geleesen het Advis van`**. Flag `formula_documents.advies` (~35k) is wording only — not gold (ES type ≈995 in 1705–1796).
- **Decision:** Mirror STEPT1a: `formulation/advies_formula_type.py` + `scripts/eval_advies_formula_type.py`; gold = ES `proposition_type=advies` → `advies_es_gold` (`--refresh-gold`); cue-window slot-cloud + DAG; wording baseline `advi[sz]`; N=500 negatives; provenanced `formula_type_advies_metrics` / `_scores`. Gates: overall recall ≥0.70, FP ≤0.05 judged, cloud accepts ≫0.
- **Full eval PASS:** recall **0.762** (n=950); FP **0.034** (17/500); cloud **686/895**; cut=4.12; Δ vs wording −0.027. Pre-1731 softer (0.60) noted, no family floor. Accept advies as formula type; next presence-bag refresh or another A / sieve.
- **Reason:** Same measured A schema as appointment on the next sharp sparse family; independent ES gold avoids circular flag detectors.

## 2026-10-20: STEPT1k — requeste opener accepted (A); FP gate questioned

- **Context:** STEPT1j left requeste as the largest unexplained skeleton in the empty band. Measure the opener as a formula type on ES `rekest` gold, same schema as STEPT1a2 advies.
- **Decision:** Accept `requeste_geleesen` as **A** on the slot-cloud/DAG baseline (method parity with appointment/advies). Recall **0.8983** (n=74205) PASS; cloud accepts 37,939 PASS; FP **0.206** (103/500) FAIL — accepted as a diagnosed limitation, not fixed, and not grounds for swapping method for one type.
- **FP diagnosis (scratch):** not calibration (no cut clears both gates; FP 0.042 only at recall 0.631). Not generic slots (single-slot ablation raised recall *and* FP: 0.880/0.136 vs 0.645/0.076). Not length (length-only barely separates; proba–length corr ~0 on random sample). Not day-order (only testable 1626–30, no overlap with 1705–1796). **Is** decision-type: FP 0.340 for negatives carrying `goedgevonden`-family markers vs 0.117 without; 66% of FPs from the 40% that have them.
- **Method-comparison caveat:** TF-IDF+LR got nearer both gates (0.79/0.054 @0.8) but answers a *different question* — order-blind document topic (≈ re-deriving the ES label) vs. ordered span presence. Both score the full document, so this is not a "more text wins" result. Treat as an upper bound on class separability, not evidence against the opener definition.
- **Net-then-sieve refuted for this signal pair:** TF-IDF-net + DAG-sieve, 7×6 cut grid — no pair clears both gates and the sieve adds nothing (TF-IDF@0.8 alone 0.791/0.054 → +DAG@4.5 0.787/0.054). Stages are redundant (same vocabulary, ordered vs. order-blind), not complementary. `candidate-then-structure` only pays when the two stages see different evidence.
- **Call:** Next = STEPT1l subtype under requeste+. **Open first:** is ≤0.05 FP reachable against ES gold at all? Four signals floor at 0.04–0.05 only below the 0.70 recall gate — the pattern expected if some "negatives" are requeste-bearing resolutions ES never typed. Cheapest test is hand-reading ~20–30 FPs, not more compute.
- **Reason:** Negatives are defined solely by ES label absence, and `proposition_type` was an administrative construction unevenly maintained; a gate built on it may measure label completeness as much as model error.

## 2026-10-20: STEPT1j2 — empty-band R1/L1 retrieval probe

- **Context:** User: prior TF-IDF type searches (R1/L1) should inform empty fingerprints. Hypothesis: contrastive vectors triage empty better than within-band clustering.
- **Decision:** `formulation/empty_band_retrieval.py` + `scripts/run_empty_band_retrieval_probe.py` — join frozen R1 harvest; L1 `fit_on_all_labelled` + score empty; P-bands × ES type. Provenanced `empty_band_retrieval_*`. Not L3; not new types.
- **1780 NOTES (PASS):** R1 **99.7% low** (med 0.022); L1 **3 high** (all missive) / 45 grey / 1281 low; empty missive soft grey (p90 0.63) but not high flood; rekest low on both. Confirms empty ≠ aanstelling/L1; fingerprints were the wrong instrument for that question.
- **Call:** Next = **requeste/rekest seeded** contrast or presence — not tighter fp clustering, not L3.
- **Reason:** Same lesson as R1/L1 design: named class needs seeds + overig, not residue clustering.

## 2026-10-20: STEPT1j — empty-band characterisation (+ fp_cut sweep)

- **Context:** STEPT1i left undecided = empty (1329); `fp_cut=0.15` one mass. Need structural characterisation before any blueprint mint; optional tighter fingerprint cuts.
- **Decision:** `formulation/empty_band.py` + `scripts/run_empty_band_characterisation.py` — join STEPT1e partition (no ES remget); type mix / length / flag catalogue; fingerprint similarity fit once, re-cluster at cuts `0.15/0.30/0.45/0.60` (operating labels @0.45); provenanced `empty_band_*`. No blueprint promotion.
- **1780 NOTES (PASS):** empty **1329**; **rekest 700** (0.53) + missive/voordracht/rapport/conclusie pockets; ontfangen_present 0; `goedgevonden`/`gedelibereert` high on rekest; conclusie sharp (`handen` 0.70). fp: 0.15 one mass; **0.45** share_largest 0.068 but 587 singletons — sample strata only. Next = **requeste/rekest opener** presence probe (or conclusie+handen) — not mint from empty n / clusters.
- **Reason:** Empty is multi-pocket, not one type; fingerprints triage sampling; largest unexplained skeleton is requeste.

## 2026-10-20: STEPT1i — formula-graph blueprints / derivatives / fingerprints

- **Context:** Unknown formulas are invisible until named; templates are combinations. Exact bags proliferate. User: object = resolution formula-graph patterns; fingerprints for variation vs different structure / derivative vs novel once blueprints exist. NER ALIGNED_TO fingerprint is the wrong instrument.
- **Decision:** STEPT1i measures (1) `accepted_core` proto-blueprints + within-core derivative mass + undecided (`empty`∪`novel_tail`); (2) content fingerprints on undecided (NN/clusters + max_sim to proto exemplars). STEPT1h cover-unknown stays auxiliary. No blueprint promotion.
- **1780 NOTES (PASS):** proto-blueprints **2** (advies 74 / appointment 28; dominant bag ~0.92); filler 1365; **empty 1329**; novel_tail **0**; only 6 exact bags. Fingerprint `fp_cut=0.15` → **one mass** (share 0.999); derivative_score p50 0.18. Next = characterise empty (T1j) and/or tighter fp cut — not mint blueprints.
- **Reason:** Thin presence inventory → no novel combinations yet; empty is the real undecided pool; loose fp cut does not split structure vs variation.

## 2026-10-20: Unknown-first doctrine + STEPT1h PASS (1780)

- **Context:** User wants resolution triage by **unknown likeliness**, then content characterisation — up-front classification from incomplete expert knowledge only rediscovers what was brought in. STEPT1g showed residual = filler mass + sparse appointment; next was not another named A from thin reading alone.
- **Decision:** Lock spine in [`plans/milestones/T1-unknown-first.md`](../plans/milestones/T1-unknown-first.md): known cover → unknown-likeliness → (fingerprints) → content characterisation → task-template promotion. STEPT1h: cover = L1 / R1 / appointment present / advies present∨gold; score `1 − hits/axes`; provenanced `resolution_unknown_*`.
- **1780 NOTES (PASS):** universe **2796**; high-unknown **2015** (0.721); cover L1 674 / R1 31 / appointment 28 / advies 76. No ≥3-axis hits. Band large because cover is thin — expected. Next = fingerprint or stratified *slice* of high-unknown, not a type from n=2015.
- **Reason:** Discovery order matches incomplete knowledge; formulas stay production support; templates become SG-task packages only after characterisation.

## 2026-10-20: STEPT1g — decisionful residual structure

- **Context:** User: STEPT1f’s info half remeasured the obvious L1 template; **probability is not typology**; formula types may have hit rates but that does not rank usefulness (ubiquitous = filler / no signal); interesting stuff is sparse; open question = structure inside ontfangen+ \\ L1.
- **Decision:** `formulation/residual_structure.py` + `scripts/run_residual_structure_probe.py` — pockets + combo catalogue + bags + stratified text sample. Provenanced `residual_structure_metrics` / `_scores` / `_sample`. No subtype ids from rates. Not STEPT1e1.
- **1780 NOTES (PASS):** residual missive **656**; solo `ontfangen_start` bag **624** (filler star); appointment pocket **26** ≈ R1 (covered); 177 flag-set combos, top-5 share 0.36 (do not mint types from head). Sample shapes: filler receipt→deliberate; creditif/install (accepted A); sparse unexplained nominations + procedural enclosures.
- **Call:** Next = named **sparse** unexplained shape (lean: provincial nomination under missive) or park Track T. Not e1; not “decisionful missive” from high-n combos.
- **Reason:** Closes the residual question with inventory + reading; frequency is not a usefulness or typology ranking.

## 2026-10-20: STEPT1f — missive subtype characterisation (circular half noted)

- **Context:** STEPT1-map named missive as not one kind structurally (info/null vs decisionful under ontfangen+). Default lean: characterise those subtypes before any A or e1 sieve.
- **Decision:** `formulation/missive_subtype_profile.py` + `scripts/run_missive_subtype_profile.py`; reuse STEPT1e scores; kind filter ES missive; subtypes = L1 `info_receipt` vs `decisionful_residual`; length from `resolutions_flat` + flag rates as characteristics. Provenanced `missive_subtype_metrics` / `_scores`. Not formula types; e1 stays parked.
- **1780 NOTES:** info 641 / decisionful 656; words med **37** vs **188.5**; flag contrast strong. **Caveat:** `info_receipt` = L1 labelled set, whose cues *are* the advertentie/geen_resolutie skeleton — that half is circular remeasurement of the obvious template. The open question was the **decisionful residual**, not L1.
- **Call (superseded):** Was rekest next; superseded by STEPT1g residual structure probe.
- **Reason:** Length split and residual focus still useful; do not treat L1 flag rates as typology evidence.

## 2026-10-20: STEPT1-map — typology before classify

- **Context:** Detectors and partitions (appointment, advies, ontfangen±, flags) outran a clear object of typing. User: without typology and characteristics, no classification. STEPT1e1 flag sieve would classify surfaces. Schemes sample is the user’s **hypothetical** sketch — resolutions may not fit fully, should usually fit partially.
- **Decision:** Docs-only map ([`STEPT1-typology-formula-map.md`](proofs/multi-template-registry/STEPT1-typology-formula-map.md)): keep resolution kind / characteristics / discourse role / formula evidence as distinct layers; schemes×STEPT0×measured crosswalk; inventory (accepted / provisional / scheme-only / overloaded). Schemes = hypothesis, not closed checklist; partial/non-fit revises the sketch. **Park STEPT1e1.** No new A until a characterisation gap from the map is chosen.
- **Call:** Next = characterisation gap (default lean: missive subtypes under ontfangen+), not flag bucketing. *(Superseded by STEPT1f PASS.)*
- **Reason:** Formula detectors support kinds/roles; they are not the typology. Map is the gate.

## 2026-10-20: STEPT1e — partition probe (ES + flags on ontfangen±)

- **Context:** STEPT1e0 left typology gaps: ES mix on ontfangen±, flag rates, residual after L1 (~724 ids). Discourse skeleton in play: opening → (expose) → decision → (defer) → (execution).
- **Decision:** Implement STEPT1e as a focused probe — `formulation/ontfangen_partition.py` + `scripts/run_ontfangen_partition_probe.py`; lean ES `mget` + `formula_documents` join + known-set tags; provenanced `ontfangen_partition_metrics` / `_scores`. Ontfangen stays provisional root/partition.
- **1780 NOTES (PASS):** P(missive\|ont+) **0.928**, P(ont+\|missive) **0.880**; residual **724** still 91% missive but decision-flag shaped (`gedelibereert`/`goedgevonden`) vs L1 null path (`geen_resolutie`+`advertentie`). Keep **opening/partition** + **decision-stage** axes. Flags = boilerplate surfaces, not outcomes; no ordered discourse spans yet.
- **Call (superseded by STEPT1-map):** Was STEPT1e1; now park e1 — typology map before classify.
- **Reason:** Closes e0 gaps with one-year measurement; residual is decisionful under the same opener, but flag sieves wait on kind characterisation.

## 2026-10-20: STEPT1e0 — ontfangen inventory before typology probe

- **Context:** T1d star + concern that formula typology needs attention. Temptation was another sparse A (rapport/…); better first inventory the composition-root population from existing 1780 artifacts.
- **Decision:** STEPT1e0 NOTES only (no new scorer, no ES): presence counts (ontfangen+ **1397/2796**), solo bags, zone, graph smoke, cheap joins (L1 673/674 under root but only ~48% of ontfangen+; R1 27/31; advies gold ∩ root **0**). Gap list: ES mix on partition, flag rates, residual after L1. **Call: STEPT1e partition probe next; no new A until then.**
- **Reason:** Half the root is unexplained by L1; datasheet/STEPT0 missive priors are untested against ontfangen±; inventory is cheaper than a wrong A or an unscoped ES join.

## 2026-10-20: STEPT1d — composition graph (co-presence)

- **Context:** T1d order parked (soft constraint only; bags still fragments). Composition should be a **graph**: nodes = types × IDF presence weight; arcs = co-presence directed by `mid_norm`. Not Track S `align_dag`. `ontfangen_start` = composition root/partition, not IDF “noise.”
- **Decision:** `formulation/formula_type_composition_graph.py` + `scripts/run_formula_type_composition_graph.py`; provenanced `formula_type_composition_graph_metrics` / `_scores`. Cheap gate: 1780 smoke `n_accepted_accepted_edges` + `graph_shape` (`provisional_root_star` vs `accepted_co_presence`). `--period-bins` only if smoke leaves dynamics open. Order CLI kept but not the composition definition.
- **1780 NOTES (PASS, `--limit 200`):** `n_accepted_accepted_edges=0`, `graph_shape=provisional_root_star` (2 spokes: ontfangen→advies, ontfangen→appointment; no advies↔appointment). **Skip `--period-bins`.** Next: another A family or sieve residual.
- **Reason:** Co-presence + relative presence is the right composition unit once sequences failed; period matrix is optional cost after the star hypothesis is tested on one year.

## 2026-10-19: STEPT1d — order / composition by start_idx

- **Context:** STEPT1c PASS — zone separates (ontfangen@opening; appointment@close) but bags remain fragments for template composition. STEPT1 §C next cheap probe is **order** (A before B).
- **Decision:** `formulation/formula_type_order.py` + `scripts/run_formula_type_order.py`: reuse T1c span scoring; per-id sort presents by `start_idx`; provenanced `formula_type_order_scores` / `_metrics` (top ordered sequences vs bags, expected opening→appointment rates, order-vs-bag diversity). Openings still provisional.
- **1780 NOTES (PASS):** n_multi=26 (0.9%); ontfangen→appointment **26/26**; only one multi bag with **one** distinct order — order does not beat bags/zone. Keep order as a soft constraint on rare multi; **stop** further sequence features. Next: another sharp A family or sieve residual.
- **Reason:** Cheapest test of sequenced composition without new detectors; T1c spans already paid for; trivial fixed order is not a template inventory.

## 2026-10-19: STEPT1c — position / zone from DAG spans

- **Context:** STEPT1b judged 1780 presence bags as **fragments** (mostly lone `ontfangen_start`); STEPT1 §C asks whether position / zone is required before templates.
- **Decision:** `formulation/formula_type_position.py` + `scripts/run_formula_type_position.py`: same models/cuts as T1b; record DAG `start_idx`/`end_idx`; `mid_norm` tertiles → `opening` / `body` / `close`; provenanced `formula_type_position_scores` + `_metrics` (per-type zone mix, `frac_in_expected_zone`, zone-tagged bags). Openings still provisional. No ES `evidence` zones in this step.
- **1780 NOTES (PASS):** ontfangen **99.6%** opening (mid_norm 0.027); appointment **0%** opening / **96%** close (mid_norm 0.90 — prior `body` wrong → set expected to `close`); zone-tagged multi bags ≈ appointment@close + ontfangen@opening (25/26). Position is a **discriminator** worth keeping on registry/scoring; bags remain fragments for template composition → next order/composition or another A family.
- **Reason:** Cheapest test of `role_depends_on_place` without new detectors; token mid-span reuses Track S alignment already paid for in presence scoring.

## 2026-10-19: STEPT1b — presence scoring + popularity bags

- **Context:** STEPT1a accepted appointment; STEPT1 §B needs corpus presence scores with IDF-style popularity weights and a judgment on whether multi-type bags look like templates.
- **Decision:** `formulation/formula_type_presence.py` + `scripts/run_formula_type_presence.py`: default POC year **1780**; freeze appointment cut from `formula_type_appointment_metrics` when present; optional provisional `ontfangen_start` / `requeste_start` for bag exploration only; provenanced `formula_type_presence_scores` (id×type, `score_weighted`) + `_metrics` (hit rates, popularity, bag size histogram + top patterns). Openings are **not** accepted types. User runs full year before NOTES judgment (templates vs fragments → STEPT1c).
- **Reason:** Weighted multi-type bags are the cheapest way to see whether presence alone composes; year POC keeps cost bounded; freezing T1a cut avoids re-litigating the appointment gate.

## 2026-10-19: T1a-fix — welkom cue-window bootstrap (full re-eval PASS)

- **Context:** STEPT1a PASS left welkom cloud at **0/2564** accepts. Root cause: datasheet canonic `wordt hij welkom geheten` ≠ corpus majority `is den selven verwelkomt,`; trailing punct on cue tokens; full texts as “hits”.
- **Decision:** Empirical canonic `is den selven verwelkomt` + ±6-token cue windows + punct-stripped align tokens + seed inject on `verwelkomt`/`selven`. Full re-eval: welkom **2251/2313** accepts; pre **0.816** / post **0.832** / FP **0**; period appointment diags **0.81–0.90**, no recalibrate signals. **Clear the 0-accept caveat.** Record side-effect: p20 cut rises to **6.0** (perfect welkom); sessie max ≈3 never clears — scoring is welkom-led; overall recall 0.829 trails wording by ~0.12. Optional later: dual-cut / length-normalize scores.
- **Reason:** Cloud now learns real OCR variants; gates still beat the 0.235 floor; stricter cut is a calibration consequence of a stronger welkom template, not a bootstrap failure.

## 2026-10-19: STEPT1a + STEPT1-period appointment eval (full run)

- **Context:** User ran `eval_appointment_formula_type.py` and `eval_formula_period_bins.py --family appointment` (not fixture).
- **Decision:** **PASS** STEPT1a gates: pre-1731 model recall 0.861 ≫ 0.235 floor; post-1731 0.937; FP 0.018 on N=500. **PASS** period-bin self-diagonals (0.86–0.95); no adjacent-backward cell under 0.5. Record caveat: welkom cloud bootstrap **accepted 0/2564** hits — live scorer is sessie-led + seed variants; fix windowed/looser welkom bootstrap before claiming welkom-variant learning. Mid-bin soft drift: 1750–74 model on 1725–49 data recall 0.613 (Δ −0.29). `formula_documents_compare` deltas are **not** same-universe (selected vs full matrix); use docs for corpus flag rarity / welkom=0 early, not as a fair bake-off.
- **Reason:** Measured bars met; caveats are explicit so next work targets welkom bootstrap and optional mid-century subtype, not re-litigating the floor test.

## 2026-10-19: STEPT1-period — family × 25y bins + measured recalibration

- **Context:** Formulas change gradually; opening-only / single-period models miss evolution. User wants independent sub-templates per family and 25-year comparison, with measurements.
- **Decision:** `formulation/formula_period_bins.py` + `scripts/eval_formula_period_bins.py`: per family (`appointment_installation`, `ontfangen_start`, `requeste_start`), fit slot-cloud/DAG per 25y bin (origin 1700), freeze in-bin p20 cut, write full **cross-bin recall matrix** with `delta_vs_data_self` and `recalibrate_signal` (adjacent backward recall < 0.5). Sparse bins (`0 < n < min_bin_n`) **borrow the nearest later self-fit model** (`borrow_from_next_period`, measured `recall_on_sparse`). Each summary includes **`formula_documents_compare`**: per-bin flag rates on resolution rows (`welkom`/`sessie`, etc.) vs model diagonal recall + deltas. Provenanced `formula_period_bin_metrics` / `_matrix`. Popularity weight from mean diagonal recall. Openings use capped substring candidate pools (seeds, not types).
- **Reason:** Makes gradual drift an evaluated claim (numbers), not a narrative; keeps families separate so one opening’s drift does not smear another; thin early opening pools still get a recalibration path from the following period; documents matrix is the wording-matcher baseline to beat or explain.

## 2026-10-19: STEPT1a — measured appointment formula type (+ popularity weight)

- **Context:** STEPT1 reframed: define formula types by slot-cloud/DAG (not regex); measure recall vs `aanstelling_selected` pre/post-1731 against wording baselines; explicit N=500 negatives. Ubiquitous formulas (*goedgevonden*, etc.) are uninformative for typology ranking.
- **Decision:** Ship `scripts/eval_appointment_formula_type.py` + `formulation/appointment_formula_type.py`: welkom+sessie clouds, DAG max score, p20-holdout cut, stratified negatives, provenanced `formula_type_appointment_metrics` / `_scores`. Report IDF-style **popularity** block: ``weight = log(1/clip(p))`` with ``p`` = hit rate on negatives at the cut; ``score_weighted = score * weight``. Single-family acceptance still uses raw cut; weighted scores reserved for multi-type ranking/composition (STEPT1b+). User runs full eval before pass/fail NOTES.
- **Reason:** Pre-1731 has no `welkom` wording — need measured cloud/DAG vs `sessie` floor; popularity punishment encodes STEPT0 lift insight (near-universal flags mean little) without changing the appointment gate.

## 2026-10-19: STEPT0 — provisional 18c proposition-type structural profile

- **Context:** Scoping surfaced two unused sources: `formula_documents` (309 181-row boolean formula-family flag matrix, 1705–1796, registered at a dead `republic_clean` path — recovered from `notebook-archive`) and the ES `full_resolutions` index's `metadata.proposition_type`/`metadata.resolution_type`/`evidence` fields, none of which `republic_es.py` requested. ES labels only the opening side (no outcome label, by design — avoids a decision-content claim); `formula_documents` carries the closing/outcome flags but stops at 1705. Composition (population proportions) and characterisation (per-type structural detail) are different questions: a strictly proportional sample vanishes the tail (e.g. `paspoort` at 0.1% of a year), so they are computed separately.
- **Decision:** New Track T (typology), one step (STEPT0): `formulation/typology_sample.py` computes (a) full-population `proposition_type` composition via ES terms agg (no sampling error) and (b) a floored-proportional characterisation sample (`DEFAULT_FLOOR=30`, `DEFAULT_SAMPLE_TOTAL=1000`), joined to `formula_documents` outcome flags on `(session_date, resolution_index)` — the only key present on both sides (ES/`resolutions_flat` key on inventory `num`; `formula_documents` doc_id is date-based with `num` constant at 1). `scripts/run_typology_profile.py` defaults to `POC_YEAR=1780` (shared with STEPS1/Track L) for a first provisional pass; `--full-18c` or explicit `--year-min`/`--year-max` widens. Output: `typology_structural_profile` (per-`proposition_type` label-zone medians/IQR from ES `evidence` offsets, length stats, `formula_documents` flag rates). This is a descriptive profile, not a model, and not a final typology — a provisional one is the explicit goal.
- **First run (1780, seed 20261019, 14 proposition_type values, 3 134 population resolutions, 1 063 sampled):** confirms the join and pipeline work end-to-end. `missive` (pop 1 489, 47.5%) and `rekest` (pop 761, 24.3%) structurally separate cleanly — e.g. `proposition_body` sits at median normalised offset 1.0 for `missive` vs ~0.40 for `rekest`/`rapport`/`voordracht`/`memorie`. Outcome-join coverage varies sharply by type: 99.8–100% for `missive`/`voordracht`/`memorie`/`advies`/`resolutie`, but only 15.6% for `onbekend` (460 resolutions, 14.7% of the year) — **expected, not a bug to chase:** `onbekend` resolutions were already unclassifiable upstream (that's why ES couldn't assign them a `proposition_type`), so low closing-formula coverage is consistent, not a signal of a join problem. Leave as-is.
- **Known caveat (flagged by user, not inferred):** `praeside_start`/`praesentibus_start` in `formula_documents` mark presidium/attendance-list openers; their small nonzero rate on resolution rows reflects upstream session-boundary parsing leakage (attendance-list text attached to an adjacent resolution), not real resolution content. Documented in `typology_sample.py`'s module docstring; do not read these two flags as resolution signal.
- **Bug fixed during this step:** the first implementation's `join_outcome_flags` lost all 31 real `formula_documents` flags after the left-merge — pandas upcasts bool columns to `object` on introduced NaN, and the downstream `dtype == bool` re-detection in `build_profile_records` silently picked up only the unrelated `outcome_joined` marker column instead. Fixed by casting joined flag columns to pandas nullable `boolean` dtype and passing the flag-column list explicitly via `joined.attrs["flag_columns"]` rather than re-deriving it from post-merge dtypes. The CLI's closing preview (`records[0]` only, always `missive` since composition is sorted by population) was also replaced with a compact per-type summary table — the underlying per-type `flag_rates`/`label_zones` were already correct in the saved jsonl; only the console preview was misleading.
- **Reason:** A provisional typology beats none; cheap single-year-first POC before any wider claim; population composition must never be read off the floored sample.

## 2026-10-21: Re-pin ES resolutions_index — id-keyed label joins were mislabelling ~31% of gold

- **Context:** User spotted that two `aanstelling_labelled` gold "appointments" are not appointments (a resolution-resumption and an advertentie receipt) and suggested URN drift against an older index. Checking the same id across index generations showed worse: resolution ids are **not stable across builds**. `session-3344-num-110-resolution-4` carries three different resolutions in `2024-11-10` / `2025-02-20` / `2025-03-15+` (onbekend missive → advertentie missive → rekest). On 150 random 1780 ids, `resolutions_flat` text matches `full_resolutions-2025-02-20` **150/150 (100%)** but the configured `full_resolutions-2026-03-25` only **101/146 (69%)**, with 4 ids absent.
- **Decision:** Pin `[elasticsearch].resolutions_index` to **`full_resolutions-2025-02-20`** (the generation `resolutions_flat` actually is), in `data_manifest.toml` and as the `republic_es` dataclass/loader default, with a comment forbidding a bump without re-checking match rate. Verified after the change: 150/150 (100%).
- **Consequence — prior measurements are contaminated, not wrong-by-method:** every `*_es_gold` set is built by fetching ids from the ES index and joining text from flat by id, so ~31% of rows had a label attached to the wrong text. Affects `rekest_es_gold` (74,205), `advies_es_gold`, `missive_es_gold` (177,045) and every metric derived from them: requeste 0.898 recall / 0.206 FP (STEPT1k), advies 0.762 / 0.034 (STEPT1a2), missive 0.887 / 0.11 (STEPT1n). **All three must be re-fetched and re-measured before their numbers are quoted again.**
- **Reason this matters beyond bookkeeping:** three separate steps hit an unreachable ≤0.05 FP floor and each explained it differently — decision-type confound (T1k), ES label incompleteness (T1k2), ontfangen+/missive boundary fuzziness (T1n). A 31% join mismatch produces exactly that signature. T1k2's hand-read found 41% of sampled FPs were genuine requeste-openers "ES had not labelled", which is what a mismatched join looks like from the inside; its conclusion that the gate is unreachable may be an artifact. Also the same root cause as the `aanstelling_gold_relocations` 18-URN patch, which treated a pervasive problem as 18 rows.

## 2026-10-21: Clean stratified recheck after the re-pin — gold contamination confirmed; FP gate left undecided

- **Context:** Rather than re-fetch 74k–177k rows per type, `scripts/recheck_es_gold_sample.py` samples 15 ES-labelled ids per year from the *pinned* index, joins flat text (same generation ⇒ exact), and verifies each sampled negative's label individually against that index. Existing frozen clouds/cuts are reused, so this isolates the gold-contamination effect rather than a retrained pipeline.
- **Result (recall / FP, clean vs stale):** requeste **0.995 / 0.171** vs 0.898 / 0.206 (n=1380, neg 374); advies **0.920 / 0.024** vs 0.762 / 0.034 (n=840, neg 499); missive **0.988 / 0.018** vs 0.887 / 0.110 (n=1380, neg 226). Wilson 95% CIs: missive FP 0.007–0.045, advies FP 0.014–0.042, requeste FP 0.136–0.213.
- **Cause of the FP collapse:** of 500 flat-sampled negatives, **274 were actually labelled `missive`** by the pinned index (126 for `rekest`, 1 for `advies`). The old negative pools excluded ids drawn from the mismatched gold set, so hundreds of genuine positives sat in the negative pool and every correct detection counted as a false positive.
- **Decision:** Gold contamination is confirmed and large: the stale negative pools held hundreds of genuine positives, so the pre-re-pin FP figures measured the join, not the model. Recall is solid on clean gold for all three (0.92–0.995) and the T1n/T1o promotions hold. STEPT1k2's "gate unreachable" conclusion is **withdrawn** — a 29-case hand-read cannot support it either way. `requeste_geleesen` fails the gate at 0.171 with a CI (0.136–0.213) well clear of 0.05, so STEPT1k's decision-type confound stands as real signal.
- **Not decided — whether the ≤0.05 FP gate is reachable.** An earlier revision of this entry claimed missive (0.018) and advies (0.024) "pass it outright". **Withdrawn as underpowered** (amended 2026-10-21 during STEPT1q): those rates rest on 4/226 and ~12/499 events, a Wilson half-width of ±0.026 against a 0.05 gate. A STEPT1q re-measurement with the same frozen cloud and cut, differing only in which negatives were drawn, gave missive FP **0.0575 (13/226)** instead of 0.018 — Fisher exact p=0.045 against the figure above. Two draws that far apart mean n≈226 cannot resolve this gate. Needs ~2,000 clean negatives (±0.009) before any pass/fail is recorded.
- **Reason:** a stratified sample with CIs cheaply answers "did the numbers move?", which is what this entry establishes. It does not answer "does the model clear a 0.05 threshold" — that needs an order of magnitude more negatives. A gate verdict resting on a handful of events is not worth recording as a decision; this project has now been burned twice that way (STEPT1k2's 29-case hand-read, and the figures above). The full re-fetch is also still owed before these datasets are used downstream.
