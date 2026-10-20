# Presence lists 1630–1704 — side plan
<!-- doc-status: sidelined -->

**Not on the active checklist.** Track F (M1 STEP2) stays primary. This plan is for offline harvest of *presentielijst* / presidium blocks from raw session JSON.

**Same research thread as Track R and M1–M3:** formulaic SG language at a different grain (session opening, attendance skeleton). R1 asked “whole resolution looks like *aanstelling*”; here “where is the presidium formula in the sitting”; M1 asks “what smaller building blocks repeat inside resolutions”. See [PLAN.md](../PLAN.md) § One research thread and [docs/research-publications.md](../docs/research-publications.md) (JOCCH + *Structure-Derived Incremental Modelling* on **attendance lists** and phrase-led structure).

**Sources (register via `data_manifest.local.toml`; canonical names in `republic_ner_matching`):**

| Logical name | Role |
|--------------|------|
| `sessions_json_source` | `sessions_json-2026-02-27.tar.gz` (**~9.4 GB** on disk; **121,119** `.json.gz` members; member payload sum **~10.0 GB**), warm tier |
| `session_index_all` | **121,119** rows (matches tar); filter `session_date` → **~56,650** sessions in 1630–1704 |

**Reuse:** `republic_corpus.republic_corpus.sessions.SessionsArchive` (index + `read_session`); preside/present heuristics from `republic_ner_matching` (`s4_session_start_scan`, `s6b_anchor_harvest` phrase lists). Do **not** depend on live Elasticsearch or `republicgit` `run_attendancelist.py` as-is (18c-indexed attendance_list objects).

---

## Goal

A **more-or-less complete inventory** of presence / presidium text per sitting, **1630–1704**: raw block text first; structured names later. Explicit abstentions when no anchor is found.

---

## Unpack the tar to disk?

| Option | Disk (order of magnitude) | Random access | Verdict |
|--------|---------------------------|---------------|---------|
| **Keep only `tar.gz`** | ~10 GB (already) | No — sequential scan ~30–60 s per random session unless you build an index | **Default for POC** |
| **Extract tar → tree of `.json.gz`** | ~**10 GB** extra (121k members; measured payload sum ~10.0 GB) | Yes, per-session `open()` by path from `tar_member` | **Optional** if you rerun harvest many times (~20 GB total if you keep both tar.gz and full tree) |
| **Gunzip all → plain `.json`** | **+ tens of GB** (often 30–80+ GB total) | Easier debugging only | **Not worth it** — JSON parses fine from `.json.gz` in memory |

**Recommendation:** Do **not** fully unpack to plain JSON. Consider extracting **only** the year/inventory subset you are actively iterating on, or a **derived** parquet/jsonl of presence blocks (megabytes–low gigabytes), not 121k full session payloads duplicated on disk.

The outer archive is **~9.4–10 GB** compressed. A full sequential pass over the tar is acceptable once per harvest version (same pattern as `s4_session_date_region_scan` on 1.5k sessions).

**No unpack.** Work is always **one batch job**: stream `sessions_json_source` once, keyed by a pre-built `tar_member` want-list from `session_index_all`, write rows with checkpointing. Not interactive per-session lookups.

---

## Batch execution (e.g. overnight)

| Mode | Want-list size | Tar read | When |
|------|----------------|----------|------|
| **P1 sample** | ~500–700 (Tier 1 + Tier 2 merged **before** the run) | Sequential until all wanted members seen — often **most of the archive** (~tens of minutes), not 57k decompressions | First batch |
| **P3 full** | ~56,650 (1630–1704) | **Full** sequential pass + heavy CPU (~hours overnight) | After P1 review |

**Tonight (typical):** one **P1 batch** — build Tier-1 stratified draw + Tier-2 extra draws (and any hand-picks) into a **single** want-list → one script invocation → `save_*` + optional `.checkpoint.jsonl`. Review metrics in the morning; Tier-2 *conditional oversample* from weak strata can be a **second batch** later if needed.

Run detached (`tmux`, `nohup`, or CI) so the tar stream is not tied to an IDE session. Do not overlap with other jobs that stream the same tar (e.g. `s6b_anchor_harvest` on the warm drive).

---

## Hand workflow → pipeline (bracket the middle)

A human would not start blind on 1630–1704. Same order for the side plan:

1. **1626–1630:** use attendance / opening-head material you already trust; open the matching **raw session JSON** and note where the list lives (`attendance` region vs `para`, presidium line, splice vs flat text). NER-matching helpers: `alignment_1626_1630` (tier3 head), `s6b_session_fingerprint_match`, `s4_session_date_region_scan`.
2. **18th c.:** use familiar **opening patterns** (`pattern_finders` / presentielijst phrasing) as *hypotheses* on the middle century—not as proof every name resolves.
3. **1630–1704:** batch harvest with **fuzzy_search as candidate layer** + structural merge; calibrate thresholds on the two-tier sample.

Full harness detail: [`.cursor/plans/harness_fuzzy_search_presence_adef5f17.plan.md`](../.cursor/plans/harness_fuzzy_search_presence_adef5f17.plan.md) (A0 P-cal).

---

## Extraction logic (after P-cal + sample validate)

1. Join **known attendance/head** when available for a session (early-century calibration rows).
2. **`text_region_class == "attendance"`** when present (not sufficient alone — presidium often sits in **`para`**, see 1640-01-01 sample).
3. **FuzzyPhraseSearcher:** all hits logged; 18c-derived seeds adjusted after P-cal.
4. **Fallback:** preside/present anchor → text until first body opener (*Is gehoort*, *Ontvangen*, *Is voorgelesen*, …).
5. Record **`extract_method`**, **`session_id`**, **`session_date`**, **`inventory_num`**, **`raw_block`**, optional president snippet; no delegate-ID linking in v1.

---

## Steps (one per session when executing)

### P-cal — Bracket calibration (before P1 batch)

**Early (1626–1630):** build `presence_calibration_1626_1630` — normative attendance/head text aligned to raw session excerpts and region evidence.

**Late (18c):** export phrase seeds from `republicgit` `pattern_finders`; score against 1626–1630 excerpts; note variants needed for 17c.

**Done when:** adjusted seed list + short write-up of how lists sit in session text (informed by hand-style spot checks, now reproducible).

### P0 — Register inputs

Add `sessions_json_source` and `session_index_all` to formulation manifest + `local.toml` paths (warm tier). `uv run python -m data_io.check`.

**Done when:** both resolve from formulation root.

### P1 — Two-tier sample harvest (no full unpack)

Formulae and classifier behaviour shift by period and register — use **two tiers**, not one inventory and not one flat random draw.

**Tier 1 — broad screen**

- **~200–300 sessions**, fixed `random_state` (e.g. 42).
- **Stratify** by **decade** (1630s … 1700s); spread across **inventories** (minimum n per decade so no century is empty).
- One tar pass on the Tier-1 `tar_member` want-list.
- Compute **success / abstain / partial** rates by decade, inventory, and `extract_method` (attendance class vs anchor fallback).

**Tier 2 — targeted deep dive**

- **~200–400 additional sessions**, same `random_state` discipline but **conditional**:
  - **Oversample** strata where Tier 1 abstain or partial rate is high.
  - Add a small **hand-picked** set if needed (e.g. inventories with Latin presidium, known mis-tagged attendance-in-`para` cases from NER-matching notes).
- **Batch default:** merge Tier 1 + Tier 2 want-lists → **one** tar pass. Reserve a **second batch** only for post-hoc oversampling of weak strata after Tier-1 metrics exist.
- Manual read **~30–40** sessions **across both tiers** (attendance vs para presidium, Latin vs Dutch openings).

**Outputs:** one provenanced explore dataset (or Tier-1 + Tier-2 logical names) with a **`sample_tier`** column (`1` | `2`).

**Done when:** both tiers harvested; Tier-2 rationale written (which strata triggered oversampling); timing estimate for full 56k pass; short note on convention gaps still open before P3.

### P2 — Decide extract vs unpack

From P1 timings:

- If **&lt;2×** full pass expected over project life → **keep tar.gz**, index-driven streaming only.
- If many reruns with heavy random access → extract **subset** `.json.gz` for 1630–1704 only to warm/scratch (not full gunzip).

**Done when:** short note in `docs/DECISIONS.md` (unpack yes/no + path).

### P3 — Full 1630–1704 harvest

Single checkpointed tar pass; filter index `1630-01-01` … `1704-12-31`.

**Done when:** registered dataset e.g. `presence_blocks_1630_1704` (name TBD) + provenance; counts by year/inventory and by `extract_method`.

### P4 — Name parsing (optional later)

Split lists on comma / *ende*; era-specific patterns — **not** 18c `delegates_18thc_raw` as sole authority (`pattern-authority` wisdom).

---

## Out of scope here

- Formula `FormulaSearch` (Track F)
- Replacing `resolutions_flat` or aanstelling retrieval
- Claiming 100% delegate resolution without 17c reference data

---

## Pointer

Root [`PLAN.md`](../PLAN.md) lists this under **Side plans** only.
