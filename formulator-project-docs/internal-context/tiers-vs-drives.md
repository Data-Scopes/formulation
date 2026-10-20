---
cursor:
  subagentId: "bc-b1f5b1a0-2045-5d68-bfb4-d6f8ac9cb2c6"
---

# Where republic-formulas lives (tiers vs drives)

## Default: local in-repo

Committed `data_manifest.toml` uses relative roots:

| Tier | Root |
|------|------|
| hot | `.` |
| warm | `./data/warm` |
| scratch | `./output` |
| cold | `./data/cold` |

Sample corpus + S4 fixture ship under `data/warm/`. After you clone into
`~/develop/republic-formulas`, that checkout is self-contained locally.

`data_manifest.local.toml` is **optional**. Drive `/Volumes/...` overrides are
commented in the `.example` only for later large corpora — not required.

## Optional later

- Full S4 file from `~/develop/republic_ner_matching/output/...` via local.toml
- Warm/scratch/cold on external drives when you choose
