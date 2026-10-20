# Steps

Linked from the progress tables in root [`PLAN.md`](../../PLAN.md). One step per session. **STEPT1k active** (requeste opener A). Next after PASS: STEPT1l requeste+ subtypes. STEPT1e1 **parked**. F/M1 paused; Track L parked. R1 judged.

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
| S1b | [STEPS1-calibrate-threshold.md](STEPS1-calibrate-threshold.md) | done |
| S2 | [STEPS2-slot-cloud-bootstrap.md](STEPS2-slot-cloud-bootstrap.md) | done |
| S3 | [STEPS3-dag-spans.md](STEPS3-dag-spans.md) | done |
| S4 | [STEPS4-residual-or-stop.md](STEPS4-residual-or-stop.md) | done (stop) |
| S5b | [STEPS5-wire-boundary-registry.md](STEPS5-wire-boundary-registry.md) | done |
| S6 | [STEPS6-institution-patterns.md](STEPS6-institution-patterns.md) | done (bookkeeping) |
| S6c | [STEPS6c-org-pattern-harvest.md](STEPS6c-org-pattern-harvest.md) | done (script; user runs full harvest) |
| S6d | (prove A/B — no step guide) | done (harvest +1 FP; tighten min-n next) |

## Track T — typology

| Step | Guide | Status |
|------|-------|--------|
| T0 | [STEPT0-typology-structural-profile.md](STEPT0-typology-structural-profile.md) | done (1780 provisional profile) |
| T1-period | [STEPT1-period-bins.md](STEPT1-period-bins.md) | done (script; user runs eval) |
| T1b | [STEPT1b-presence-scoring.md](STEPT1b-presence-scoring.md) | done (1780; bags=fragments → T1c) |
| T1c | [STEPT1c-position-zones.md](STEPT1c-position-zones.md) | done (1780; zone separates; bags still fragments) |
| T1d order | [STEPT1d-order-composition.md](STEPT1d-order-composition.md) | done / parked (1780 soft constraint) |
| T1d graph | [STEPT1d-composition-graph.md](STEPT1d-composition-graph.md) | done (PASS; provisional_root_star; skip bins) |
| T1e0 | [STEPT1e0-ontfangen-inventory.md](STEPT1e0-ontfangen-inventory.md) | done (call → STEPT1e probe) |
| T1e | [STEPT1e-partition-probe.md](STEPT1e-partition-probe.md) | done (PASS → map, not e1) |
| T1-map | [STEPT1-typology-formula-map.md](STEPT1-typology-formula-map.md) | done (docs; e1 parked) |
| T1e1 | [STEPT1e1-residual-flag-sieve.md](STEPT1e1-residual-flag-sieve.md) | parked |
| T1a2 | [STEPT1a2-advies-formula-type.md](STEPT1a2-advies-formula-type.md) | done (PASS; recall 0.762 / FP 0.034) |
| T1f | [STEPT1f-missive-subtype-characterisation.md](STEPT1f-missive-subtype-characterisation.md) | done (PASS w/ circular L1 caveat) |
| T1g | [STEPT1g-residual-structure-probe.md](STEPT1g-residual-structure-probe.md) | done (PASS; filler mass + sparse appointment) |
| T1h | [STEPT1h-unknown-likeliness.md](STEPT1h-unknown-likeliness.md) | done (PASS; high-unk 0.72) |
| T1k | [STEPT1k-requeste-formula-type.md](STEPT1k-requeste-formula-type.md) | **active** (requeste opener vs ES rekest) |
| T1l | (requeste+ subtype — TBD) | next |

## Track F — formulas (M1), paused

| Step | Guide | Status |
|------|-------|--------|
| 0 | [STEP0-local-data-wiring.md](STEP0-local-data-wiring.md) | done |
| 1 | [STEP1-formula-detection-adapters.md](STEP1-formula-detection-adapters.md) | done |
| 2 | [STEP2-sample-corpus-and-seeds.md](STEP2-sample-corpus-and-seeds.md) | not started |
| 3 | [STEP3-formula-search-script.md](STEP3-formula-search-script.md) | not started |
| 4 | [STEP4-tests-and-demo.md](STEP4-tests-and-demo.md) | not started |

Workflow MCP reads this directory (legacy: `docs/steps/`). Prefix `STEPR*` / `STEPS*` still matches the `STEP*.md` glob.
