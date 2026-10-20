# STEPL0 — Define missive-receipt type + seed inventory

**Goal:** Lock the document-type definition, register hand seed texts, and measure how often high-precision cues fire on `resolutions_flat` (sample year or vectorized scan — no model yet).  
**Done when:** seeds are in the manifest; cue hit counts are recorded in `docs/DECISIONS.md` or the step notes; `data_io.check` is clean for new logical names.

## Prerequisites

Read [`plans/milestones/L1-missive-receipt-retrieval.md`](../milestones/L1-missive-receipt-retrieval.md). Reuse `resolutions_flat` from Track R (`data_manifest.local.toml`). Do **not** start formula STEP2 or touch aanstelling selection in this session.

## Type (working definition)

Positive = whole resolution that:

1. Opens with receipt of a **missive** or **brief** (*ontfangen* / *ontfangen eenen brieff* / …), and
2. Closes with **no substantive resolution** (*geen resolutie is gevallen* / *geen resolutie vereischende* / close equivalents),

usually with *houdende advertentie* or similar in between.

## You do

1. Confirm seeds file exists: `tests/fixtures/missive_receipt_seeds.jsonl`.
2. Register in `data_manifest.toml`:

```toml
[datasets.missive_receipt_seeds]
tier = "hot"
path = "tests/fixtures/missive_receipt_seeds.jsonl"
phase = "explore"
description = "Hand seed texts for L1 missive-receipt (geen resolutie) type"
parent = ""
```

3. Run `uv run python -m data_io.check`.
4. Cue inventory (advise — user runs; prefer one year POC first):

```bash
uv run python - <<'PY'
import re
import pandas as pd
import pyarrow.parquet as pq
from data_io import resolve, load

seeds = load("missive_receipt_seeds")
print("seeds", len(seeds))

# High-precision close cues (tune in STEPL1 if noisy)
CLOSE = re.compile(
    r"geen\s+resolutie\s+(?:is\s+)?gevallen|"
    r"geen\s+resolutie\s+vere[iy]sch",
    re.I,
)
OPEN = re.compile(
    r"ontfangen\s+een(?:en)?\s+(?:missive|missiue|brief|brieff)",
    re.I,
)

# POC: one year from harvest-era print if available
path = resolve("resolutions_flat")
# Column projection only — adjust year filter to a light slice you already use
import pyarrow.compute as pc
table = pq.read_table(path, columns=["id", "date", "resolutions_text"])
df = table.to_pandas()
df["year"] = pd.to_numeric(df["date"].astype(str).str[:4], errors="coerce")
# Start narrow — e.g. 1780 or 1705 — then widen
year = 1780
slice_ = df.loc[df["year"] == year]
text = slice_["resolutions_text"].fillna("").astype(str)
open_hit = text.str.contains(OPEN)
close_hit = text.str.contains(CLOSE)
both = open_hit & close_hit
print(f"year {year}: n={len(slice_)} open={open_hit.sum()} close={close_hit.sum()} both={both.sum()}")
# Spot-check a few "both" vs open-only (open-only often aanstelling/referral)
print("open-only sample ids", slice_.loc[open_hit & ~close_hit, "id"].head(5).tolist())
print("both sample ids", slice_.loc[both, "id"].head(5).tolist())
PY
```

5. Record counts + whether open-only is dominated by aanstellingen in a short DECISIONS note (STEPL0 inventory).

## Cursor guides

- Register dataset **before** code references it.
- Do not hardcode `/Volumes/…` paths.
- Do not write a classifier yet (that is STEPL2).
- Do not mix Track R `aanstelling_*` outputs into L1 positives without an explicit exclusion list.

## Next

STEPL1 — build `missive_receipt_labelled` (seed/cue positives + 10× overig; exclude `aanstelling_selected` ids from positives).
