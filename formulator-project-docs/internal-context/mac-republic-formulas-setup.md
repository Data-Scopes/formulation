---
cursor:
  subagentId: "bc-ce87d349-7f81-5891-916f-5df3010dd45d"
---

# Mac republic-formulas setup — BLOCKED

## Gate checks (must all pass; failed → stop)

| Check | Result |
|-------|--------|
| Darwin / Mac hostname | **FAIL** — `uname -a`: `Linux cursor 6.12.94+ ... x86_64 GNU/Linux`; `hostname`: `cursor` |
| `/Volumes` present | **FAIL** — `ls: cannot access '/Volumes': No such file or directory` |
| `privateWorkerId` | **FAIL** — `null` (`usePrivateWorker`: false) |

This agent ran on the cloud Linux VM (`/workspace`), not on RiksMacBook. Per instructions: do not invent paths; no checkout, local.toml, uv, or pytest.

## Run identity

- bcId: `bc-ce87d349-7f81-5891-916f-5df3010dd45d`
- URL: https://cursor.com/agents/bc-ce87d349-7f81-5891-916f-5df3010dd45d
- Repo: `https://origin.cursor.com/git/rik-hoekstra/tmp-79310ac0a01cc22a`
- Target branch (not checked out here): `cursor/republic-formulas-evolve-b2c6`

## RiksMacBook workers (visible but not bound to this run)

Connected Darwin workers on machine `RiksMacBook` (machineId `fb91939c5fed740a…`), all `eligibleForSubagent: true` / `sharedAssignmentAllowed: true` at check time. Example workerIds:

- `5722827a-9d5a-57f9-be97-8f60ef8cd79d` — `~/develop/dighum_template`
- `3f4cb657-9337-5ac6-9965-ed5753ed8745` — `~/develop/republic_ner_matching`
- plus trifecta, schutte-bewerkingen, rpp-analysis-framework, huygens_name_index, jsonforms, raa_modernized, gnb_analysis

## Checklist status

1. `ls /Volumes` / `uname -a` — done; not Darwin; `/Volumes` missing
2. Grep sibling `data_manifest.local.toml` on Mac — **not run**
3. Checkout `/Users/rikhoekstra/develop/republic-formulas` — **not run**
4. Configure `data_manifest.local.toml` — **not run**
5. Wire S4 full source — **not run**
6. `uv sync` / `data_io.check` / pytest — **not run**
7. Return paths/outputs — **N/A** (blocker)

## Unblock

Re-dispatch this agent (or a sibling) with `privateWorkerId` set to a RiksMacBook worker so the process actually runs on Darwin with `/Volumes` and `~/develop/...` available. Related prior note: `internal/mac-setup-blocker.md`.
