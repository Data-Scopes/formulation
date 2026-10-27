# STEPT1t — Short-requeste blueprint promotion (NOTES)

**Status:** done (2026-10-22). Gates 2–3 **PASS**; gate 1 **FAIL** (empty unchanged — expected). `requeste_op_de` promoted to `role: "blueprint"`.  
**Guide:** [`plans/steps/STEPT1t-requeste-op-de-blueprint-promotion.md`](../../../plans/steps/STEPT1t-requeste-op-de-blueprint-promotion.md)  
**Baseline:** STEPT1o 4-core empty **0.122** on year 1780.

```bash
uv run pytest tests/test_formula_type_presence.py tests/test_composition_unknown.py tests/test_formula_templates.py -q
uv run python scripts/run_formula_type_presence.py --year 1780
uv run python scripts/run_composition_unknown.py --year 1780
uv run python -m data_io.check
```

## What changed

`requeste_op_de` (STEPT1s, frozen cut 4.5) wired into the shared accepted-core machinery — `composition_unknown.ACCEPTED_TYPE_IDS` now holds five openers (long + short requeste siblings):

- `formulation/formula_type_presence.py`: `fit_requeste_op_de_presence_model` / `load_frozen_requeste_op_de_cut` / `score_fn == "requeste_op_de"` / fixture.
- `formulation/composition_unknown.py`: `+ REQUESTE_OP_DE_ID`.
- `scripts/run_formula_type_presence.py`: `--no-requeste-op-de` / `--requeste-op-de-cut`.
- `tests/fixtures/formula_templates.jsonl`: new `requeste_op_de` row, `role: "blueprint"`.

**Scope held:** five downstream modules untouched (same follow-up as STEPT1m/o).

## Results: STEPT1o 4-core vs STEPT1t 5-core (year 1780)

| Metric | STEPT1o (4-core) | STEPT1t (5-core) |
|---|---:|---:|
| n_universe | 2796 | 2796 |
| n_unique_exact_bags | 16 | 19 |
| n_unique_accepted_cores | 11 | 14 |
| n_proto_blueprints (support≥5) | 8 | 11 |
| empty (undecided, no hits) | 342 (0.122) | 342 (0.122) |
| known_sparse | 2450 (0.876) | 2450 (0.876) |
| filler_star | 0 (0.000) | 0 (0.000) |
| novel_tail | 4 (0.001) | 4 (0.001) |

Presence: `requeste_op_de` n_present=**304** (hit_rate 0.1087) at frozen cut 4.5.

**Headline is not empty-mass (unchanged) — it's dual-opener cores.** Every one of the 304 short-opener presents also fires `requeste_geleesen` (188 long+short alone; 109 with missive; 7 with advies). No solo `requeste_op_de` core clears support≥5. That co-fire is the STEPT1q/r cut collision: long model at 4.5 already scores short `Op de Requeste` texts at the three-slot max, so empty could not drop further. The typology gain is naming the dual-opener composition patterns that were previously collapsed into long-only cores (`requeste_geleesen` alone dropped 931→743; `missive+requeste` 182→73).

## Proto-blueprint catalogue (5-core)

| accepted_core | support | n_unique_exact_bags | dominant_bag_frac |
|---|---:|---:|---:|
| `missive_ontfangen` | 1239 | 2 | 0.960 |
| `requeste_geleesen` | 743 | 1 | 1.000 |
| `requeste_geleesen` + `requeste_op_de` | 188 | 1 | 1.000 |
| `missive` + `requeste_geleesen` + `requeste_op_de` | 109 | 1 | 1.000 |
| `missive` + `requeste_geleesen` | 73 | 2 | 0.918 |
| `advies` + `requeste_geleesen` | 47 | 1 | 1.000 |
| `appointment` + `missive` + `requeste_geleesen` | 20 | 1 | 1.000 |
| `advies_geleesen` | 10 | 1 | 1.000 |
| `advies` + `missive` | 7 | 2 | 0.714 |
| `advies` + `requeste_geleesen` + `requeste_op_de` | 7 | 1 | 1.000 |
| `appointment` + `missive` | 7 | 2 | 0.857 |

## Eval gates

1. **Empty/undecided shrink vs 0.122? FAIL (expected).** Empty stays 0.122 — short texts were already covered by long `requeste_geleesen` at cut 4.5.
2. **New accepted_core clears support≥5? PASS.** Three short-bearing cores: long+short (188), missive+long+short (109), advies+long+short (7). No solo short core.
3. **dominant_bag_frac low-noise on short-bearing cores? PASS.** All three are 1.000; full catalogue 0.714–1.000 — same range as STEPT1o.
4. **Call: promote.** Gate 3 holds. Promoted `requeste_op_de` to `role: "blueprint"`. Caveat: dual-opener bags partly reflect long@4.5 absorbing short form; STEPT1s cross-fire (short→long-head) was 0.02, so the types are still distinct under the short model — the asymmetry is the long cut, not the short definition.

## Next

Letter/missive short-opener parallel stays parked. Downstream re-wire of the five closed modules still deferred. Clear the chat before the next step.
