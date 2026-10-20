# STEPT1i — Composition unknown (blueprints / derivatives / fingerprints)

**Goal:** Measure resolution **formula-graph patterns** on 1780: proto-blueprints (`accepted_core`), within-core **derivatives**, **undecided** band (`empty` ∪ `novel_tail`), then **content fingerprints** on undecided (clusters + max_sim to proto-blueprint exemplars).  
**Done when:** provenanced metrics/scores/sample written; NOTES record structure vs variation vs undecided; `data_io.check` clean; `PLAN.md` updated.

**Prerequisite:** STEPT1h done; `formula_type_presence_scores` on disk for 1780. Doctrine: [`plans/milestones/T1-unknown-first.md`](../milestones/T1-unknown-first.md).

## Constraint (locked)

- Object = formula-graph **patterns**, not gold-set cover and not NER ALIGNED_TO.
- Exact bags proliferate → alikeness via **`accepted_core`** (appointment/advies); ontfangen = context.
- Same core → **derivative** mass; different cores → **proto-blueprints**; fingerprints for **undecided** (derivative vs novel candidates).
- Do **not** mint types or promote `formula_templates` rows.

## You do

```bash
uv run pytest tests/test_composition_unknown.py tests/test_content_fingerprint.py -q

uv run python scripts/run_composition_unknown.py --fixture-only

# Full 1780 (graph + fingerprint on undecided)
uv run python scripts/run_composition_unknown.py --year 1780

# Graph only (cheap)
uv run python scripts/run_composition_unknown.py --year 1780 --skip-fingerprint

uv run python -m data_io.check
```

Fill: [`docs/proofs/multi-template-registry/STEPT1i-composition-unknown.md`](../../docs/proofs/multi-template-registry/STEPT1i-composition-unknown.md).

## Design locks

| Piece | Rule |
|-------|------|
| Universe | Presence year slice (1780) |
| `accepted_core` | bag ∩ {appointment_installation, advies_geleesen} |
| `min_support` | Default 5 (hypothesis) — rarer cores → novel_tail |
| Motifs | filler_star · known_sparse · empty · novel_tail |
| Fingerprints | Undecided only; word+char TF-IDF blend; NN + max_sim to proto-blueprint exemplars |
| Sample | Undecided stratified (+ cluster id when fingerprint ran) |

## Eval gates (NOTES)

1. Few proto-blueprints? Within-core derivative noise?
2. Undecided size triage-worthy?
3. Fingerprints: one mass vs many singletons / far from proto-blueprints?
4. Call: characterise novel/undecided samples next — not mint blueprints from n.

## Do not

- Promote registry blueprints; mint As from clusters
- Import republic_ner fingerprint package
- Treat STEPT1h high_unknown as the definition of unknown (crosstab only)
