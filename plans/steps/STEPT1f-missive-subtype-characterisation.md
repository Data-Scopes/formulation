# STEPT1f — Missive subtype characterisation (ontfangen+)

**Goal:** Characterise **provisional missive subtypes** under ontfangen+ — info/null receipt vs decisionful residual — as a STEPT0-style structural profile. Formula detectors stay evidence; subtypes are characteristics of kind `missive`, not new accepted formula types.  
**Done when:** provenanced metrics (+ optional per-id scores) written; NOTES filled with side-by-side subtype tables + call; `data_io.check` clean; `PLAN.md` updated.

**Prerequisite:** STEPT1-map done; STEPT1e PASS with `ontfangen_partition_scores` on disk (1780).

## You do

```bash
uv run pytest tests/test_missive_subtype_profile.py -q

# Fixture smoke (no parquet / no formula_documents)
uv run python scripts/run_missive_subtype_profile.py --fixture-only

# Full 1780 characterisation (cheap: reuse STEPT1e scores + flag join + word counts)
uv run python scripts/run_missive_subtype_profile.py --year 1780

uv run python -m data_io.check
```

Fill / judge: [`docs/proofs/multi-template-registry/STEPT1f-missive-subtype-characterisation.md`](../../docs/proofs/multi-template-registry/STEPT1f-missive-subtype-characterisation.md).

## Design locks

| Piece | Rule |
|-------|------|
| Universe | `ontfangen_present` from STEPT1e scores (presence year) |
| Kind filter | Primary tables = ES `proposition_type == missive`; report non-missive ontfangen+ as leakage count only |
| Subtypes | `info_receipt` = `is_l1`; `decisionful_residual` = `residual_not_l1` — already named in STEPT1e, not new classes |
| Characteristics | Length (`resolutions_flat` word count), flag rates + top combos, known-set overlaps (R1 / advies) |
| Flags | Boilerplate surfaces describing each subtype — **not** a discourse-flag typology (STEPT1e1 stays parked) |
| Ontfangen / subtypes | Provisional characteristics cuts — **not** accepted formula types |

## Measurements (required)

| Metric | Where |
|--------|--------|
| `n_ontfangen_plus` / `n_missive` / leakage | metrics |
| Per subtype: n, frac_of_missive | metrics.subtypes[] |
| Per subtype: n_words median / q1 / q3 | subtypes[].length |
| Per subtype: flag rates + top combos | subtypes[].flags_* |
| Per subtype: n_r1 / n_advies_gold | subtypes[].known |
| Side-by-side contrast (length Δ, key flag Δ) | metrics.contrast |

## Eval gates (NOTES)

1. Do info vs decisionful **separate structurally** (length and/or flag signature)?
2. Are they characteristics of one kind (`missive`), or do they look like distinct kinds that deserve ES-level names? (Expect: still one kind, two shapes.)
3. Call: stop / characterise rekest next / unpark STEPT1e1 only if a *kind* gap remains / no new A from bag density alone.

## Do not

- Accept `info_receipt` / `decisionful_residual` / `ontfangen_start` as formula types
- Implement STEPT1e1 flag sieve (further bucketing residual by discourse flags)
- Start another A family unless NOTES names a kind-support probe
- Pull full resolution text from ES
- Classify flags as archival outcomes / “no decision”
- Rescore presence or re-run STEPT1e ES `mget` (reuse scores)

## After this step

Mark STEPT1f in `PLAN.md`. Follow NOTES call. Clear the chat before the next step.
