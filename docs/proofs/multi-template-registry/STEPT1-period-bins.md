# STEPT1-period — Eval NOTES

**Status:** `--family all` run done (appointment + ontfangen_start + requeste_start).

## Gates summary

| Family | Self diags ≥ 0.5 | Recalibrate signals | Borrow | Notes |
|--------|------------------|---------------------|--------|-------|
| appointment_installation | **PASS** 0.86–0.95 | 0 (soft slip 1750→1725 = 0.61) | none | gold pool |
| ontfangen_start | **PASS** 0.93–1.00 | 0 | none | cap 200/bin; stable cross-bin |
| requeste_start | **PASS** early 0.99–1.00 | 0 | late bins failed (see below) | search pool collapses after ~1750 |

## requeste_start — late thin pools (re-run after previous-borrow)

| Bin | n | Model | recall_on_sparse / diag |
|-----|--:|-------|-------------------------|
| 1700–24 | 200 | self | diag **0.995** |
| 1725–49 | 200 | self | diag **0.990** |
| 1750–74 | **2** | borrowed←1725–49 | **1.0** on sparse |
| 1775–99 | **24** | borrowed←1725–49 | **1.0** on sparse |

**PASS** previous-period borrow: both sparse bins covered; `recall_on_sparse=1.0` under donor cut. That means the *few* late hits still match the early cloud — the problem is **candidate harvest** (seed almost silent late), not that late wording rejects the early model.

Docs still show `request_start` ~0.26–0.34 corpus-wide vs our thin seed pool. **Next:** widen seeds (`request_start` / other surfaces), not more borrow logic.

## formula_documents_compare (same caveats)

- **Appointment:** model on selected vs docs on full corpus → large +Δ (expected).  
- **ontfangen:** docs rate ~0.49–0.64; model diag on seeded pool ~0.93–1.0; Δ ~+0.3–0.5.  
- **requeste:** docs `request_start` ≫ `requeste_start`; model only early bins.

## Next

Widen `requeste_start` candidate seeds (e.g. `request_start` surfaces / looser patterns) so late bins can self-fit; borrow already proves the few late hits match the 1725–49 cloud.
