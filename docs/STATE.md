# Current Project State (SvZ)

Last updated: 2026-10-19 10:24

```mermaid
flowchart TD
    classDef done fill:#2e7d32,stroke:#1b5e20,color:#fff,stroke-width:2px;
    classDef inprogress fill:#f57c00,stroke:#e65100,color:#fff,stroke-width:2px;
    classDef todo fill:#424242,stroke:#212121,color:#ddd,stroke-width:1px,stroke-dasharray: 5 5;
    classDef blocked fill:#c62828,stroke:#b71c1c,color:#fff,stroke-width:2px;

    S0["S0: Project setup"] :::todo
    R1["R1: Aanstelling retrieval"] :::done
    M1["M1: First runnable formula slice"] :::inprogress
    S0 --> R1
    R1 --> M1
```

## Overall Progress

- [ ] S0: Project setup — Initialize manifest, data paths, and first reproducible checks.
- [x] R1: Aanstelling retrieval — Selection frozen 3820 ids (~18x gold). Results: docs/r1-aanstelling-results.md
- [/] M1: First runnable formula slice — STEP0-1 done. Next: STEP2 sample corpus and S4 seeds. R1 judged: stop after TF-IDF.

## Active Focus

Track L STEPL0 (after R1 results report) — or formula STEP2

## Key Intermediate Results & Metrics

- **R1 — holdout recall:** 0.860465
- **R1 — holdout precision:** 0.973684
- **R1 — holdout F1:** 0.913580
- **R1 — remainder high (>0.85):** 1012
- **R1 — remainder p>0.5:** 2883
- **R1 — remainder (0.15,0.5]:** 4137
- **R1 — holdout high-or-grey recall:** 0.976744
- **R1 — selected resolutions:** 3820
- **R1 — selected / gold multiplier:** 17.93
- **R1 — selected with rough name:** 0.785
- **R1 — selected before 1705:** 615
- **R1 — review_suspect keep rate:** 0.72
- **L1 — recall:** 0.933824
- **L1 — precision:** 0.907143
- **L1 — f1:** 0.920290

## Blockers / Open Questions

No blockers recorded.

## Next Actions

- Read plans/steps/STEP2-sample-corpus-and-seeds.md
- Register sample_resolutions and s4_opening_phrase_candidates; data_io.check

<!-- Manual notes below this line are preserved by scripts/svz.py render. -->
## Notes
