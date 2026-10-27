# STEPT1ai — Hinge witness adjudicate (NOTES)

**Status:** done (code + provenanced full run on disk). Soft membership only — mid does not mint/merge.  
**Guide:** [`plans/steps/STEPT1ai-hinge-witness-adjudicate.md`](../../../plans/steps/STEPT1ai-hinge-witness-adjudicate.md)  
**Ontology:** DECISIONS 2026-10-26 formula-in-effect (witness adjudication).

```bash
uv run pytest tests/test_formula_hinge_witness.py -q
uv run python scripts/run_formula_hinge_witness.py --fixture-only
uv run python scripts/run_formula_hinge_witness.py
uv run python -m data_io.check
```

## Deliverables

| Logical name | Role |
|--------------|------|
| `formula_hinge_witness_adjudication` | Per-witness best hinge + sim + band; human fields blank |
| `formula_hinge_witness_metrics` | Band counts, cuts, vectorizer, near-by-hinge hist |

## Settings

- Vectorizer: `char_wb` 3–5, `sublinear_tf=True`
- Cuts: near ≥ **0.80**, mid ≥ **0.50**, far &lt; 0.50
- Targets: hinge rows with non-null `canonic` (**14**); pockets excluded

## Fixture smoke

| Gate | Result |
|------|--------|
| Every row has best_hinge_id / best_sim / band | **PASS** |
| Pockets not in target set | **PASS** (14 targets from n=20 ledger) |
| Band counts sum to n_witnesses | **PASS** (8 → near 4 / mid 2 / far 2) |
| No write to human_keep / templates | **PASS** (`--fixture-only`) |

## Full run (`formula_family_candidates` exemplars)

| Metric | Value |
|--------|------:|
| n_witnesses | 1261 |
| n_hinge_targets | 14 |
| near | 20 |
| mid | 72 |
| far | 1169 |
| best_sim p50 / p90 | 0.069 / 0.385 |

Near hits by hinge (top): `advertentie` 4, `goedgevonden` 4, `in_handen` 2, `missive` 2, `requeste_op_de` 2, `voldoening` 2, `welkom_sessie` 2, `ontfangen` 1, `advies` 1.

## Gates

| Gate | Result |
|------|--------|
| Every scored witness has best_hinge_id / best_sim / band ∈ {near,mid,far} | **PASS** |
| No hinge target lacks canonic; pockets excluded | **PASS** |
| Band counts sum to n_witnesses; metrics record cuts + vectorizer | **PASS** |
| Script never writes human_keep / never mutates templates | **PASS** |

## Read

Far dominates (≈93%) — expected: archaeology exemplars are mostly not hinge-sized matches to the 14 seeded canonics. Near (20) confirms a thin variant shell; mid (72) is the human triage queue (split / composition / reject), **not** auto-mint.

## Next

Human skim **near** (confirm variant) + **mid** (split / composition / reject). Likely follow-up: name `voordracht` pocket, or mid-band hand triage. Clear the chat before the next step.
