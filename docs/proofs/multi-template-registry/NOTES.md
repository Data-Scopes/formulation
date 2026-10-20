# Prove-first: multi-template registry + appointment institution

Scratch evidence for the prove-first gate. **Registered stub:** logical name `formula_templates` → [`tests/fixtures/formula_templates.jsonl`](../../../tests/fixtures/formula_templates.jsonl) via `formulation.formula_templates`. Keep this folder as proof audit trail; do not load the scratch JSONL from pipeline code.

**Design questions** (research north star): [`docs/template-design-questions.md`](../../template-design-questions.md).

**Notebook (JSON + code sketch):** [`notebooks/proof_formula_schemas.ipynb`](../../../notebooks/proof_formula_schemas.ipynb)

Re-run institution metrics (surfaces from `institution_patterns`, not template rows). **S6d:** A/B fixture seeds vs ORG harvest on one locked sample (sibling pool always from seeds):

```bash
# Side-by-side (default): writes sample_* + metrics_compare.jsonl
uv run python scripts/prove_appointment_institution.py --source compare

# Single arm (overwrites appointment_institution_{sample,metrics}.jsonl)
uv run python scripts/prove_appointment_institution.py --source seeds
uv run python scripts/prove_appointment_institution.py --source harvest
```

Compare file: [`appointment_institution_metrics_compare.jsonl`](appointment_institution_metrics_compare.jsonl) — keys `seeds`, `harvest`, `deltas_harvest_minus_seeds`. Sibling `rekenkamer` recall is biased high (pool defined by Rekenkamer mention); watch selected FP, `none` rates, and non-rekenkamer primaries.

### S6d results (locked sample, RNG=0)

| Metric | Seeds (14) | Harvest (43 581 / 17 838 unique) |
|--------|-----------:|---------------------------------:|
| Sibling primary = `rekenkamer` | 50/50 | 50/50 |
| Selected primary = `rekenkamer` (FP) | **0/50** | **1/50** |
| Sibling `none` | 0.00 | 0.00 |
| Selected `none` | 0.82 | 0.80 |
| Gate `pass_no_fp_rekenkamer_on_selected` | true | **false** |

Harvest FP: `session-3812-num-136-resolution-10` (1757) — span *Generaliteyts Reekenkaamer* (seed arm: `none`). Selected `none` only −0.02; HHM primary count unchanged (9/50).

**Call:** keep provenanced harvest as `load_patterns` default for lexicon coverage, but **do not** treat the raw 43k surfaces as a drop-in discriminator — tighten `--min-n` (or equivalent frequency filter) before production gating. Seeds remain the strict no-FP baseline.

## 1. Registry schema scratch

File: [`formula_templates_scratch.jsonl`](formula_templates_scratch.jsonl)

| `template_id` | `role` | Checks |
|---------------|--------|--------|
| `opening_requeste_18c` | framing | tokens + frozen 0.40; no `<START>` in tokens |
| `requeste_start` | doc_flag | `nlp_start_marker: true` (artefact) |
| `requeste_any_zone` | doc_flag | `role_depends_on_place: true` |
| `rapport_surface` | doc_flag | dual-zone illustration |
| `goedgevonden_decision_opener` | doc_flag | `outcome_signal: false` |
| `appointment_vergadering` | appointment_subtype | `discriminators: ["institution"]` |
| `appointment_rekenkamer` | appointment_subtype | same cues family; different institution target |

**Pass (human):** framing vs catalogue vs appointment-sibling is readable from fields alone; nothing treats `<START>` or *goedgevonden* as archival/outcome truth.

## 2. Institution discriminator

Files: [`appointment_institution_metrics.jsonl`](appointment_institution_metrics.jsonl), [`appointment_institution_sample.jsonl`](appointment_institution_sample.jsonl)

Setup: 50 `aanstelling_selected` vs 50 harvest rows with Rekenkamer mention **and** `has_aanstelling_cue`.

| Metric | Value |
|--------|------:|
| Sibling primary = `rekenkamer` | 28/50 (56%) |
| Selected primary = `rekenkamer` (FP) | **0/50** |
| Sibling `none` | 32% |
| Selected `none` | 86% |

**Pass with caveats:** Institution is a usable **positive** discriminator for Rekenkamer vs the vergadering list (no false Rekenkamer on selected; ≥50% recall on cued siblings). Incomplete alone: many selected rows lack a matched institution span (need better HHM/vergadering target patterns); sibling misses include OCR/other colleges (`raad_van_state`, admiralty). Do **not** ship a separate TF-IDF per sibling until institution gating is tried.

### Next pattern source (republic_ner) — over time

Do **not** freeze one regex set. In [`republic_ner_matching`](https://github.com/) the ORG layer already carries **inventory-dated surface forms**:

| Source | What it gives |
|--------|----------------|
| `ORG-annotations.json` (`tag_text` + `inv`) | Empirical spellings per inventory (period proxy) |
| `ORG-entities.json` | Canonical ids (e.g. Generaliteitsrekenkamer `O0000072`, admiralties) |
| `instituten_lookup_cleaned` | GNB `ID_instelling` → naam (enriched `institutions` ids; different id space from ORG) |

Observed shift (same college family):

- inv **3185** (~1626): *Gecommitteerde Raden ter Admirt. tot Rotterdam*
- inv **3835** (~1780): *Collegie ter Admiraliteit te Amsterdam*

So registry `institution_patterns` (when implemented) should be **period- or inventory-keyed variants** harvested from that ORG annotation stream, not a single timeless string. Delegate `patterns_reference` (`year_min`/`year_max`) is person-side analogy; ORG needs the same discipline.

## 3. Gate

See `docs/DECISIONS.md` — proceed to implement registry with `discriminators: ["institution"]` for appointment subtypes; **prefer republic_ner ORG surfaces over time** before hand-tuned regex alone.

## 4. Agreed approach and open problems

**Approach (confirmed):** wide categories → finer subtypes; **recall before precision**. Appointment siblings: `discriminators: ["institution"]` (+ later period-keyed `institution_patterns`), not a TF-IDF model per sibling until needed.

**Open problems (design constraints, not this session’s build):**

| Issue | Implication |
|-------|-------------|
| Many templates unknown / rare | Registry must allow **unknown / residual** catalogue rows; do not pretend the scheme is closed |
| Few opening phrases → many templates | Model **branching**: shared opener skeleton, then subtype by zone, institution, period |
| Same for formulas generally | Composition / branching, not one-id-per-surface-string |
| 18c better known; 17c thinner (some in republic_ner) | Period-scoped entries; 17c inventory deferred until period map |
| Imperfect resolution parsing (esp. 17c) | **Later:** use resolution templates to help re-segment / separate misparsed units — out of scope until catalogue + framing bases exist |

### Committees (republic_ner) ≠ template class

ORG/committee mentions (colleges, Gecommitteerde Raden, Rekenkamer, admiralties, …) are useful as **subject / content** tags on a resolution or hit — *what the business is about*.

That is **not** formula-template classification. Keep separate:

| Layer | Question | Example |
|-------|----------|---------|
| Template / formula class | *How* is it worded / which skeleton? | `opening_requeste_18c`, decision opener |
| Appointment subtype discriminator | *Which office* is being filled? (still structural for R1 siblings) | `discriminators: ["institution"]` |
| Subject / content (committees etc.) | *What* domain or body is referred to? | tag `Generaliteitsrekenkamer` on a missive about accounts |

Do not collapse committee NER labels into `template_id`. Optional later field e.g. `subject_hints` / content facets on catalogue rows or on span/doc outputs — orthogonal to `role` / framing.
