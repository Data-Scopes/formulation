# STEPT1c — Position / zone (NOTES)

**Status:** PASS (1780). Position **separates** families; bags still **fragments**.  
**T1c-refresh:** PASS — accepted `advies_geleesen` zoned (prior opening holds softly).

```bash
uv run python scripts/run_formula_type_position.py
uv run python -m data_io.check
```

## Results — T1c-refresh (1780, n=2796, 4 types)

| Type | present | mid_norm median | zone mix | frac_expected |
|------|--------:|----------------:|----------|--------------:|
| `appointment_installation` | 28 | **0.90** | close 27 / body 1 / opening **0** | **0.96** → close |
| `advies_geleesen` | 74 | **0.032** | opening **50** / body 9 / close 15 | **0.68** → opening (soft) |
| `ontfangen_start` (prov.) | 1397 | **0.027** | opening **1392** / body 4 / close 1 | **0.996** |
| `requeste_start` (prov.) | 0 | — | — | — (dead at cut) |

### Zone-tagged bags (top)

| pattern | n | rate |
|---------|--:|-----:|
| `ontfangen`@opening alone | 1360 | 0.486 |
| `advies`@opening alone | 50 | 0.018 |
| `appointment`@close + `ontfangen`@opening | 25 | 0.009 |
| `advies`@close alone | 11 | 0.004 |
| `advies`@body alone | 7 | 0.003 |
| `advies`@close + `ontfangen`@opening | 4 | 0.001 |
| `advies`@body + `ontfangen`@opening | 2 | 0.001 |

Bare bags = T1b-refresh (multi 1.1%). Of the **6** advies∩ontfangen ids: advies lands **later** (body/close), not co-opening with ontfangen.

## Gates

| Gate | Result |
|------|--------|
| Openings concentrate in opening | **PASS** — ontfangen 99.6% |
| Appointment not mostly opening | **PASS** — 0% opening; 96% close |
| Advies home zone | **PASS soft** — median early (0.03); 68% opening, but 20% close / 12% body |
| Zone vs bare bags / vs openers | **PASS as discriminator** — solo advies ≈ opening; with ontfangen, advies shifts mid/late |
| Judgment | Position **keeps**; still **fragments** for template composition |

## Caveats

- Advies is **not** as zone-locked as ontfangen or appointment; opening prior stays, but expect body/close spills.
- `data_io.check` exit 1 is template `example_*` MISSING only; position datasets ok.

## Earlier run (pre-advies)

Appointment@close + ontfangen@opening; same fragment shape.

## Next

- **STEPT1d refresh** — order: does ontfangen precede advies when both present? (zone already hints yes on the 6).  
Clear chat before starting.
