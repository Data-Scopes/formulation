# STEPT1m — Blueprint promotion (NOTES)

**Status:** done (2026-10-20). All three gates **PASS**; `appointment_installation` / `advies_geleesen` / `requeste_geleesen` promoted to `role: "blueprint"` in `formula_templates`.

```bash
uv run pytest tests/test_formula_type_presence.py tests/test_composition_unknown.py tests/test_formula_templates.py -q
uv run python scripts/run_formula_type_presence.py --year 1780
uv run python scripts/run_composition_unknown.py --year 1780
uv run python -m data_io.check
```

## What changed

`requeste_geleesen` (STEPT1k, frozen cut 4.5) was accepted as a formula type but never wired into the shared accepted-core machinery — `composition_unknown.ACCEPTED_TYPE_IDS` only held `{appointment_installation, advies_geleesen}`. Wired in:

- `formulation/formula_type_presence.py`: new `fit_requeste_presence_model()` (mirrors `fit_advies_presence_model`, reuses `build_requeste_cloud`/`score_text` + frozen STEPT1k cut), `load_frozen_requeste_cut()`, `score_fn == "requeste"` branch, `requeste_accepted` metric, requeste fixture model.
- `formulation/composition_unknown.py`: `ACCEPTED_TYPE_IDS = {APPOINTMENT_ID, ADVIES_ID, REQUESTE_ID}`.
- `scripts/run_formula_type_presence.py`: `--no-requeste` / `--requeste-cut` flags, requeste in default model build + provenance parents.
- `formulation/formula_templates.py`: `ROLES` gains `"blueprint"`.
- `tests/fixtures/formula_templates.jsonl`: three new rows (`appointment_installation`, `advies_geleesen`, `requeste_geleesen`), `role: "blueprint"`.

**Scope held per the step guide:** `formula_type_composition_graph.py`, `formula_type_order.py`, `formula_type_position.py`, `residual_structure.py`, `unknown_likeliness.py` each define their own `ADVIES_ID`/`APPOINTMENT_ID` usage (zone assignment, order pairs, named columns, cover-set checks) — these are not shared constants with `composition_unknown.py` and each encodes its own already-closed step's design call (T1c zones, T1d order/graph, T1g residual, T1h cover-set). Re-wiring requeste into them would reopen five closed steps in this one session. **Left untouched** — flagged as a separate follow-up decision per type, not mechanical.

## Results: STEPT1i 2-core baseline vs STEPT1m 3-core re-run (year 1780)

| Metric | STEPT1i (2-core) | STEPT1m (3-core) |
|---|---:|---:|
| n_universe | 2796 | 2796 |
| n_unique_exact_bags | 6 | 12 |
| n_unique_accepted_cores | 3 | 6 |
| n_proto_blueprints (support≥5) | 2 | 5 |
| empty (undecided, no hits) | 1329 (0.475) | 392 (0.140) |
| known_sparse | 102 (0.036) | 1215 (0.435) |
| filler_star | 1365 (0.488) | 1189 (0.425) |
| novel_tail | 0 | 0 |

## Proto-blueprint catalogue (3-core)

| accepted_core | support | n_unique_exact_bags | dominant_bag_frac |
|---|---:|---:|---:|
| `requeste_geleesen` | 1113 | 2 | 0.842 |
| `advies_geleesen` + `requeste_geleesen` | 57 | 2 | 0.982 |
| `appointment_installation` + `requeste_geleesen` | 21 | 2 | 0.952 |
| `advies_geleesen` | 17 | 2 | 0.706 |
| `appointment_installation` | 7 | 2 | 0.857 |

Sanity check: `advies_geleesen` alone (17) + `advies+requeste` (57) = 74 = STEPT1i's original `advies_geleesen` core support. `appointment_installation` alone (7) + `appointment+requeste` (21) = 28 = STEPT1i's original `appointment_installation` core support. The 3-core split exactly partitions the 2-core baseline — no appointment∩advies core clears the floor either before or after (unchanged from STEPT1i).

## Eval gates

1. **Does adding requeste meaningfully shrink undecided/empty mass? PASS.** Empty drops from 0.475 to 0.140 (937 of 1329 previously-empty ids now carry a requeste hit) — consistent with STEPT1j's finding that the empty band is rekest-headed.
2. **Does a new accepted_core clear the support floor (5)? PASS.** Three new cores: `requeste_geleesen` alone (1113), `advies+requeste` (57), `appointment+requeste` (21).
3. **Does dominant_bag_frac stay low-noise on requeste-bearing cores? PASS.** All three new cores have exactly 2 unique exact bags (same structure as every existing core — present with vs. without the bare `ontfangen_start` filler root), dominant_bag_frac 0.84–0.98, in the same range as the STEPT1i baseline (0.71–0.93). No bag proliferation.
4. **Call: promote.** All three opener types (`appointment_installation`, `advies_geleesen`, `requeste_geleesen`) promoted to `role: "blueprint"` in `formula_templates`, provenance pointing at STEPT1a / STEPT1a2 / STEPT1k / STEPT1i / this step.

## Caveats

- This re-run used the same single comparison year (1780) as STEPT1i, per the step guide's scope lock — not the full corpus. The corpus-wide requeste+ population (66,657 per STEPT1l) is much larger; the 1780 slice is a fair before/after comparison, not a full-corpus blueprint census.
- Routing subtypes (`referred` / `granted_direct` / `routing_unclear`, STEPT1l) are **not** promoted and are not new `template_id`s — they stay characteristics of the `requeste_geleesen` blueprint, not separate catalogue rows.
- `requeste_geleesen` (STEPT1k, slot-cloud/DAG, cut 4.5) is distinct from the pre-existing `opening_requeste_18c` registry row (STEPS1b boundary-span framing, cosine cut 0.40) and the provisional `requeste_start` opening family (STEPT1b, per-year-bin calibrated single-cloud) — three different scorers over related surface language, now disambiguated by role (`blueprint` vs `framing` vs `doc_flag`) in the registry.
- Two pre-existing test failures in `tests/test_data_io.py` (`sample_parquet` manifest lookup) are unrelated to this step — not touched, not introduced here.

## Next

Blueprint promotion closed at the 1780-comparison-year level of detail. Wiring the five downstream modules (order/position/residual/unknown-likeliness/graph zone semantics) for requeste is a separate follow-up, not opened here — each requires its own zone/order/cover-set judgment call, not a mechanical constant add. Clear the chat before the next step.
