# M3 — Gappy composition and position-aware typing

**Status:** not started — after M2  
**Notions:** [`docs/formula-conceptual-overview.md`](../../docs/formula-conceptual-overview.md)

## Goal

Represent larger formulas as **compositions of building blocks plus variable slots**, including **non-contiguous** skeletons. Use **document position** (opening / body / decision zone, offsets) so the same cue can be typed differently (e.g. decision-final vs opening resumption).

## Done when

- Candidate records retain span/section fields and can be grouped as gappy templates, not only contiguous n-grams.
- At least one attested composition pattern (e.g. opening “ontfangen een missive …” vs decision-zone reuse of a related cue) is documented from the sample/frozen corpus.
- Interpretation notes distinguish string identity from position-sensitive type.

## Machinery to lean on (do not fork)

`formula_detection` layers: `extract_phrases` variable/skip knobs, `phrase_cooccurrence`, `motif`, `boundary`, later `clustering` / `phrase_typing`.

## Later still (not this milestone)

Year-sliced clustering; phrases ↔ *hoedanigheden*; full REPUBLIC corpus; HITL typing UI.
