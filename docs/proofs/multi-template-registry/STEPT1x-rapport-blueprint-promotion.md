# STEPT1x — Rapport blueprint promotion (NOTES)

**Status:** done (2026-10-25). Gates 1–3 **PASS**. `rapport_gehoord` promoted to `role: "blueprint"`.  
**Guide:** [`plans/steps/STEPT1x-rapport-blueprint-promotion.md`](../../../plans/steps/STEPT1x-rapport-blueprint-promotion.md)  
**Baseline:** STEPT1t 5-core empty **0.122** on year 1780.  
**Canonic:** `IS gehoord het rapport van` · id `rapport_gehoord` · frozen cut **7.5** (STEPT1w).

```bash
uv run pytest tests/test_formula_type_presence.py tests/test_composition_unknown.py tests/test_formula_templates.py -q
uv run python scripts/run_formula_type_presence.py --year 1780
uv run python scripts/run_composition_unknown.py --year 1780
uv run python -m data_io.check
```

## What changed

`rapport_gehoord` (STEPT1w) wired into the shared accepted-core machinery — `composition_unknown.ACCEPTED_TYPE_IDS` now holds six openers:

- `formulation/formula_type_presence.py`: `fit_rapport_presence_model` / `load_frozen_rapport_cut` / `score_fn == "rapport"` / fixture.
- `formulation/composition_unknown.py`: `+ RAPPORT_ID`.
- `scripts/run_formula_type_presence.py`: `--no-rapport` / `--rapport-cut`.
- `tests/fixtures/formula_templates.jsonl`: new `rapport_gehoord` row, `role: "blueprint"`.

**Scope held:** five downstream modules untouched (same follow-up as STEPT1m/o/t). Period label remains `18c` / 1705–1796; promote evidence is the 1780 comparison year (recalibrate later for other periods).

## Results: STEPT1t 5-core vs STEPT1x 6-core (year 1780)

| Metric | STEPT1t (5-core) | STEPT1x (6-core) |
|---|---:|---:|
| n_universe | 2796 | 2796 |
| n_unique_exact_bags | 19 | 26 |
| n_unique_accepted_cores | 14 | 21 |
| n_proto_blueprints (support≥5) | 11 | 14 |
| empty (undecided, no hits) | 342 (0.122) | **300 (0.107)** |
| known_sparse | 2450 (0.876) | 2488 (0.890) |
| filler_star | 0 (0.000) | 0 (0.000) |
| novel_tail | 4 (0.001) | 8 (0.003) |

Presence: `rapport_gehoord` n_present=**63** (hit_rate 0.0225) at frozen cut 7.5.

**Headline:** empty shrinks (−42 / −0.015) — STEPT1u’s residual skeleton call holds under composition. Unlike STEPT1t (empty flat; dual-opener rename only), rapport pulls real empty mass into known cores. Solo `rapport_gehoord` clears support 42 with dominant 1.0.

## Proto-blueprint catalogue (6-core)

| accepted_core | support | n_unique_exact_bags | dominant_bag_frac |
|---|---:|---:|---:|
| `missive_ontfangen` | 1238 | 2 | 0.960 |
| `requeste_geleesen` | 733 | 1 | 1.000 |
| `requeste_geleesen` + `requeste_op_de` | 181 | 1 | 1.000 |
| `missive` + `requeste_geleesen` + `requeste_op_de` | 109 | 1 | 1.000 |
| `missive` + `requeste_geleesen` | 72 | 2 | 0.917 |
| `advies` + `requeste_geleesen` | 46 | 1 | 1.000 |
| **`rapport_gehoord`** | **42** | **1** | **1.000** |
| `appointment` + `missive` + `requeste_geleesen` | 20 | 1 | 1.000 |
| **`rapport` + `requeste_geleesen`** | **10** | **1** | **1.000** |
| `advies_geleesen` | 9 | 1 | 1.000 |
| `advies` + `missive` | 7 | 2 | 0.714 |
| `advies` + `requeste_geleesen` + `requeste_op_de` | 7 | 1 | 1.000 |
| `appointment` + `missive` | 7 | 2 | 0.857 |
| **`rapport` + `requeste_geleesen` + `requeste_op_de`** | **7** | **1** | **1.000** |

## Eval gates

1. **Empty/undecided shrink vs 0.122? PASS.** 0.122 → **0.107** (342→300).
2. **New accepted_core clears support≥5? PASS.** Solo rapport 42; +long requeste 10; +both requestes 7.
3. **dominant_bag_frac low-noise on rapport-bearing cores? PASS.** All three are 1.000; full catalogue 0.714–1.000.
4. **Call: promote.** Gate 3 holds. Promoted `rapport_gehoord` to `role: "blueprint"`.

## Next

Human-judged `opener_candidates` queue + measure→wire→propose-promote driver (voordracht / conclusie still named pockets). Or 6-core empty re-char. Clear the chat before the next step.
