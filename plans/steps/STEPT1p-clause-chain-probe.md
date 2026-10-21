# STEPT1p — Clause-chain probe (confined: appointment welkom / sessie)

**Goal:** Test whether a **clause-level** form vocabulary carries structure that the coarse `present_bag` discards, on the cheapest available case: decollapse `appointment_installation` into its two existing clause clouds (welkom, sessie), build ordered clause chains, and measure chain-vs-bag. Design: [`docs/resolution-graph-design.md`](../../docs/resolution-graph-design.md).
**Done when:** provenanced `clause_chain_metrics` + `_scores` written; NOTES pass/fail on gates below; `data_io.check` clean.

**Prerequisite:** none beyond existing frozen cuts. Uses `build_appointment_clouds` (welkom + sessie clouds already built together) and the frozen STEPT1a cut; no new cloud, no new calibration, no content markers.

**Scope lock:** form only. No `institution_patterns`, no ORG NER, no `formula_documents` flags as nodes. Comparison year 1780 (same as T1b/T1c/T1i/T1m/T1o).

## You do

```bash
uv run pytest tests/test_clause_chain.py -q

# Confined probe: appointment welkom/sessie only (fast — clouds bootstrap from aanstelling_selected)
uv run python scripts/run_clause_chain_probe.py --year 1780

# Richer chains incl. the three accepted openers (slower: missive cloud bootstraps 141k texts)
uv run python scripts/run_clause_chain_probe.py --year 1780 --with-openers

# Smoke (no parquet / gold)
uv run python scripts/run_clause_chain_probe.py --fixture-only

uv run python -m data_io.check
```

Fill / judge: `docs/proofs/multi-template-registry/STEPT1p-clause-chain-probe.md` (create).

## Measurements (required)

| Metric | Where |
|--------|-------|
| Per-clause hit counts at frozen cuts (welkom, sessie, ± openers) | `metrics.clauses` |
| Distinct **bags** with support vs distinct **chains** with support | `metrics.bag_inventory` / `metrics.chain_inventory` |
| **Collapse factor**: `n_chains / n_bags`, and share of resolutions sitting in a bag that maps to >1 chain | `metrics.collapse` |
| **Order stability**: per clause-set (support ≥ min), `dominant_order_frac`; support-weighted mean | `metrics.order_stability` |
| Appointment decollapse: welkom_only / sessie_only / both counts + median n_words + mean zone per clause | `metrics.appointment_decollapse` |
| Independence vs partition: `P(sessie\|welkom)` vs `P(sessie\|¬welkom)`, lift | `metrics.independence` |
| `keep`/`drop` rate per sub-pattern where joinable to `aanstelling_review_labels` | `metrics.appointment_decollapse.review_join` |

## Eval gates (NOTES)

1. **G1 Collapse — does chain space distinguish mass bags collapse?** `n_chains > n_bags` **and** ≥ 10% of resolutions sit in a multi-chain bag. If not: clause granularity adds nothing here, stop and keep bags.
2. **G2 Order stability — is order real?** Support-weighted mean `dominant_order_frac` **≥ 0.80** → clause order is rigid enough to treat chains as skeletons. **< 0.60** → order is noise, bags were the right abstraction; **the design is refuted for this clause set** and must be reported as such, not reframed.
3. **G3 Decollapse signal** — do welkom_only / sessie_only / both differ on at least one *independent* property (median length, zone, or `keep`/`drop` rate) beyond what the defining clause presence trivially implies?
4. **G4 Independence vs partition** — report the lift and state which reading it supports (variant marker vs candidate distinct type). No promotion either way in this step.
5. Pass/fail written in proof NOTES.

## Do not

- Admit any content marker (institution, person, place, topical word list) as a node.
- Mint new `template_id`s or touch `ACCEPTED_TYPE_IDS` / `formula_templates` — this probe is measurement only.
- Recalibrate the appointment cut (frozen STEPT1a, currently 6.0).
- Claim a vergadering-vs-rekenkamer result: those labels do not exist (only `keep`/`drop`); see the design note's "What is not available".
- Extend to advertentie / null-decision close in this step (needs a new clause cloud — separate step).

## After this step

Mark STEPT1p in `PLAN.md` + design note. If G1+G2 hold: next step builds the **null-decision close clause** cloud and re-runs the probe on the advertentie case (breaks STEPT1f's circular L1 caveat). If G2 fails: record the refutation, keep bags, and the institution question goes back to needing a content layer. Clear the chat before the next step.
