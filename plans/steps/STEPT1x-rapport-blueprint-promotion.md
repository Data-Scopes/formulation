# STEPT1x — Rapport blueprint promotion (`rapport_gehoord` joins the accepted core)

**Goal:** Wire `rapport_gehoord` (STEPT1w, frozen cut 7.5) into the shared accepted-type presence/composition machinery alongside the five current openers, then re-run the STEPT1i composition-unknown measurement with six core types on the same comparison year (1780). If the proto-blueprint catalogue stays low-noise, promote `rapport_gehoord`'s `formula_templates` row to `role: "blueprint"`.
**Done when:** `ACCEPTED_TYPE_IDS` imports `rapport_gehoord`; `formula_type_presence.py` scores it; composition-unknown re-run on `POC_YEAR` (1780) produces a 6-core proto-blueprint table + undecided-mass delta vs the STEPT1t 5-core baseline (empty 0.122); registry row updated with provenance; `data_io.check` clean; `PLAN.md` + milestone doc updated.

**Prerequisite:** STEPT1w done (`formula_type_rapport_metrics` on disk, cut frozen at 7.5). STEPT1u named this as a residual empty-band skeleton — empty shrink is the interesting gate this time (unlike STEPT1t, where empty stayed flat).

## Touch points (same scope as STEPT1t — mechanical constant add only)

| Module | Add |
|--------|-----|
| `formulation/composition_unknown.py` | `+ RAPPORT_ID` in `ACCEPTED_TYPE_IDS` |
| `formulation/formula_type_presence.py` | `fit_rapport_presence_model` / `load_frozen_rapport_cut` / `score_fn == "rapport"` branch |
| `scripts/run_formula_type_presence.py` | `--no-rapport` / `--rapport-cut` flags, rapport in default model build + provenance parents |
| `tests/fixtures/formula_templates.jsonl` | new `rapport_gehoord` row, `role: "blueprint"` **only if** gate 3 holds |

Per STEPT1m/o/t precedent, the five downstream modules (`formula_type_order.py`, `formula_type_position.py`, `residual_structure.py`, `formula_type_composition_graph.py`, `unknown_likeliness.py`) stay untouched — re-wiring them is a separate follow-up, not mechanical.

## You do

```bash
uv run pytest tests/test_composition_unknown.py tests/test_formula_type_presence.py tests/test_formula_templates.py -q

uv run python scripts/run_formula_type_presence.py --year 1780
uv run python scripts/run_composition_unknown.py --year 1780

uv run python -m data_io.check
```

Fill / judge: `docs/proofs/multi-template-registry/STEPT1x-rapport-blueprint-promotion.md` (create).

## Eval gates (NOTES)

1. Does adding `rapport_gehoord` meaningfully shrink undecided/empty mass vs the STEPT1t 5-core baseline (0.122)? (STEPT1u residual suggests yes.)
2. Does a new accepted_core (rapport alone, or combined with other openers) clear `min_support=5`?
3. Does dominant_bag_frac stay low-noise on rapport-bearing cores (comparable to the existing 0.71–1.0 range)?
4. **Call:** promote `rapport_gehoord` to blueprint status only if gate 3 holds; otherwise characterise its core before promoting.

## Do not

- Widen scope to full corpus — keep the 1780 comparison-year lock.
- Mint new `template_id`s from fingerprint clusters.
- Open voordracht / Doc B L3 / letter / leave-k in this step.
- Re-wire the five downstream modules — separate follow-up.

## After this step

Mark STEPT1x in `PLAN.md` and `plans/milestones/T1-unknown-first.md`. Add a `docs/DECISIONS.md` entry. Clear the chat before the next step.
