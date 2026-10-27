# STEPT1y — Opener candidates queue + driver (NOTES)

**Status:** done (2026-10-25). Infrastructure PASS — no new A / blueprint.  
**Guide:** [`plans/steps/STEPT1y-opener-candidates-driver.md`](../../../plans/steps/STEPT1y-opener-candidates-driver.md)  
**Decision:** [`docs/DECISIONS.md`](../../DECISIONS.md) 2026-10-25 STEPT1y opened.

```bash
uv run pytest tests/test_opener_candidates.py -q
uv run python scripts/run_opener_candidates_driver.py --phase measure --candidate-id rapport_gehoord --fixture-only
uv run python scripts/run_opener_candidates_driver.py --seed-from-fixture
uv run python -m data_io.check
```

## What this step delivered

- Provenanced `opener_candidates` queue (`data_manifest.toml` + `output/opener_candidates.jsonl`).
- Seed: 6 blueprint audit rows + `voordracht` (n=80) / `conclusie_handen` (n=41) pockets (STEPT1u).
- Module [`formulation/opener_candidates.py`](../../../formulation/opener_candidates.py) + [`scripts/run_opener_candidates_driver.py`](../../../scripts/run_opener_candidates_driver.py).
- Phases `measure` / `wire` / `propose-promote` write evidence only; human helpers `name_candidate` / `set_a_verdict` / `set_promote_verdict`; `--apply-promote` default off and never invents verdicts.
- Audit adapters for the six done openers (fixture write-back); voordracht measure refuses until a later adapter.

## Gates

| Gate | Result |
|------|--------|
| 1 Seed 6 blueprint + 2 pocket | **PASS** |
| 2 Measure refuses pocket / unknown; audit write-back works | **PASS** (11 tests) |
| 3 Wire / promote refuse without human verdict; apply-promote off | **PASS** |
| 4 Driver never sets a_verdict / promote_verdict | **PASS** |

## Next

Human names voordracht canonic (`pocket` → `named`); next step adds measure adapter + gold eval. Clear the chat before the next step.
