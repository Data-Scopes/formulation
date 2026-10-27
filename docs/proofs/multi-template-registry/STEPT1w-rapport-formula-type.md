# STEPT1w — Rapport opener formula-type measure (NOTES)

**Status:** PASS (full eval after `--refresh-gold`, 2026-10-25).  
**Guide:** [`plans/steps/STEPT1w-rapport-formula-type.md`](../../../plans/steps/STEPT1w-rapport-formula-type.md)  
**Canonic:** `IS gehoord het rapport van` · id `rapport_gehoord` · gold = ES `proposition_type=rapport` (n=13,928).

```bash
uv run pytest tests/test_rapport_formula_type.py -q
uv run python scripts/eval_rapport_formula_type.py --refresh-gold
# later:
uv run python scripts/eval_rapport_formula_type.py
uv run python -m data_io.check
```

## Results (RNG 20261019, cut=7.5 p20-holdout)

| Gate | Result |
|------|--------|
| Overall recall ≥ 0.70 | **PASS** — **0.895** (n=13,928) |
| FP rate ≤ 0.05 on N=500 | **PASS** — **0.006** (3/500); popularity weight **5.12** |
| Cue-window accepts ≫ 0 | **PASS** — **10,642 / 12,839** (10,502/11,142 texts with cue) |

| Slice | Model recall | Wording `rapport` | Δ |
|-------|-------------:|------------------:|--:|
| Overall | 0.895 | 0.942 | −0.047 |
| Pre-1731 | 0.848 | 0.886 | −0.038 |
| Post-1731 | 0.924 | 0.977 | −0.053 |

Align: gold mean **7.23** (min 2.75 / max 7.5); neg mean **2.78** (min 0.75 / max 7.5). Operating cut **7.5** = full 5-slot exact-hit ceiling (p20 sits on the max — ≥80% of holdout gold is a clean canonic hit).

## Notes

1. **Sharp A.** STEPT1u’s “clearest residual skeleton” call holds under full ES gold: high recall, almost no FP (0.006 — cleanest FP of the opener series so far).
2. **Model trails wording** (~5 pts) — same pattern as missive/advies: bare `rapport` catches mid-text / variant surfaces the DAG at cut 7.5 does not. Type stays alignment-defined.
3. **Pre-1731 softer** (0.85) but still well above the 0.70 floor; no family break appointed.
4. **Cut at ceiling** is informative: the canonic is highly stereotyped on gold; residual FNs are the non-stereotyped tail, not a cut-calibration problem. Low 18c surface drift here is mainly **printing standardisation** (Resolutiën as print), not just formula rigidity — expect more orthographic spread if the same opener is ever measured on pre-print / manuscript periods.

## Call

1. **Accept `rapport_gehoord` as A** (recall PASS, FP PASS).
2. Do **not** promote / wire into `ACCEPTED_TYPE_IDS` this step.
3. **Next:** blueprint promotion + 6-core composition-unknown re-run (STEPT1m-style), or park and take voordracht / Doc B L3.

Clear the chat before the next step.
