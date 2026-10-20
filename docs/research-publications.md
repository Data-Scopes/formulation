# Research publications — map to this repo

Canonical **research framing** for Track F, judged Track R, and side plans. PDFs may live in Cursor attachments or your literature folder; cite by title/DOI in code and decisions, not absolute paths.

## Core REPUBLIC / formula stack

| Publication | Focus | Implication for `formulation` |
|-------------|--------|-------------------------------|
| **The Value of Preexisting Structures for Digital Access: Modelling the Resolutions of the Dutch States General** (Koolen, Hoekstra, Oddens, Sluijter et al., *ACM JOCCH* 16(1), 2023, [doi:10.1145/3575864](https://doi.org/10.1145/3575864)) | Exploit **existing archival structure**; **fuzzy string search** on **formulaic boundary phrases**; meetings → resolutions; metadata layers; prioritise **qualifications (*hoedanigheden*)** over bare names for research utility | NER-matching axis, entity layers, and **fuzzy as boundary finder** — not a complete typology by itself. Aligns with **candidate-then-structure** harness. |
| **Modelling Resolutions of the Dutch States General for Digital Historical Research** (Collect and Connect / conference paper, ~2020; overlaps JOCCH narrative) | **Incremental modelling** with **phrase models**; need metadata on meetings, dates, **attendants**, resolutions, topics; digitisation ≠ structure | Side plan **presence lists** and session JSON work are the same problem class: attendants + session structure missing or coarse in flat exports. |
| **Structure-Derived Incremental Modelling: The Case of the Resolutions of the Dutch States General** (Koolen, Hoekstra, Oddens, Sluijter; in *Digital Scholarly Edition and Pre-modern Parliamentarism*, Vandenhoeck & Ruprecht 2022) | Analogue **structure** (volumes, paragraphs, fonts, **formulaic phrases**); **attendance lists** change by period; incremental extraction of sessions, **attendance**, resolutions; opening formulas (e.g. petition vs *OP de Requeste*) | **P-cal bracket** (1626–30 in session text + 18c patterns) matches “structure-derived” + cross-century attendance evolution. |
| **Formulaic Language and Regularisation in the Administrative Processes of the States General (1576–1796)** (Hoekstra & Koolen, working paper / CHRI lineage) | **Regularisation** via templates; **eleven periods** of formula use; cumulative repetition; variation (HTR/OCR, spelling, grammatical alternates) | Track F **M2 criteria** and M3 **position/composition**; Track R whole-resolution similarity is a **coarse** view of the same phenomenon. PyPI **`formula_detection`** implements search/clustering side of this agenda. |

## Broader context (lighter tie-in)

| Publication | Tie-in |
|-------------|--------|
| **Organizational and Technical Aspects of an Electronic Publishing Framework for Historical Sources** (Hoekstra, ING/Zope, ~2000) | Modular publication layers — analogue to **`data_io` tiers + manifest** and not collapsing heterogeneous sources into one schema. |

## One sentence for agents

We are continuing the REPUBLIC thesis: **repetitive formulaic language is the lever** for segmentation, access, and historical argument; **fuzzy search finds candidate boundaries**; **structure, position, and period** decide what a formula *means*; attendance and presidium blocks are **first-class structural layers**, not optional metadata.

## Related in-repo docs

- [`docs/formula-conceptual-overview.md`](formula-conceptual-overview.md) — building blocks, gaps, position
- [`PLAN.md`](../PLAN.md) — One research thread
- [`plans/presence-lists-1630-1704-side-plan.md`](../plans/presence-lists-1630-1704-side-plan.md) — attendance in raw sessions
- [`plans/milestones/R1-aanstelling-retrieval.md`](../plans/milestones/R1-aanstelling-retrieval.md) — one formula **type** at document grain
