# STEPT1aj — Human skim near + mid hinge witnesses

**Goal:** Emit a **near+mid-only** Excel skim of STEPT1ai adjudication (92 rows: 20 near + 72 mid). Human fills `human_keep` / `human_note`; ingest writes provenanced verdicts. Far stays parked (noise). Soft membership only — no auto-mint.
**Done when:** skim xlsx + ingest path registered; fixture/unit tests pass; `data_io.check` clean; NOTES filled; `PLAN.md` + milestone updated. Human fill may complete in this chat or the next.

**Prerequisite:** STEPT1ai full run on disk (`formula_hinge_witness_adjudication`). Ontology: [`docs/DECISIONS.md`](../../docs/DECISIONS.md) 2026-10-26 formula-in-effect (witness adjudication).

## Constraint (locked)

- Skim **near + mid only**. Far (≈93%) is not the triage queue.
- **Near** default ask: confirm **variant** of `best_hinge_id`, or **reject**.
- **Mid** default ask: **split** (different hinge / note proposed id) / **composition** (too wide / multi-hinge) / **reject** / rare **variant**.
- Blank `human_keep` = not reviewed. Prefer undecided over a wrong merge.
- Do **not** mutate `formula_templates` or hinge ledger canonics in this step.
- Do **not** reopen STEPT1aa–ag fold / residual ladder.
- Do **not** name `voordracht` canonic here unless the skim itself forces it (separate pocket step remains available).
- Decision-polarity / referral watchwords (DECISIONS 2026-10-26 cues; still null canonic): **`afgewezen`** (+ friends) → negative pocket / reject-as-noise if not; **`Naar Y gestuurt voor advies` after goedgevonden** (Y often Raad van State / commissie `om te … examineren`) → **`composition`**; **`afgehandeld te worden`**, **`resolutie commissoriaal`**, **`hebben … geexamineerd`**, **`op advies van`** → composition / role TBD, not bare `ter_advies`. Exposition citing these or earlier resoluties → **`composition`**, not a second decide hinge.

## `human_keep` vocabulary

| Value | Meaning |
|-------|---------|
| `variant` | Same hinge; surface/spelling variant of canonic |
| `split` | Not this hinge — different function; put proposed `hinge_id` in `human_note` |
| `composition` | Too wide / multi-hinge span; keep as composition evidence, not a type |
| `reject` | Noise / not formula-sized / misband |
| *(blank)* | Not reviewed |

## You do

```bash
uv run pytest tests/test_formula_hinge_witness_skim.py -q
uv run python scripts/run_formula_hinge_witness_skim.py --fixture-only
uv run python scripts/run_formula_hinge_witness_skim.py
# After human fill:
uv run python scripts/run_formula_hinge_witness_skim.py --ingest
uv run python -m data_io.check
```

Fill: [`docs/proofs/multi-template-registry/STEPT1aj-hinge-witness-skim.md`](../../docs/proofs/multi-template-registry/STEPT1aj-hinge-witness-skim.md).

## Eval gates (NOTES)

1. Skim rows = adjudication rows with `band` ∈ {near, mid}; far excluded; counts match STEPT1ai (20+72).
2. Workbook has blank `human_keep` / `human_note` on emit; guide sheet documents vocabulary.
3. Ingest refuses unknown `human_keep` values; writes only filled rows; never mutates templates / hinge seed.
4. Script never auto-promotes mid/far into the ledger.

## Do not

- Auto-mint hinges or blueprints from skim counts
- Include far band in the skim sheet
- Word-TF-IDF re-score (STEPT1ai cuts stay frozen)

## After this step

If skim names a clear gap → seed/extend hinge ledger or name `voordracht` pocket. Else park mid reject mass. Clear the chat before the next step.
