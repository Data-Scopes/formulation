# STEPT1e0 — Ontfangen population inventory

**Goal:** Inventory what is already known about the ontfangen composition-root population before a typology partition probe.  
**Done when:** NOTES written with counts, known-set overlaps, gap list, and call; `PLAN.md` updated.

**Prerequisite:** STEPT1b/c presence+zones on 1780; T1d graph smoke.

## You do

Read existing provenanced metrics (no rescoring, no ES):

```bash
# Optional: cheap overlap check (reads presence scores + known id sets)
uv run python -c "
from data_io import load
import pandas as pd
scores = pd.DataFrame(load('formula_type_presence_scores'))
ont = set(scores.loc[(scores.formula_type_id=='ontfangen_start') & scores.present, 'id'].astype(str))
print('ontfangen+', len(ont))
"
```

Fill / judge: [`docs/proofs/multi-template-registry/STEPT1e0-ontfangen-inventory.md`](../../docs/proofs/multi-template-registry/STEPT1e0-ontfangen-inventory.md).

## Do not

- Accept ontfangen as a formula type
- Rescore the year or run `--period-bins`
- Implement STEPT1e population probe in the same session
- Start another A family until inventory call says so

## After this step

Follow NOTES call (default: STEPT1e partition probe). Clear the chat first.
