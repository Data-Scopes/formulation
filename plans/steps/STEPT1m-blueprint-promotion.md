# STEPT1m — Blueprint promotion (requeste joins the accepted core)

**Goal:** Wire `requeste_geleesen` (STEPT1k, frozen cut 4.5) into the shared accepted-type presence/composition machinery that currently only knows `appointment_installation` + `advies_geleesen`, then re-run the STEPT1i composition-unknown measurement with three core types on the same comparison year. If the proto-blueprint catalogue stays low-noise, promote the three opener types' `formula_templates` rows to settled/blueprint status. Only the **opener** (`requeste_geleesen`) is in scope — STEPT1l's routing subtypes (`referred` / `granted_direct` / `routing_unclear`) stay characteristics, never enter the accepted core.
**Done when:** `ACCEPTED_TYPE_IDS` and the touch-point modules import `requeste_geleesen` alongside the other two; composition-unknown re-run on the STEPT1i comparison year (`POC_YEAR`, 1780) produces a 3-core proto-blueprint table + undecided-mass delta vs the STEPT1i 2-core baseline; registry rows updated with provenance; `data_io.check` clean; `PLAN.md` + milestone doc updated.

**Prerequisite:** STEPT1k + STEPT1l done. `formula_type_requeste_scores` on disk. `requeste_formula_type.py` already exposes `build_requeste_cloud` / `score_text` in the same shape as `advies_formula_type.build_advies_cloud` / `score_text` and `appointment_formula_type.build_appointment_clouds` / `score_text` — this step mirrors existing wiring, it does not design a new scorer.

## Touch points (mirror existing appointment/advies wiring)

| Module | Current import | Add |
|--------|-----------------|-----|
| `formulation/composition_unknown.py` | `ACCEPTED_TYPE_IDS = {APPOINTMENT_ID, ADVIES_ID}` | `+ REQUESTE_ID` |
| `formulation/formula_type_presence.py` | live-scores appointment + advies per year slice | live-score requeste via `build_requeste_cloud`/`score_text` + frozen cut 4.5 |
| `formulation/formula_type_composition_graph.py` | imports ADVIES_ID/APPOINTMENT_ID | add REQUESTE_ID to bag vocabulary |
| `formulation/formula_type_order.py` | same pair | same addition |
| `formulation/formula_type_position.py` | same pair | same addition |
| `formulation/residual_structure.py` | same pair | same addition |
| `formulation/unknown_likeliness.py` | same pair | same addition (cover-set, stays auxiliary per T1-unknown-first.md) |

## You do

```bash
uv run pytest tests/test_composition_unknown.py tests/test_formula_type_composition_graph.py -q

# Re-run composition-unknown on the STEPT1i comparison year with 3 accepted types
uv run python scripts/run_composition_unknown.py --year 1780

uv run python -m data_io.check
```

Fill / judge: `docs/proofs/multi-template-registry/STEPT1m-blueprint-promotion.md` (create).

## Design locks

| Piece | Rule |
|-------|------|
| Accepted core set | Grows from `{appointment_installation, advies_geleesen}` to `+ requeste_geleesen` — opener only |
| Routing subtypes | `referred` / `granted_direct` / `routing_unclear` are **not** promoted, not new `template_id`s, not added to `ACCEPTED_TYPE_IDS` |
| Scoring reuse | Mirror `build_advies_cloud`/`score_text` wiring exactly with `build_requeste_cloud`/`score_text` + frozen cut 4.5 (STEPT1k) — no new threshold calibration here |
| Comparison scope | Re-run on the same year STEPT1i used (`POC_YEAR` = 1780) for an apples-to-apples before/after; do not silently widen to full corpus in this step |
| Registry write | "Promotion" = a settled marker on the three opener rows in `formula_templates` (check existing schema fields — e.g. `threshold_frozen`/`notes` — before inventing a new column), provenance pointing at STEPT1a / STEPT1a2 / STEPT1k |
| Derivative noise | STEPT1i found dominant_bag_frac ~92–93% within advies/appointment cores — promotion holds only if requeste's own core (alone or combined) stays similarly low-noise |

## Measurements (required)

| Metric | Where |
|--------|-------|
| 3-core proto-blueprint table (accepted_core, support, n_unique_exact_bags, dominant_bag_frac) | metrics.proto_blueprints |
| Undecided (empty/novel_tail) mass before (STEPT1i: 0.475 empty) vs after | metrics.undecided_delta |
| Does a requeste-only or combined core clear `min_support=5`? | metrics.new_cores |
| n_unique_accepted_cores before (3) vs after | metrics |

## Eval gates (NOTES)

1. Does adding requeste meaningfully shrink undecided/empty mass, given STEPT1j found empty is rekest-headed?
2. Does a new accepted_core (requeste alone, or combined with appointment/advies) clear the support floor?
3. Within any new requeste-bearing core, does dominant_bag_frac stay high (low derivative noise), matching the existing two cores?
4. **Call:** promote all three opener types to blueprint status only if gate 3 holds; otherwise characterise requeste's core before promoting (do not promote a noisy core).

## Do not

- Reopen STEPT1l's routing subtypes as new accepted types or registry rows
- Recalibrate the requeste opener cut (frozen 4.5 per STEPT1k)
- Widen scope to full corpus in this step — keep the STEPT1i year-for-year comparison
- Mint new `template_id`s from fingerprint clusters (same caution as STEPT1i)
- Touch `formula_type_requeste_scores` / re-run the ES fetch — reuse what STEPT1k/T1l already wrote

## After this step

Mark STEPT1m in `PLAN.md` and `plans/milestones/T1-unknown-first.md`. Add a `docs/DECISIONS.md` entry. Follow NOTES call. Clear the chat before the next step.
