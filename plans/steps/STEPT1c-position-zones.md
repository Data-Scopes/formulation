# STEPT1c — Formula-type position / zone

**Goal:** Attach **document position** (opening / body / close) to formula-type hits via DAG span midpoints; ask whether zone-conditioned bags look like templates after STEPT1b judged presence bags as fragments.  
**Done when:** provenanced `formula_type_position_scores` + `formula_type_position_metrics` written; NOTES judge whether position separates families / composes templates; `data_io.check` clean.

**Prerequisite:** STEPT1b / T1b-refresh PASS (bags = fragments; accepted appointment + advies). Same models and cuts as T1b-refresh (frozen STEPT1a / STEPT1a2; openings provisional).

## You do

```bash
uv run pytest tests/test_formula_type_position.py -q
uv run python scripts/run_formula_type_position.py --fixture-only

# Default: POC year 1780, appointment + advies + provisional openings
uv run python scripts/run_formula_type_position.py

# Accepted types only (faster)
uv run python scripts/run_formula_type_position.py --no-openings

# Cap rows for a smoke on real data
uv run python scripts/run_formula_type_position.py --limit 200

uv run python -m data_io.check
```

## Measurements (required)

| Metric | Where |
|--------|--------|
| Per-type zone histogram among presents (`opening` / `body` / `close`) | metrics.types[].zone |
| `frac_in_expected_zone` (openings+advies→opening; appointment→close) | metrics.types[] |
| `mid_norm` median per type | metrics.types[] |
| Zone-tagged co-occurrence patterns `(type, zone)` | metrics.bags.top_zone_patterns |
| Bare type bags (compare to T1b-refresh) | metrics.bags.top_patterns |

Zone rule: `mid_norm = (start_idx + end_idx) / 2 / n_tokens`; tertiles at 1/3 and 2/3 (override with `--opening-cut` / `--close-cut`).

## Eval gates (NOTES after run)

1. Provisional openings (when they fire) concentrate in **opening** more than chance.  
2. Appointment presents are **not** mostly opening (1780: mostly **close**).  
3. Advies home zone recorded (prior = opening; update if mid_norm says otherwise).  
4. Zone-tagged patterns vs bare bags: does zone show where advies sits relative to ontfangen?  
5. **Judgment:** does position turn fragments into templates? If still fragments → STEPT1d order, or another A family.

## Do not

- Treat openings as accepted formula types  
- Redefine the appointment or advies operating cut  
- Use ES `evidence` labels as the zone definition in this step (token mid-span only; ES is a later cross-check)  
- Use `praeside_start` / `praesentibus_start` as types  
- Score full 18c in this step (year POC first)

## After this step

Mark STEPT1c / T1c-refresh in `PLAN.md`. Next: STEPT1d order refresh (ontfangen → advies when both present), or another A family. Clear the chat before the next step.
