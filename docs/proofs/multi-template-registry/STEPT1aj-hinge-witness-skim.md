# STEPT1aj — Hinge witness near+mid skim (NOTES)

**Status:** code + emit done; **human fill pending**.  
**Guide:** [`plans/steps/STEPT1aj-hinge-witness-skim.md`](../../../plans/steps/STEPT1aj-hinge-witness-skim.md)  
**Ontology / cues:** DECISIONS 2026-10-26 formula-in-effect + decision-polarity surface cues.

```bash
uv run pytest tests/test_formula_hinge_witness_skim.py -q
uv run python scripts/run_formula_hinge_witness_skim.py --fixture-only
uv run python scripts/run_formula_hinge_witness_skim.py
# After fill:
uv run python scripts/run_formula_hinge_witness_skim.py --ingest
uv run python -m data_io.check
```

## Deliverables

| Logical name | Role |
|--------------|------|
| `formula_hinge_witness_skim_xlsx` | near+mid workbook; blank `human_keep` / `human_note` |
| `formula_hinge_witness_skim_metrics` | Emit (or ingest) summary |
| `formula_hinge_witness_verdicts` | Filled rows only (after `--ingest`) |

## Emit (from STEPT1ai adjudication)

| Metric | Value |
|--------|------:|
| n_adjudication | 1261 |
| n_skim (near+mid) | 92 |
| near | 20 |
| mid | 72 |
| far parked | 1169 |

## Gates

| Gate | Result |
|------|--------|
| Skim = near+mid only; far excluded; counts match STEPT1ai | **PASS** |
| Emit blanks human_keep/human_note; guide vocab present | **PASS** |
| Ingest refuses unknown keep; filled-only; no template/ledger mutate | **PASS** (unit) |
| No auto-promote mid/far | **PASS** |

## Human fill (owed)

Vocab: `variant` / `split` / `composition` / `reject`. Watchwords: afgewezen; Naar Y gestuurt voor advies (post-goedgevonden); afgehandeld te worden; resolutie commissoriaal; hebben … geexamineerd; op advies van; exposition citations of these / earlier resoluties → composition.

## Next

Fill skim → `--ingest` → NOTES verdict tallies. Then seed gaps or name `voordracht`. Clear chat before next step.
