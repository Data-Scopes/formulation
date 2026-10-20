# STEPT1-period — Family × 25y bins + measured recalibration

**Goal:** Independent sub-templates per formula family; fit a model per 25-year bin; **measure** cross-bin recall so gradual drift shows up as recalibration signals (later model weak on earlier bin).  
**Done when:** provenanced `formula_period_bin_metrics` + `formula_period_bin_matrix` written for at least `appointment`; openings optional via `--family all`; NOTES gate filled; `data_io.check` clean.

## Prerequisites

STEPT0 done; STEPT1a appointment scorer available (`formulation/appointment_formula_type.py`).

## You do

```bash
uv run pytest tests/test_formula_period_bins.py -q
uv run python scripts/eval_formula_period_bins.py --fixture-only

# Appointment gold (measured bins + cross matrix)
uv run python scripts/eval_formula_period_bins.py --family appointment

# Independent opening rows (capped candidates per bin; heavier)
uv run python scripts/eval_formula_period_bins.py --family ontfangen_start
uv run python scripts/eval_formula_period_bins.py --family requeste_start
# or
uv run python scripts/eval_formula_period_bins.py --family all

uv run python -m data_io.check
```

## Measurements (required)

| Metric | Where |
|--------|--------|
| `bin_n` / `bins_modeled` / `bins_skipped_low_n` | summary |
| Per-bin `cuts` (p20 in-bin scores) | summary |
| `diagonal_recall` (model_bin = data_bin) | summary |
| Full cross matrix `recall`, `score_mean`, `score_p20` | matrix rows |
| `delta_vs_data_self` (cross recall − that bin’s self recall) | matrix |
| `recalibrate_signal` (adjacent + backward + recall < 0.5) | matrix + summary count |
| `borrow_from_next_period` (sparse bin uses nearest later self-fit model) | summary |
| `recall_on_sparse` under donor cut | summary.borrow rows |
| `formula_documents_compare` (flag rates vs model diagonal per bin) | summary |
| `popularity.weight` from mean diagonal recall | summary |
| `eval_gates.pass_all_self_bins_diagonal` | summary (self-fit only) |

## Eval gates (NOTES after run)

1. Every **self-fit** bin has diagonal recall ≥ 0.5 (else cloud too weak for that bin).  
2. List `recalibrate_signals` — expected if drift is gradual; empty may mean stable or bins too coarse.  
3. Sparse bins (`0 < n < min_bin_n`): must appear under `borrow_from_next_period` with a later donor (or `no_later_donor`); judge `recall_on_sparse`.  
4. Compare families: appointment vs `ontfangen_start` vs `requeste_start` (independent rows).  
5. Popularity weight: near-1 diagonal mean ⇒ low weight (ubiquitous).  
6. Read `formula_documents_compare.per_bin`: model diagonal vs documents flag rate (`welkom`/`sessie`, `ontfangen_start`, `requeste_start`∪`request_start`).

## Do not

- Merge all openings into one template  
- Treat substring candidate harvest as the formula type (seeds only for openings)  
- Skip writing the matrix  
- Mix 17c parsing claims into this 1705–1796 window without a separate gate  

## After this step

Mark STEPT1-period in `PLAN.md`. Next: period-subtype registry rows where recalibrate_signal fires, or STEPT1b presence scoring with popularity weights. Clear the chat before the next step.
