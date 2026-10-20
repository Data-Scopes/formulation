# STEPT1e0 — Ontfangen population inventory (1780)

**Goal:** Consolidate what we already know about the composition-root population before a typology-facing partition probe. No new scorer; no live ES in this step.

**Sources:** `formula_type_presence_*` (full 1780), `formula_type_position_*`, `formula_type_composition_graph_*` (limit 200), `typology_structural_profile` (STEPT0), datasheet `ontfangen_start`, cheap id joins to `aanstelling_selected` / `missive_receipt_labelled` / `advies_es_gold`.

## 1. Counts (presence, full year)

| Metric | Value | Source |
|--------|------:|--------|
| `n_resolutions` | 2796 | `formula_type_presence_metrics` year=1780, limit=null |
| `n_ontfangen+` | **1397** | present at opening cut |
| hit_rate | **0.4996** | |
| `n_ontfangen−` | 1399 | 2796 − 1397 |
| Solo bag `{ontfangen_start}` | 1365 (0.488 of year) | bags.top_patterns |
| `{ontfangen, appointment}` | 26 | |
| `{ontfangen, advies}` | 6 | |
| `{appointment}` alone | 2 | |
| `{advies}` alone | 68 | |
| frac_multi (any types) | 0.0114 | |
| `requeste_start` presents | **0** | |

Inside ontfangen+: with appointment **26**, with advies **6**, neither (solo-ish) **1365**.

## 2. Zone / graph

| Signal | Result | Grain |
|--------|--------|-------|
| Position | ontfangen mid_norm median **0.027**; opening **1392/1397 (99.6%)** | full year |
| Composition graph | `provisional_root_star`, `n_accepted_accepted_edges=0`, 2 spokes | **limit 200 only** |

Graph is a smoke; presence bags already show the same star shape on the full year (almost no accepted↔accepted co-bags).

## 3. Priors

| Prior | Claim |
|-------|--------|
| Datasheet | `ontfangen_start` → canonic *Ontfangen een missive van*; `proposition_type` **missive**; intention opening |
| STEPT0 1780 | ES missive **1489 / 3134 (47.5%)** — close to ontfangen hit rate (~50%), **not** the same set until measured |
| STEPT0 / Track R | Appointments mostly labelled ES `missive`; 29/31 selected in 1780 were missive |
| Design lock | Ontfangen = composition **root/partition**, provisional — not an accepted T1a formula type |

## 4. Known-set coverage (cheap id joins)

Universe = 1780 presence-score ids (2796). Ontfangen+ = 1397.

| Known set | n (1780) | ∩ ontfangen+ | not in ontfangen+ |
|-----------|---------:|-------------:|------------------:|
| R1 `aanstelling_selected` | 31 | **27** | 4 |
| L1 `missive_receipt` positives | 674 | **673** | 1 |
| `advies_es_gold` | 31 | **0** | 31 |

Notes:

- **L1 ≈ subset of ontfangen+** (673/674). But L1 covers only **673/1397 ≈ 48%** of ontfangen+ — ~**724** ontfangen+ ids are not L1 missive-receipt positives.
- **R1** mostly sits under the root (27/31), matching STEPT0 “appointments hide in missive/opening.”
- **ES advies gold** does not co-occur with ontfangen+ on id join (0); presence-model advies∩ontfangen (6) is not the same as gold.

## 5. Gap list (typology)

Still missing for a formula-typology call:

1. ES `proposition_type` mix **inside** ontfangen+ vs ontfangen− (is the root ≈ missive, or a cross-cutting cut?).
2. `formula_documents` flag rates / top combinations on each partition (`geen_resolutie`, `advertentie`, `goedgevonden`, `rapport_start`, …) — exploratory only.
3. Structure of the **~724** ontfangen+ \ L1 residual (other missive? decisionful? noise?).
4. Whether provisional typology needs an **opening/partition axis** (formula) in addition to ES `proposition_type`.

## 6. Call

**Proceed to STEPT1e partition probe** (ES types + known-set tags + flag rates on ontfangen±). Do **not** start another sparse A family until that probe’s NOTES.

Inventory alone is enough to reject “ontfangen+ = L1 missive-receipt”: half the root is unexplained. Typology attention is justified; the next measurement is the partition mix, not a new spoke.

**Deferred this session:** heavy `ontfangen_population` module — clear chat, then STEPT1e.
