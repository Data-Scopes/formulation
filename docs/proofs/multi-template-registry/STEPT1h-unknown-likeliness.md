# STEPT1h — Unknown-likeliness POC (1780)

**Goal:** Score year-slice resolutions by unexplainedness under the accepted cover set.  
**Status:** **PASS** (band + cover sensible; no new types).

**Sources:** `formula_type_presence_scores`, known sets (`aanstelling_selected`, `missive_receipt_labelled`, `advies_es_gold`). Provenanced: `resolution_unknown_metrics` / `_scores` / `_sample`.

**Doctrine:** [`plans/milestones/T1-unknown-first.md`](../../../plans/milestones/T1-unknown-first.md).

## 1. Universe / band

| Metric | Value |
|--------|------:|
| `n_universe` | **2796** |
| `n_high_unknown` (`unknown_score == 1`) | **2015** |
| `frac_high_unknown` | **0.721** |

Score hist: `0.50` → 28 (2 cover hits); `0.75` → 753 (1 hit); `1.00` → 2015. No row hits ≥3 axes.

## 2. Cover axis hits

| Axis | n | frac |
|------|--:|-----:|
| L1 | 674 | 0.241 |
| R1 | 31 | 0.011 |
| appointment present | 28 | 0.010 |
| advies (present ∨ gold) | 76 | 0.027 |

L1 is the only large cover pocket. Appointment ≈ R1 (sparse, aligned). Advies thin. Matches prior Track T.

## 3. Gates

1. **Band size triage-worthy?** Yes — majority unexplained under a *thin* accepted cover set is expected, not a bug. Not empty; not “everything covered.”
2. **Cover axes sensible?** Yes — L1 dominates known mass; sparse As stay sparse.
3. **Call:** High-unknown (2015) is too wide to characterise blindly. Next = **stratify / fingerprint** the high-unknown band before reading, or a cheap sub-band (e.g. length × ontfangen±) — not a new A from `n=2015`.

## 4. Call

**PASS.** Unknown-first scorer works. Cover is intentionally thin → large triage pool. Do **not** mint types from the band. Next session: fingerprints bridge **or** stratified characterisation of a *slice* of high-unknown (not the whole 2015).
