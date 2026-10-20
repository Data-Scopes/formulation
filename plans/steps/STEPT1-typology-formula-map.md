# STEPT1-map — Typology ↔ formula characteristics

**Goal:** Map resolution kinds (STEPT0 + schemes) to formula evidence before any further classification. Make explicit what is typed, provisional, scheme-only, or overloaded.  
**Done when:** NOTES filled with layers + crosswalk + inventory + call; `PLAN.md` and `DECISIONS.md` updated; STEPT1e1 parked until the call says otherwise.

**Prerequisite:** STEPT0 profile on disk; schemes sample; T1a / T1a2 / T1e NOTES.

## You do

Docs only — read existing artifacts, write NOTES. No new scorer, script, or provenanced write.

```bash
# Optional: skim STEPT0 types (agent-safe)
uv run python -c "
from data_io import load
for r in sorted(load('typology_structural_profile'), key=lambda x: -(x.get('population_n') or 0)):
    print(r['proposition_type'], r.get('population_n'), r.get('population_pct'))
"
```

Fill / judge: [`docs/proofs/multi-template-registry/STEPT1-typology-formula-map.md`](../../docs/proofs/multi-template-registry/STEPT1-typology-formula-map.md).

Sources:

| Source | Role |
|--------|------|
| `typology_structural_profile` | ES type composition + characterisation |
| [`formula_schemes_sample.json`](../../docs/proofs/multi-template-registry/formula_schemes_sample.json) | Sketch: function / intention / proposition_type |
| STEPT1a / T1a2 / T1e NOTES | Accepted vs provisional formula evidence |
| [`docs/template-design-questions.md`](../../docs/template-design-questions.md) | North star (not a checklist) |

## Design locks

| Piece | Rule |
|-------|------|
| Object of typing | Resolution kinds + characteristics first |
| Formula detectors | Evidence for kinds / discourse roles — not free-floating classes |
| Schemes | **Hypothetical** sketch; expect partial fit; non-fit revises the hypothesis |
| Flags | Boilerplate surfaces, not archival outcomes |
| Ontfangen | Provisional partition, not accepted formula type |

## Do not

- Implement or run STEPT1e1 flag sieve
- Accept a new formula type
- Rewrite schemes JSON or re-run STEPT0
- Start another A family unless the NOTES call names a characterisation gap

## After this step

Follow NOTES call. Clear the chat before the next step.
