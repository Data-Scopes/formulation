# STEPT1a — Appointment formula-type measure

**Status:** full eval after T1a-fix (welkom cue-window bootstrap). Metrics in `formula_type_appointment_metrics`.

```bash
uv run python scripts/eval_appointment_formula_type.py
```

## Results (RNG 20261019, cut=6.0 p20-holdout)

| Gate | Result |
|------|--------|
| Beats pre-1731 sessie floor (0.235) | **PASS** — model recall **0.816** (n=664) |
| Post-1731 ≥ ~0.60 | **PASS** — **0.832** (n=2541) |
| FP rate on N=500 negatives | **PASS** — **0.000** (0/500); popularity weight **9.21** |
| Welkom cloud learns variants | **PASS** — **2251/2313** accepts (was 0/2564) |

Overall model recall **0.829** vs wording `welkom`∪`sessie` 0.948 / `sessie` 0.924 (Δ −0.12 / −0.09).

## T1a-fix (cleared)

Empirical canonic `is den selven verwelkomt` + ±6-token cue windows + punct-stripped align tokens. Bootstrap input: 2309/2564 texts with cue → 2313 windows → **2251 accepted**.

## Side-effect (cut=6.0)

p20 holdout positives land at perfect welkom score (4 slots × 1.5). Sessie cloud max ≈ 3.0 never clears the cut — scoring is **welkom-led**. Recall dropped vs pre-fix (0.86/0.94 → 0.82/0.83) because the cut is stricter, not because the cloud failed. Optional later: dual-cut / normalize by template length / keep sessie as OR under its own p20.

## Period refresh (`--family appointment`)

| Bin | Diagonal recall | Cut |
|-----|----------------:|-----:|
| 1700–1724 | 0.808 | 6.0 |
| 1725–1749 | 0.875 | 3.5 |
| 1750–1774 | 0.899 | 6.0 |
| 1775–1799 | 0.812 | 6.0 |

No recalibrate signals (adjacent-backward all ≥ 0.5). Soft mid-bin slip remains (1750→1725 recall 0.776, Δ −0.10).

## Next

- Optional: openings `--family all`, or dual-cut so sessie recovers short-template positives.  
- Or STEPT1b / next typology step. Clear chat before starting.
