# STEPT1f — Missive subtype characterisation (ontfangen+, 1780)

**Goal:** STEPT0-style profile of provisional missive subtypes under ontfangen+: `info_receipt` (L1) vs `decisionful_residual`. Not new formula types; not STEPT1e1.  
**Status:** **PASS** with caveat — `info_receipt` half is circular (L1 cues → L1 signature). Open question was always the decisionful residual → STEPT1g. Provenanced: `missive_subtype_metrics` / `_scores`.

**Sources:** `ontfangen_partition_scores` (STEPT1e), `formula_documents` flags, `resolutions_flat` word counts.

## 1. Universe

| Metric | Value |
|--------|------:|
| `n_ontfangen_plus` | 1397 |
| `n_missive` (kind filter) | **1297** |
| `n_non_missive_leakage` | 100 (onbekend 35, rekest 30, …) |
| frac missive of + | 0.928 |
| outcome join coverage | 0.977 |
| text join coverage | 1.0 |

## 2. Subtypes (missive ∩ ontfangen+)

| Subtype | n | frac | words med (q1–q3) | n_r1 | top flag combo |
|---------|--:|-----:|-------------------:|-----:|----------------|
| `info_receipt` | **641** | 0.494 | **37** (29–42) | 0 | `advertentie`+`geen_resolutie`+`ontfangen_start` (0.75) |
| `decisionful_residual` | **656** | 0.506 | **188.5** (131.5–282.5) | **27** | `gedelibereert_start`+`ontfangen_start` (0.12; long-tail combos) |

### Flag rates (outcome-joined)

| Flag | info | decisionful | Δ (dec − info) |
|------|-----:|------------:|---------------:|
| `geen_resolutie` | **0.964** | 0.045 | **−0.919** |
| `advertentie` | **0.841** | 0.267 | −0.573 |
| `goedgevonden` | 0.024 | **0.544** | **+0.521** |
| `gedelibereert_start` | 0.028 | **0.874** | **+0.846** |

## 3. Contrast

| Contrast | Value |
|----------|------:|
| words med Δ (decisionful − info) | **+151.5** |
| n_r1 in info / decisionful | 0 / **27** |

## 4. Gates

1. **Structural separation?** **Yes** — short null-receipt vs ~5× longer decisionful missives; near-complementary flag signatures (`geen_resolutie`/`advertentie` vs `gedelibereert`/`goedgevonden`). R1 appointments sit entirely in decisionful.
2. **One kind, two shapes?** **Yes** — both still ES `missive` under the same opener; not grounds for new ES kinds or accepted formula types. Leakage (100 non-missive ontfangen+) stays side count.
3. **Call:** Characterisation gap from the map for missive is **closed**. STEPT1e1 stays **parked** (flag rates already describe the two shapes; further flag bucketing would classify surfaces). Prefer next characterisation of **rekest** (dominant non-missive kind), or stop Track T until a named kind-support A is chosen. No new A from bag density alone.

## 5. Call

**PASS with caveat.**

1. `info_receipt` remeasures the L1 prototype (circular). Useful signal is residual size + length vs L1, not flag rates as typology.
2. **Next:** [STEPT1g](STEPT1g-residual-structure-probe.md) residual structure probe (probability ≠ typology).
