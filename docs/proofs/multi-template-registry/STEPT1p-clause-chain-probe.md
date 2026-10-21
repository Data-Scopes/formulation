# STEPT1p — Clause-chain probe (NOTES)

**Status:** done (2026-10-21). **G1 FAIL, G2 PASS** — and the two results are the same fact seen twice, which corrects the design's premise rather than confirming it. No promotion, no registry change, no new accepted type. Design: [`docs/resolution-graph-design.md`](../../resolution-graph-design.md).

```bash
uv run pytest tests/test_clause_chain.py -q
uv run python scripts/run_clause_chain_probe.py --year 1780                     # run 1
uv run python scripts/run_clause_chain_probe.py --year 1780 --per-clause-cuts   # run 2
uv run python -m data_io.check
```

## Run 1 — shared frozen cut (blocked, my error)

Both clause nodes inherited the frozen STEPT1a cut of 6.0.

| clause | cut | hits / 2796 |
|---|---:|---:|
| welkom | 6.0 | 28 |
| sessie | 6.0 | **0** |

Max chain length 1 ⇒ zero multi-clause chains ⇒ G1 fails trivially (`collapse_factor` 1.0) and **G2 could not be evaluated at all**.

This was predictable before running and I missed it. `docs/DECISIONS.md` already records, from the STEPT1a welkom-bootstrap fix: *"p20 cut rises to 6.0 (perfect welkom); **sessie max ≈3 never clears** — scoring is welkom-led."* The 6.0 cut was calibrated on `max(welkom, sessie)`, so per clause it is strictly harder than the type-level test ever was, and sessie cannot fire by construction. The step guide's "do not recalibrate" lock — written to prevent scope creep — made the probe unable to measure its own headline gate. Recorded rather than quietly re-scoped.

## Run 2 — per-clause cuts (the actual measurement)

Each clause calibrated on its **own** holdout p20 (same rule as the type-level cut, applied per clause). `appointment_installation`'s frozen 6.0 is untouched everywhere else; these are new cuts for two new clause nodes.

| clause | cut | cut rule | hits / 2796 | median mid_norm | modal zone |
|---|---:|---|---:|---:|---|
| welkom | 6.0 | p20_own_clause_holdout | 28 | 0.904 | close |
| sessie | **3.0** | p20_own_clause_holdout | 46 | 0.985 | close |

sessie's own p20 landing at 3.0 confirms the DECISIONS note quantitatively.

| chain | support |
|---|---:|
| (empty) | 2750 |
| `welkom → sessie` | 28 |
| `sessie` | 18 |
| `welkom` alone | **0** |

## Gates

| Gate | Result |
|---|---|
| **G1** chains > bags, ≥10% of resolutions in a multi-chain bag | **FAIL** — `n_chains == n_bags == 3`, collapse_factor 1.0, frac_multi **0.0** |
| **G2** support-weighted dominant_order_frac ≥ 0.80 | **PASS** — **1.0** (28/28 are `welkom → sessie`, 1 of 2 possible orders observed) |
| **G3** sub-patterns differ on an independent property | **PASS** — median n_words: both **74**, sessie_only **270**, neither **151** |
| **G4** independence vs partition | lift `P(sessie\|welkom)/P(sessie)` = **60.8**, `P(sessie\|welkom)` = **1.000** exactly |

**Order is real, not a tie-break artifact.** `chain_of` breaks ties on `clause_id`, which would yield `(sessie, welkom)` alphabetically; all 28 observed chains are `(welkom, sessie)`, so the order comes from genuine `start_idx` differences. Independently corroborated by the spans themselves (welkom mid_norm 0.904 < sessie 0.985).

## What this means — the design premise needs correcting

**G1 fails precisely because G2 passes perfectly.** A deterministic order carries zero information beyond the unordered set: if welkom is *always* before sessie, then knowing the chain tells you nothing the bag didn't. Chains can only beat bags where order **varies** — which the design note implicitly assumed and did not state.

So the appointment case does **not** establish "chains > bags." What it establishes is narrower and still useful: **the appointment skeleton is rigid** (welkom always precedes sessie, and never occurs without it). For chain-over-bag gain, the design needs cases with one of:
1. **Order variation** — the same clause set appearing in different orders across resolutions;
2. **Clause multiplicity** — the same clause twice (two missives received), which a tuple-of-ids currently loses (design note open question 2);
3. **Position variation** — a clause whose zone differs by type (an opener vs a closing use of the same skeleton).

None of those are present in a rigid 2-clause family. The advertentie/null-decision case is a better test on criterion 3, since a close-clause plus an opener gives two clauses with genuinely different zone anchors.

## Second finding (independent of the chain question)

At clause granularity the appointment family reads as **`sessie` backbone + optional `welkom`**, not the reverse:

- `P(sessie | welkom) = 1.000` — welkom *never* fires without sessie (0 welkom-only chains).
- 18 of 46 clause-level hits (39%) are **invisible to the type-level detector**, which only fires when `max(welkom, sessie) ≥ 6.0` — i.e. effectively when welkom ≥ 6.0, since sessie tops out near 3.
- By the design note's own discovery rule, welkom's presence is therefore a **variant marker on a sessie backbone**, not a separate type.

This inverts STEPT1a's working reading ("scoring is welkom-led"). That reading was true *of the collapsed scorer at the frozen cut*; at clause granularity, sessie is the clause that is always there.

**Do not over-read it.** Alternative explanation that this probe cannot exclude: sessie's cut of 3.0 is weak, and the 18 sessie-only resolutions have a median length of **270 words** vs 74 for the both-clause group — more consistent with a short sessie-like span matching incidentally inside long unrelated resolutions than with 18 genuinely missed appointments. Deciding between "recall gain" and "weak-cut noise" needs a hand-read of those 18, which was not done.

## Run 3 — on human gold (corrects run 2's unvalidated claims)

1780 holds **exactly 1** gold appointment, so the year slice was the wrong universe. Re-run on `aanstelling_labelled` (the repo's original human-harvested delegate collection, `delegates_resolutie_refs` rc5 → STEPR1): 213 gold positives (1685–1791) + 2130 overig. `uv run python scripts/run_clause_chain_probe.py --on-gold --per-clause-cuts`

| clause | cut | recall on gold | FP on overig |
|---|---:|---:|---:|
| sessie | 3.0 | **0.930** | 0.022 |
| welkom | 6.0 | 0.784 | 0.004 |

| gold chain | support | frac of gold |
|---|---:|---:|
| `welkom → sessie` | 167 | 0.784 |
| `sessie` | 31 | 0.146 |
| (empty — missed) | 15 | 0.070 |
| `welkom` alone | **0** | 0.000 |

**The sessie-backbone finding survives human gold.** Zero welkom-only chains among 213 real appointments; sessie recall 0.930 vs welkom 0.784. And run 2's worry that sessie-only was weak-cut noise is **refuted**: sessie-only is 14.6% of *gold* appointments (31 rows) at an overig FP of just 2.2%, so it is a real appointment variant, not incidental matching.

**Concrete consequence:** the frozen type-level detector fires only when `max(welkom,sessie) ≥ 6.0`, i.e. effectively on welkom — recall 0.784. The sessie clause at its own cut reaches **0.930 at 2.2% FP**, so decollapsing buys **+15pp recall** on the human gold. That is a usable result, independent of the (failed) chains-beat-bags question: order stability stays 1.0 and chains still equal bags (4 == 4).

## What could not be checked

- **Known-case validation did not run.** `aanstelling_review_labels` (`keep` 301 / `drop` 107, 1621–1796) does not overlap the 1780 slice usefully: 0 rows joined for the `both` and `sessie_only` groups, 2 for `neither` (both `drop`). So G3's separation rests on length alone, with no human label behind it.
- **Vergadering vs rekenkamer remains untestable** — those labels were never exported (see design note "What is not available").

## Next

1. **Hand-read the 18 sessie-only resolutions** — cheapest way to settle recall-gain vs weak-cut noise, and it decides whether the sessie-backbone finding survives.
2. **Advertentie / null-decision close clause** — the better chain test (two clauses with different zone anchors ⇒ position variation), and it breaks STEPT1f's circular L1 caveat. Needs one new clause cloud.
3. Design note amendment: state the order-*variation* precondition explicitly, and promote open question 2 (multiplicity) since a rigid-order family makes tuple-of-ids provably lossless and therefore pointless.
