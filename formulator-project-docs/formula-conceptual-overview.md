# Conceptual overview: formula work → this Project

## What “formulas” means here

In REPUBLIC (Resolutions of the Dutch States General), **formulas** are recurring *templated* stretches of language — openings, decisions, “in handen van …”, role phrases (*hoedanigheden*), and similar — not mathematical equations.

They vary in spelling and in variable slots (names, places, dates) while keeping a recognisable skeleton. The research problem is: **find, group, and type those skeletons** across a large historical corpus despite orthographic variation and nested document structure.

## Core research notions

### Formulas have building-block sub-formulas

Longer formulaic expressions often contain **shorter sub-formulas** that act as reusable building blocks. Not every frequent 2- or 3-word string qualifies. We need explicit **criteria for “building block” status**, for example (to be refined in the Project):

- Recurs as a stable unit across many resolutions / years (not just local repetition)
- Appears in more than one larger formula type (compositional reuse)
- Survives orthographic variation as the same skeleton
- Carries a recognisable discourse or procedural function (opening move, referral, decision cue, …)
- Is productive with variable slots around or inside it — not a frozen hapax collocation

Criteria are part of the scientific design of this Project, not an afterthought of n-gram mining.

### How building blocks combine

Larger formulas are **compositions** of these blocks (plus variable material), not flat bags of words. Open questions the Project should make answerable:

- Which blocks co-occur or order-constrain each other?
- Which combinations form attested larger formula types vs accidental adjacency?
- Where does a block boundary end and a variable (name, date, body) begin?

Graph / sequence views from the `republic_clean` “formula elements” work are early attempts at this composition story; `formula_detection`’s motif / co-occurrence layers are machinery that can support it.

### Shorter formulas need not be contiguous

Building blocks (and the larger formulas they form) **need not be contiguous token spans**. Variable parts — person names, places, dates, case-specific content — may sit **between** stable formulaic pieces.

Detection and representation must allow **gappy / templated patterns** (fixed skeleton + slots), not only unbroken n-grams. That aligns with `FormulaSearch`’s notion of phrases with variable elements, and with earlier fuzzy / template search in the notebooks.

### Position in the resolution matters

The **same (or closely related) formula can mean different things depending on where it appears** in a resolution’s discourse structure. Example:

- A formula that marks a **decision** near the **end** of a resolution
- may signal **resumption** when the same cue appears in the **opening** (*proposition*)

So formula identity is not only string/skeleton identity: **rhetorical / document position** (opening vs body vs decision zone, and relations between zones) is part of interpretation and possibly of typing. Pipelines should retain span offsets or section labels, not only phrase types.

## Earlier candidate material (extra source)

Besides `republic_clean` notebooks and the `formula_detection` package, there is an earlier machine-generated candidate set:

- `~/develop/republic_ner_matching/output/s4_opening_phrase_candidates.jsonl`

Shape (sampled): one JSON envelope with **271** frequency-ranked opening n-grams (`phrase`, `count`, `word_count`), kept at `minimum_frequency=5`, after excluding gold dates from tier-1 resolution text. Examples: `ontfangen een` / `ontfangen een missive` / `is gelesen` / `ontfangen een missive van`. Word lengths are mostly 2–5.

These are useful as an additional seed inventory of formulaic openings to compare, filter, and reinterpret under the building-block / position notions above. Treat as candidate archaeology (like gold tables), not as ground truth.

**Gaps relative to our notions:** records have **no span or document-position fields**, and many short items (e.g. bigrams) still need building-block criteria — frequency alone does not decide which are compositional units vs fragments of longer openings.

## Two lineages (same problem, different maturity)

```mermaid
flowchart TB
  problem[Formulaic language in resolutions]
  notebooks[republic_clean notebooks]
  package[formula_detection package]
  s4[s4 opening phrase candidates]
  project[This Project republic-formulas]

  problem --> notebooks
  problem --> package
  problem --> s4
  notebooks -->|"requirements + gold archaeology"| project
  package -->|"technical core dependency"| project
  s4 -->|"earlier opening candidates"| project
  shell[dighum_template shell] -->|"data_io + provenance"| project
```

### 1. `republic_clean` notebooks — domain prototypes

Exploratory REPUBLIC work: writeups, year-by-year clustering, graphs of formula *elements*, links to *hoedanigheden*, hand-curated CSV/XLSX tables, some Flair tagging experiments.

- Backed by **live Elasticsearch** and hard-coded local paths
- Uses `republic.*` helpers and `fuzzy-search`, **not** the published `formula_detection` package
- Best treated as **problem framing + labelled reference material**, not as application code to copy

### 2. `formula_detection` — reusable library

Marijn Koolen’s published package ([PyPI](https://pypi.org/project/formula_detection/) / [GitHub](https://github.com/marijnkoolen/formula_detection)). Core idea: **`FormulaSearch`** over tokenized texts builds vocab/co-occurrence structure and surfaces candidate formulaic phrases (contiguous or with variable slots).

Around that core sit orthographic normalisation/variants, motif/boundary helpers, clustering/typing, and REPUBLIC-oriented **iterables** (`resolution_iterables.py`) that turn corpora into token streams.

This is the **technical core to depend on**, not fork.

### 3. S4 opening-phrase candidates — earlier inventory

Frequency-ranked opening n-grams from `republic_ner_matching` (271 candidates in the current file). Complements notebook gold and library demos as another prior pass over formulaic openings; to be loaded via manifest paths when the Project ingests seed lists. Reinterpret with building-block criteria and (when possible) re-attach position in the resolution.

### 4. This Project — dighum shell + domain pipeline

Already bootstrapped from `dighum_template`: Python/uv, `data_manifest.toml`, `data_io` with provenance. The intended evolution is a thin **project layer** that:

- feeds clean token streams into `FormulaSearch`
- represents **gappy building blocks** and their **combinations**
- keeps **document position** with candidates (for cues like decision vs resumption)
- writes outputs through `data_io`
- uses ES-free sample/frozen corpora plus seed lists (notebook gold, S4 openings)
- lifts *ideas* from the notebooks without lifting the notebook tree

## Mental model of the detection pipeline

```mermaid
flowchart LR
  texts[Tokenized resolutions with position]
  search[FormulaSearch and related layers]
  blocks[Building-block sub-formulas]
  compose[Combinations with gaps and slots]
  typed[Types sensitive to document position]
  out[Provenanced outputs]

  texts --> search --> blocks --> compose --> typed --> out
```

1. **Input:** iterable of token lists (any tokenizer; often `fuzzy-search` tokens), with enough structure to recover **position in the resolution**.
2. **Index:** term frequencies, skip/co-occurrence filtering.
3. **Building blocks:** candidate short formulas that meet **building-block criteria** (not raw short n-grams).
4. **Composition:** how blocks combine into larger formulas, allowing **non-contiguous** skeletons with variables between them.
5. **Position-aware typing:** interpret / label formulas using where they occur (e.g. decision-final vs opening resumption).
6. **Project wrap:** manifest paths + provenance sidecars (what the dighum shell adds).

## What to keep vs leave behind

| Keep / evolve | Leave behind (for now) |
|---------------|------------------------|
| `FormulaSearch` + vocab/candidate pipeline | Copying the whole notebook tree |
| Resolution/corpus iterables pattern | Live ES as a hard dependency |
| Writeup concepts (why formulas; elements; hoedanigheden) | Downloads-path loaders, mega output notebooks |
| Building-block criteria + composition + position | Treating every frequent bigram/trigram as a formula |
| Curated labelled tables + S4 opening candidates (path-cleaned) | Flair `.pt` models unless tagging becomes a goal |
| dighum `data_io` + provenance | Forking/vendoring all of `formula_detection` |

## Suggested reading order (conceptual)

1. `formulas_writeup.ipynb` — why REPUBLIC needs formulas  
2. `formulas_elements_writeup.ipynb` — formula *elements* as graph pieces (composition precursor)  
3. `formula_detection` README / `FormulaSearch` — how detection works mechanically (incl. variable elements)  
4. `docs/Document-Pattern-Detection-Findings.md` — design rationale in the package  
5. `notebooks/resolution_iterables.py` — how REPUBLIC texts become token streams  
6. `s4_opening_phrase_candidates.jsonl` — earlier opening-candidate inventory  

## Implication for this Project

**Shell is ready; domain layer is the work.** First useful slice still: sample tokenized text → `FormulaSearch` → provenanced candidates — without Elasticsearch — but the *target conceptual model* is richer than flat phrase lists: **criteria-governed building blocks, gappy composition, and position-sensitive interpretation**, seeded by notebook gold and S4 opening candidates.
