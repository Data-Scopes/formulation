# STEPT1d — Order / composition (NOTES)

**Status:** PASS (1780 full year). Order **confirms** the trivial opener→install sequence (26/26); does **not** invent templates beyond T1c. Bags still fragments → next another A family or sieve residual.

```bash
uv run python scripts/run_formula_type_order.py
uv run python -m data_io.check
```

## Results (1780, n=2796, n_multi=26)

| Metric | Value |
|--------|------:|
| frac_zero / frac_one / frac_multi | 0.500 / 0.491 / **0.009** |
| top ordered multi | `ontfangen` → `appointment` (26) |
| frac expected ontfangen→appointment | **1.0** (26/26) |
| requeste→appointment | n_both=0 (requeste dead at cut) |
| order_vs_bag distinct orders | **1** (bag has only one order) |

### Zone-tagged ordered multi

| sequence | n |
|----------|--:|
| ontfangen@opening → appointment@close | 25 |
| ontfangen@opening → appointment@body | 1 |

## Gates

| Gate | Result |
|------|--------|
| Opening precedes appointment when both present | **PASS** — 26/26 |
| Ordered sequences ≠ mere bags | **NO** — one multi bag, one order; order ≈ zone already known |
| Judgment | Order **keeps** as soft constraint on rare multi; **still fragments** for templates → stop sequence features |

## Caveats

- `data_io.check` exit 1 is template `example_*` MISSING only; order datasets ok.
- Multi rate unchanged from T1b/c (0.9%); composition does not grow the multi set.

## Next

- Another sharp A family (STEPT1a-style), or sieve residual (STEPT1 §6-alt) — **not** more order/sequence probes.  
Clear chat before starting.
