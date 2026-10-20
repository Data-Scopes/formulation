# Deferred — Track S: 17c requeste opening templates

**Status:** deferred (do not execute while STEPS1 framing is 18c-only)  
**Parent:** [`plans/milestones/S1-formula-boundary-evolution.md`](../milestones/S1-formula-boundary-evolution.md), [`plans/steps/STEPS1-tfidf-window-framing.md`](../steps/STEPS1-tfidf-window-framing.md)

## Why deferred

STEPS1 scopes TF-IDF framing to the **18c** opening `IS ter Vergaderinge geleesen de Requeste` (`opening_requeste_18c`). Expanding to the 17th century needs a **period map / small template cloud**, not a single swapped string.

## What to pick up later

Slice evidence (head ~300 docs / year, 2026-10-18):

| Period | Dominant requeste-related openings | Notes |
|--------|--------------------------------------|-------|
| ~1610–1625 | *Is gelesen de requeste*; early *Opte reqte.* / *Opde requeste* | Before *ter Vergaderinge* dominates |
| ~1630 | *Is/Synde gelesen de requeste*; *Opde requeste* | Compact *Opde* without space |
| ~1640–1670 | *Is/Sijnde ter Vergaderinge gelesen de Requeste* | Also *Op de Requeste van …* as a minority opening |
| 1715–1780 | *IS ter Vergaderinge gele(e)sen de Requeste* | Current STEPS1 default |

Also seen mid-doc: *bericht/advis/antwoorden op de Requeste* — not openings; watch false positives if the query is only *op de requeste*.

## Suggested implementation (when chosen)

1. Period → template list (or slot-cloud) in `formulation/boundary/` (e.g. year bands).
2. Score max cosine over the period’s templates (or STEPS2 cloud), still `char_wb` 3–5 + `sublinear_tf`.
3. Re-threshold per period (18c cut will not transfer).
4. Keep STEPS0 `formula_boundary_cases` for SW/DAG gold; do not overwrite with 17c inventory alone.

## Out of scope until chosen

Running 17c year-slice framing as the active STEPS1 default; mixing 17c templates into the 18c POC without a written cut.
