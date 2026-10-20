# STEPT1e — Ontfangen partition probe

**Goal:** Measure ES `proposition_type` mix, known-set tags, and `formula_documents` flag rates on **ontfangen+** vs **ontfangen−** (1780 presence universe), including the ontfangen+ \ L1 residual. Close the STEPT1e0 gap list with a typology call.  
**Done when:** provenanced metrics (+ optional per-id scores) written; NOTES filled with mix tables + residual structure + call; `data_io.check` clean; `PLAN.md` updated.

**Prerequisite:** STEPT1e0 inventory NOTES; full-year `formula_type_presence_*` for 1780.

## You do

```bash
uv run pytest tests/test_ontfangen_partition.py -q

# Fixture smoke (no ES / no parquet joins beyond fixtures)
uv run python scripts/run_ontfangen_partition_probe.py --fixture-only

# Full 1780 probe (user terminal — ES mget ~2.8k ids + formula_documents join)
uv run python scripts/run_ontfangen_partition_probe.py --year 1780

uv run python -m data_io.check
```

Fill / judge: [`docs/proofs/multi-template-registry/STEPT1e-partition-probe.md`](../../docs/proofs/multi-template-registry/STEPT1e-partition-probe.md).

## Design locks

| Piece | Rule |
|-------|------|
| Universe | Presence-score ids for the year (not full ES composition) |
| Partition | `ontfangen_start` present at operating cut → + / − |
| ES | `mget` lean `_source` only (`proposition_type`, `session_date`, year) — no live text |
| Flags | `formula_documents` via `(session_date, resolution_index)`; exploratory rates + top combos — not decisions |
| Known sets | Tag R1 selected / L1 missive_receipt / advies ES gold; do not redefine them |
| Ontfangen | Still **provisional composition root / partition**, not an accepted formula type |

## Measurements (required)

| Metric | Where |
|--------|--------|
| `n_plus` / `n_minus` / hit_rate | metrics |
| ES type mix (+/−) | metrics.es_type_mix_plus / `_minus` |
| Missive ↔ partition contingency | metrics.missive_contingency |
| Flag rates + top combinations (+/−, residual) | metrics.flags_* |
| Residual ontfangen+ \ L1: n + ES mix + top flags | metrics.residual_not_l1 |
| Known-set ∩ partition | metrics.known_sets |

## Eval gates (NOTES)

1. Is ontfangen+ ≈ ES `missive`, or a cross-cutting cut?
2. Does L1 (`geen_resolutie`-style receipt) explain only half the root — what is the residual’s ES/flag shape?
3. Call: keep an **opening/partition axis** in typology (yes/no), and what to do next (sieve residual / another A / stop).

## Do not

- Accept `ontfangen_start` as a formula type
- Start another sparse A family before NOTES call
- Pull full resolution text from ES
- Classify flags as archival outcomes / “no decision”
- Rescore presence or run period bins

## After this step

Mark STEPT1e in `PLAN.md`. Follow NOTES call. Clear the chat before the next step.
