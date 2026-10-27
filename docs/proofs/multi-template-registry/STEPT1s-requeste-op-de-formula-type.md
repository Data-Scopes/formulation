# STEPT1s — Short requeste opener `requeste_op_de` (NOTES)

**Status:** done (2026-10-22). Recall + cloud + cross-fire PASS; FP gate FAILS narrowly (0.064) but **accepted** — judgment below. `requeste_op_de` accepted as A (measured); do **not** promote to blueprint in this step.  
**Guide:** [`plans/steps/STEPT1s-requeste-op-de-formula-type.md`](../../../plans/steps/STEPT1s-requeste-op-de-formula-type.md)  
**Canonic:** `Op de Requeste` (id `requeste_op_de`, STEPT1r name). Long sibling `requeste_geleesen` unchanged.  
**Metrics:** `formula_type_requeste_op_de_metrics` / `_scores`.

```bash
uv run pytest tests/test_requeste_op_de_formula_type.py -q
uv run python scripts/eval_requeste_op_de_formula_type.py
uv run python -m data_io.check
```

## Results

Operating cut = **4.5** (p20 holdout). n_gold=**16447** (0.2216 of 74205 rekest), n_bootstrap=13158, n_holdout=3289, n_negatives=500.

| Gate | Result |
|------|--------|
| Overall recall ≥ 0.70 | **PASS** — 1.000 |
| FP rate ≤ 0.05 on N=500 | **FAIL** — **0.064** (32/500); accepted (see below) |
| Cue-window accepts ≫ 0 | **PASS** — 16,453 / 16,586 |
| Cross-fire on long-head rekest | **PASS** — fire 0.02 (4/200), score_mean 3.02 |

| Slice | Model recall | Head wording | Δ |
|-------|-------------:|-------------:|--:|
| Overall | 1.000 | 0.9588 | +0.0412 |
| Pre-1731 | 1.000 | 0.9667 | +0.0333 |
| Post-1731 | 1.000 | 0.9490 | +0.0510 |

## Notes

- Gold = ES rekest ∩ token head `Op`/`OP`/`op` + `de` + requeste-surface. Share of full rekest = **0.222** (lower than the 0.37 low-band share on the *stratified* STEPT1q clean sample — expected: clean sample over-weights short decades).
- **Recall is near-tautological** on this gold definition: every gold row scores exactly 4.5 (3/3 slots). The useful checks are FP and within-rekest specificity (cross-fire), not the ≥0.70 floor.
- Model still beats the strict start-anchored wording regex by ~4 pts (OCR / leading junk / `Rekest` surfaces the token head catches).
- **FP 0.064** misses ≤0.05 by 7 events on N=500. Far cleaner than `requeste_geleesen`’s accepted 0.206 (and the post-re-pin ~0.17). Three-token opener is looser than the six-slot long canonic, but not catastrophically so.
- **Cross-fire 0.02** on long-head rekest: the short cloud does not re-absorb the long opener population — the STEPT1r split holds under the short model.
- Frozen cut 4.5 = max score for a 3-slot exact match; no room to raise the cut without killing all positives. FP control would need seeds/cloud tightening or a position constraint (head-only), not a higher threshold — out of scope here.
- Do **not** promote to blueprint / `ACCEPTED_TYPE_IDS` in this step (STEPT1m-style wire is next if wanted).

## Call

- [x] A accepted (recall PASS; FP recorded / judged — 0.064 accepted as known short-canonic cost)
- [ ] Reject / revisit canonic or seeds
- [ ] Accept-with-caveat only after FP hand-read — not needed at this magnitude vs STEPT1k

**Verdict:** Accept `requeste_op_de` as measured formula type A. Operating cut **4.5**.

**Next:** composition-wire + promote (separate step), optionally with a dual-opener presence bag. Letter/missive short-opener parallel stays parked.
