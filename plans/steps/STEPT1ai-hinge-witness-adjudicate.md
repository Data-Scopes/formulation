# STEPT1ai — Witness adjudicate vs hinge archetypes

**Goal:** Score archaeology witnesses (family exemplars) against the seeded hinge canonics with **char_wb 3–5 TF-IDF** cosine → **near / mid / far**. Soft membership only; mid does not mint or merge.
**Done when:** provenanced adjudication + metrics; fixture tests pass; `data_io.check` clean; NOTES filled; `PLAN.md` + milestone updated.

**Prerequisite:** STEPT1ah ledger seeded (`formula_hinge_candidates`). Ontology: [`docs/DECISIONS.md`](../../docs/DECISIONS.md) 2026-10-26 formula-in-effect. Prefer a post-STEPT1af `--overlap` `formula_family_candidates` on disk for the full run.

## Constraint (locked)

- **Archetypes first** — hinge ledger is fixed input; do not invent hinges from witnesses.
- **Char n-gram TF-IDF** soft membership only (not discovery, not a classifier to deploy).
- Bands (provisional defaults): `near ≥ 0.80`, `mid ≥ 0.50`, `far < 0.50`. CLI-overridable; report distribution in metrics.
- **Mid does not auto-mint or auto-merge.** Far is not a new type by itself.
- Pockets with null `canonic` are **not** archetype targets.
- Do **not** mutate `formula_templates` / `formula_hinge_candidates` human fields.
- Do **not** reopen STEPT1aa–ag fold / residual patch ladder.

## Witness source

Primary: `formula_family_candidates` exemplars (`exemplar` / `exemplar_norm` + `family_id` + `phrase_freq_max`). Fixture path for CI smoke. Optional `--limit` for skim runs.

## You do

```bash
uv run pytest tests/test_formula_hinge_witness.py -q
uv run python scripts/run_formula_hinge_witness.py --fixture-only
uv run python scripts/run_formula_hinge_witness.py
uv run python -m data_io.check
```

Fill: [`docs/proofs/multi-template-registry/STEPT1ai-hinge-witness-adjudicate.md`](../../docs/proofs/multi-template-registry/STEPT1ai-hinge-witness-adjudicate.md).

## Eval gates (NOTES)

1. Every scored witness has `best_hinge_id`, `best_sim`, `band` ∈ {near, mid, far}.
2. No hinge target lacks canonic; pockets excluded from target set.
3. Band counts sum to `n_witnesses`; metrics record cuts + vectorizer settings.
4. Script never writes `human_keep` / never mutates templates.

## Do not

- Auto-promote mid/far into the hinge ledger or registry
- Re-run fold / residual sieve as typology growth
- Word-TF-IDF blend (char-only this step; ContentFingerprint stays STEPT1i)

## After this step

Human skim near (confirm variant) + mid (split / composition / reject) bands. Clear the chat before the next step (likely: name voordracht pocket, or mid-band hand triage).
