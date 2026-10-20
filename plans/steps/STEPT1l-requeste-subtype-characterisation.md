# STEPT1l — Requeste+ routing subtype characterisation

**Goal:** Characterise **provisional routing subtypes** under requeste+ — referred vs granted-direct vs routing-unclear — as a STEPT1f-style structural profile. Routing flags stay evidence; subtypes are characteristics of kind `rekest`, not new accepted formula types. Answers the "looks answerable now" lever named in [`docs/template-design-questions.md`](../../docs/template-design-questions.md) (structural outcome/routing, not requester identity — that lever stays blocked, ES fields null corpus-wide).
**Done when:** provenanced metrics (+ per-id scores) written; NOTES filled with side-by-side subtype tables + call; `data_io.check` clean; `PLAN.md` updated.

**Prerequisite:** STEPT1k done; `formula_type_requeste_scores` on disk (role=="gold" rows = full ES rekest 18c population with model `pred`).

## You do

```bash
uv run pytest tests/test_requeste_subtype_profile.py -q

# Fixture smoke (no parquet / no formula_documents)
uv run python scripts/run_requeste_subtype_profile.py --fixture-only

# Full 18c characterisation (cheap: reuse STEPT1k scores + flag join + word counts)
uv run python scripts/run_requeste_subtype_profile.py

# Optional single-year slice (comparison only)
uv run python scripts/run_requeste_subtype_profile.py --year 1780

uv run python -m data_io.check
```

Fill / judge: [`docs/proofs/multi-template-registry/STEPT1l-requeste-subtype-characterisation.md`](../../docs/proofs/multi-template-registry/STEPT1l-requeste-subtype-characterisation.md).

## Design locks

| Piece | Rule |
|-------|------|
| Universe | `requeste_plus` = `formula_type_requeste_scores` rows with `role == "gold"` **and** `pred` True (model-detected opener on ES rekest gold) — not raw ES label alone |
| Recall-miss | `role == "gold"` & `pred` False (ES rekest the model didn't detect) — reported as a count only, **not characterised** (opener-detection miss, not a requeste+ subtype) |
| Kind filter | Trivial — gold rows are ES `proposition_type == rekest` by construction (STEPT1k fetch); no leakage axis needed |
| Subtypes | `referred` = `handen` or `in handen` present; `granted_direct` = `goedgevonden` present and not referred; `routing_unclear` = outcome joined, neither flag present — already-named routing markers, not new classes |
| Characteristics | Length (`resolutions_flat` word count), flag rates + top combos, `advies` co-occurrence rate per subtype |
| Flags | Boilerplate surfaces describing routing — **not** an archival-outcome typology (STEPT1e1 stays parked) |
| Requeste+ / subtypes | Provisional characteristics cuts — **not** accepted formula types |
| session_date join | `formula_type_requeste_scores` has no `session_date`; derive from `resolutions_flat.date` by `id` before `join_outcome_flags` (unlike STEPT1e/STEPT1f, which already carried it from ES metadata) |

## Measurements (required)

| Metric | Where |
|--------|-------|
| `n_requeste_plus` / `n_recall_miss` / `outcome_join_coverage` | metrics |
| Per subtype: n, frac_of_requeste_plus | metrics.subtypes[] |
| Per subtype: n_words median / q1 / q3 | subtypes[].length |
| Per subtype: flag rates + top combos | subtypes[].flags_* |
| Per subtype: `advies` co-occurrence rate | subtypes[].flags.flag_rates.advies |
| Side-by-side contrast (length Δ referred vs granted_direct, advies rate by subtype) | metrics.contrast |

## Eval gates (NOTES)

1. Do `referred` vs `granted_direct` **separate structurally** (length and/or flag signature, esp. `advies` co-occurrence)?
2. Is `routing_unclear` a small residual (clean two-way split mostly holds) or a large third mass (routing isn't binary)?
3. Call: stop / characterise a further routing axis only if NOTES names a kind-support probe / no new A from routing density alone.

## Do not

- Accept `referred` / `granted_direct` / `routing_unclear` as formula types
- Attempt requester-identity sub-typology (civilian / institution / ambassador) — ES `proposer`/`proposer_role`/`proposition_organisation` are null corpus-wide (see template-design-questions.md); that lever needs a separate NER-frequency probe, out of scope here
- Implement STEPT1e1 flag sieve (further bucketing by discourse flags)
- Pull full resolution text from ES / re-run STEPT1k ES fetch (reuse `formula_type_requeste_scores` + `rekest_es_gold`)
- Classify flags as archival outcomes / "what was decided"
- Rescore the requeste opener or recalibrate its operating cut

## After this step

Mark STEPT1l in `PLAN.md`. Follow NOTES call. Clear the chat before the next step.
