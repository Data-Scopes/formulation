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

## How to use this list

1. Prefer a **small empirical probe** that answers 1–3 questions over a new track ladder.
2. Record answers in [`DECISIONS.md`](DECISIONS.md); leave unresolved items here.
3. Do not turn every question into a milestone until chosen in `PLAN.md`.
