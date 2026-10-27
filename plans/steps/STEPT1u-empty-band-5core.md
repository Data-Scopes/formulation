# STEPT1u — Empty-band re-characterisation (5-core)

**Goal:** Re-characterise composition-unknown **empty** after STEPT1t’s five-opener accepted core (n=342 / 0.122 on 1780). STEPT1j’s empty (n=1329) was rekest-headed; that mass is now covered — what’s left?  
**Done when:** provenanced `empty_band_*` rewritten from current `composition_unknown_scores`; NOTES name remaining pockets vs STEPT1j; call (probe / park / L2); `data_io.check` clean; `PLAN.md` updated.

**Prerequisite:** STEPT1t PASS; `composition_unknown_scores` on disk for 1780 with 5-core empty. Doctrine: [`plans/milestones/T1-unknown-first.md`](../milestones/T1-unknown-first.md). Baseline: [`STEPT1j NOTES`](../../docs/proofs/multi-template-registry/STEPT1j-empty-band-characterisation.md).

## Constraint (locked)

- Object = **empty** under the **current** 5-core scores (`motif_class == empty`), not the archived STEPT1j 1329-row band.
- Inventory + reading only — **do not mint** blueprints from type mix, flag combos, or fp clusters.
- Reuse STEPT1e partition scores for ES types / known-set tags — **no ES remget**.
- Compare to STEPT1j pockets in NOTES (what disappeared vs what remains).

## You do

```bash
uv run pytest tests/test_empty_band.py -q

# Structure + sample (fingerprint optional; n≈342 is cheap)
uv run python scripts/run_empty_band_characterisation.py --year 1780 --skip-fingerprint
# or full:
uv run python scripts/run_empty_band_characterisation.py --year 1780

uv run python -m data_io.check
```

Fill: [`docs/proofs/multi-template-registry/STEPT1u-empty-band-5core.md`](../../docs/proofs/multi-template-registry/STEPT1u-empty-band-5core.md).

## Design locks

| Piece | Rule |
|-------|------|
| Universe | `composition_unknown_scores` where `motif_class == empty` (post-STEPT1t) |
| Reuse | Existing `formulation/empty_band.py` + `scripts/run_empty_band_characterisation.py` — no new scorer |
| ES / known | Join `ontfangen_partition_scores` (no remget) |
| Sample | Stratified by type × length for NOTES reading |

## Eval gates (NOTES)

1. Type mix vs STEPT1j: is rekest gone? What’s the new head?
2. Named ≤2 readable residual shapes (or “thin tail / noise”)?
3. Call: next probe / park empty / pivot to L2 — **not** mint from n=342.

## Do not

- Promote new `formula_templates` rows
- Unpark letter short-opener or STEPT1e1 from empty n alone
- Re-run STEPT1i / presence unless scores missing
- Treat this as STEPT1j2 R1/L1 retrieval redo

## After this step

Mark STEPT1u in `PLAN.md` + T1 milestone. Follow NOTES call. Clear the chat before the next step.
