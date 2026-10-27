# STEPT1r — Requeste low-score band (NOTES)

**Status:** part A + part B written (2026-10-22); **call confirmed** — name `op_de_requeste` / id `requeste_op_de`; mint+calibrate is the next step (not this one). Letter/missive likely has a parallel short vs receipt opener — park until after requeste mint.  
**Guide:** [`plans/steps/STEPT1r-requeste-low-band.md`](../../../plans/steps/STEPT1r-requeste-low-band.md)  
**Metrics:** `requeste_low_band_profile_metrics`. Tests: `tests/test_requeste_low_band_profile.py` 2 passed. `resolutions_flat` ok after remount.

## Doctrine (do not skip)

- Naming a new type/blueprint is a **human** decision after reading.
- Scaffolding (standard openers/decisions) ≠ type-carriers (often rarer, easier to find once named).
- Wording drift → variants / period keys, not automatic new ids.

## Part A — quantitative

```bash
uv run python scripts/run_requeste_low_band_profile.py
```

| Check | Result |
|-------|--------|
| n_gold / band counts | Clean gold n=1380. Low (≤4.6) **513** (0.372, CI 0.347–0.398), mid 26, high (≥8) **841** (0.609). Of the 513, **512 have score ≤4.5** (505 exactly 4.5) and one scores 4.59 — that is STEPT1q’s 512, plus the ≤4.6 edge. Full predicted-positive population n=66,657: low 17,111 (0.257), mid 2,711 (0.041), high 46,835 (0.703). |
| length median low vs high | Clean gold `n_tokens` 69 vs 175. Full population `n_words` 72 vs 187. |
| decade share of low (1760s peak?) | **On clean gold, yes:** low share peaks at **0.520 in the 1760s** (0.293 in the 1700s, 0.257 in the 1790s). **On the full population, no:** 1760s low share is 0.212; the peak is the **1700s at 0.397**. Same length story, different period story. |
| routing subtype × band | Among rows with a subtype (942/17,111 low-band, 5.5%, have none). Low: granted_direct 0.916 / referred 0.040 / routing_unclear 0.044. High: 0.685 / 0.260 / 0.054. Of 47,274 `granted_direct` rows, **0.651 high / 0.313 low**. Real association, not a partition. |
| `gedelibereert_start` × band | Full population. `gedelibereert_start` **0.134 low vs 0.864 high**. `handen` 0.038 vs 0.250, `in handen` 0.036 vs 0.242, `advies` 0.027 vs 0.197. `goedgevonden` does not move (0.902 vs 0.901). |

**Gate 1.** Length and the 1760s peak reproduce STEPT1q on the clean-gold sample. The full population agrees on length and disagrees on decade.

**Gate 2.** Orthogonal to the STEPT1l routing cut. Tracks absence of later deliberation/referral language together with shorter texts.

## Part B — hand-read (`resolutions_flat` mounted)

Stratified sample from already-labelled clean-gold ids (`load_clean_gold_bands()`): **20 low** (10×1760s + 10×1700/1780/1790) and **10 high** controls. Texts via `flat_texts`. Align with the frozen requeste presence cloud (`fit_requeste_presence_model`); do not change `score_text`.

| Band | n sampled | Readable short-form? | Cloud miss? | Noise? |
|------|----------:|----------------------|-------------|--------|
| low | 20 | **Yes — different opener** `Op`/`OP de Requeste van …` | No (middle clause not present to miss) | No |
| high | 10 | Full `IS ter Vergaderinge geleesen/gelesen/geleezen de Requeste` | No | No |

**Per-row tally (guide (i)/(ii)/(iii)) on the 20 low rows:** **20/20 = (i) middle clause literally absent.** None are (ii) uncovered variant or (iii) DP miss. High controls: 10/10 full six-slot match at score 9.0.

**What the short form actually is (not the guide’s hypothesized `IS … de Requeste`):** every low sample opens with **`Op`/`OP de Requeste van …`**, then typically jumps to a decision formula (`IS na voorgaande deliberatie goedgevonden …`). The long canonic’s middle (`ter Vergaderinge geleesen`) is not clipped — it was never there.

**Why frozen score lands at 4.5:** with the frozen cloud, a typical low row matches `('OP', 'de', 'Requeste')` (span at the head) → score 4.5. `OP` collides with the `IS` slot; `de Requeste` matches slots 4–5. So the low band is not a weak match of the long opener — it is a **short opener colliding with three slots of the long canonic**.

**Population check on all 1,380 clean-gold rows** (flat join, head-token classifier):

| band | `op_de_requeste` | `is_ter_vergaderinge_geleesen` | other |
|------|-----------------:|------------------------------:|------:|
| low (513) | **499 (0.973)** | 0 | 14 |
| high (841) | 0 | **834 (0.992)** | 7 |
| mid (26) | 0 | 4 | 22 |

The bimodal score split **is** an opener bipartition on clean gold.

## Call (human)

- [ ] `keep_one_type_accept_fp_tradeoff`
- [x] `split_short_form_subtype_after_human_name` — **confirmed** name: **`op_de_requeste`** (id `requeste_op_de`; canonic `Op de Requeste`)
- [ ] `characteristics_only_no_new_id`

**Verdict:** **(a) real alternate short-form wording.** User confirmed the split and name (2026-10-22).

**Not this step:** mint/calibrate, extend long-opener seeds, or Doc B L2. **Next step** = mint + calibrate `requeste_op_de` (watch FP: three-token opener is loose). Expect a **parallel short-vs-receipt split for letters/missives** later (user note) — do not open that until the requeste short opener is measured; STEPT1q already saw a missive score cliff with almost all gold in the high band, so the letter analogue may be rarer or differently shaped.

Notes: Part A’s “terseness” prior was right about length and missing deliberation language, wrong about mechanism — the opener itself differs.
