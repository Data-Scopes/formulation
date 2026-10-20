# R2 — Pre-1705 aanstelling expansion (separate track)

**Status:** registered, **not started** — do not execute until explicitly chosen (active work stays Track L / Track F).  
**Parent:** judged R1 ([R1-aanstelling-retrieval.md](R1-aanstelling-retrieval.md)); reuses corpus and cues, different period and label semantics.

## Goal

Improve **recall and ranking** for *vergadering-aanstelling*–like whole resolutions in **`year < 1705`** on `resolutions_flat`, using R1’s **615 reviewed pre-1705 keeps** in `aanstelling_selected` as **high-recall exemplars**—not as new gold and not as proof of completeness.

Output (when run): a provenanced **candidate list** for human spot-check and optional merge into a period-specific inventory—distinct from `aanstelling_selected` (18c-weighted R1 freeze).

## Why a separate track

| R1 (done) | R2 (this track) |
|-----------|-----------------|
| Primary gold window 1705–1795; model + review tuned there | Pre-1705 HTR, sparser gold (**13** labelled positives before 1705) |
| Treat `resolutions_flat` row ≈ one act (adequate in 18c) | Same row grain, but **resolution separation ≤ ~70% at best** in earlier material—metrics and joins are **upper-bounded** |
| `aanstelling_selected` = frozen R1 completeness harvest | **615 pre-1705** rows = mostly **review-band** keeps (median `p ≈ 0.30`); use as **soft positives / k-NN seeds** |

Do **not** reinterpret R1’s 615 as verified 17c gold. Do **not** block Track L or M1 STEP2.

## Method (planned — char first, dense optional)

1. **Slice:** all `resolutions_flat` with calendar year &lt; 1705; exclude ids already in `aanstelling_selected` if evaluating *new* finds only.
2. **Hard evaluation set:** 13 pre-1705 rows in `aanstelling_labelled` with `label == aanstelling` (tiny but honest recall@K).
3. **Exemplars:** 615 pre-1705 `aanstelling_selected` (optionally cluster by `cue_hits` for medoids).
4. **Retrieval (primary):** char `char_wb` TF-IDF (same family as R1)—**k-NN to exemplars** and/or **period-specific refit** with down-weighted or PU-style use of the 615.
5. **Rerank:** existing [`formulation/aanstelling_cues.py`](../../formulation/aanstelling_cues.py) + Levenshtein on top-K (mirror char-window phrase harness).
6. **Optional residual:** GysBERT (or similar) **rerank top-K only** on pre-1705 slice—not a full-corpus embedding index until segmentation tier is documented.

Out of scope for R2: live Elasticsearch; mixing into L1 positives; formula `FormulaSearch`; presence session JSON (see side plan).

## Document grain and ledger (required when executing)

Every hit/candidate row should carry:

- `parent_id` — `resolutions_flat.id`
- `parent_kind` — `resolution_row` (derived unit, not session JSON)
- `segmentation_tier` — e.g. `weak_pre1705` (explicit cap ~70% separation)
- scores: char similarity, cue pass, optional dense rerank
- **no** silent promotion to gold without review

Session/region-first search for the same period remains the [presence side plan](../presence-lists-1630-1704-side-plan.md), not a substitute for R2.

## Done when (future)

- Logical name registered (e.g. `aanstelling_pre1705_candidates`) + `data_io.check`
- Holdout recall@K on 13 gold documented with decade breakdown
- Manual precision sample on top hits (stratified)
- Short write-up in `docs/DECISIONS.md`: char-only vs +embedding rerank

## Steps (placeholder — one per session when activated)

| Step | Done when |
|------|-----------|
| R2-0 | Scope + manifest placeholders; reproduce 615/13 counts from `aanstelling_selected` / `aanstelling_labelled` |
| R2-1 | Char k-NN / refit baseline on pre-1705 remainder; provenanced candidate parquet/jsonl |
| R2-2 | Cue + Levenshtein rerank; compare to R1 frozen scores on same slice |
| R2-3 | Optional dense rerank experiment; decision recorded |
| R2-4 | Human review sample → accept/reject policy for merging |

## Inputs (existing)

- `resolutions_flat`, `aanstelling_labelled`, `aanstelling_selected`, `aanstelling_cues`
- `aanstelling_pre1705_gold_review_xlsx` — human `gold_label` on **to_score** (earliest years first); feeds future gold expansion, not R1 freeze

## Outputs (register at R2-0 — not in manifest yet)

- `aanstelling_pre1705_candidates` (name TBD) — scratch-tier provenanced table
- `aanstelling_pre1705_metrics` (name TBD) — semi JSONL metrics
