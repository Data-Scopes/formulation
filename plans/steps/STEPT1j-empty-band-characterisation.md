# STEPT1j — Empty-band characterisation (+ tighter fp_cut)

**Goal:** Characterise the STEPT1i **empty** undecided band (no known formula hits): ES type mix, length, flag catalogue, stratified text sample; optionally sweep **tighter `fp_cut`** values to see whether fingerprints split the one-mass cluster.  
**Done when:** provenanced metrics/scores/sample written; NOTES name readable shapes + whether any `fp_cut` is discriminative; `data_io.check` clean; `PLAN.md` updated.

**Prerequisite:** STEPT1i PASS; `composition_unknown_scores` + `ontfangen_partition_scores` on disk for 1780. Doctrine: [`plans/milestones/T1-unknown-first.md`](../milestones/T1-unknown-first.md).

## Constraint (locked)

- Object = **empty** composition band (unexplained = no presence hits), not cover-unknown and not novel_tail (still 0).
- Inventory + reading only — **do not mint blueprints** from cluster n, top flag combos, or type mix head.
- Reuse STEPT1e partition scores for ES types / known-set tags — **no ES remget**.
- Fingerprint sweep: fit similarity **once**, re-cluster at each cut. Clusters ≠ types.

## You do

```bash
uv run pytest tests/test_empty_band.py -q

uv run python scripts/run_empty_band_characterisation.py --fixture-only

# Full 1780 (structure + fp_cut sweep 0.15/0.30/0.45/0.60; operating labels @0.45)
uv run python scripts/run_empty_band_characterisation.py --year 1780

# Structure only (cheap)
uv run python scripts/run_empty_band_characterisation.py --year 1780 --skip-fingerprint

uv run python -m data_io.check
```

Fill / judge: [`docs/proofs/multi-template-registry/STEPT1j-empty-band-characterisation.md`](../../docs/proofs/multi-template-registry/STEPT1j-empty-band-characterisation.md) — **by reading the sample**, not by crowning top clusters as types.

## Design locks

| Piece | Rule |
|-------|------|
| Universe | `composition_unknown_scores` where `motif_class == empty` |
| ES / known | Join `ontfangen_partition_scores` (no remget) |
| Characteristics | `proposition_type` mix, word-count length, `formula_documents` flag rates + combo catalogue |
| Fingerprints | Optional cut sweep; default cuts `0.15,0.30,0.45,0.60`; operating labels at `0.45` |
| Sample | Stratified by type × length (± top fp clusters) for NOTES reading |

## Measurements (required)

| Piece | Where |
|-------|--------|
| `n_empty` + type mix | metrics |
| Length median / IQR (overall + per major type) | metrics.length / by_proposition_type |
| Flag focus rates + combo catalogue | metrics |
| Known-set leakage (L1/R1/advies; ontfangen sanity ~0) | metrics.known_set_leakage |
| Per-cut: n_clusters, share_largest, singletons | metrics.fingerprint_sweep.by_cut |
| Stratified sample | `empty_band_sample` |

## Eval gates (NOTES)

1. Is empty **one** ES-type mass (e.g. mostly rekest) or several structural pockets?
2. Does any tighter `fp_cut` leave `share_largest_cluster` ≪ 0.99 with readable multi-member clusters — or still one mass / mostly singletons?
3. Call: name ≤1 sparse shape worth a formula/kind probe, or park / add presence types first — **not** mint blueprints from empty n≈1329.

## Do not

- Promote proto-blueprints or new `formula_templates` rows
- Mint types from fingerprint clusters or combo-chart head
- Unpark STEPT1e1
- ES live text remget / re-run STEPT1i unless scores missing
- Treat STEPT1h high_unknown as this universe

## After this step

Mark STEPT1j in `PLAN.md`. Follow NOTES call. Clear the chat before the next step.
