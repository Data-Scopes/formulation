---
name: Evolve formula detection
overview: 'Bootstrap this Project from dighum_template, then evolve REPUBLIC formulaic-language work from local `formula_detection` and formula-related `republic_clean` notebooks into a real DH pipeline (not a web app).'
todos:
  - id: survey-merge
    content: Merge local survey of formula notebooks + formula_detection into a concrete port list
    status: pending
  - id: retarget-bootstrap
    content: Stop naive cloud derive; bootstrap this repo via dighum_template as republic-formulas
    status: pending
  - id: wire-formula-lib
    content: Add formula_detection dependency and project adapters for tokenized REPUBLIC-style input
    status: pending
  - id: lift-notebooks
    content: Port durable formula notebook logic into packages/scripts; keep demos only if useful
    status: pending
  - id: first-slice
    content: 'Ship sample run + provenance outputs, README, and basic adapter tests'
    status: pending
isProject: false
---
# Evolve formula work into this Project

## Goal

Turn this empty Project into a **dighum_template-based digital humanities pipeline** whose domain is **formulaic language detection** for REPUBLIC-style historical text — evolving from existing local work rather than copying it wholesale.

## Sources

| Source | Role |
|--------|------|
| [HoekR/dighum_template](https://github.com/HoekR/dighum_template) | Project shell: `bootstrap.sh`, `packages/data_io`, provenance, `wisdom/`, editor rules |
| `~/develop/formula_detection` (upstream: [marijnkoolen/formula_detection](https://github.com/marijnkoolen/formula_detection)) | Core library: `FormulaSearch` for templated/formulaic phrases in tokenized historical text |
| `~/develop/republic_clean/notebooks` (formula-related) | Applied REPUBLIC prototypes to lift into scripts/modules |

A readonly local survey is already running and will land at the Project store internal survey file; execution will use that inventory to pick which notebooks become first-class code.

## Approach (decided)

1. **Bootstrap correctly** with `dighum_template/scripts/bootstrap.sh` into this repo (or recreate layout to match what bootstrap produces). Working project slug: `republic-formulas`. Include `--with-wisdom`. No RPP/TRIFECTA addon unless survey shows a clear fit.
2. **Stop/retarget** the earlier cloud “derive as generic app” worker — this is a Python data pipeline, not a Next.js surface.
3. **Depend on `formula_detection`** (PyPI / editable local path) rather than forking the whole library into the repo. Put *project-specific* adapters, corpora iterators, and analysis scripts in this Project.
4. **Evolve notebooks → package + scripts**: identify durable formula workflows in `republic_clean` notebooks; reimplement the lasting paths as importable modules under the bootstrapped layout (e.g. `src/` or `packages/` per template conventions) plus thin CLI/scripts; keep 1–2 cleaned notebooks only as demos/docs if useful.
5. **First runnable slice**: sample tokenized corpus → `FormulaSearch` → candidate formulas written through `data_io` with provenance sidecars; README with how to run; basic tests around the adapter (not re-testing upstream library exhaustively).

```mermaid
flowchart LR
  notebooks[republic_clean formula notebooks]
  lib[formula_detection FormulaSearch]
  tmpl[dighum_template bootstrap]
  proj[republic-formulas Project]
  notebooks -->|"lift durable logic"| proj
  lib -->|"dependency"| proj
  tmpl -->|"shell + data_io"| proj
  proj --> out[formula candidates + provenance]
```

## Out of scope for the first slice

- Full REPUBLIC corpus ETL or production-scale runs
- New UI / web app
- Rewriting upstream `formula_detection` itself
- Non-formula notebooks from `republic_clean`

## Execution owners

Work on **RiksMacBook** (self-hosted) so bootstrap and local sources stay on the same machine; push commits to this Project’s remote branch.
