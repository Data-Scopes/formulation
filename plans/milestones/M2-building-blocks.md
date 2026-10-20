# M2 — Building-block criteria

**Status:** not started — after M1  
**Notions:** [`docs/formula-conceptual-overview.md`](../../docs/formula-conceptual-overview.md)

## Goal

Stop treating every frequent bigram/trigram as a formula. Define and apply **criteria for building-block status**, then filter/annotate first-slice candidates (and S4 seeds) against those criteria.

Draft criteria (refine with evidence from M1 output):

- Recurs as a stable unit across many resolutions / years
- Appears in more than one larger formula type (compositional reuse)
- Survives orthographic variation as the same skeleton
- Carries a recognisable discourse or procedural function
- Is productive with variable slots — not a frozen hapax collocation

## Done when

- Criteria are written as a project decision (short `docs/DECISIONS.md` entry + a small module or documented rule table).
- Candidates and S4 seeds carry an explicit building-block judgement (or “fragment / too short / local only”).
- Frequency is no longer the sole promotion rule.

## Inputs

M1 provenanced candidates; S4 inventory; notebook gold tables only after they are path-cleaned and registered in the manifest.

## Do not

Implement a full composition graph here. Do not resurrect ES year-loops from `clustering_formulas.ipynb`.
