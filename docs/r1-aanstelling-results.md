# R1 results — aanstelling retrieval

**Status:** judged (stop after TF-IDF); selection frozen 2026-09-23  
**Artifacts:** `aanstelling_labelled`, `aanstelling_tfidf_harvest`, `aanstelling_retrieval_xlsx`, `aanstelling_review_labels`, `aanstelling_selected`, `aanstelling_pre1705_gold_review_xlsx`  
**Milestone:** [`plans/milestones/R1-aanstelling-retrieval.md`](../plans/milestones/R1-aanstelling-retrieval.md)

## 1. Model (holdout)

Char n-gram TF-IDF (`char_wb` 3–5) + logistic regression, stratified 80/20 on `aanstelling_labelled` (213 aanstelling / 2130 overig; `random_state=42`). Not tuned on the test split.

| Metric | Value |
|--------|------:|
| Recall @ 0.5 | 0.860 (37/43) |
| Precision @ 0.5 | 0.974 |
| F1 | 0.914 |
| High-or-grey recall (p > 0.15) | 0.977 (42/43) |

Of 6 holdout FNs, 5 fall in the review band `(0.15, 0.5]`; one is 1690 HTR at p≈0.023. **STEPR4:** no residual neural pass.

## 2. Harvest (unlabelled remainder)

Scored 691 943 non-gold resolutions (model refit on all labelled rows).

| Band | Cut | n |
|------|-----|--:|
| High | p > 0.85 | 1 012 |
| Completeness (ingest) | p > 0.5 | 2 883 |
| Review | 0.15 < p ≤ 0.5 | 4 137 |
| Low | p ≤ 0.15 | 684 923 |

Post-filters on the Excel export: aanstelling formula cues, length + cosine-to-gold shape, unique-delegate pattern match (ingest match rate ≈ 0.54 among eligible).

## 3. Human + rule review (suspect sheets)

| Sheet | Labeled | keep | drop | keep rate |
|-------|--------:|-----:|-----:|----------:|
| `ingest_suspect` | 33 | 31 | 2 | 94% |
| `review_suspect` | 375* | 270 | 105 | 72% |

\*Includes human labels plus rule fill: bare `sessie_genomen` / `sessie_genomen;aengenaem` → keep; bare `verwelkom` → drop. A small mixed-cue tail left unlabeled.

Stable patterns from review:

- Bare `verwelkom` → reject (81/81 in the human pass).
- Bare `sessie_genomen` (+ optional `aengenaem`) → keep (17c formula variants included).
- Sibling types (e.g. Generaliteits Rekenkamer) → out of R1 completeness; keep for later tracks as `other_appointment` when tagged.

## 4. Final selection (`aanstelling_selected`)

**3 820** unique resolution ids (≈ **18×** the 213 gold positives).

| Source | n | Share |
|--------|--:|------:|
| Gold (`aanstelling_labelled` positives) | 213 | 5.6% |
| Ingest cued, not shape-suspect | 2 827 | 74.0% |
| Ingest suspect → keep | 31 | 0.8% |
| Review cued, shape-ok | 479 | 12.5% |
| Review suspect → keep | 270 | 7.1% |

### Year coverage

| Window | n |
|--------|--:|
| Before 1705 | 615 |
| 1705–1795 | 3 192 |
| After 1795 | 13 |
| **Total** | **3 820** |

Median year **1748** (min 1621, max 1796). Density rises through the 18c (peak decades 1740s–1760s).

### Pre-1705 vs 18c (model score and cues)

18c-trained TF-IDF scores are **much lower** on pre-1705 keeps; review + cues carried R1 there, not the global probability.

| Slice | Selected n | Median `proba_aanstelling` | Typical entry path |
|-------|----------:|-----------------------------:|--------------------|
| Before 1705 | 615 | **~0.30** | Mostly review band `(0.15, 0.5]` |
| 1705–1795 | 3 192 | **~0.81** | Mostly ingest `p > 0.5` |

Hand **gold** before 1705 in `aanstelling_labelled` (rc5 / STEPR1): **13** rows — separate provenance from the review workbook.

**Review workbook** (`gold_pre1705` sheet): **125** rows with `review=keep` (years ~1621–1658 in current file), exported as `aanstelling_gold_pre1705_review`. **No id overlap** with the 13 rc5 gold rows (different anchors); treat as **additional** pre-1705 positives until merged in a future join step. Use **`Notes`** for concatenated resolutions.

Top `cue_hits` on selected rows differ: pre-1705 is **`sessie_genomen`-heavy**; **`creditief` / `op_den_heer`** are rarer than in 1705–1795. Treat 17c as a **template shift**, not “low quality” labels.

**New 17c gold scoring:** workbook `aanstelling_pre1705_gold_review_xlsx` (build via `scripts/build_pre1705_gold_review_xlsx.py`) — earliest years first among cue+ / review-band harvest rows. Use column **`review_snippet`** (`[YYYY-MM-DD (weekday)]` + text). Patch an existing file: `uv run python scripts/patch_pre1705_gold_review_snippets.py`. Rebuild keeps your `gold_pre1705` sheet and skips ids already reviewed there.

**Calibration (did review gold help early retrieval?):** after updating `aanstelling_gold_pre1705_review`, run:

```bash
uv run python scripts/eval_pre1705_gold_impact.py
```

Compares char `char_wb` centroid **213 STEPR1 gold only** vs **213 + review keeps** (equal rows vs **review-upweighted**, default `--review-weight 4` so ~70% centroid mass is 17c). Reports cosine to review texts and median harvest rank (pool year ≤ 1658). Metrics: `aanstelling_pre1705_gold_impact_metrics`.

**Impact (125 review keeps, harvest pool year ≤ 1658, n = 169 470):** vs 18c-only baseline (mean cos **0.4136**) — equal augment **0.4751** (+0.0615), median rank **23 863 → 9 733**; review-weight **4** augment **0.5329** (+0.1193), median rank **→ 4 997**. All 125 review ids in pool.

### Rough names

| | |
|--|--:|
| Rows with ≥1 rough name | 3 000 (78.5%) |
| Exactly 1 name | 2 006 |
| 2+ names | 994 |
| Holland-multi frame hits | 17 |

Name extractors cover *creditief op*, *op(den) heer*, *gecommitteert*, *deputeren*, Holland multi (*stonden te worden … weegens de Steeden*), and 17c *verwillecompt* / *gemelten heer*.

## 5. Takeaways

1. **Doel A (complete the list):** gold 213 → selected 3 820 after TF-IDF + cues + light review; residual neural pass not needed.
2. **Do not treat 17c as done from 18c training alone**, but review showed many early *gecommitteert / sessie genomen* rows are true positives and were kept.
3. **Opening *Ontfangen een missive* is shared** with null-decision receipts and referrals — motivates Track L (missive receipt with *geen resolutie*).
4. **Sibling appointments** (Rekenkamer, etc.) should stay out of this list but remain in harvest/review for a later type track.

## 6. Reproduce

```bash
uv run python -c "from data_io import load; s=load('aanstelling_selected'); print(len(s), s.selection_source.value_counts().to_dict())"
# Human workbook (includes selected sheet):
#   output/aanstelling_retrieval.xlsx
```
