---
cursor:
  subagentId: "bc-b1f5b1a0-2045-5d68-bfb4-d6f8ac9cb2c6"
---

# Formula port list (concrete)

Derived from `internal/formula-sources.md`, `docs/formula-conceptual-overview.md`, and
`internal/s4-opening-phrases-sample.md`. **Do not fork** upstream
[marijnkoolen/formula_detection](https://github.com/marijnkoolen/formula_detection)
— depend on PyPI `formula_detection`.

## First-slice ports (this Project)

| Source | Port as | Destination in `republic-formulas` |
|--------|---------|--------------------------------------|
| `FormulaSearch` + `extract_phrases` | dependency | `formula_detection` (PyPI) |
| `notebooks/resolution_iterables.py` / `corpus_iterables.ResolutionSentences` pattern | adapter | `republic_formulas/adapters.py` — iterable of token lists (or dicts with `words`) for FormulaSearch |
| Sample REPUBLIC-style resolutions (offline) | warm dataset | `data/warm/datasets/corpus/sample_resolutions.jsonl` + manifest `sample_resolutions` |
| `FormulaSearch` → candidates + provenance | script | `scripts/run_formula_search.py` via `data_io.save_semi_structured` |
| Adapter + search smoke tests | tests | `tests/test_adapters.py` |
| Thin demo of the slice | notebook | `notebooks/01_formula_search_demo.ipynb` |

## Seed inventory (path note — not full ETL)

| Source | Role | How this Project treats it |
|--------|------|----------------------------|
| `~/develop/republic_ner_matching/output/s4_opening_phrase_candidates.jsonl` | Full frequency-ranked opening n-grams (271) | Source of truth on Rik's machine. Optional cold/local override via `data_manifest.local.toml`. |
| Warm fixture `data/warm/datasets/seeds/s4_opening_phrase_candidates.jsonl` | Offline trimmed envelope (15 candidates) | Manifest logical name `s4_opening_phrase_candidates`. Reader: `republic_formulas.seeds.load_s4_opening_seeds`. Wired as `seed_phrases` + candidate annotation in first-slice script. |
| `documents.parquet` (`formula_documents`) | Formula-type boolean matrix per doc_id | Registered in `data_manifest.toml`; path override in `local.toml` |
| Notebook gold CSVs (`csvs/`, other `form_variant_*.csv`) | Labelled reference | Manifest when path-cleaned & licensable |

S4 gaps vs conceptual model: **no span / document-position fields**; short n-grams still need building-block criteria (frequency alone is not enough). Sample notes: store `internal/s4-opening-phrases-sample.md`.

## Lift later (durable notebook *ideas*, not notebook trees)

| `republic_clean` source | Why keep | Lift target |
|-------------------------|----------|-------------|
| `formulas_writeup.ipynb` / `formulas_elements_writeup.ipynb` | Problem framing: building blocks, composition | Project README / `docs/` notes; light comments in adapters |
| Opening / decision / “in handen van” types | Domain gold types | labelled tables under cold/warm |
| Gappy / templated patterns | Formulas need not be contiguous | `max_variables` / `max_skips` on `extract_phrases` once sample grows |
| Position in the resolution | Same cue ≠ same meaning (decision vs resumption) | Retain `section` / offsets on sample docs and candidate records |
| `clustering_formulas.ipynb` idea | Year-sliced clustering | wrap `formula_detection.clustering` later |
| `formulas_and_hoedanigheden.ipynb` (logic only) | Phrases ↔ roles | optional module after ES-free corpus exists |

## Do **not** port (first slice / ever as app code)

| Source | Reason |
|--------|--------|
| Entire `republic_clean/notebooks` tree | Scratch, ES-coupled, hard-coded local paths |
| `frm_frm_frm.ipynb`, `t_templ-*`, typo `fromulas_*` | Throwaway exploration |
| `clustering_formulas-output.ipynb` | Huge embedded outputs |
| Flair `frms_tagged/*.pt` | Out of scope; large private artefacts |
| Live Elasticsearch loaders | No full REPUBLIC ETL; sample JSONL only |
| Fork of `formula_detection` package tree | Depend on library |
| Full building-block criteria engine | Conceptual target; do not block first slice |

## Conceptual model (light reflection in first slice)

From `docs/formula-conceptual-overview.md` — encode lightly in docs/comments, not a full engine:

1. **Building blocks** — short formulas that meet criteria (recurrence, reuse, function), not every frequent bigram.
2. **Gappy composition** — skeletons with variable slots between stable pieces.
3. **Position** — keep section / offsets so opening vs decision interpretation stays possible.

## Dependency

```toml
# pyproject.toml
"formula_detection>=0.5.0,<0.6"
```

Requires transitive `fuzzy-search`. Keep runtime on Python `>=3.12,<3.13` (upstream upper bound).
