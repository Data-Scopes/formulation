# STEPT1e1 — Discourse-flag sieve on ontfangen+

**Goal:** Bucket the ontfangen+ population by **decision-stage boilerplate flags** (null / decision / defer / other), using existing joins — no new scorer. Judge whether typology should treat decision-stage as a second axis beside the opening partition.  
**Done when:** NOTES with bucket counts + overlap with L1/R1; call written; `PLAN.md` updated.

**Prerequisite:** STEPT1e PASS ([NOTES](../../docs/proofs/multi-template-registry/STEPT1e-partition-probe.md)); `ontfangen_partition_metrics` / `_scores` on disk.

## You do

Reuse `formula_documents` (or enrich `ontfangen_partition_scores` with the few needed flags) on **ontfangen+ only**. Assign each id to one primary bucket:

| Bucket | Primary rule (first match wins; tune in NOTES) |
|--------|------------------------------------------------|
| `null_decision` | `geen_resolutie` |
| `decision` | `gedelibereert_start` or `goedgevonden` or `verstaen` (and not already null) |
| `defer` | `handen` or `in handen` (may co-occur with decision — report overlap) |
| `other` | none of the above |

Report: n per bucket; L1 ∩ each; residual-not-L1 mix; top flag combos per bucket; optional ES type mix.

Fill: [`docs/proofs/multi-template-registry/STEPT1e1-residual-flag-sieve.md`](../../docs/proofs/multi-template-registry/STEPT1e1-residual-flag-sieve.md) (create with NOTES).

Prefer a thin script over ad-hoc notebook; register any new provenanced output in the manifest before write.

## Design locks

| Piece | Rule |
|-------|------|
| Universe | ontfangen+ from STEPT1e / presence (1780 first) |
| Signals | `formula_documents` flags only — exploratory |
| Outcomes | Flags ≠ archival decisions |
| Ontfangen | Still provisional opening/partition, not accepted formula type |
| Not | New A family; Track S span boundaries; ES live text |

## Eval gates (NOTES)

1. Does `null_decision` ≈ L1?
2. Is residual-not-L1 mostly `decision` (+ some `defer`)?
3. Call: keep decision-stage axis; next step (stop / another A / span probe later).

## Do not

- Accept ontfangen as a formula type
- Start another sparse A before NOTES call
- Treat `goedgevonden` / `geen_resolutie` as “what was decided”
- Implement ordered discourse-span segmentation (later Track S if ever)

## After this step

Follow NOTES call. Clear the chat before the next step.
