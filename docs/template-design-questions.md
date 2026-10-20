# Design questions: templates (and formulas)

Research north star for template / formula typology work. **Not** a pipeline checklist — answers shape what we build next; steps stay under [`PLAN.md`](../PLAN.md) and [`plans/`](../plans/).

Related: [`formula-conceptual-overview.md`](formula-conceptual-overview.md) (building blocks, gaps, position), [`formula-boundary-evolution.md`](formula-boundary-evolution.md) (span harness), registry prove-first [`proofs/multi-template-registry/NOTES.md`](proofs/multi-template-registry/NOTES.md), stub `formula_templates`.

## Working distinction (to keep sharp)

| Term | Working sense |
|------|----------------|
| **Formula** | Recurring templated language: skeleton + variable slots; may be a short building block or a longer stretch |
| **Template** | A typed catalogue entry / detection target: which skeleton (and role, period, zone, discriminators) we claim to recognise |
| **Discriminator** | Gate that splits lookalikes without a new model (institution, zone, period, close-cue, …) |

Refine these as evidence accumulates; do not collapse NER subject tags into `template_id`.

## Power and period

- How far do known templates get us on a year slice before recall collapses?
- Which templates are period-bound vs reusable with period-/inventory-keyed variants?
- How much does harvest quality drop when the year window moves (esp. 18c → 17c)?

## Discrimination

- How do we discriminate lookalikes that share an opening or cue family?
- Which gate first: institution / college, zone, period, null-decision close, other?
- When is a second classifier justified vs another discriminator field?
- Can we discriminate *further* inside a wide class without closing the catalogue prematurely?

## Formulas ↔ templates

- What is the relation: is a template one formula, a composition of blocks + slots, or a role over several surfaces?
- Which building blocks are shared across templates (branching from few openers)?
- When must representation be gappy (non-contiguous) vs a contiguous span?

## Formulas: length and typology (which end to start)

Harvested formula lists (notebook schemes, S4 openings, `formula_documents` flags, long `FormulaSearch` / fuzzy hits) often contain **overlong** strings: several blocks plus variable material glued together. They still need a typology — but **not by labelling that list top-down**.

Earlier typology starts in-repo (treat as archaeology, not the growth edge):

- Proof sample: [`proofs/multi-template-registry/formula_schemes_sample.json`](proofs/multi-template-registry/formula_schemes_sample.json) (`phrasename`, function, intention, …)
- Notebook / port notes: `formulas_schema`, elements writeups — see [`formula-conceptual-overview.md`](formula-conceptual-overview.md) and `formulator-project-docs/internal-context/formula-sources.md`
- Milestone intent (later): [`plans/milestones/M2-building-blocks.md`](../plans/milestones/M2-building-blocks.md)

Design questions:

- When is a harvested formula **too long** (composite) vs a single template skeleton?
- Do we start typology from **short blocks / framing markers**, or from the long harvest rows? (Working preference: short → compose; schemes as `seed_refs` only.)
- How do we mark overlong rows: split candidates, “contains blocks X+Y”, or reject until cut?
- What criteria promote a short stretch to building-block status (reuse, function, slots) vs fragment / local only?
- How should legacy scheme fields (`function`, `intention`, `proposition_type`) map into registry `role` / zones without forcing a closed inventory?

## Harvest and detection feasibility

- How fast is template harvesting (TF-IDF windows → SW/cloud → DAG) per year / per family?
- Is **template detection** feasible at corpus scale, or only on candidate windows / known families?
- What latency / quality tradeoff for framing vs alignment vs (later) neural residual?
- How much human review is needed before trusting a new `template_id`?

## Coverage and ontology

- How many templates are we missing vs over-splitting OCR/period surface variants?
- When is something a new template vs a variant of an existing id?
- Where does `unknown_residual` stop being a bin and require new catalogue rows?

## Position and discourse

- Does the same skeleton change type by zone (opening vs decision / referral)?
- Can templates later help re-segment misparsed resolutions (esp. 17c) — or is that out of scope until framing bases exist?

## Downstream (keep layers separate)

- What do templates buy for typology vs whole-resolution retrieval (R/L) vs subject/content tags?
- Which results are Doel A (usable catalogue / spans) vs Doel B (methods bake-off)?
- **Rekest sub-typology by requester** (civilian / institution / foreign ambassador): structural outcome/routing (`goedgevonden` vs `handen`/`in handen` vs `advies` co-occurrence — STEPT0 `top_flag_combinations`) looks answerable now. Requester identity does not — `proposer`/`proposer_role`/`proposition_organisation` are null corpus-wide in ES.
  - Semantic lever: unregistered `republic_ner_matching` "Hoedanigheden" vocabulary (`hoe_vocab.parquet`, 6 categories: person_citizen/title/profession/legal_status/meeting_role/family) — needs a mapping step from 6 generic categories to the 3 target buckets, and still doesn't say *which* mention in a resolution is the requester.
  - **Distributional lever (purely structural, no semantic mapping — user's framing):** most mentioned persons occur once (likely one-off requesters); delegates/ambassadors/regular SG interlocutors occur often. Corpus-wide mention frequency per entity is a rough, cheap proxy for requester-vs-government-actor role — low frequency ≈ requester, high frequency ≈ recurring official. Not yet computed: `PER-entities.json` (766KB) is an id→name dict with no counts; frequency needs one streaming pass over `PER-annotations.json` (2GB) — `Counter(entity_id) → n` globally, same mechanics as `institution_pattern_harvest.py`'s ORG aggregation, just not scoped to institution targets. Then, within a rekest resolution's PER mentions, the lowest-frequency entity is the requester-identity candidate.
  - Either lever is its own probe, not folded into STEPT0.

## How to use this list

1. Prefer a **small empirical probe** that answers 1–3 questions over a new track ladder.
2. Record answers in [`DECISIONS.md`](DECISIONS.md); leave unresolved items here.
3. Do not turn every question into a milestone until chosen in `PLAN.md`.
