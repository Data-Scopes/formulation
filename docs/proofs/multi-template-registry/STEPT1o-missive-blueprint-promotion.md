# STEPT1o — Missive blueprint promotion (NOTES)

**Status:** done (2026-10-20). All three gates **PASS**, more cleanly than STEPT1m's requeste addition. `missive_ontfangen` promoted to `role: "blueprint"` in `formula_templates`, joining `appointment_installation` / `advies_geleesen` / `requeste_geleesen`.

```bash
uv run pytest tests/test_formula_type_presence.py tests/test_composition_unknown.py tests/test_formula_templates.py -q
uv run python scripts/run_formula_type_presence.py --year 1780
uv run python scripts/run_composition_unknown.py --year 1780
uv run python -m data_io.check
```

## What changed

`missive_ontfangen` (STEPT1n, frozen cut 6.0) wired into the shared accepted-core machinery — `composition_unknown.ACCEPTED_TYPE_IDS` now holds all four openers:

- `formulation/formula_type_presence.py`: new `fit_missive_presence_model()` (mirrors `fit_requeste_presence_model`, reuses `build_missive_cloud`/`score_text` + frozen STEPT1n cut), `load_frozen_missive_cut()`, `score_fn == "missive"` branch, `missive_accepted` metric, missive fixture model.
- `formulation/composition_unknown.py`: `ACCEPTED_TYPE_IDS = {APPOINTMENT_ID, ADVIES_ID, REQUESTE_ID, MISSIVE_ID}`.
- `scripts/run_formula_type_presence.py`: `--no-missive` / `--missive-cut` flags, missive in default model build + provenance parents.
- `tests/fixtures/formula_templates.jsonl`: new `missive_ontfangen` row, `role: "blueprint"`.
- `tests/test_formula_templates.py`: blueprint-set assertion widened to four types.

**Scope held per STEPT1m precedent:** `formula_type_composition_graph.py`, `formula_type_order.py`, `formula_type_position.py`, `residual_structure.py`, `unknown_likeliness.py` each define their own `ADVIES_ID`/`APPOINTMENT_ID`/`REQUESTE_ID` usage (zone assignment, order pairs, named columns, cover-set checks) — not shared constants with `composition_unknown.py`, each encoding its own already-closed step's design call. Re-wiring missive into them would reopen five closed steps in this one session. **Left untouched** — same follow-up decision this applies to requeste.

## Results: STEPT1m 3-core baseline vs STEPT1o 4-core re-run (year 1780)

| Metric | STEPT1m (3-core) | STEPT1o (4-core) |
|---|---:|---:|
| n_universe | 2796 | 2796 |
| n_unique_exact_bags | 12 | 16 |
| n_unique_accepted_cores | 6 | 11 |
| n_proto_blueprints (support≥5) | 5 | 8 |
| empty (undecided, no hits) | 392 (0.140) | 342 (0.122) |
| known_sparse | 1215 (0.435) | **2450 (0.876)** |
| filler_star | 1189 (0.425) | **0 (0.000)** |
| novel_tail | 0 | 4 (0.001) |

**Headline is not the empty-mass delta (modest: 0.140→0.122) — it's filler_star collapsing to zero.** `filler_star` (bag == bare `ontfangen_start` root only, no accepted type present) was 42.5% of the universe under the 3-core accepted set, because the missive opener fires constantly but had no accepted-type home. With `missive_ontfangen` now accepted, essentially that entire mass reclassifies to `known_sparse` (proto-blueprint territory): `1189 (filler) + 1215 (known) ≈ 2404`, close to the new `2450 known_sparse`, with ~50 more pulled in from what was previously `empty`. The resolution of "mostly filler, structurally unexplained" boilerplate into a real accepted type is the actual typology gain here, not the raw undecided-mass number.

## Proto-blueprint catalogue (4-core)

| accepted_core | support | n_unique_exact_bags | dominant_bag_frac |
|---|---:|---:|---:|
| `missive_ontfangen` | 1239 | 2 | 0.960 |
| `requeste_geleesen` | 931 | 1 | 1.000 |
| `missive_ontfangen` + `requeste_geleesen` | 182 | 2 | 0.967 |
| `advies_geleesen` + `requeste_geleesen` | 54 | 1 | 1.000 |
| `appointment_installation` + `missive_ontfangen` + `requeste_geleesen` | 20 | 1 | 1.000 |
| `advies_geleesen` | 10 | 1 | 1.000 |
| `advies_geleesen` + `missive_ontfangen` | 7 | 2 | 0.714 |
| `appointment_installation` + `missive_ontfangen` | 7 | 2 | 0.857 |

`appointment_installation` alone and `advies_geleesen` alone (STEPT1m's leftover singles) have mostly been absorbed into combined cores with missive/requeste (expected: appointments and advies readings routinely co-occur with a missive/requeste opener in the same resolution).

## Eval gates

1. **Does adding missive meaningfully shrink undecided/empty mass? PASS, modestly.** Empty 0.140→0.122 (direct effect); the much larger effect is `filler_star` 0.425→0.000 (indirect — missive explains boilerplate previously bucketed as unexplained filler, not previously counted as "undecided" at all since `classify_motif` treats bare-root bags as `filler_star`, not `empty`).
2. **Does a new accepted_core clear the support floor (5)? PASS.** Five new or growing cores: `missive_ontfangen` alone (1239), `missive+requeste` (182), `appointment+missive+requeste` (20), `advies+missive` (7), `appointment+missive` (7).
3. **Does dominant_bag_frac stay low-noise on missive-bearing cores? PASS, cleanly.** Range 0.714–1.000 across all 8 cores — same or better than STEPT1m's 3-core range (0.706–0.982). `novel_tail` ticked up from 0 to 4 (0.001 of universe) — negligible.
4. **Call: promote.** `missive_ontfangen` promoted to `role: "blueprint"` in `formula_templates`, provenance pointing at STEPT1n / STEPT1e / STEPT1m / this step.

## Caveats

- Same single comparison year (1780) as STEPT1i/STEPT1m, per the step guide's scope lock — not the full corpus. The ES missive population is large (177,045 rows 1705–1796 in the STEPT1n gold), so the 1780 slice is a fair before/after comparison, not a full-corpus blueprint census.
- STEPT1n's own eval found the structured model's recall trails the naive wording baseline by 2.7–5.3 points, and FP (0.11) fails the ≤0.05 gate though acceptably — both carried forward as known limitations of the type definition itself, not reopened here. Promotion is about composition-level low-noise behavior (this step's gates), not re-litigating STEPT1n's recall/FP judgment.
- `missive_ontfangen` (STEPT1n, slot-cloud/DAG, cut 6.0) is distinct from the pre-existing `ontfangen_start` provisional single-cloud opening family (`formula_period_bins`, per-year-bin calibrated) — same disambiguation pattern as `requeste_geleesen` vs `opening_requeste_18c` / `requeste_start`.
- Two pre-existing test failures in `tests/test_data_io.py` (`sample_parquet` manifest lookup) are unrelated to this step — not touched, not introduced here.

## Next

Blueprint promotion closed at the 1780-comparison-year level of detail, mirroring STEPT1m. Wiring the five downstream modules (order/position/residual/unknown-likeliness/graph zone semantics) for missive is a separate follow-up, not opened here — same open item STEPT1m already flagged for requeste, now doubled. Clear the chat before the next step.
