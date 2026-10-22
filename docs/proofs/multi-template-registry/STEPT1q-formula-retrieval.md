# STEPT1q — Single-formula retrieval + discrimination (NOTES)

**Status:** done (2026-10-22) for G1–G4; **G5 not run**, span hand-read (STEPT1q2) not run. **G1 answered: the substring does not win.** Slot-cloud/DAG holds 0.985 recall at FP 0.031 on missive against the best substring's 0.995 at 0.133. Design: [`docs/formula-abstraction-design.md`](../../formula-abstraction-design.md) (Doc B). Guide: [`plans/steps/STEPT1q-formula-retrieval.md`](../../../plans/steps/STEPT1q-formula-retrieval.md).

```bash
uv run pytest tests/test_formula_retrieval_arms.py -q            # 29 passed
uv run python scripts/run_formula_retrieval_arms.py --type missive  --per-year 15 --boot-per-year 100 --neg-n 2500
uv run python scripts/run_formula_retrieval_arms.py --type requeste --per-year 15 --boot-per-year 100 --neg-n 2500
uv run python -m data_io.check
```

Gold is the clean post-re-pin stratified sample (`full_resolutions-2025-02-20`, 1380/1380 joined per type), **not** the stale `*_es_gold` sets. Negatives are verified individually against the pinned index. `dag_clean_boot`'s cloud is bootstrapped from a disjoint 7,820-text pool, so the eval rows never inform cloud or cut.

## Missive — gold 1380, negatives 1154, both DAG cuts 6.0

| arm | recall | recall CI95 | FP | FP CI95 | FP events |
|---|---:|---|---:|---|---:|
| substring_wording | 0.9587 | 0.9469–0.9680 | 0.2071 | 0.1847–0.2314 | 239/1154 |
| substring_scheme (`tfange`) | 0.9949 | 0.9896–0.9975 | 0.1326 | 0.1142–0.1534 | 153/1154 |
| tfidf_window (0.400) | 0.6870 | 0.6620–0.7109 | 0.0425 | 0.0323–0.0557 | 49/1154 |
| tfidf_window_p20 (0.382) | 0.8000 | 0.7781–0.8203 | 0.0494 | 0.0383–0.0635 | 57/1154 |
| **dag_frozen** | 0.9877 | 0.9804–0.9923 | **0.0321** | 0.0233–0.0439 | 37/1154 |
| **dag_clean_boot** | 0.9848 | 0.9768–0.9900 | **0.0312** | 0.0226–0.0429 | 36/1154 |

## Requeste — gold 1380, negatives 1984, cuts frozen 4.5 / clean 3.0

| arm | recall | FP | FP CI95 | FP events |
|---|---:|---:|---|---:|
| substring_wording | 0.9848 | 0.0973 | 0.0850–0.1111 | 193/1984 |
| substring_scheme (`op\s?[td]+e reques`) | **0.0000** | — | — | **inapplicable** |
| tfidf_window (0.400) | 0.4254 | 0.0151 | 0.0106–0.0215 | 30/1984 |
| tfidf_window_p20 (0.127) | 0.8000 | 0.3609 | 0.3400–0.3823 | 716/1984 |
| dag_frozen | 0.9949 | 0.1815 | 0.1651–0.1990 | 360/1984 |
| dag_clean_boot | 0.9964 | 0.3669 | 0.3460–0.3884 | 728/1984 |

`substring_scheme` scored **0/1380** gold and is marked `applicable: false`. Its phrase is the 17c form *op de requeste*; the 18c canonic is `IS ter Vergaderinge geleesen de Requeste`. This is not a measured result, it is an inapplicable arm — and incidentally a live instance of Doc B point 4 (*a hand-written canonic can simply be wrong*). It is excluded from `deltas` and from the unanimity denominator (`fp_overlap.arms_counted`).

## Gates

| Gate | Result |
|---|---|
| **G1** substring vs DAG (judged on `dag_clean_boot`) | **PASS — substring loses.** `substring_wording` is worse on both axes (−0.026 recall, +0.173 FP). `substring_scheme` "trades": +0.010 recall for **+0.106 FP**, i.e. 4.3× the false positives. Operating point: the DAG. |
| **G2** any arm clears FP ≤ 0.05 for requeste | **Yes, but only at ~0.62 recall.** `dag_frozen` at cut 6.3 gives FP 0.0358 (CI 0.0285–0.0449, 71/1984) at recall 0.625. At its frozen 4.5 it is 0.1815. So the confound is **not** arm-independent — it is a cut-and-population problem (see below). |
| **G3** span agreement | **PASS, all three criteria, both types.** DAG↔DAG IoU median **1.000**; DAG-in-window containment 0.982 (missive) / 1.000 (requeste); anchor-in-DAG 0.9947 / 0.9948. Midpoint offsets 0.5–7.5 tokens, well inside the 16-token window. The STEPT1q2 hand-read can stay at ≈30 rows. |
| **G4** unanimous FPs | missive **0.0977** of 307 firing negatives (~30 rows fired by all six arms) — residual gold-label gaps worth a look. requeste **0.0184** of 815 — FPs are arm-specific slop there. No promotion or gold edit taken. |
| **G5** sampling robustness | **NOT RUN.** Both runs are `systematic_id_asc`. The systematic-vs-random comparison is still owed; until then every rate here inherits whatever bias lowest-id-per-year selection carries. |
| **G6** pass/fail written with CIs | this file |

## G1 in context: the premise of Doc B point 2 was wrong

Doc B recorded STEPT1n's "model 0.887 vs substring 0.915" as evidence the structured model might lose. That comparison was **recall-only, on gold that was ~31% mislabelled**. On clean gold the model is at 0.985–0.988, and once FP enters the comparison the substring's apparent edge inverts. The substring never won; the measurement was incomplete. Doc B's abstraction ladder does not need a rev 3 on these grounds — L2 reduction remains worth pursuing.

## Requeste: the FP is a cut artifact over a bimodal gold population

Cut sweep on `dag_frozen`, computed from the saved per-row scores (no re-run):

| cut | recall | FP | FP events |
|---:|---:|---:|---:|
| 4.5 (frozen) | 0.9949 | 0.1815 | 360 |
| 4.6 | 0.6283 | 0.1134 | 225 |
| 5.2 | 0.6261 | 0.0519 | 103 |
| 6.3 | 0.6254 | 0.0358 | 71 |
| 8.0 | 0.6094 | 0.0020 | 4 |
| 9.0 | 0.6043 | 0.0005 | 1 |

Recall collapses 0.995 → 0.628 between cut 4.5 and 4.6, then sits flat for four more points of cut while FP falls by two orders of magnitude. That is not a tradeoff curve, it is **two populations**:

| band (`dag_frozen_score`) | n of 1380 | median tokens |
|---|---:|---:|
| low (≈4.5) | 512 | **69** |
| mid | 27 | 175 |
| high (≥8) | 841 | 175 |

The low band is half the length of the high band, and its share of gold varies with period — ~0.26–0.29 at both ends of the century, peaking at **0.52 in the 1760s**:

| decade | 1700 | 1710 | 1720 | 1730 | 1740 | 1750 | 1760 | 1770 | 1780 | 1790 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| low-band share | .293 | .253 | .273 | .333 | .487 | .507 | .520 | .440 | .273 | .257 |

So STEPT1k's "decision-type confound" is better described as: **~37% of ES-labelled rekest are short-form, score at the detector's floor, and sit where the negatives live.** Missive shows the same cliff shape (cut 4.5 → 4.8 moves FP 0.846 → 0.048 at recall ≥0.99), but with almost all its gold in the high band, which is why its gate passes outright.

**Operating point chosen (user call): cut 4.5, FP 0.18 accepted.** The alternative is not slightly less recall but losing 512 of 1380 instances; a known, filterable 18% beats a silent 37% miss for building an inventory of one formula.

## The stale-bootstrap concern is retired

Cut-matched at 9.0 the two clouds are equivalent: `dag_frozen` FP 0.0005 at recall 0.604, `dag_clean_boot` FP 0.0000 at 0.597; and DAG↔DAG span IoU is 1.000. The entire frozen-vs-clean difference was the cut (4.5 vs 3.0), not cloud quality learned from mislabelled text. Arm 4 was still worth building — that is how we know.

## Caveats and known defects

1. **`recall_matched` in the metrics is inapplicable — do not quote it.** It derives a cut from the gold-score quantile, but DAG gold scores spike at a single value, so the cut overshoots: asking missive for 0.687 recall still yields 0.9877, and requeste for 0.4254 yields 0.6043. The cut sweep above is the honest instrument. Same degenerate-score-distribution effect STEPT1n and STEPT1a recorded ("cut lands at the cloud's own score max").
2. **`tfidf_window_p20` is not a fair TF-IDF result for requeste.** p20 on gold window scores calibrated to 0.127, which is why FP hit 0.361. The frozen 0.400 belongs to `opening_requeste_18c`, a different template. Neither threshold is right for these types; a proper TF-IDF arm needs its own calibration target.
3. **Underpowered figures were corrected mid-step.** The first run used 226 clean negatives (Wilson half-width ±0.026 against a 0.05 gate) and gave missive FP 0.0575; the recorded 2026-10-21 recheck gave 0.018 on a different 226-negative draw (Fisher p=0.045). The powered value is 0.031. Both earlier figures were noise around it. `--neg-n` default is now 2500 (~1100 clean after the ~55% actually-target-type drop).
4. **Full `*_es_gold` re-fetch still owed.** Not a prerequisite here — this step never loads those sets — but required before they are used downstream.
5. **Systematic within-year sampling** (lowest ids per year), inherited from the recheck sampler. See G5.

## Next

**STEPT1r — characterise the 512-row low band before any L2 reduction.** If the short-form requesten are a distinguishable subpopulation (clipped opener, period-weighted), splitting the type gets high recall *and* low FP instead of trading them, which is a better outcome than any slot ablation on the current single type. Doc B's L2 reduction then applies per sub-type.

Optional, cheap, still owed: G5 (`--random-within-year`), and `build_span_review_xlsx.py` → STEPT1q2 hand-read (≈30 rows, since G3 passed).
