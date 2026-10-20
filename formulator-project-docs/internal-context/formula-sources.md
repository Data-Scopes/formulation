---
cursor:
  subagentId: "bc-9a3f98dc-810b-5dfa-90a1-606c823f3faf"
---

# Formula sources inventory (readonly survey)

Survey date: 2026-09-21. No files under `~/develop` were modified.

Sources:

1. `~/develop/republic_clean/notebooks` — REPUBLIC-domain formula notebooks and artefacts
2. `~/develop/formula_detection` — published Python package (Marijn Koolen; PyPI / GitHub)

---

## 1. `formula_detection` — key file tree

```
formula_detection/                          # repo root (v0.5.0)
├── README.md                               # usage + FormulaSearch tutorial (long)
├── pyproject.toml                          # Poetry; package formula_detection
├── poetry.lock
├── Pipfile / Pipfile.lock                  # legacy Pipenv (broader exploratory deps)
├── Makefile                                # editable install, wheel, bumpver, publish
├── pytest.ini
├── LICENSE (MIT)
├── .readthedocs.yaml
├── formula_detection/                      # installable package (no separate src/)
│   ├── __init__.py                         # __version__ = "0.5.0"
│   ├── search.py                           # FormulaSearch (core)
│   ├── vocabulary.py / candidate.py / cooccurrence.py / sentence.py
│   ├── context.py / phrases.py / transitions.py / variants.py / variant_index.py
│   ├── phrase_vectorizer.py / clustering.py
│   ├── phrase_cooccurrence.py / motif.py / window_estimator.py / boundary.py
│   ├── phrase_typing.py / phrase_typing_ui.py   # HITL typing (+ ipywidgets UI)
│   ├── merge_bigrams.py                    # FastText-assisted bigram variants
│   ├── visualisation.py
│   ├── normalisation/
│   │   ├── normaliser.py / rewrite.py / rewrite_historic_dutch.py
│   ├── patterns/pattern.py
│   ├── variation/edit.py
│   ├── tokenization/tokenizer.py
│   └── stats/freq.py
├── tests/                                  # unit tests (no ML model fixtures)
│   ├── test_candidate.py / test_cooccurrence.py / test_merge.py
│   ├── test_pattern.py / test_search.py / test_sentence.py / test_vocabulary.py
├── notebooks/                              # corpus adapters (REPUBLIC-oriented)
│   ├── resolution_iterables.py / corpus_iterables.py / stabe_mapper.py
│   └── Context-Transition-Probabilities.ipynb
└── docs/                                   # Sphinx + tutorial/demo notebooks
    ├── Usage.md / search_doc.md / vocabulary_doc.md / api.rst / index.rst
    ├── Document-Pattern-Detection*.ipynb (+ Findings.md)
    ├── Motif-Based-Boundary-Detection*.ipynb
    ├── Phrase-Recurrence-Scale-Grouping*.ipynb
    ├── Phrase-Typing-Workbench.ipynb
    ├── Formulaic-Language-Over-Time.ipynb
    ├── Formula-Detection-Usage.ipynb
    └── tutorials/01–07-*.ipynb
```

**Models:** none vendored in-repo. Optional FastText models are *inputs* to `BigramMerger` (caller-supplied). No `.pkl` / `.pt` / joblib artefacts in the package tree.

**Remote:** `https://github.com/marijnkoolen/formula_detection` (also on PyPI).

---

## 2. Formula-related notebooks under `republic_clean/notebooks`

### Primary (name match: `*formula*`, `*frm*`, typo `*fromulas*`)

| Path | One-line purpose |
|------|------------------|
| `formulas_writeup.ipynb` | Research writeup: why REPUBLIC needs formulas; variable form/content; corpus-driven detection vs context. |
| `formulas_elements_writeup.ipynb` | Graph-based formula *elements* from 18th-c lexical bundles (overlaps, longest common subsequences). |
| `formulas_hoedanigheden_writeup.md` | Companion notes: hoedanigheden vs lexical bundles / search recall (not a notebook). |
| `formulas_and_hoedanigheden.ipynb` | Link formula phrases to hoedanigheden; NetworkX + ES-backed resolution data. |
| `formula_elements.ipynb` | Working notebook: template_detection / collate helpers to extract formula elements. |
| `formulas_verwerken.ipynb` | Process manually classified formulas (overlap refs, graphs, HTML export). |
| `clustering_formulas.ipynb` | Year-by-year formula clustering via republic ES + `template_detection` / fuzzy_search. |
| `clustering_formulas-output.ipynb` | Output / follow-on pass of clustering pipeline (large saved outputs). |
| `frm_frm_frm.ipynb` | Heavy exploration of 5-gram phrase dumps (Downloads) + `republic.formulas.frmls.clustering`. |
| `formulas/formula_calc_flat.ipynb` | Flat calculation / tabular work over formula CSVs in `formulas/`. |
| `formulas/formulas_schema.ipynb` | Schema / structure of formula tables (`formula_schemes.xlsx` etc.). |
| `formulas/t_templ.ipynb` | Ad-hoc phrase selections with FuzzyPhraseSearcher + skipgrams. |
| `formulas/t_templ-0.ipynb` | Earlier/sibling ad-hoc template selection (same stack). |
| `formulas/t_templ-1.ipynb` | Minimal pandas scratch around formula tables. |
| `formulas/t_templ_2.ipynb` | `SelectByPhrases` helper experiments on formula DataFrames. |
| `working_notebooks/formulas_from_searches.ipynb` | Marked experimental: sift candidate formulas from phrase searches (ES inventories). |
| `working_notebooks/fromulas_from_searches.ipynb` | Typo-named shorter sibling of the above. |

### Closely related (content/path; formula or template detection)

| Path | One-line purpose |
|------|------------------|
| `skipgrams.ipynb` | Skipgram / fuzzy phrase work (also loads location data — mixed focus). |
| `seqsim.ipynb` | Sequence similarity + clustering (seqsim / sklearn); used by formula clustering path. |
| `template_example.ipynb` | Short example of an 18th-c resolution template. |
| `Template_test.ipynb` | FuzzyTemplateSearcher against `resolution_phrase_model` / opening templates. |
| `Fuzzy-Templates/Resolution-Opening-Template.ipynb` | Same opening-template labelling workflow (ES-backed). |
| `variants_in_graph.ipynb` | NetworkX variant graphs over sequences (generic; feeds formula-element thinking). |
| `working_notebooks/visualize_phrases.ipynb` | Visualise / inspect phrases and hoedanigheden from ES extracts. |

### Supporting artefacts (not notebooks, but formula pipeline outputs)

- `notebooks/formulas/` — large CSV/XLSX/parquet of form variants per phrase type (`form_variant_*.csv`, `documents.csv`, pickles).
- `notebooks/frms_tagged/` — Flair sequence-tagging train/dev/test + **418MB** `best-model.pt` / `final-model.pt`.
- `notebooks/csvs/` — tagged/linked formula spreadsheets (`formula_tagged_1757.xlsx`, `linked_formulas.xlsx`, …).

**Cross-import check:** no notebook under `republic_clean/notebooks` imports `formula_detection`. They use `republic.*` (especially `republic.extraction.template_detection`, `republic.formulas.frmls.clustering`) and `fuzzy_search` instead.

---

## 3. Stack / languages / deps

### `formula_detection` (package)

| Item | Detail |
|------|--------|
| Language | Python `^3.8,<3.13` |
| Packaging | Poetry (`pyproject.toml`); legacy Pipenv still present |
| Core deps | `fuzzy-search ^2.4.5`, `scikit-learn`, `scipy`, `networkx`, `ipywidgets` |
| Docs | Sphinx, nbsphinx, myst-parser, ipykernel |
| Pipfile extras (exploratory) | levenshtein, nltk, beautifulsoup4, collatex, graphviz |
| Optional runtime | FastText models for `merge_bigrams.BigramMerger` (not declared in poetry deps) |
| Tests | pytest, 7 modules covering search/vocab/pattern/candidate/cooc/merge/sentence |

### `republic_clean` formula notebooks

| Item | Detail |
|------|--------|
| Language | Python 3.9 (`.venv` traces in notebooks) |
| Domain package | local `republic` tree (`republic_clean`) |
| Shared NLP | `fuzzy-search` (same family as formula_detection) |
| Data access | Elasticsearch (`initialize_es(host_type="external")`) |
| Analysis | pandas, networkx, scikit-learn, scipy, seqsim, occasionally analiticcl / torch / Flair |
| Requirements highlights | elasticsearch, fuzzy-search, torch≈1.13, analiticcl, networkx, sklearn |

---

## 4. How the two relate

| Aspect | Relationship |
|--------|----------------|
| Shared code? | **No direct import link.** Zero `formula_detection` imports in republic notebooks. |
| Shared dependency | Both build on **`fuzzy-search`** (tokenization / fuzzy phrase matching). |
| Conceptual link | Same research problem: formulaic language in States General resolutions (orthographic variation, variable slots, nested document structure). |
| Division of labour | **`formula_detection`** = generalisable reusable library + demos (incl. `*-resolutions.ipynb` and `notebooks/resolution_iterables.py`). **`republic_clean` notebooks** = domain prototypes against live ES + hand-curated formula tables + Flair tagging experiment. |
| Parallel in-repo code | `republic_clean` also has thin `republic/formulas/frmls/` and top-level `formulas/fmls/` (KMeans/silhouette clustering with `seqsim`) — notebook-era helpers, not the published package. |
| Evolution path | Notebooks look like earlier/parallel REPUBLIC exploration; package looks like the cleaned, tested generalisation (plus later boundary/motif/typing work documented in `Document-Pattern-Detection-Findings.md`). |

---

## 5. Lasting core vs throwaway exploration

### Prefer to port / keep (lasting core)

From **`formula_detection`:**

- `FormulaSearch` + `Vocabulary` / `candidate` / skip-cooccurrence pipeline
- Orthographic cascade: `variant_index`, `normalisation/*`, `variation/edit`
- Structure discovery: `phrase_cooccurrence`, `motif`, `window_estimator`, `boundary`
- Phrase semantics: `phrase_vectorizer`, `clustering`, `phrase_typing` (+ UI optional)
- Tests + Sphinx tutorials as living documentation
- Findings doc as design rationale for a new Project

From **`republic_clean` notebooks** (content, not notebook form):

- Conceptual writeups: `formulas_writeup.ipynb`, `formulas_elements_writeup.ipynb`
- Curated labelled tables under `csvs/` and `formulas/form_variant_*.csv` (domain gold / reference, if licensable and path-cleaned)
- Problem framing around openings, decisions, “in handen van”, hoedanigheden

### Likely throwaway / archive-only

- Untitled / typo notebooks (`fromulas_from_searches`, `t_templ-*` scratch, `frm_frm_frm` mega-scratch)
- Huge output notebooks (`clustering_formulas-output.ipynb` ~27MB of embedded state)
- Hard-coded `/Users/.../Downloads/formulas/*.tsv.gz` loaders
- Duplicate ES year loops marked “experimental — leave for reference”
- Flair `frms_tagged/*.pt` unless sequence tagging is an explicit Project goal (private/local artefact, 418MB×2)
- `usecase.md` under `formulas/` (governance-networks influence case — adjacent, not formula detection)

---

## 6. Blockers for a new Project

| Blocker | Detail |
|---------|--------|
| Elasticsearch | Most working notebooks call `initialize_es(host_type="external")` — needs REPUBLIC ES credentials/host; not runnable offline. |
| Missing Downloads data | `frm_frm_frm.ipynb` expects `~/Downloads/formulas/phrases-5_gram-18th_century.*` etc. |
| Local path coupling | Notebooks hard-code `~/develop/republic_clean`, `~/develop/analiticcl`, Downloads PNG/HTML exports. |
| Private / sibling deps | `analiticcl` path imports; `seqsim` used by clustering helpers; Flair models only in `frms_tagged/`. |
| FastText (package) | `BigramMerger` needs external FastText models — not in repo or poetry.lock. |
| Dual packaging history | Poetry is canonical for the package; Pipfile is stale/broader — clarify before bootstrap. |
| No shared package bridge | Porting notebook workflows means re-expressing republic ES → token streams as `formula_detection` iterables (pattern already sketched in `resolution_iterables.py`). |
| Data volume / PII-ish research data | Large CSV/parquet of resolutions and tagged phrases may not belong in a new public repo without a manifest + cold tier. |

---

## 7. Implication for evolving into a new Project

Treat **`formula_detection` as the technical core to vendor or depend on**, and treat **`republic_clean` formula notebooks as requirements + gold-data archaeology** (writeups, labelled spreadsheets, known formula types). Do not try to “lift” the notebook tree as application code. A dighum-template Project would wrap the package with `data_manifest.toml` paths, ES-free frozen corpora (parquet/JSONL), and step guides that reimplement the republic demos cleanly.
