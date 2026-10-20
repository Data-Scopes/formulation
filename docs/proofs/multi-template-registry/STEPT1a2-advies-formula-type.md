# STEPT1a2 — Advies formula-type measure (NOTES)

**Status:** PASS (full eval after `--refresh-gold`). Metrics in `formula_type_advies_metrics`.

```bash
uv run python scripts/eval_advies_formula_type.py --refresh-gold
uv run python -m data_io.check
```

## Results (RNG 20261019, cut=4.12 p20-holdout)

| Gate | Result |
|------|--------|
| Overall recall ≥ 0.70 | **PASS** — **0.762** (n=950 of ~995 ES) |
| FP rate ≤ 0.05 on N=500 | **PASS** — **0.034** (17/500); popularity weight **3.38** |
| Cue-window accepts ≫ 0 | **PASS** — **686/895** (599/760 texts with cue) |

| Slice | Model recall | Wording `advi[sz]` | Δ |
|-------|-------------:|-------------------:|--:|
| Overall | 0.762 | 0.789 | −0.027 |
| Pre-1731 | 0.601 | 0.661 | −0.060 |
| Post-1731 | 0.801 | 0.820 | −0.020 |

## Notes

- Empirical canonic `geleesen het Advis van` holds; cloud learns OCR variants.
- Model trails wording slightly (same pattern as appointment after a strict p20 cut) — acceptable; type is alignment-defined, not the substring.
- Pre-1731 weaker (0.60) but no appointed floor for this family; post-1731 strong.
- `data_io.check` exit 1 is template `example_*` MISSING only; advies datasets ok.

## Next

- **T1b-refresh** (presence with accepted advies) — code wired; run year 1780.  
Clear chat before starting.
