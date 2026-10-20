# STEPT1d — Composition graph (period-binned)

**Goal:** Model formula-type **composition** as a **graph** — nodes = types (IDF-weighted by relative presence), arcs = co-presence directed by mid_norm — and measure how that graph **evolves across 25y bins**. Not document-order sequences (parked). Naming: this is **not** Track S token-span `align_dag` (Smith-Waterman / skip-DAG); reserve “DAG” for that.

**Done when:** fixture + cheap 1780 smoke written; if 1780 has zero accepted↔accepted edges, NOTES can stop (hypothesis killed/confirmed) without a full period matrix; otherwise provenanced period matrix + shape-over-time judgment; `data_io.check` clean.

**Prerequisite:** STEPT1b/c PASS (presence + zones); accepted appointment + advies; openings provisional (`ontfangen_start` = composition root / partition, not IDF “noise”). T1-period bin axis (origin 1700, width 25).

## You do

```bash
uv run pytest tests/test_formula_type_composition_graph.py -q
uv run python scripts/run_formula_type_composition_graph.py --fixture-only

# Cheap smoke first — kill/confirm before paying for bins
uv run python scripts/run_formula_type_composition_graph.py --year 1780 --limit 200

# Only if 1780 leaves the time-dynamic question open (user terminal; heavy)
uv run python scripts/run_formula_type_composition_graph.py --period-bins

uv run python -m data_io.check
```

If 1780 shows `n_accepted_accepted_edges == 0` (hub via provisional root only), record that in NOTES and **skip** `--period-bins` unless you explicitly need diachronic confirmation of the same star.

## Design locks

| Piece | Rule |
|-------|------|
| Nodes | formula types; `weight = log(1/clip(hit_rate))` **in-bin**; tag accepted vs provisional; `ontfangen_start` may be high-rate **root/partition** |
| Arcs | co-presence on same id; direction = earlier median `mid_norm` → later; report `n` and `n·w_a·w_b` |
| Cheap gate | 1780 smoke: `n_accepted_accepted_edges` + `graph_shape` |
| Period gate | only if cheap gate leaves dynamics open; per-bin same metrics + `shape_over_time` |
| Not | A-before-B sequence features; Track S token DAG / `align_dag`; Bayesian edge shrinkage |

## Measurements (required)

| Metric | Where |
|--------|--------|
| Per-bin nodes (hit_rate, weight, role) | metrics.period_matrix[].nodes |
| Per-bin arcs (from, to, n, n_weighted, zone_arc) | metrics.period_matrix[].arcs |
| `n_accepted_accepted_edges` | metrics.period_matrix[].n_accepted_accepted_edges |
| `graph_shape` | metrics.period_matrix[].graph_shape |
| Cross-bin shape summary | metrics.shape_over_time |

## Eval gates (NOTES)

1. **1780 smoke:** record `n_accepted_accepted_edges` and whether the graph is a provisional-root star (hub spokes) vs accepted↔accepted path.
2. If accepted↔accepted is already 0 on 1780 — judgment can stop; period matrix optional.
3. If running bins: does `graph_shape` change over time, or stay star? Do **not** invent sequence features if the answer is “star.”

## Do not

- Call this a “DAG” in PLAN headlines (Track S owns that word for span alignment)
- Treat openings as accepted formula types
- Redefine appointment / advies operating cuts
- Replace or delete `run_formula_type_order.py` (parked soft constraint only)
- Score annual series (bins only)
- Mix Track S token alignment into this graph

## Parked

Linear order / composition by `start_idx` ([STEPT1d-order-composition.md](STEPT1d-order-composition.md)) remains historical NOTES; CLI stays for soft-constraint checks, not the template definition.

## After this step

Mark STEPT1d composition-graph in `PLAN.md`. Next: another A family if still star, or sieve residual. Clear the chat before the next step.
