# STEPT1k — Requeste opener formula-type measure (NOTES)

**Status:** pending full eval (fixture smoke only until `--refresh-gold`).

```bash
uv run python scripts/eval_requeste_formula_type.py --refresh-gold
uv run python -m data_io.check
```

## Results (fill after full run)

| Gate | Result |
|------|--------|
| Overall recall ≥ 0.70 | |
| FP rate ≤ 0.05 on N=500 | |
| Cue-window accepts ≫ 0 | |

| Slice | Model recall | Wording requeste/rekest | Δ |
|-------|-------------:|------------------------:|--:|
| Overall | | | |
| Pre-1731 | | | |
| Post-1731 | | | |

## Notes

- Empirical canonic: `IS ter Vergaderinge geleesen de Requeste` (STEPT1j empty-band head; Track S framing skeleton).
- Gold = ES `rekest`; formula type id = `requeste_geleesen` (opener ≠ ES type name).
- Provisional `requeste_start` presence stays provisional until gates PASS.

## Next

- **STEPT1l** — subtype characterisation under requeste+ (mirror STEPT1f).  
Clear chat before starting.
