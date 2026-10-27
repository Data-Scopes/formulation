# STEPT1ag — Residual triviality sweep (NOTES)

**Status:** implemented (code); full run on disk candidates = user.  
**Guide:** [`plans/steps/STEPT1ag-residual-triviality-sweep.md`](../../../plans/steps/STEPT1ag-residual-triviality-sweep.md)

```bash
uv run pytest tests/test_formula_family_residual_sweep.py -q
uv run python scripts/run_formula_family_residual_sweep.py --fixture-only
uv run python scripts/run_formula_family_residual_sweep.py
```

## Deliverables

| Logical name | Role |
|--------------|------|
| `formula_family_residual_metrics` | Counts + trivial_reason_hist |
| `formula_family_residual_trivial` | Parked trivia (not skimmed) |
| `formula_family_residual_review` | Capped absorb/truncate proposals |

## Gates (fixture)

| Gate | Result |
|------|--------|
| Trivial parks tok/short-tail | **PASS** (unit) |
| Review capped; overflow parked | **PASS** (unit) |
| `freq_below_min` parks cue’d hapax | **PASS** (unit) |
| No auto-merge / `human_keep` null | **PASS** |

## Freq floor (fix)

Earlier dry-run only **sorted** by freq and **count-capped**; no hard floor — so `fam_1186` (`in handen van hunnen Lieutenant`, freq=1) reached review. Fixed: `min_review_freq=500` (= Pass A `DEFAULT_MIN_FREQ`); below → `freq_below_min`.

## Dry-run on disk candidates (pre–af re-fold, 2026-10-26)

input 1265 / thin 976 → **trivial 916** / **review 60** (overflow 23). Dominant trivial reasons: `tok_hinge_no_cue` 645, `token_len_le3` 248. Re-run after floor fix before skim.

## Next

```bash
uv run python scripts/run_formula_family_fold.py --overlap   # STEPT1af
uv run python scripts/run_formula_family_residual_sweep.py   # write trivial+review
```

Skim **`formula_family_residual_review` only** — not the trivial park.
