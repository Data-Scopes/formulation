---
cursor:
  subagentId: "bc-8d182330-3baf-56e8-8967-f41635449bf8"
---

# Mac setup blocker — not on RiksMacBook

## Verdict

**Cannot complete** `~/develop/republic-formulas` + `data_manifest.local.toml` + `/Volumes` work from this run.

This agent (`bc-8d182330-3baf-56e8-8967-f41635449bf8`, “Setup ~/develop/republic-formulas”) was instructed “You are on RiksMacBook” but landed on the **managed cloud VM**:

| Fact | Value |
|------|--------|
| Hostname / OS | `cursor`, Linux 6.12 |
| `privateWorkerId` | `null` |
| `usePrivateWorker` | `false` |
| `/Volumes` | missing |
| `~/develop` | missing |
| `/Users/rikhoekstra` | missing |

No Task / CreateAgent tool is available to this subagent to re-place onto a self-hosted worker.

## What was checked

1. `ls /Volumes` → `No such file or directory`
2. Self-hosted workers: **9 connected**, all `machineDisplayName=RiksMacBook`, `eligibleForSubagent=true`, `sharedAssignmentAllowed=true`
3. Prior Mac agents that succeeded used worker `3f4cb657-9337-5ac6-9965-ed5753ed8745` (`~/develop/republic_ner_matching @ RiksMacBook`) — e.g. S4 sample `bc-aa0292ab…`, survey `bc-9a3f98dc…`
4. Their transcripts do **not** contain real `/Volumes/...` mount names (only regex / placeholder mentions)
5. Sibling doc [tiers-vs-drives.md](tiers-vs-drives.md) already notes cloud cannot fill drive-backed config

## Recommended re-dispatch

Re-spawn this exact checklist on a **RiksMacBook private worker**, preferably:

- **`3f4cb657-9337-5ac6-9965-ed5753ed8745`** — `~/develop/republic_ner_matching` (S4 JSONL lives next door), or
- **`5722827a-9d5a-57f9-be97-8f60ef8cd79d`** — `~/develop/dighum_template` (best peer for grepping other `data_manifest.local.toml` tier roots)

Checklist to run **on the Mac** (unchanged):

1. `ls /Volumes`
2. Grep/read `~/develop/*/data_manifest.local.toml` for real `/Volumes` roots
3. Ensure `~/develop/republic-formulas` on branch `cursor/republic-formulas-evolve-b2c6` (clone from Origin if needed)
4. `cp data_manifest.local.toml.example data_manifest.local.toml` and edit real Volume paths; hot → `~/develop/republic-formulas`; **do not commit** local.toml
5. Wire full S4 at `~/develop/republic_ner_matching/output/s4_opening_phrase_candidates.jsonl` (override or symlink under cold)
6. `uv sync` → `uv run python -m data_io.check` → `uv run pytest tests/ -q`
7. Return checkout path, full local.toml, check output, pytest summary, `ls /Volumes`

## Known path from prior Mac work

Full S4 file (confirmed by Mac agent):  
`/Users/rikhoekstra/develop/republic_ner_matching/output/s4_opening_phrase_candidates.jsonl`
