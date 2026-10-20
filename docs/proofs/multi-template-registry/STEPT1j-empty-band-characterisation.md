# STEPT1j — Empty-band characterisation (1780)

**Goal:** Characterise composition-unknown `empty` (n=1329) + tighter `fp_cut` sweep.  
**Status:** **PASS** (inventory + reading; no blueprints minted).

**Doctrine:** empty = no known formula hits; inventory + reading; do not mint blueprints from cluster n.

## 1. Structural profile

| Metric | Value |
|--------|------:|
| n_empty | **1329** |
| length median (q1–q3) | **194** (108–383) |
| top proposition_types | rekest 700 (0.53); missive 170; voordracht 135; rapport 87; onbekend 84; conclusie 51 |
| ontfangen_present (sanity) | **0** |
| known leakage L1 / R1 / advies | 1 / 2 / 2 |

### Per major type (length + focus flags)

| proposition_type | n | frac | words med | notes |
|------------------|---:|-----:|----------:|-------|
| rekest | 700 | 0.53 | 202 | Decision-shaped (`goedgevonden` 0.94, `gedelibereert` 0.76); `requeste_start` only 0.19 — wording gap vs presence |
| missive | 170 | 0.13 | 170 | Below ontfangen presence cut but flags: `ontfangen_start` 0.70, L1-ish `advertentie`/`geen_resolutie` ~0.4 |
| voordracht | 135 | 0.10 | 145 | Provincial bring-in / report; mid decision flags |
| rapport | 87 | 0.07 | **348** | Longer; `rapport_start` 0.76 |
| onbekend | 84 | 0.06 | 269 | Mixed; lower outcome-join quality |
| conclusie | 51 | 0.04 | 132 | Sharp: `handen`/`in handen` 0.70; almost no gedelibereert |
| memorie | 40 | 0.03 | 169 | Diplomatic/enclosure memorie openers |

### Combo catalogue (top; not subtypes)

| combo | n |
|-------|--:|
| gedelibereert + goedgevonden + request_start + vergaderinge_start | 120 |
| advertentie + geen_resolutie + ontfangen_start | 81 |
| +forma on request/vergaderinge skeleton | 61 |
| goedgevonden + paspoort + request* | 49 |
| handen + rapport_start + request/vergaderinge + … | 41 |

355 unique combos; top-5 share 0.28 — long tail. High-n = filler decision/requeste scaffolding, not new types from n alone.

## 2. Fingerprint cut sweep

| fp_cut | n_clusters | share_largest | n_singletons | nn_sim p50 |
|-------:|-----------:|--------------:|-------------:|-----------:|
| 0.15 | 2 | **0.999** | 1 | 0.494 |
| 0.30 | 285 | **0.647** | 217 | 0.494 |
| 0.45 | 704 | **0.068** | 587 | 0.494 |
| 0.60 | 983 | 0.022 | 872 | 0.494 |

Operating labels written at `fp_cut=0.45`.

At 0.45, multi-member heads loosely track ES pockets (e.g. cluster 2≈rekest/conclusie requeste; 15≈voordracht/provincial; 23≈short missive) but **majority are singletons** — fingerprints triage for sampling, not a typology cut.

## 3. Sample shapes (read `empty_band_sample`)

- **Rekest / requeste:** `IS ter Vergaderinge geleesen de Requeste van …` → colonial/legal suppliant matter → goedgevonden/gedelibereert. Dominant empty mass; presence inventory misses this opener.
- **Missive (empty):** still often `Ontfangen een Missive…` / resume-deliberate — below operating ontfangen cut, or non-L1 decisionful path without accepted A hits.
- **Voordracht / provincial:** `Gedeputeerden … hebben … ingebragt / voorgedraagen` + missive/rapport enclosure.
- **Rapport:** `BY resumtie gedelibereert … op het Rapport…` — long, sparse vs rekest.
- **Conclusie:** `Conclusie van eisch/consent …` + **handen** referral — distinct short pocket.
- **Memorie:** `geleesen een Memorie van den Heer …` (diplomatic / admiralty).

## 4. Call

1. Empty is **several ES-type pockets**, not one mass — rekest is the head (~half), not the whole.
2. Tighter `fp_cut`: **0.15 useless**; **0.45** splits the blob but mostly into singletons — use for sample strata only, not types.
3. Next = presence/formula probe for the **requeste / rekest opener** (largest unexplained skeleton), or sparse **conclusie+handen** — **not** mint blueprints from empty n≈1329 or fp clusters. STEPT1e1 stays parked.

## 5. STEPT1j2 — R1/L1 contrastive probe (PASS)

Reuse frozen char TF-IDF+LR: R1 = harvest join; L1 = `fit_on_all_labelled` + score empty. Cuts high>0.85 / low<0.15 (diagnostic for L1).

| Model | high | grey | low | proba med / p90 |
|-------|-----:|-----:|----:|----------------:|
| R1 | **0** | 4 | 1325 | 0.022 / 0.053 |
| L1 | **3** | 45 | 1281 | 0.014 / 0.042 |

- **R1:** empty ≈ all low (expected). Rekest 700/700 low. Not appointment residue.
- **L1:** only **3 high**, all ES missive. Empty missive (170): high 3 / grey 40 / low 127; p90 **0.63** — soft grey tail, not a high flood. Rekest 698/700 low.
- **Lesson vs fingerprints:** contrastive models correctly place empty **outside** both known types. Unsupervised cosine inside empty was never going to recover R1/L1 structure; the rekest head needs its **own** seeded contrast (requeste vs rest), not tighter clustering.

**Call:** Proceed to **requeste/rekest opener** probe (R1/L1-style or presence). Do not unpark L3; do not mint from empty bands.
