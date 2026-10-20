# STEPT1j2 — Empty-band R1/L1 retrieval probe

**Goal:** Score the STEPT1j empty band with the **frozen** R1/L1 char TF-IDF+LR contrast (not unsupervised fingerprints): P-bands × ES `proposition_type`.  
**Done when:** provenanced metrics/scores written; NOTES say whether L1 lights empty missives and whether R1 stays low; `data_io.check` clean; `PLAN.md` updated.

**Prerequisite:** STEPT1j PASS; `empty_band_scores`, `aanstelling_tfidf_harvest`, `missive_receipt_labelled`, `ontfangen_partition_scores` on disk.

## Constraint (locked)

- Diagnostic reuse of trained contrast — **not** L3 harvest, **not** a new requeste model, **not** blueprint minting.
- R1 = join frozen harvest (no refit). L1 = `fit_on_all_labelled` + score empty only (same frozen architecture as STEPL2).
- Buckets = R1 cuts (high > 0.85, low < 0.15) for both — L1 bands are diagnostic labels only.

## You do

```bash
uv run pytest tests/test_empty_band_retrieval.py -q

uv run python scripts/run_empty_band_retrieval_probe.py --fixture-only

# Full 1780 (R1 join + L1 refit/score on ~1329 empty texts)
uv run python scripts/run_empty_band_retrieval_probe.py --year 1780

# R1 only (cheap)
uv run python scripts/run_empty_band_retrieval_probe.py --year 1780 --skip-l1

uv run python -m data_io.check
```

Fill: [`docs/proofs/multi-template-registry/STEPT1j-empty-band-characterisation.md`](../../docs/proofs/multi-template-registry/STEPT1j-empty-band-characterisation.md) §5.

## Eval gates (NOTES)

1. R1 on empty mostly **low**? (Expected — appointment not the empty head.)
2. L1 **high** concentrated on ES missive (and maybe onbekend), not on rekest?
3. Call: confirms contrastive TF-IDF still useful for triage → proceed to requeste seed model; or L1 floods empty → re-read missive empty pocket first.

## Do not

- Run STEPL3 harvest / rescore full year with L1
- Mint types from high-band n
- Change R1/L1 hyperparameters
