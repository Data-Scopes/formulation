# STEPT1z — Probabilistic formula sequence matrix (NOTES)

**Status:** done (2026-10-25). Primary = row-stochastic P(next|current).  
**Guide:** [`plans/steps/STEPT1z-formula-sequence-matrix.md`](../../../plans/steps/STEPT1z-formula-sequence-matrix.md)  
**Decision:** [`docs/DECISIONS.md`](../../DECISIONS.md) 2026-10-25 STEPT1z.

```bash
uv run pytest tests/test_formula_sequence_matrix.py -q
uv run python scripts/run_formula_sequence_matrix.py --fixture-only
uv run python scripts/run_formula_sequence_matrix.py --year 1780
uv run python -m data_io.check
```

## Deliverables

| Logical name | Role |
|--------------|------|
| `formula_sequence_matrix` | Edge table: **`p_adjacent`** (primary) + `n_adjacent` / `n_from` companion + precedes/gap |
| `formula_sequence_matrix_metrics` | Summary + wide `P_adjacent` / `N_adjacent` |
| `formula_sequence_nodes` | Blueprint / harvest / EMPTY / END |
| `formula_sequence_scores` | Per-id ordered formula ids |
| `formula_sequence_harvest` | Scheme + STEPT1u pocket shortlist (not auto-named) |
| `formula_sequence_matrix_xlsx` | **Human workbook** — `P_adjacent`, `N_adjacent`, `edges`, `nodes`, `harvest`, **`examples`**, **`edge_examples`** |
| `formula_sequence_examples` | Archetypal truncated snippets (pick_rule=`shortest_hit`); **illustrative, not completeness** |

### STEPT1z2 — archetypal examples

Per node with `n_from>0`: up to 3 shortest-hit resolutions (tie: earliest `start_idx`, then id); `text_trunc` ≈280 chars around the span. Top ~20 adjacent edges with `n_adjacent≥5`: one shortest realizing pair. Rebuild:

```bash
uv run python scripts/run_formula_sequence_matrix.py --year 1780
```

Open `output/formula_sequence_matrix.xlsx` → sheets `examples` / `edge_examples`.

## 1780 result (headline)

- n_resolutions **2796**; row_sum_ok **True**; n_edges **251**; n_harvest surfaces **28**
- n_empty **40** (0.014) — **much lower than composition empty 0.107** because harvest substrings fire widely (see caveats)
- Six blueprints + harvest + EMPTY/END present

Useful signal examples (read with `n_from`):

| from → to | p_adjacent | n |
|-----------|----------:|--:|
| `praeside_start` → `harvest_voordracht_voorgedragen` | 0.26 | 26/100 |
| `appointment` → `requeste_geleesen` | 0.36 | 10/28 |
| `advies_geleesen` → `harvest_scheme_advies` | 0.43 | 32/74 (overlap / alias) |

## Gates

| Gate | Result |
|------|--------|
| 1 Rows sum ≈ 1; END column | **PASS** (`row_sum_ok`) |
| 2 Six blueprints + harvest nodes | **PASS** |
| 3 Companion n; voordracht/conclusie pockets in harvest | **PASS** |
| 4 No auto-named / blueprint mint | **PASS** |

## Caveats (read before naming)

1. **Harvest noise / nested surfaces:** top P cells include `in handen` → `handen`, `rapport_gehoord` → scheme `rapport`, `requeste_op_de` → `request` — substring nesting → **negative gaps**. Treat as harvest hygiene debt, not typology.
2. **EMPTY collapse:** substring harvest makes almost every resolution non-empty; do not compare this empty rate to STEPT1x composition empty.
3. **Order = substring among presence-present blueprints** — not DAG spans. Fine for overview; not for frozen cuts.
4. Still **no auto-mint** into `opener_candidates.named`.

## Next

Human: skim xlsx `P_adjacent` + `examples` / `edge_examples`; merge nested harvest noise; name into `opener_candidates`. Clear the chat before the next step.
