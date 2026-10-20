# STEPR0 — Register retrieval inputs

**Goal:** Point `data_io` at `resolutions_flat` and the delegates gold (`resolutie_refs`) without copying files or hardcoding paths in Python.  
**Done when:** both logical names resolve; `uv run python -m data_io.check` shows them; grain and year coverage are recorded.

## Prerequisites

Read [`docs/DATA.md`](../../docs/DATA.md) and [`plans/milestones/R1-aanstelling-retrieval.md`](../milestones/R1-aanstelling-retrieval.md). Formula STEP0–1 are done; do not start formula STEP2 in this session.

## You do

Committed `data_manifest.toml` already declares the logical names. Copy the local override if you do not have `data_manifest.local.toml`:

```bash
cp data_manifest.local.toml.example data_manifest.local.toml
# Uncomment the Track R absolute-path blocks. Do not commit this file.
uv run python -m data_io.check
```

Then inspect (schema / counts only — no join, no model):

```bash
uv run python -c "
from data_io import resolve, load
import pandas as pd
import pyarrow.parquet as pq
import re

flat_path = resolve('resolutions_flat')
pf = pq.ParquetFile(flat_path)
print('parquet', flat_path)
print('rows', pf.metadata.num_rows)
print('schema', pf.schema_arrow)
df = load('resolutions_flat')
print('columns', list(df.columns))
print('id sample', df['id'].head(3).tolist() if 'id' in df.columns else None)
if 'date' in df.columns:
    years = pd.to_numeric(df['date'].astype(str).str[:4], errors='coerce')
    print('year min/max', int(years.min()), int(years.max()))
    print('n 1626-1630', int(((years >= 1626) & (years <= 1630)).sum()))
    print('n 1705-1795', int(((years >= 1705) & (years <= 1795)).sum()))

gold_path = resolve('delegates_resolutie_refs')
print('gold', gold_path)
gold = pd.read_excel(gold_path)
print('gold rows', len(gold), 'cols', list(gold.columns)[:20])
refs = gold['resolutie_refs'].dropna().astype(str)
refs = refs[refs.str.strip() != '']
urns = []
for cell in refs:
    urns.extend([p.strip() for p in re.split(r'[;,\s]+', cell) if 'urn:republic:' in p])
print('rows with refs', len(refs), 'urns', len(urns), 'unique', len(set(urns)))
years_u = [int(m.group(1)) for u in urns if (m := re.search(r'date-(\d{4})-', u))]
print('urn year min/max', min(years_u) if years_u else None, max(years_u) if years_u else None)
"
```

**Do not commit** `data_manifest.local.toml`. Keep committed `[tiers.warm]` as `data/warm` — do not remount warm onto the 2TB disk.

## Cursor guides

- Register `[datasets.resolutions_flat]` and `[datasets.delegates_resolutie_refs]` in `data_manifest.toml` **before** any Python references.
- Machine paths (2TB parquet, rc5 xlsx) live only in gitignored `data_manifest.local.toml` as **absolute** `path` overrides (`data_io` does not `expanduser` dataset paths).
- Gold is `resolutie_refs` URNs, not a text column. Use the rc5 workbook, not the unique-table release (too few URNs).
- Record grain (paragraph vs whole resolution) and year overlap in `docs/DECISIONS.md`. Collapse, if needed, is STEPR1.
- `load()` does not dispatch `.xlsx`; inspect gold with `pd.read_excel(resolve(...))`.
- Do not copy `resolutions_flat`. Do not join URNs yet. Do not talk to Elasticsearch.

## Next step

[STEPR1-join-urns.md](STEPR1-join-urns.md)
