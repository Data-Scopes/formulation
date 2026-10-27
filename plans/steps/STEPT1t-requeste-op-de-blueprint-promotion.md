# STEPT1t — Short-requeste blueprint promotion (`requeste_op_de` joins the accepted core)

**Goal:** Wire `requeste_op_de` (STEPT1s, frozen cut 4.5) into the shared accepted-type presence/composition machinery alongside `appointment_installation` / `advies_geleesen` / `requeste_geleesen` / `missive_ontfangen`, then re-run the STEPT1i composition-unknown measurement with five core types on the same comparison year (1780). If the proto-blueprint catalogue stays low-noise, promote `requeste_op_de`'s `formula_templates` row to `role: "blueprint"`.
**Done when:** `ACCEPTED_TYPE_IDS` imports `requeste_op_de`; `formula_type_presence.py` scores it; composition-unknown re-run on `POC_YEAR` (1780) produces a 5-core proto-blueprint table + undecided-mass delta vs the STEPT1o 4-core baseline (empty 0.122); registry row updated with provenance; `data_io.check` clean; `PLAN.md` + milestone doc updated.

**Prerequisite:** STEPT1s done (`formula_type_requeste_op_de_metrics` on disk, cut frozen at 4.5). Long sibling `requeste_geleesen` stays in the core unchanged — both openers are distinct accepted types (dual-opener presence bag).

## Touch points (same scope as STEPT1o — mechanical constant add only)

| Module | Add |
|--------|-----|
| `formulation/composition_unknown.py` | `+ REQUESTE_OP_DE_ID` in `ACCEPTED_TYPE_IDS` |
| `formulation/formula_type_presence.py` | `fit_requeste_op_de_presence_model` / `load_frozen_requeste_op_de_cut` / `score_fn == "requeste_op_de"` branch |
| `scripts/run_formula_type_presence.py` | `--no-requeste-op-de` / `--requeste-op-de-cut` flags, short opener in default model build + provenance parents |
| `tests/fixtures/formula_templates.jsonl` | new `requeste_op_de` row, `role: "blueprint"` **only if** gate 3 holds |

Per STEPT1m/o precedent, the five downstream modules (`formula_type_order.py`, `formula_type_position.py`, `residual_structure.py`, `formula_type_composition_graph.py`, `unknown_likeliness.py`) stay untouched — re-wiring them is a separate follow-up, not mechanical.

## You do

```bash
uv run pytest tests/test_composition_unknown.py tests/test_formula_type_presence.py tests/test_formula_templates.py -q

uv run python scripts/run_formula_type_presence.py --year 1780
uv run python scripts/run_composition_unknown.py --year 1780

uv run python -m data_io.check
```

Fill / judge: `docs/proofs/multi-template-registry/STEPT1t-requeste-op-de-blueprint-promotion.md` (create).

## Eval gates (NOTES)

1. Does adding `requeste_op_de` meaningfully shrink undecided/empty mass vs the STEPT1o 4-core baseline (0.122)?
2. Does a new accepted_core (short opener alone, or combined with long requeste / other openers) clear `min_support=5`?
3. Does dominant_bag_frac stay low-noise on short-opener-bearing cores (comparable to the existing 0.71–1.0 range)?
4. **Call:** promote `requeste_op_de` to blueprint status only if gate 3 holds; otherwise characterise its core before promoting.

## Do not

- Widen scope to full corpus — keep the 1780 comparison-year lock.
- Mint new `template_id`s from fingerprint clusters.
- Fold long and short requeste into one id — they stay siblings.
- Re-wire the five downstream modules — separate follow-up.
- Open the letter/missive short-opener parallel (parked).

## After this step

Mark STEPT1t in `PLAN.md` and `plans/milestones/T1-unknown-first.md`. Add a `docs/DECISIONS.md` entry. Clear the chat before the next step.
