# STEPT1q — Single-formula retrieval + discrimination (three arms, clean gold)

**Goal:** For **one formula at a time**, compare the three ways of locating its instances — substring, TF-IDF window, slot-cloud+DAG — on *clean* gold, and settle the open question Doc B rev 2 flagged: **does the bare substring still beat the structured model once the gold is not mislabelled?** Design: [`docs/formula-abstraction-design.md`](../../docs/formula-abstraction-design.md) (Doc B), §"Retrieval arms to compare".
**Done when:** provenanced `formula_retrieval_arms_metrics` + `_scores` written; span-review workbook built for STEPT1q2; NOTES pass/fail on gates below; `data_io.check` clean.

**Prerequisite:** the 2026-10-21 ES re-pin (`resolutions_index = full_resolutions-2025-02-20`). Reuses frozen clouds/cuts for the DAG arm — no retraining.

## Gold: clean sample, not the stale sets

Do **not** load `missive_es_gold` / `rekest_es_gold` / `advies_es_gold`. They are pre-re-pin and ~31% mislabelled (`DECISIONS.md` 2026-10-21); the full re-fetch is still owed and is **not** a prerequisite here. Instead reuse the validated sampler from `scripts/recheck_es_gold_sample.py`:

- gold = `stratified_gold_ids` (k ids/year from the *pinned* index) + `flat_texts` (same generation ⇒ exact join),
- negatives = `verified_negatives` (flat-sampled, minus any the pinned index labels as the target type).

All three arms score the **identical** gold and negative rows. Arm comparison is internally valid on a sample even though absolute rates carry sampling error — report Wilson CIs and never quote a point estimate bare.

`stratified_gold_ids` is stratified by year but, by default, **systematic within year**: it sorts by `_id` ascending and takes the lowest N ids per year, not a random draw. `--random-within-year` opts into random-within-year sampling (via ES `function_score`/`random_score`) for comparison. The default is kept as-is so results stay comparable to the recorded 2026-10-21 recheck figures, which were produced with the systematic sampler.

## Formulas in scope (one run each)

| Type | Why this one | Question it answers |
|------|--------------|---------------------|
| `missive_ontfangen` | Doc B point 2: stale model 0.887 vs substring 0.915; clean model 0.988, substring **never re-measured** | **Retrieval** — does structure buy anything over a hinge token? |
| `requeste_geleesen` | Only type still failing the FP gate on clean gold (0.171, CI 0.136–0.213); STEPT1k's decision-type confound is real signal | **Discrimination** — can any arm separate it, or is the confound arm-independent? |

`advies_geleesen` optional (`--type advies`) as a third data point; it already passes both gates, so it is a control, not a question.

## Arms (identical rows, each with its own cut)

1. **Substring** — two variants, both boolean (no cut), both reported:
   - `substring_wording` — the type's existing `wording_flags()` regex. This is the baseline STEPT1n actually reported, so it is the only apples-to-apples comparison against the stale 0.915.
   - `substring_scheme` — the scheme's `search phrase` from `formula_schemes_sample.json` (`tfange` for `ontfangen_start`, `op\s?[td]+e reques` for `requeste_start`). Doc B's nominated arm 1.

   These are **anchor** matchers: a few characters, so their span is 1–2 tokens by construction, not a formula span. Measure them by *containment* (§Span geometry), never by IoU.
2. **TF-IDF window** — `formulation/boundary/tfidf_windows.py`: `collect_windows` → `score_windows` vs the type's canonic → `select_candidates`. The frozen 0.40 cut (STEPS1b) was calibrated for `opening_requeste_18c` only; for other types calibrate on this sample at p20 of gold-positive window scores and **report both** the frozen and the calibrated cut, as two arms: `tfidf_window` (frozen 0.40) and `tfidf_window_p20` (this-sample p20, same best-window scores, no refit). A low `tfidf_window` recall is not evidence the arm is weak if it has never been calibrated for this template — `tfidf_window_p20` is what tells you whether it's the threshold or the arm.
3. **Slot cloud + DAG** — the type's `score_text(text, cloud)` with the frozen cut from `fit_*_presence_model()`. Span = returned `start_idx`/`end_idx`.
4. **Slot cloud + DAG, clean bootstrap** (`dag_clean_boot`) — same machinery, cloud re-bootstrapped from a bootstrap split of the *clean* sampled gold, cut recalibrated at p20 on its holdout (**not** the frozen cut).

### Why arm 4 is not optional

`fit_missive_presence_model()` / `fit_requeste_presence_model()` bootstrap their clouds from `load_*_gold_18c()` — the **stale** sets. So arm 3's cloud was learned from ~31%-mislabelled text. The recheck accepted that deliberately (it isolated gold contamination from pipeline change), but here it confounds the headline question: if the substring beats a cloud trained on bad text, that is not evidence that structure fails.

Consequently **G1 is judged on arm 4 vs arm 1**, with arm 3 reported alongside as the deployed-model number. If arm 1 beats arm 4 too, the substring win is real. If arm 1 beats arm 3 but loses to arm 4, the verdict is "stale-bootstrap artifact" and the owed re-fetch becomes the blocking next step rather than STEPT1r.

The clean arm must also match arm 3 on bootstrap **volume**, or the comparison is confounded on two axes at once (gold quality *and* bootstrap size) instead of one. At the default `--per-year 15`, `dag_clean_boot`'s own-gold bootstrap split is only ~1,104 texts against `dag_frozen`'s 141,636 — a ~128x gap that would let volume, not gold quality, explain any gap in the arms' scores. `--boot-per-year 100` samples a second, disjoint stratified pool (ids already in the eval gold are dropped) and bootstraps `dag_clean_boot`'s cloud from that pool instead, giving ~7,800 disjoint bootstrap texts — still asymmetric against the frozen cloud's 141,636, but no longer 128x.

### Span geometry (common token grid)

All arms report spans on **one** grid: `align_tokenize(text)`, joined back with single spaces so `tfidf_windows.tokenize` (whitespace split) reproduces it exactly. Then:

Spans are not comparable lengths across arms, so each pair gets the geometry it admits. A TF-IDF window is a **fixed 16 tokens** (`tfidf_windows.WINDOW_SIZE`); a DAG span is the formula itself (~5–7 tokens); an anchor is 1 token. Raw IoU between a window and a DAG span is therefore capped near **0.35 by construction** and would measure window granularity, not disagreement.

| Pair | Measure | Why |
|------|---------|-----|
| `dag_frozen` ↔ `dag_clean_boot` | **IoU** | the only pair with comparable span lengths |
| TF-IDF window ↔ DAG | **containment** (DAG span inside the window) + **midpoint distance** in tokens | window is a coarse locator; the question is whether it picked the right region |
| substring (either variant) ↔ any span arm | **containment** | anchors are 1 token; IoU would be ~0.06 regardless of agreement |

## You do

```bash
uv run pytest tests/test_formula_retrieval_arms.py -q

# Smoke (no ES / parquet)
uv run python scripts/run_formula_retrieval_arms.py --fixture-only

# The two real runs (ES + resolutions_flat; ~minutes each at default per-year)
uv run python scripts/run_formula_retrieval_arms.py --type missive --per-year 15 --boot-per-year 100
uv run python scripts/run_formula_retrieval_arms.py --type requeste --per-year 15 --boot-per-year 100

# G5: same primary type, both sampling modes (default vs random-within-year).
# The default-mode missive run above already supplies one half of this
# comparison (systematic_id_asc); only the random-within-year half is new.
uv run python scripts/run_formula_retrieval_arms.py --type missive --per-year 15 --boot-per-year 100 --random-within-year

# Span-review workbook for STEPT1q2 (hand-read)
uv run python scripts/build_span_review_xlsx.py --type missive --sampling-mode systematic_id_asc

uv run python -m data_io.check
```

Fill / judge: `docs/proofs/multi-template-registry/STEPT1q-formula-retrieval.md` (create).

## Measurements (required)

| Metric | Where |
|--------|-------|
| Per-arm recall + FP on the same rows, with Wilson 95% CIs | `metrics.arms[*]` |
| Cut used per arm + rule (frozen / p20-on-sample) | `metrics.arms[*].cut` |
| **Arm deltas**: substring − DAG recall, and FP at that recall | `metrics.deltas` |
| **Recall-matched FP**: `tfidf_window` / `dag_frozen` / `dag_clean_boot` each cut to the same (minimum achieved) gold recall before comparing FP — two arms fitted at different, independently-chosen cuts are not comparable on raw FP alone | `metrics.recall_matched` |
| **DAG↔DAG span IoU** (frozen vs clean bootstrap): median + p10 + disjoint share | `metrics.span_agreement.iou` |
| **Containment**: DAG span inside the TF-IDF window; each anchor inside each span arm | `metrics.span_agreement.containment` |
| **Midpoint distance** in tokens (median + p90) per containment pair | `metrics.span_agreement.midpoint_offset` |
| **FP overlap matrix**: negatives fired by 1 / 2 / 3 arms; unanimous-FP share | `metrics.fp_overlap` |
| ES `evidence` offset inside each arm's span, where present — **covariate only** | `metrics.evidence_covariate` |
| Per-row arm spans + fire flags | `formula_retrieval_arms_scores` |
| Sampling mode + seed (systematic vs random-within-year) | `metrics.sampling_mode` / `.sampling_seed` |

Both `formula_retrieval_arms_metrics` and `formula_retrieval_arms_scores`
**accumulate** across runs rather than being overwritten: each write is
keyed by `(type, sampling_mode)`, so re-running the same pair replaces just
that record and a run for a different pair (e.g. `requeste`, or `missive`
with `--random-within-year`) is appended alongside the others. `--fresh`
discards the accumulation and writes only the current run. The span
workbook (`build_span_review_xlsx.py`) selects its rows by `--type` +
`--sampling-mode`, so it can never silently read another pair's rows.

## Eval gates (NOTES)

1. **G1 Substring vs DAG on clean gold — the open question.** Judged on **arm 1 vs arm 4** (clean bootstrap); arm 3 reported alongside. State the verdict in one line, no reframing: substring **wins** if its recall ≥ DAG's **and** its FP ≤ DAG's; **loses** if worse on both; **trades** otherwise (then name which operating point you would pick and why). A substring win is a valid, publishable result — Doc B says so explicitly: it would mean identity is carried by the hinge token. If arm 1 beats arm 3 but not arm 4, record "stale-bootstrap artifact" and do not claim either way.
2. **G2 Does any arm clear FP ≤ 0.05 for requeste?** The gate is now known reachable (missive 0.018, advies 0.024). If no arm clears it for requeste, the decision-type confound is **arm-independent** — a gold/ontology problem, not a retrieval one — and must be recorded as such. A verdict here needs enough clean negatives to actually resolve 0.05: at `n=226`, the Wilson half-width is **±0.026**, which straddles the gate either way. Always quote the Wilson CI and the event count (`k`/`n`) beside any FP rate — never the bare rate — and prefer the `--neg-n 2500` default (~1100 clean negatives after the actually-target-type drop) before judging this gate.
3. **G3 Is this a span question at all?** Pass when **all three** hold: DAG↔DAG IoU median **≥ 0.80**; DAG-span-inside-TF-IDF-window containment **≥ 0.80**; anchor-inside-DAG containment **≥ 0.90**. Then the arms localise the same text, the choice is recall/FP only, and the STEPT1q2 hand-read can stay small (≈30 rows). Any of them below **0.60** ⇒ arms disagree about where the formula *is*; no arm may be preferred until the hand-read span gold exists. Report midpoint distance alongside — a high containment rate with a large median offset means the window is merely wide, not accurate.
4. **G4 Unanimous FPs.** Report the share of negatives every arm fires on. A high share is evidence of residual gold-label gaps (T1k2's "bearing" FPs after the re-pin) rather than model noise; a low share says FPs are arm-specific alignment slop. No promotion or gold edit either way in this step.
5. **G5 Sampling robustness.** Run the primary type both ways (default and `--random-within-year`). If any arm's recall or FP moves outside its Wilson CI between the two modes, the systematic sample was biased — report it, and note that the recorded 2026-10-21 recheck figures inherit the same bias. If every arm stays inside its CI, say so explicitly; that is also the evidence that the recorded figures are sound.
6. Pass/fail written in proof NOTES, with CIs.

## Do not

- Re-fetch the full `*_es_gold` sets (74k–177k rows) — still owed, separate step; not needed for an arm comparison.
- Quote any pre-re-pin number as current (stale figures appear only as a labelled `*_stale` column).
- Treat ES `evidence` as span gold: it is a point anchor and upstream silver. Covariate only.
- Retrain or recalibrate the accepted DAG clouds/cuts (missive 6.0, requeste 4.5) — frozen.
- Do slot ablation / formula reduction (L1→L2). That is the next step, and mixing it in makes the arm comparison unreadable.
- Mint `template_id`s, touch `ACCEPTED_TYPE_IDS` / `formula_templates`, or revise STEPT1k2's record beyond what the re-pin decision already says.
- Read a better recall/FP number as a better *answer* — the arms must be measured on span presence, not on a resolution-level profile (Doc B, "the comparison pitfall").
- Bootstrap the clean cloud from the eval rows when a disjoint pool is available (`--boot-per-year > 0`) — that is the confound this step exists to remove.
- Report an arm with 0/N gold hits as a measured recall. A period/type-mismatched anchor (e.g. a 17c phrase regex on 18c text) will legitimately go 0/N; `arm_rates` marks it `applicable: False` with an `applicability_note` — carry that mark through `deltas` and `fp_overlap` rather than quoting the 0.000 as a finding.

## Datasets to register first

| Logical name | Tier | Contents |
|--------------|------|----------|
| `formula_retrieval_arms_metrics` | semi | Per-arm recall/FP + CIs, deltas, span agreement, FP overlap |
| `formula_retrieval_arms_scores` | explore | Per-row per-arm fire flag + span token indices |
| `formula_span_review_xlsx` | explore | STEPT1q2 hand-read workbook (stratified by arm agreement) |
| `formula_span_review_meta` | semi | Workbook build stats (strata, n per stratum, seed) |

Register in `data_manifest.toml`, then `uv run python -m data_io.check`, **before** any code references them.

## After this step

Mark STEPT1q in `PLAN.md` + Doc B status line. Then:

- **STEPT1q2** — ingest the hand-read span verdicts → honest span accuracy per arm (mirrors STEPT1k2's build/ingest pattern). Required if G3 fails.
- **STEPT1r** — formula reduction L1→L2: ablate one slot at a time via `align_dag(optional_slots=...)`, recalibrate each configuration at its own p20 (`calibrate_cut`, as `clause_chain.build_appointment_clause_specs(per_clause_cuts=True)` already does), keep the minimal localising subset. Only meaningful if G1 says structure earns its place.
- If G1 says substring wins outright, Doc B's abstraction ladder needs a rev 3 before STEPT1r: L2 reduction is pointless if L0 is already sufficient.

Clear the chat before the next step.
