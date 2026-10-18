# Steps

Linked from the progress tables in root [`PLAN.md`](../../PLAN.md). One step per session. **Active: STEPS1 threshold calibration.** L1 STEPL1 done; STEPL2 available. F/M1 paused. R1 judged.

## Track R — retrieval (R1)

| Step | Guide | Status |
|------|-------|--------|
| R0 | [STEPR0-register-retrieval-inputs.md](STEPR0-register-retrieval-inputs.md) | done |
| R1 | [STEPR1-join-urns.md](STEPR1-join-urns.md) | done |
| R2 | [STEPR2-tfidf-baseline.md](STEPR2-tfidf-baseline.md) | done |
| R3 | [STEPR3-harvest-buckets.md](STEPR3-harvest-buckets.md) | done |
| R4 | [STEPR4-residual-or-stop.md](STEPR4-residual-or-stop.md) | done (stop) |

## Track L — missive receipt (L1)

| Step | Guide | Status |
|------|-------|--------|
| L0 | [STEPL0-define-missive-receipt-type.md](STEPL0-define-missive-receipt-type.md) | done |
| L1 | [STEPL1-labelled-table.md](STEPL1-labelled-table.md) | done (1780) |
| L2–L4 | (guides TBD) | not started |

## Track S — formula boundary evolution (S1)

| Step | Guide | Status |
|------|-------|--------|
| S0 | [STEPS0-boundary-scaffold.md](STEPS0-boundary-scaffold.md) | done |
| S1 | [STEPS1-tfidf-window-framing.md](STEPS1-tfidf-window-framing.md) | done |
| S1b | [STEPS1-calibrate-threshold.md](STEPS1-calibrate-threshold.md) | **active** |
| S2 | [STEPS2-slot-cloud-bootstrap.md](STEPS2-slot-cloud-bootstrap.md) | done |
| S3 | [STEPS3-dag-spans.md](STEPS3-dag-spans.md) | done |
| S4 | [STEPS4-residual-or-stop.md](STEPS4-residual-or-stop.md) | done (stop) |

## Track F — formulas (M1), paused

| Step | Guide | Status |
|------|-------|--------|
| 0 | [STEP0-local-data-wiring.md](STEP0-local-data-wiring.md) | done |
| 1 | [STEP1-formula-detection-adapters.md](STEP1-formula-detection-adapters.md) | done |
| 2 | [STEP2-sample-corpus-and-seeds.md](STEP2-sample-corpus-and-seeds.md) | not started |
| 3 | [STEP3-formula-search-script.md](STEP3-formula-search-script.md) | not started |
| 4 | [STEP4-tests-and-demo.md](STEP4-tests-and-demo.md) | not started |

Workflow MCP reads this directory (legacy: `docs/steps/`). Prefix `STEPR*` / `STEPS*` still matches the `STEP*.md` glob.
