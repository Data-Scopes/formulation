# STEPT1g — Decisionful residual structure probe (1780)

**Goal:** Structure / inventory inside missive ∩ ontfangen+ \\ L1 — shapes, not probability subtypes.  
**Status:** **PASS** (structure inventory + sample reading).

**Constraint:** Probability is not typology. A formula type’s hit rate does not rank usefulness — ubiquitous = filler / no signal; interesting structure is **sparse**. STEPT1f `info_receipt` was circular (L1 cues → L1 signature); this residual was the open question.

**Sources:** `ontfangen_partition_scores`, `formula_type_presence_scores`, `formula_documents`, `resolutions_flat`. Provenanced: `residual_structure_metrics` / `_scores` / `_sample`.

## 1. Universe

| Metric | Value |
|--------|------:|
| `n_residual_missive` | **656** |
| non-missive residual leakage | 68 |

## 2. Known pockets (accepted evidence)

| Pocket | n |
|--------|--:|
| appointment present | **26** |
| advies present | 6 |
| R1 selected ∩ residual | 27 |
| appointment ∩ R1 | 26 |

Appointment ≈ R1 under residual — sparse, sharp, already an accepted formula type.

## 3. Surface-combination catalogue (not types)

| Summary | Value |
|---------|------:|
| `n_unique_combos` | **177** |
| share in top 5 / top 20 | 0.36 / 0.62 |

Top combos (inventory only — **filler concentration**, not subtype ids):

| n | flags |
|--:|-------|
| 78 | `gedelibereert_start` + `ontfangen_start` |
| 64 | `advertentie` + `gedelibereert_start` + `ontfangen_start` |
| 47 | `gedelibereert_start` + `goedgevonden` + `ontfangen_start` |
| 22 | `advertentie` + `geen_resolutie` + `ontfangen_start` (L1 leakage / near-null under residual labels) |
| 21 | `advertentie` + `gedelibereert` + `goedgevonden` + `ontfangen` |

Long tail (177 distinct sets) — do not mint types from the head.

## 4. Accepted-formula bags (inventory)

| Bag shape | n |
|-----------|--:|
| `ontfangen_start` alone | **624** |
| `appointment_installation` + `ontfangen_start` | **26** |
| `advies_geleesen` + `ontfangen_start` | 6 |

**624 solo opener = filler star.** Bag density is not signal.

## 5. Shapes from sample reading (`residual_structure_sample`, n=21)

| Shape (working name) | Evidence | Covered by accepted A? |
|----------------------|----------|------------------------|
| **Filler receipt→deliberate** | Long/mid college missives: *houdende advis/berigt op de Requeste…*; envoy *advertentie* then decide; solo `ontfangen_start` bag | No — and should **not** become a type from n≈600 |
| **Creditif / installation** | *houdende creditif op den Heer…* → welkom/sessie; short–mid; appointment bag | **Yes** — `appointment_installation` (≈ R1) |
| **Sparse unexplained: provincial nomination** | e.g. Overijssel/Stad en Lande voordracht-like under missive opener (Muyden; Lewe → admiralty) | No accepted A |
| **Sparse unexplained: procedural enclosure** | Revisie/pandkeering/goederenlijst missives | No |
| **Sparse: advies∩ontfangen** | n=6 presence pocket | Thin; do not promote from n alone |

## 6. Gates

1. **One shape or several?** Several — but **one dominant filler mass** (solo ontfangen + gedelibereert boilerplate) plus **sparse** interesting pockets.
2. **Covered vs unexplained?** Appointment/creditif covered. Unexplained sparse: nominations, procedural enclosures, thin advies∩ontfangen. Filler mass is not a typology target.
3. **Call?** See §7.

## 7. Call

**PASS.**

1. Residual is mostly **trivial filler** under the same opener; interesting structure is **sparse** (appointment first).
2. Hit rate / top-combo rank ≠ usefulness — same as “too many, no signal.”
3. Do **not** run STEPT1e1 or invent a “decisionful missive” type from `gedelibereert`+`ontfangen`.
4. **Next (after clear chat):** kind-support or characterisation for a **named sparse** unexplained shape (default lean: **provincial nomination / creditif-adjacent voordracht under missive**), or park Track T. Not rekest-by-rate; not bag-density A.
