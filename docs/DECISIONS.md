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

## 2026-09-23: STEPL0 — missive-receipt cue inventory (1780)

- **Context:** Seeds registered (`missive_receipt_seeds`, 6 hand texts). Cue POC on `resolutions_flat` year 1780 via `pd.read_parquet(..., columns=[id, date, resolutions_text])`.
- **Decision:** Keep open+close conjunction as the high-precision cue. Inventory: n=2796, open=1401, close=741, both=674. Open-only (~727) is large enough that opening alone is unusable; both≈close suggests most null-decision closes co-occur with the receipt open in this year.
- **Reason:** Matches L1 type definition; STEPL1 can seed from both-hits (then exclude `aanstelling_selected`) plus hand seeds.
