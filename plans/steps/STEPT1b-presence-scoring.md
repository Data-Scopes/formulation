# STEPT1b — Formula-type presence scoring (with popularity weights)

**Goal:** Score a year slice of `resolutions_flat` for **presence** of accepted (and optional provisional) formula types; apply IDF-style popularity weights; summarise co-occurrence bags.  
**Done when:** provenanced `formula_type_presence_scores` + `formula_type_presence_metrics` written; NOTES judge whether bags look like templates or fragments; `data_io.check` clean.

**Prerequisite:** STEPT1a PASS (appointment) + STEPT1a2 PASS (advies). Openings are **provisional** bag fillers only — not accepted formula types yet.

## You do

```bash
uv run pytest tests/test_formula_type_presence.py -q
uv run python scripts/run_formula_type_presence.py --fixture-only

# Default: POC year 1780, appointment + advies + provisional openings
uv run python scripts/run_formula_type_presence.py

# Accepted types only (faster; no openings)
uv run python scripts/run_formula_type_presence.py --no-openings

# Appointment + openings (skip advies)
uv run python scripts/run_formula_type_presence.py --no-advies

# Cap rows for a smoke on real data
uv run python scripts/run_formula_type_presence.py --limit 200

uv run python -m data_io.check
```

## Measurements (required)

| Metric | Where |
|--------|--------|
| Per-type `hit_rate` / `n_present` / `operating_cut` | metrics.types |
| Per-type `popularity.weight` from year-slice hit rate | metrics.types |
| `score_weighted` on every score row | scores |
| Bag size histogram (`n_present` 0 / 1 / 2+) | metrics.bags |
| Top co-occurrence patterns (sorted type sets) | metrics.bags.top_patterns |
| `appointment_accepted` / `advies_accepted` / `openings_provisional` | metrics |

## Eval gates (NOTES after run)

1. Appointment hit rate on the year is sparse (few %), weight high — not near-universal.  
2. Advies hit rate sparse-to-moderate; weight between appointment and ubiquitous openings.  
3. Opening hit rates (if enabled) are higher → lower popularity weights.  
4. Most resolutions have 0 types; multi-type bags are rare (watch appointment∩advies).  
5. **Judgment:** do bags look like recognisable resolution templates, or fragments? (If fragments → STEPT1c position / more.)

## Do not

- Treat openings as accepted formula types  
- Redefine the appointment or advies operating cut (freeze from STEPT1a / STEPT1a2 metrics when present)  
- Score full 18c in this step (year POC first; widen only as a follow-up)  
- Use `praeside_start` / `praesentibus_start` as types  

## After this step

Mark STEPT1b (or T1b-refresh) in `PLAN.md`. Next: STEPT1c refresh with advies if bags still fragments, or another A family / sieve. Clear the chat before the next step.
