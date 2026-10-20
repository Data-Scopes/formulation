# STEPT1b — Presence scoring (NOTES)

**Status:** PASS (1780). Bags = **fragments**.  
**T1b-refresh:** PASS — accepted `advies_geleesen` in bags (frozen T1a2 cut 4.12).

```bash
uv run python scripts/run_formula_type_presence.py
uv run python -m data_io.check
```

## Results — T1b-refresh (1780, n=2796, 4 types)

| Type | present | hit_rate | weight | note |
|------|--------:|---------:|-------:|------|
| `appointment_installation` | 28 | **0.010** | **4.60** | sparse; accepted (cut 6.0) |
| `advies_geleesen` | 74 | **0.0265** | **3.63** | sparse; accepted (cut 4.12) |
| `ontfangen_start` (prov.) | 1397 | **0.500** | 0.69 | near-half year — uninformative |
| `requeste_start` (prov.) | 0 | 0.000 | 9.21 | cut=6.0 never fires |

### Bags

| size | n | frac |
|-----:|--:|-----:|
| 0 | 1329 | 0.475 |
| 1 | 1435 | 0.513 |
| 2 | 32 | **0.011** |

Top patterns: `ontfangen_start` alone (48.8%); `advies_geleesen` alone (2.4%); `appointment`∩`ontfangen` (0.9%); `advies`∩`ontfangen` (0.2%); `appointment` alone (2 rows). **No** `appointment`∩`advies` in top patterns.

## Gates

| Gate | Result |
|------|--------|
| Appointment hit rate sparse + high popularity weight | **PASS** — 1%, weight 4.60 |
| Advies sparse-to-moderate; weight between appointment and openings | **PASS** — 2.7%, weight 3.63 |
| Opening rates higher → lower weights | **PASS** (ontfangen); requeste dead at cut |
| Bag histogram: mostly 0, rare multi | **PASS** — multi 1.1% (was 0.9%) |
| Judgment: templates vs fragments | **fragments** — advies mostly solo; no accepted-type co-template |

## Caveats

- Provisional openings still dominate bags; advies adds a clean sparse accepted type but does not compose with appointment.
- `data_io.check` exit 1 is template `example_*` MISSING only; presence datasets ok.

## Earlier run (pre-advies, for comparison)

Appointment 28/1.0%; ontfangen 50%; multi 0.9% — same fragment shape; advies alone accounts for the small multi bump and the new solo pattern.

## Next

- **STEPT1c refresh** (position/zone with advies in the bag), or another A family / sieve residual.  
Clear chat before starting.
