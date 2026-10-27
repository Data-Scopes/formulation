# STEPT1r — Requeste low-score band characterisation

**Goal:** Characterise the STEPT1q **bimodal** requeste gold split (low ≈4.5 / high ≥8) before any Doc B L2 slot reduction. Decide — with a **human NOTES call** — whether the low band is a distinguishable short-form subpopulation, a coverage/OCR gap in the existing cloud, or weak-cut noise on one type.
**Done when:** part A metrics written; part B sample read (when `resolutions_flat` mounted) or explicitly deferred with reason; NOTES call recorded; no new `template_id` without human name; `data_io.check` clean; `PLAN.md` updated.

**Prerequisite:** STEPT1q PASS; `formula_retrieval_arms_scores` + `requeste_subtype_scores` on disk. Doctrine: [`plans/milestones/T1-unknown-first.md`](../milestones/T1-unknown-first.md), [`docs/DECISIONS.md`](../../docs/DECISIONS.md) 2026-10-22 (naming / scaffolding / drift).

## Constraint (locked)

- **Do not mint** a new `formula_templates` row or blueprint from band n, flag rates, or decade share.
- **Naming is human:** measurements propose; NOTES chooses among keep-one-type / split-with-human-name / characteristics-only.
- Default against new ids (variant dissipation). Do not admit a type by popularity (statistical irrelevance).
- Ubiquitous opening/decision scaffolding does not decide the type; if the low band’s signal is a **rarer** carrier, that is a feature (often easier to localise once named) — still needs a human name and period-aware variants for wording drift.
- No L2 slot ablation in this step. No ES remget for part A.

## Parts

| Part | Needs | Answers |
|------|-------|---------|
| **A — quantitative** | scores already on disk | Band × length, decade share, routing subtype, lexical flags (esp. `gedelibereert_start`) on clean gold + full requeste+ population |
| **B — hand-read** | `resolutions_flat` mounted | Is low-band wording a clipped/short opener, cloud miss, or noise? Stratified sample low vs high |

## You do

```bash
uv run pytest tests/test_requeste_low_band_profile.py -q

# Part A (no resolutions_flat / no ES)
uv run python scripts/run_requeste_low_band_profile.py --fixture-only
uv run python scripts/run_requeste_low_band_profile.py

uv run python -m data_io.check
```

Part B (when flat is mounted): draw a stratified low/high text sample from clean-gold ids in `formula_retrieval_arms_scores`, read side-by-side, fill NOTES. Prefer advising a small notebook or one-off script over a heavy harvest.

Fill / judge: [`docs/proofs/multi-template-registry/STEPT1r-requeste-low-band.md`](../../docs/proofs/multi-template-registry/STEPT1r-requeste-low-band.md).

## Design locks

| Piece | Rule |
|-------|------|
| Universe A | `formula_retrieval_arms_scores` `type=requeste` `role=gold` + join `requeste_subtype_scores` by id |
| Bands | low if `dag_frozen_score` ≤ 4.6; high if ≥ 8.0; else mid (STEPT1q NOTES cliff) |
| Part B sample | Stratified by band (± decade); truncated snippets; human read |
| Call options | `keep_one_type_accept_fp_tradeoff` / `split_short_form_subtype_after_human_name` / `characteristics_only_no_new_id` |

## Eval gates (NOTES)

1. Does length + decade share reproduce STEPT1q’s short-form / 1760s peak story on disk?
2. Do routing subtype or `gedelibereert_start` separate bands, or is the split orthogonal to STEPT1l cuts?
3. Part B: readable short-form opener vs same opener with weak align vs junk?
4. **Call:** one of the three options above — human name required if split.

## Do not

- Promote a new blueprint or `template_id` from metrics alone
- Run Doc B L2 reduction here (later step after the call)
- Treat ubiquitous decision markers as the type-deciding formula without characterisation
- Invent 17c wording; period drift → variants / period keys, not guessed synonyms

## After this step

Mark STEPT1r in `PLAN.md`. Next follows the NOTES call (split → named subtype + per-band cuts; keep → accept FP tradeoff and proceed to L2 or another family). Clear the chat before the next step.
