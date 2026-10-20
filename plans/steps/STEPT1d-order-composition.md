# STEPT1d — Formula-type order / composition (parked)

**Status:** historical. 1780 PASS — order is a soft constraint only; does not define templates.

**Superseded by:** [STEPT1d-composition-graph.md](STEPT1d-composition-graph.md) — composition **graph** with 25y period matrix (nodes = types × relative presence; arcs = co-presence / zone; not A-before-B sequences; not Track S `align_dag`).

## Historical goal

Ask whether **sequence** of formula-type hits (A before B by DAG `start_idx`) turns STEPT1b/c bags into recognisable resolution templates.

## You do (parked CLI — soft constraint only)

```bash
uv run pytest tests/test_formula_type_order.py -q
uv run python scripts/run_formula_type_order.py --fixture-only
uv run python scripts/run_formula_type_order.py   # 1780 POC; not the composition gate
```

Do **not** run T1d-refresh order as the next composition step. Use the composition-graph guide instead.

## After this step

See [STEPT1d-composition-graph.md](STEPT1d-composition-graph.md).
