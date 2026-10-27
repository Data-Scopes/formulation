# STEPT1ad — Overlap-cue fold prove (NOTES)

**Status:** **accepted** (2026-10-26) — fixture prove 10/10; fold wire = STEPT1ae.  
**Guide:** [`plans/steps/STEPT1ad-overlap-cue-fold.md`](../../../plans/steps/STEPT1ad-overlap-cue-fold.md)  
**Decision:** [`docs/DECISIONS.md`](../../DECISIONS.md) 2026-10-26 *Prove-first overlap-cue fold*.

```bash
uv run pytest tests/test_overlap_cue_prove.py -q
uv run python scripts/prove_overlap_cue_fold.py --fixture-only
# optional stream smoke (local.toml path):
# uv run python scripts/prove_overlap_cue_fold.py --overlap
```

## Intent

Separate prove module — **not** wired into [`formula_family_fold.py`](../../../formulation/formula_family_fold.py) yet. Production wire-up = STEPT1ae after NOTES accept.

## Scenarios (fixture run 2026-10-26)

| Scenario | Gate | Result |
|----------|------|--------|
| `overlap_chain` | 4 gedelibereert windows + edges → 1 family, cue=`waar_op` | **PASS** |
| `no_edge_split` | same windows, no edges → still split | **PASS** |
| `overlap_freq_vs_presence` | merge weight ≠ corpus hit fields | **PASS** |
| `bottom_up_cues` | seeds present; induced hub (`voorgaande_deliberatie…`); dominant `waar_op` | **PASS** |
| `place_bands` | cross-place similars stay 2 families | **PASS** |
| `paradigm_slots` | `een brief`+`twee brieven` merge; missive apart | **PASS** |
| `straddle_refuse` | advertentie\|waar op not re-glued | **PASS** |
| `cardinal_corpus_test` | shortlist capped; zero-hit→review; no short tails | **PASS** |
| `no_auto_mint` | `human_role` always null | **PASS** |
| `split_f1a_f1b` | `houdende dat` not cardinal; `part_of` linked | **PASS** (best-effort) |

## F1b note

Short-tail linking is **best-effort**. Do not FAIL the prove on low F1b recall. Lookahead from F1a in resolution text is **parked** (post wire-up).

## Next

**STEPT1ae** — wire prove helpers into `formula_family_fold` (`--overlap`).
