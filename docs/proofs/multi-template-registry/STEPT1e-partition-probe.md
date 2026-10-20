# STEPT1e — Ontfangen partition probe (1780)

**Goal:** Close STEPT1e0 gaps: ES `proposition_type` mix, flag rates, and ontfangen+ \ L1 residual structure on the presence universe. Typology call only — do not accept ontfangen as a formula type.

**Sources:** `formula_type_presence_scores` (1780), ES `mget` (lean), `formula_documents`, known sets (`aanstelling_selected`, `missive_receipt_labelled`, `advies_es_gold`). Provenanced: `ontfangen_partition_metrics` / `_scores`.

## 1. Counts

| Metric | Value |
|--------|------:|
| `n_resolutions` | 2796 |
| `n_ontfangen+` | **1397** |
| `n_ontfangen−` | 1399 |
| hit_rate | 0.500 |
| ES join coverage | 0.984 |
| `formula_documents` join coverage | 0.956 |

## 2. ES proposition_type mix

| Type | ontfangen+ n | + rate | ontfangen− n | − rate |
|------|-------------:|-------:|-------------:|-------:|
| missive | **1297** | **0.928** | 177 | 0.127 |
| rekest | 30 | 0.021 | **714** | **0.510** |
| onbekend | 35 | 0.025 | 89 | 0.064 |
| voordracht | 10 | 0.007 | 141 | 0.101 |
| rapport | 9 | 0.006 | 95 | 0.068 |
| other / (none) | … | | … | |

Missive contingency:

| | ont+ | ont− |
|--|-----:|-----:|
| ES missive | **1297** | 177 |
| not missive | 100 | **1222** |

- P(missive \| ont+) = **0.928**
- P(missive \| ont−) = 0.127
- P(ont+ \| missive) = **0.880**

**Gate 1:** Strong missive alignment, **not** identity (100 non-missive in +; 177 missive in −). Ont− is rekest-dominated.

## 3. Known sets

| Set | n (year) | ∩ ont+ | ∩ ont− |
|-----|---------:|-------:|-------:|
| R1 selected | 31 | **27** | 4 |
| L1 missive_receipt | 674 | **673** | 1 |
| advies ES gold | 31 | **0** | 31 |

L1 ≈ subset of ontfangen+ but only **48%** of + (673/1397).

## 4. Flags (exploratory — boilerplate surfaces, not outcomes)

Marginal rates (outcome-joined rows):

| Flag | ont+ | ont− | residual not-L1 |
|------|-----:|-----:|----------------:|
| `geen_resolutie` | **0.488** | 0.089 | **0.060** |
| `advertentie` | 0.534 | 0.083 | 0.264 |
| `goedgevonden` | 0.311 | **0.808** | **0.557** |
| `rapport_start` | 0.071 | 0.178 | 0.115 |
| `ontfangen_start` | 0.897 | 0.186 | 0.895 |
| `handen` / `in handen` | ~0.07 | ~0.16–0.17 | ~0.13 |

Top combinations:

| Partition | top combo | n | rate |
|-----------|-----------|--:|-----:|
| ontfangen+ | `advertentie` + `geen_resolutie` + `ontfangen_start` | 519 | 0.380 |
| ontfangen+ | `gedelibereert_start` + `ontfangen_start` | 80 | 0.059 |
| ontfangen− | `gedelibereert_start` + `goedgevonden` + `request_start` + `vergaderinge_start` | 121 | 0.093 |
| residual | `gedelibereert_start` + `ontfangen_start` | 78 | 0.111 |
| residual | `advertentie` + `gedelibereert_start` + `ontfangen_start` | 64 | 0.091 |
| residual | `gedelibereert_start` + `goedgevonden` + `ontfangen_start` | 48 | 0.068 |

## 5. Residual ontfangen+ \ L1

| Metric | Value |
|--------|------:|
| n | **724** (0.518 of +) |
| top ES type | missive **656** (0.906) |
| n_r1 in residual | 27 |
| n_advies_gold | 0 |
| flag shape | low `geen_resolutie` (0.06); high `goedgevonden` (0.56); top = `gedelibereert` ± decision |

**Gate 2:** Residual is still missive-opening, but **decisionful** (gedelibereert/goedgevonden), not L1 info-receipt.

## 6. Discourse-stage recognition (partial)

Hypothetic structure: opening → (expose) → decision → (elaboration/defer) → (execution).

| Stage | Evidence today | Strength |
|-------|----------------|----------|
| Opening | `ontfangen_start` / `requeste`; T1c opening zone | **Strong** |
| Expose | `rapport_start`, `advies`, `geexamineert` | Weak–medium |
| Decision | `gedelibereert_start` + `goedgevonden` / `verstaen`; null = `geen_resolutie` | **Strong as flags** (not outcome truth) |
| Elaboration / defer | `handen` / `in handen` | Medium |
| Execution | `betalinge`, `versonden`, `paspoort`, … | Weak |

Under the same opener, STEPT1e already sees the **decision vs null-decision** fork (full + ≈ info path; residual ≈ decisionful).

## 7. Call

**PASS** (typology-facing; ontfangen still provisional).

1. Ontfangen+ = missive-aligned **opening partition** — not ES-missive equality and not L1.
2. Under that opener: L1 ≈ **null-decision / info** half; residual ≈ **decisionful missives**.
3. Typology needs an **opening/partition axis** plus a **decision-stage axis** (flag combinations today).
4. Do **not** accept `ontfangen_start` as a formula type. Flags ≠ archival outcomes. Ordered discourse spans not measured yet.
5. **Next (superseded):** Was STEPT1e1 flag sieve. **STEPT1-map** parked e1 — typology before classify; next = characterisation gap from the map.
