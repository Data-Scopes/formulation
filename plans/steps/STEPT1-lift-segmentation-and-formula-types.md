# STEPT1 — Formula types first (alignment), then resolution scoring

**Status:** proposed; STEPT1a eval script wired (user runs full measure). Written for review.
**Prerequisite:** STEPT0 done — see [`STEPT0-typology-structural-profile.md`](STEPT0-typology-structural-profile.md) and `docs/DECISIONS.md` (2026-10-19).

### STEPT1a — You do

```bash
uv run pytest tests/test_appointment_formula_type.py -q
uv run python scripts/eval_appointment_formula_type.py --fixture-only   # smoke
uv run python scripts/eval_appointment_formula_type.py                 # full 18c gold + N=500 negatives
uv run python -m data_io.check
```

Outputs: `formula_type_appointment_metrics`, `formula_type_appointment_scores`. Judge pass/fail in NOTES from pre-1731 recall vs 0.235 floor, post-1731 ballpark, FP rate, and `popularity` block.

**Goal:** Reliably define **formula types** without regex detectors, then score resolutions for those types and ask what else (position, composition, …) is needed before calling something a resolution template.

**Two complementary entry plans** (same destination; pick one session to start):

| Entry | Idea |
|-------|------|
| **Align-first (A→B→C)** | Build a formula-type model, then score the corpus (§6). |
| **Sieve-first** | Remove resolutions we **already know**, then study what is left (§6-alt). |

**Sessions:** Do **not** ship a full entry in one chat. Align-first cut: STEPT1a = first formula-type model + held-out check; STEPT1b = presence scoring; STEPT1c = position / more. Sieve-first cut: STEPT1s0 = provenanced residual after known sieves; then feed residual into A on a sharp family or into exploratory profile.

---

## 1. What STEPT0 established (motivation, not the method)

Run: 1780, seed 20261019, 14 `proposition_type` values, 3 134 population resolutions, 1 063 sampled, 86.4% outcome-flag join. Output: `typology_structural_profile`.

**ES `proposition_type` is an entry point, not a typology.** Cross-checked against Track R gold (`aanstelling_selected`, 31 rows in 1780): **29 of 31 known appointments are labelled plain `missive`** (1 `rekest`, 1 `onbekend`). ES's own typing cannot isolate them — they sit among 1 489 missives.

They *are* separable structurally: 21/31 (68%) carry `ontfangen_start + vergaderinge_start + welkom`; 26/31 (84%) share a `welkom`-anchored pattern.

---

## 2. Core finding: the flags are wording matchers, not type matchers

`welkom` has **zero** occurrences before 1731, despite `formula_documents` covering 1705–1796. `eed` runs 1705–**1759** and then stops dead at 48/yr. These look like institutional change but are not.

Test (`sessie` spans the full period, `welkom` does not):

| period | detector | n | in `aanstelling_selected` | recall vs selected |
|---|---|---:|---:|---:|
| 1705–1730 | `sessie` (no `welkom` exists) | 526 | 301 (57.2%) | **23.5%** (301/1 279) |
| 1731–1796 | `welkom` ∪ `sessie` | 1 815 | 1 534 (84.5%) | **60.4%** (1 534/2 541) |

Same formula type; recall collapses 60% → 24% when the wording shifts. Older variants ('verwellecomt', 'sessie genomen' and friends) are absent from the matrix entirely, so 23.5% is a floor, not a measurement.

**Consequence:** the 31 flags are *seeds for a variant cloud*, not detectors. `welkom`/`sessie`/`verwellecomt`/`sessie genomen` are **one slot's variant set, not four features**. This is exactly what `boundary/slot_cloud.py` + `align_dag.py` already implement — currently thin on real stakes. STEPT1 makes that machinery the **definition** of a formula type, not a polish step after flag segmentation.

`eed` stopping in 1759 is almost certainly the same artefact and needs no separate investigation.

---

## 3. Why the lift→segment→cloud order felt off

Lift-over-baseline on flags is still useful **exploratory** evidence (which surfaces co-travel with which ES types; leakage traps). It is **not** how we define a formula type:

- Flags are period-bound wording; ranking them reifies the matcher problem.
- Exact flag-vector segments fragment; min-frequency floors delete the targets (e.g. `welkom` inside `missive`).
- Building clouds *after* flag segments puts the reliable object last.

**Reframe:** (A) find formula types by alignment / period subtype → (B) score resolutions for presence → (C) ask whether presence is enough or we need more structure.

Lift tables from STEPT0 stay as priors for **which families to try first** (sharp sparse: `advies`, `rapport`, `memorie`, `conclusie`, appointment/`welkom`–`sessie` kin). Do **not** require a settled rule that `missive` is residual — that remains to be seen.

**Leakage (still enforce in any flag-touching code):** never treat `praeside_start` / `praesentibus_start` as defining features.

**Event rates:** use for interpretation and narrative (appointments ~fortnightly), not as an automatic promotion threshold until a second institutional series exists.

---

## 4. Baseline reframe: event rate, not corpus share (interpretation)

Percentages are the wrong denominator for *how common a real-world act is*. Appointments run **27.5/yr** by `welkom` (median 26), **38.5/yr** by Track R's selection — plausible institutional rhythm. Absolute numbers matter: `welkom` = 1 677 resolutions, **8× Track R's entire gold set** (213).

Note `formula_documents` covers 283 870 resolutions (1705–1796), *not* the full ~692k corpus — do not extrapolate rates across the 17c.

---

## 5. The formula datasheet: inventory + skeleton seeds, not variants

`docs/proofs/multi-template-registry/formula_schemes_sample.json` — 27 rows. `phrasename` ≈ `formula_documents` columns. **`forms` empty** → cannot seed variant clouds; **`first_appeared` empty** → no diachronic anchors.

Usable: `canonic_formula` (where real) as alignment template seed; `intention` as semantic label; `search phrase` as **seed only**.

**Conflict:** datasheet `welkom` → `proposition_type: request`; ES → mostly `missive` for the same gold appointments.

**Division of labour:** datasheet → naming / intention / partial canonic seeds. Corpus + Track S slot-cloud / DAG (or MSA) → formula-type model. Flags → weak labels for candidate pools, not detectors.

---

## 6. Proposed method (inverted)

### A — Reliably find a formula type (not by regex)

For one family at a time (start with appointment / `welkom`–`sessie` kin — Track R gold + canonic seeds; then a sharp sparse family from STEPT0 lift priors):

1. **Candidate pool** from weak signals (flag OR, ES type, gold list) — pool only, not the type definition.
2. **Build a formula-type model** that tolerates wording drift:
   - Prefer existing Track S path: seed from `canonic_formula` / known surfaces → `slot_cloud` variants → **SW / DAG** skeleton; **or**
   - MSA over tokenised candidates if DAG bootstrap is too thin; **or**
   - **Period subtypes** of the same formula type when one cloud fails across 1705–1730 vs 1731–1796 (same type, different subtype rows / period-keyed clouds — not new regexes).
3. **Measure (required — STEPT1a does not “feel done” without numbers).** Write provenanced metrics for the candidate formula-type model, at least:

   | Metric | What |
   |--------|------|
   | **Recall vs gold** | On `aanstelling_selected` (appointment family): overall + **split pre-1731 / post-1731** |
   | **Baseline delta** | Same splits for wording matcher `welkom`∪`sessie` (and `sessie`-only pre-1731) — report model − baseline |
   | **Precision proxy** | FP rate / precision at the operating cut on the **explicit negative set** (below) |
   | **Align quality** | On held-out pool hits: distribute SW/DAG align score and/or span IoU vs seed/canonic span where available |
   | **Period subtype** | If two period clouds: metrics **per subtype** and pooled — show whether split helps |

   Operating cut (score threshold) frozen in the metrics row; no silent defaults.

   **Explicit negative set (appointment family, STEPT1a — locked):**

   - Universe: same 18c window as the recall eval (or the POC year slice under test).
   - **Exclude** from negatives: all `aanstelling_selected` ids; any id already in the candidate pool used to build the cloud (no train/pool leakage into FP).
   - **Negatives =** stratified random sample of remaining resolutions, size **N = 500** (fixed `random_state` recorded in metrics), **not** “flag-negative only” (that would re-bake the wording matcher).
   - Report: FP count, FP rate, and precision if treating gold∪pool-holdout as the positive side of the score table.
   - Do **not** use attendance leakage flags or ORG hits to define negatives.
   - Later families: same schema — named gold, named pool exclusions, N=500 stratified residual sample unless DECISIONS changes N.

4. **Acceptance bar (appointment family, first model):** pre-1731 recall **materially beats 23.5%** (`sessie`-only floor), with baseline delta reported; post-1731 recall at least in the ~60% `welkom`∪`sessie` ballpark or better; **FP rate on the N=500 negative sample recorded and judged** (not ignored). Other families get the same metric schema with their own gold/weak pool.

STEPT1a stops when metrics JSONL/parquet is written and the bar above is judged pass/fail in NOTES — not when a cloud merely exists.

### B — Score resolutions for presence of each formula type

4. Run the accepted model(s) over a year slice / 18c window of `resolutions_flat` (or flagged subset): per resolution, presence / best align score per formula type.
5. **Popularity punishment (required when ranking / composing types):** formulas that fire almost everywhere mean little. Estimate corpus hit rate ``p`` (random / negative-universe proxy); weight ``log(1/p)`` (IDF-style) and report ``score_weighted = score * weight``. Near-universal boilerplate (*goedgevonden*, *ontfangen_start*, …) gets a tiny weight; sharp rare types keep a large one. Acceptance bars for a *single* family (STEPT1a) still use the raw operating cut; weighted scores matter for multi-type bags and template composition.
7. Ask: do co-occurring formula-type hits **add up to** recognisable resolution templates (multi-label composition), or only a bag of fragments?

### C — If presence is not enough: position and maybe more

8. Test whether **position / zone** (opening vs decision vs close; offsets from evidence or framed windows) is required to turn formula-type bags into templates (`role_depends_on_place` already exists on registry rows).
9. **Maybe more** than presence + position — only open these if B/C fail:
   - **Order / composition** (A before B): sequenced formula types as a template
   - **Discriminators** (institution, etc.) inside a formula family — surfaces stay in `institution_patterns`
   - **Multiplicity** (repeated blocks)
   - **Gappy vs contiguous** match
   - Period already handled as subtype in A when needed

### Registry

10. Fill empty `tokens` on `appointment_*` (and new rows) from accepted A skeletons. Keep `discriminators` / `institution_targets` structure; no ORG strings in `formula_templates`.
11. **Cross-validate** every claim on ≥2 signals (ES `proposition_type`, flags, Track R gold, datasheet).

### 6-alt — Sieve-first: known out, then look at the rest

Another plan: **do not invent new types until the residual after known lists is characterised.**

1. **Sieve (union of known sets)** on an 18c year slice / window — ids only, no new classifiers:
   - Track R: `aanstelling_selected` (vergadering appointments).
   - Track L: labelled missive-receipt positives if using a labelled year; do **not** require L3 harvest.
   - Optional weak carve-outs already in hand: high-confidence appointment-sibling pools (e.g. Rekenkamer + cue) — mark as `other_appointment`-class, not R1.
   - Optional: resolutions that already hit an **accepted** A formula-type model once T1a exists.
2. **Write provenanced residual:** `typology_sieve_residual` (or metrics + id list): n in / n out per sieve layer; residual rate; ES `proposition_type` mix on residual; flag rates on residual (exploratory).
3. **Inspect residual** (small sample): is it still mostly generic missive boilerplate, or do sharp formula families appear that deserve A next?
4. **Hand off:** pick the next A family from residual structure (or park if residual is undifferentiated noise).

Sieve-first does **not** assume `missive` is the residual label — residual is whatever remains after known sieves. It also does not define formula types by regex; sieves are existing judged/labelled sets (and later accepted A models).

**Relation to align-first:** sieve shrinks the haystack before A; A→B eventually becomes another sieve layer. Either order is valid; sieve-first is cheaper when the question is “how much of 1780 is still unknown?”

---

## 7. Verification

- **Align-first (A measured):** provenanced metrics with recall (pre/post-1731), baseline delta vs wording flags, FP rate on explicit N=500 negative sample, align-score/IoU distribution; NOTES pass/fail on the appointment bar. Presence scoring (B) provenanced; NOTES state whether bags look like templates or need C+.
- **Sieve-first:** provenanced residual after documented sieves; per-layer counts; residual sample noted; next A family chosen or park decided.
- No accepted type is defined by `praeside_start`/`praesentibus_start`.
- `uv run python -m data_io.check` clean; registry edits keep discriminator / institution_patterns split.

---

## 8. Open questions for review

- Start with sieve-first or align-first for the next session?
- For A: slot-cloud + DAG first, or MSA when candidate sets are small and homogeneous?
- When does period subtype beat one cloud with skip-edges? (decide from **measured** per-subtype recall/FP, not intuition)
- Presence score: binary hit vs continuous align score vs calibrated threshold (reuse STEPS1b-style cut?) — threshold chosen from A metrics, then frozen
- Is N=500 negatives enough once non-appointment families run, or should N scale with year-slice size?
- How many formula types in the bag before “template” needs explicit order (C)?
- What else beyond position actually moves the needle (composition, institution, …)?
- Which known sets belong in the first sieve (R1 only vs R1+L1 labelled vs weak siblings)?
- Should `sessie` and extra `formula_documents` flags (`handen`, `in handen`, `versonden`) get datasheet rows as seeds only?

---

## 9. Scope guards (carried from STEPT0)

- 18c only for type definition and scoring; 17c parsing is unreliable — don't confound formula drift with segmentation error.
- Closing boilerplate is reported **as formula**, never as a claim about what was decided.
- One step per session (1a / 1b / 1c).
- Flags and lift remain exploratory; they do not define formula types.
