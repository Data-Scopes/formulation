# STEPT1u — Empty-band re-characterisation under 5-core (NOTES)

**Status:** done (2026-10-22). Inventory + reading; no blueprints minted.  
**Guide:** [`plans/steps/STEPT1u-empty-band-5core.md`](../../../plans/steps/STEPT1u-empty-band-5core.md)  
**Baseline:** STEPT1j empty n=**1329** (rekest 0.53); STEPT1t 5-core empty n=**342** (0.122).  
**Reuse:** `scripts/run_empty_band_characterisation.py --year 1780 --skip-fingerprint` (overwrote `empty_band_*`).

```bash
uv run pytest tests/test_empty_band.py -q
uv run python scripts/run_empty_band_characterisation.py --year 1780 --skip-fingerprint
uv run python -m data_io.check
```

## 1. Structural profile (1780, 5-core empty)

| Metric | STEPT1j | STEPT1u |
|--------|--------:|--------:|
| n_empty | 1329 | **342** |
| length median (q1–q3) | 194 (108–383) | **139** (89–302) |
| head type | rekest 0.53 | **voordracht 0.234** |
| rekest share | 0.53 | **0.105** |
| known leakage L1 / R1 / advies | 1 / 2 / 2 | **0 / 2 / 1** |
| ontfangen_present | 0 | **0** |

### Type mix (new head)

| proposition_type | n | frac | words med | notes |
|------------------|---:|-----:|----------:|-------|
| voordracht | 80 | 0.234 | 110 | Provincial / praeses bring-in; `gedelibereert` 0.61, `goedgevonden` 0.60; no `requeste_start` |
| rapport | 49 | 0.143 | **340** | Long; `rapport_start` 0.80; decision-shaped |
| onbekend | 49 | 0.143 | 130 | Mixed; `ontfangen`/`advertentie`/`geen_resolutie` ~0.47–0.56 |
| missive | 45 | 0.132 | 114 | Below missive cut or atypical; `ontfangen_start` 0.70 |
| conclusie | 41 | 0.120 | 125 | Sharp: `handen`/`in handen` 0.69; almost no gedelibereert |
| rekest | 36 | 0.105 | 142 | Residual only (was 700) |
| (none) / memorie / … | 42 | — | — | Thin tail |

### Combo catalogue (top; not subtypes)

| combo | n |
|-------|--:|
| advertentie + geen_resolutie + ontfangen_start | 29 |
| goedgevonden + handen + in handen | 26 |
| vergaderinge_start alone | 17 |
| goedgevonden alone | 10 |

139 unique combos; top-5 share 0.29 — same long-tail shape as STEPT1j, different head (L1-ish + conclusie/handen, not requeste scaffolding).

## 2. Sample shapes (read `empty_band_sample`)

- **Voordracht:** `DE Heer … praesideerende, heeft … voorgedragen`; provincial `Gedeputeerden … hebben … ingebragt`; also gecommitteerden-rapport surfaces mis-typed as voordracht. Varied — largest pocket, not one canonic.
- **Rapport:** very stable `IS gehoord het rapport van de Heeren … Gedeputeerden … in gevolge … Resolutie commissoriaal … geëxamineert …`. Long, sparse vs openers, clear skeleton.
- **Conclusie:** `OP/DE Conclusie van eisch/versoek/antwoord …` + **handen** referral — same sparse pocket STEPT1j already named; still here.
- **Missive residual:** some real `Ontfangen een Missive…` below operating cut; some ES-missive rows that open as Conclusie/resumtie.
- **Rekest residual:** mostly rapport-/memorie-headed texts still labelled rekest in ES — not the old long/short requeste openers.
- **Onbekend:** resumtie + memorie/rapport mix; L1-ish advertentie closes without accepted missive hit.

## 3. Call

1. **Rekest is no longer the empty problem** (700 → 36). Five openers did their job.
2. Remaining empty is **several pockets**, not one mass. Clearest named skeletons:
   - **rapport opener** (`IS gehoord het rapport…`) — sharpest A candidate
   - **conclusie + handen** — still ~41; STEPT1j already flagged
   - **voordracht** — largest n but surface-varied (ingebragt / voorgedragen / gecommitteerden-rapport)
3. **Call:** next A probe = **rapport opener** (or short voordracht characterisation if preferring the head by n). Do **not** mint from n=342. Letter short-opener and L2 stay parked. Fingerprint sweep skipped (STEPT1j already showed 0.45 → mostly singletons).

Clear the chat before the next step.
