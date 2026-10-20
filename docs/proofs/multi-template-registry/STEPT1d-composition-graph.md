# STEPT1d — Composition graph (NOTES)

**Guide:** [`plans/steps/STEPT1d-composition-graph.md`](../../../plans/steps/STEPT1d-composition-graph.md)

Not Track S token-span `align_dag`. Order CLI remains parked ([STEPT1d-order-composition.md](STEPT1d-order-composition.md)).

## Commands

```bash
uv run pytest tests/test_formula_type_composition_graph.py -q
uv run python scripts/run_formula_type_composition_graph.py --fixture-only

# Cheap smoke first
uv run python scripts/run_formula_type_composition_graph.py --year 1780 --limit 200

# Only if 1780 leaves dynamics open
uv run python scripts/run_formula_type_composition_graph.py --period-bins

uv run python -m data_io.check
```

## Design locks

| Piece | Rule |
|-------|------|
| Nodes | types; `weight = log(1/clip(hit_rate))` in-slice; `ontfangen_start` = composition root |
| Arcs | co-presence; direction = earlier `mid_norm` → later |
| Cheap gate | `n_accepted_accepted_edges` + `graph_shape` |
| Period gate | only if smoke leaves time-dynamic question open |

## 1780 smoke (`--limit 200`)

| Metric | Value |
|--------|------:|
| `n_resolutions` | 200 |
| `n_arcs` | 2 |
| `n_accepted_accepted_edges` | **0** |
| `graph_shape` | **provisional_root_star** |

| Node | n_present | hit_rate | role |
|------|----------:|---------:|------|
| `ontfangen_start` | 80 | 0.40 | root |
| `advies_geleesen` | 9 | 0.045 | accepted |
| `appointment_installation` | 1 | 0.005 | accepted |
| `requeste_start` | 0 | 0 | provisional |

Arcs (both hub spokes): `ontfangen_start`→`advies_geleesen` (n=1, opening→body); `ontfangen_start`→`appointment_installation` (n=1, opening→close). No advies↔appointment co-presence.

**Call (PASS / hypothesis confirmed):** composition is a **provisional-root star** — accepted types do not co-occur with each other on this slice. **Skip `--period-bins`.** Do not invent sequence features. Keep `ontfangen_start` as composition root/partition; graph shape is diagnostic, not a template inventory.

**Next:** STEPT1e0 ontfangen inventory → STEPT1e partition probe (not another A until typology gaps closed).

## Period matrix

Skipped (1780 already kills accepted↔accepted).