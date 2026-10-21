# STEPT1o — Missive blueprint promotion (missive joins the accepted core)

**Goal:** Wire `missive_ontfangen` (STEPT1n, frozen cut) into the shared accepted-type presence/composition machinery alongside `appointment_installation` / `advies_geleesen` / `requeste_geleesen`, then re-run the STEPT1i/STEPT1m composition-unknown measurement with four core types on the same comparison year (1780). If the proto-blueprint catalogue stays low-noise, promote `missive_ontfangen`'s `formula_templates` row to `role: "blueprint"`.
**Done when:** `ACCEPTED_TYPE_IDS` imports `missive_ontfangen`; `formula_type_presence.py` scores it; composition-unknown re-run on `POC_YEAR` (1780) produces a 4-core proto-blueprint table + undecided-mass delta vs the STEPT1m 3-core baseline (empty 0.140); registry row updated with provenance; `data_io.check` clean; `PLAN.md` + milestone doc updated.

**Prerequisite:** STEPT1n done (`formula_type_missive_metrics` on disk, cut frozen).

## Touch points (same scope as STEPT1m — mechanical constant add only)

| Module | Add |
|--------|-----|
| `formulation/composition_unknown.py` | `+ MISSIVE_ID` in `ACCEPTED_TYPE_IDS` (done inline with STEPT1n per explicit user direction to run both in one session) |
| `formulation/formula_type_presence.py` | `fit_missive_presence_model` / `load_frozen_missive_cut` / `score_fn == "missive"` branch (done) |
| `scripts/run_formula_type_presence.py` | `--no-missive` / `--missive-cut` flags, missive in default model build + provenance parents (done) |

Per STEPT1m precedent, the five downstream modules (`formula_type_order.py`, `formula_type_position.py`, `residual_structure.py`, `formula_type_composition_graph.py`, `unknown_likeliness.py`) stay untouched — each encodes its own closed step's design call and re-wiring them is a separate follow-up decision, not mechanical.

## You do

```bash
uv run pytest tests/test_composition_unknown.py tests/test_formula_type_composition_graph.py tests/test_formula_type_presence.py -q

uv run python scripts/run_formula_type_presence.py --year 1780
uv run python scripts/run_composition_unknown.py --year 1780

uv run python -m data_io.check
```

Fill / judge: `docs/proofs/multi-template-registry/STEPT1o-missive-blueprint-promotion.md` (create).

## Eval gates (NOTES)

1. Does adding missive meaningfully shrink undecided/empty mass vs the STEPT1m 3-core baseline (0.140)?
2. Does a new accepted_core (missive alone, or combined with appointment/advies/requeste) clear `min_support=5`?
3. Does dominant_bag_frac stay low-noise on missive-bearing cores (comparable to the existing 0.71–0.98 range)?
4. **Call:** promote `missive_ontfangen` to blueprint status only if gate 3 holds; otherwise characterise its core before promoting.

## Do not

- Widen scope to full corpus in this step — keep the 1780 comparison-year lock.
- Mint new `template_id`s from fingerprint clusters.
- Re-wire the five downstream modules (order/position/residual/graph-zone/cover-set) — separate follow-up.

## After this step

Mark STEPT1o in `PLAN.md` and `plans/milestones/T1-unknown-first.md`. Add a `docs/DECISIONS.md` entry. Clear the chat before the next step.
