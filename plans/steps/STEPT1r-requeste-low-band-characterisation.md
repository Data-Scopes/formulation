# STEPT1r — characterise the requeste low-score band before any L2 reduction

**Goal:** STEPT1q found requeste's `dag_frozen_score` is bimodal, not a smooth recall/FP tradeoff: at the frozen cut (4.5) gold splits into a **low band** (512/1380, score ≈4.5 = exactly 3 of 6 canonic slots matched, median 69 tokens) and a **high band** (841/1380, score ≈9.0 = all 6 matched, median 175 tokens), with the low band's share peaking at 0.52 in the 1760s (`docs/proofs/multi-template-registry/STEPT1q-formula-retrieval.md`, "Requeste: the FP is a cut artifact over a bimodal gold population"). Settle **why** before Doc B's L2 slot-ablation step: is the low band (a) a genuinely different, shorter requeste-opener wording that deserves its own canonic, (b) an OCR/spelling-variant-coverage gap in the existing cloud (cheaper fix: add variants, no new canonic), or (c) inherent brevity with no missing clause at all (nothing to split; the FP stays an accepted cost)? Splitting the type into two canonics, if (a), gets high recall *and* low FP instead of trading them — a better outcome than slot ablation on the single current type (Doc B's L2). Design: [`docs/formula-abstraction-design.md`](../../docs/formula-abstraction-design.md) (Doc B), point 4 ("a hand-written canonic can simply be wrong").

**Done when:** Part A (quantitative, no fetch) + Part B (text hand-read) both written up in proof NOTES with a named verdict (a) / (b) / (c) and a next-step recommendation; `requeste_low_band_profile_metrics` written; `data_io.check` clean.

**Mechanics, so the NOTES don't re-derive this:** the requeste canonic (`REQUESTE_CANONIC` in `formulation/requeste_formula_type.py`) tokenizes to 6 slots — `IS / ter / Vergaderinge / geleesen / de / Requeste` — **none marked optional** in the frozen cloud (`fit_requeste_presence_model()['cloud']['slots'][*]['optional']` is `False` for all six; checked this step). `align_dag`'s per-slot match score is `3.0*sim - 1.5`, so one exact-matched slot contributes 1.5 and six give the max 9.0. A row scoring exactly 4.5 is **not** a partial/fuzzy match smeared across all six slots — it is the DP finding a 3-slot run (e.g. `IS ... de Requeste`) as its global-max peak and never climbing back up, because continuing to align the remaining three slots only costs gap penalty and lowers the running score. So low-band rows are not noisier matches of the full phrase — they appear to be missing a contiguous 3-token chunk (plausibly `ter Vergaderinge geleesen`) from the text entirely, or have it in a form no injected variant covers.

## Part A — quantitative, already done this session (no fetch needed)

Reuses two datasets already on disk, joined by `id` — no `resolutions_flat`, no ES:

- `formula_retrieval_arms_scores` (STEPT1q) — the clean, post-re-pin 1380-row stratified requeste gold, with `dag_frozen_score` / `n_tokens` / `year` per row.
- `requeste_subtype_scores` (STEPT1l) — the full 66,657-row model-predicted-positive population (`pred==True`), with routing subtype (`referred` / `granted_direct` / `routing_unclear`) and lexical flags (`goedgevonden`, `handen`, `in handen`, `advies`, `gedelibereert_start`) already extracted when that dataset was built.

```bash
uv run pytest tests/test_requeste_low_band_profile.py -q
uv run python scripts/run_requeste_low_band_profile.py --fixture-only
uv run python scripts/run_requeste_low_band_profile.py
uv run python -m data_io.check
```

**Findings (recorded, not re-measured by you):**

- Band sizes: clean gold low 513/1380 under the ≤4.6 rule (0.372, CI 0.347–0.398), high 841/1380 (0.609). Score ≤4.5 is 512, which is STEPT1q's figure; the extra row scores 4.5909.
- `gedelibereert_start` (the decision-stage marker from STEPT1e/f, documented in `formulation/requeste_subtype_profile.py`) is the sharpest band separator found: **0.134 low-band vs 0.864 high-band**, on the full 66,657-row population — far more separating than routing subtype (among labelled rows, P(`granted_direct`\|low)=0.916 vs P(`granted_direct`\|high)=0.685; the other way, **31.3% of `granted_direct` rows are low-band and 65.1% are high-band**) or decade (on clean gold the low share peaks at 0.52 in the 1760s; on the full population it peaks at 0.397 in the 1700s and is 0.212 in the 1760s).
- `handen` / `in handen` / `advies` are all also markedly lower in the low band (≈0.03–0.04 vs ≈0.20–0.26) — consistent with low-band rows being shorter resolutions that skip the referral/advice clause too, not just the requeste-opener's own middle tokens.
- `n_words` (full population) and `n_tokens` (clean gold) agree: low-band median ≈69–72, high-band ≈175–187.

**Reading:** the low band is not explained by routing outcome (too weak a split) or period alone (varies but never approaches a clean cut) — it correlates most with the *absence of any later deliberation/referral language*, i.e. these are globally terser resolutions, and the requeste opener's own middle clause is plausibly one casualty of that general brevity, not a special case. This argues against a sharp "two openers" story and toward (b)/(c) over (a) — but Part A cannot see the actual text, so this reading is a prior for Part B, not the verdict.

## Part B — text hand-read (**done** 2026-10-22 after remount)

1. `resolutions_flat` ok. Sampled 20 low + 10 high from `load_clean_gold_bands()`; texts via `flat_texts` (no ES redraw).
2. Frozen cloud `align_dag` `matched_tokens`: low rows match `('OP'|'Op', 'de', 'Requeste')` at score 4.5 — collision with three slots of the long canonic, not a partial long-opener match.
3. Tally: **20/20 = (i)** middle clause absent. Full clean-gold head classifier: low **499/513 (0.973) `Op de Requeste`**, high **834/841 (0.992) `IS ter Vergaderinge …`**.
4. Verdict: **(a) real alternate short-form wording.** Consensus canonic is **`Op de Requeste`**, not the earlier guess `IS … de Requeste`. Proposed human name `op_de_requeste` / id `requeste_op_de`. Mint+calibrate is the *next* step after name confirmation (short opener = FP risk).

## Do not

- Re-fetch `rekest_es_gold` / re-run `stratified_gold_ids` against ES — the low-band ids are already known from `formula_retrieval_arms_scores`; only the text join (`flat_texts`, local parquet) is needed.
- Retrain or recalibrate the frozen requeste cloud/cut (4.5) in this step — characterisation only. Minting a second canonic or adding seed variants is the *next* step, gated on Part B's verdict.
- Conflate the 1380-row clean-gold sample and the 66,657-row predicted-positive population as one denominator — they answer different questions (sample-level band share vs population-level correlation) and have very different CI widths.
- Treat the `requeste_subtype` (referred/granted_direct) correlation as the explanation — it is real but weak (31% of `granted_direct` is high-band); do not report it as "the low band is granted_direct."

## Datasets registered

| Logical name | Tier | Contents |
|---|---|---|
| `requeste_low_band_profile_metrics` | scratch/semi | Part A: band sizes + CI, length-by-band, decade-by-band (clean gold); band × subtype, band × lexical flag, length, decade (full population) |

Registered in `data_manifest.toml`; `uv run python -m data_io.check` clean (Part A does not touch `resolutions_flat`).

## After this step

If Part B gives verdict (a): open a new step to mint + calibrate the second canonic. If (b): open a new step (or fold into a small follow-up) to extend the seed variants and recalibrate. If (c)/no majority: record the accepted-FP decision as final and close the requeste-opener line of work; Doc B's L2 ablation then applies to the single current canonic, if anything.

Clear the chat before the next step.
