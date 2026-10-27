# Formula abstraction (Doc B: finding and telling apart one formula)

**Status:** design note, rev. 2 (2026-10-21) + scaffolding/carriers note (2026-10-22) + L2 ablation note (2026-10-23) + hard-drop result (2026-10-23). Companion: [`resolution-graph-design.md`](resolution-graph-design.md) (Doc A). Experiment: **STEPT1v** soft optional = no-op; **STEPT1v2** hard-drop PASS ([`NOTES`](proofs/multi-template-registry/STEPT1v2-formula-reduction-hard-drop.md)) — no recall hinge; **Requeste** is the FP/specificity hinge; other five slots singly ablatable for recall.

**Rev 2 narrows the scope, because rev 1 overreached.** Rev 1 used formula abstraction to discriminate **resolution types** — TF-IDF over the 31-flag profile, k=12 clustering of 309k resolutions. That is the *combination* question (what a resolution's mix of formulas implies), which is a different and later problem. This doc is now about the prior question only:

1. **Retrieval** — given one formula, how do we find its instances?
2. **Discrimination** — how do we tell a formula instance from something that is not one?

The unit is the **formula instance (a span)**, not the resolution. The rev 1 clustering result is retained below as an appendix, marked as belonging to the other question.

## The problem: literal formulas do not scale

Every accepted formula type is defined by a short literal canonic plus hand-listed spelling variants: `is den selven verwelkomt`, `IS ter Vergaderinge geleesen de Requeste`, `Ontfangen een missive van`. Slot clouds tolerate OCR drift *within* a slot, but identity still rests on specific words in specific positions.

1. **A type can hinge on one word.** STEPT1k's ablation found that dropping requeste's frame slots (`is`/`ter`/`vergaderinge`/`geleesen`/`de`) raised recall *and* FP together, while the `requeste` slot was where negatives got through — the frame contributed little, the noun carried the type. ⚠️ Measured on gold that the 2026-10-21 ES re-pin showed was ~31% mislabelled; the direction is probably right but the magnitude needs re-measuring.
2. **The structured model may lose to a bare substring.** STEPT1n reported `missive_ontfangen` recall 0.887 vs. the naive wording matcher's 0.915. ⚠️ **Now in doubt:** the clean recheck puts model recall at **0.988**, but the wording baseline was *not* re-measured on clean gold, so whether the substring still wins is **unknown**. Re-measuring it is part of STEPT1q.
3. **Fillers do not match literally.** `houdende[refsexien]` (OCR for *reflexien*) will never group with `houdende[reflexien]`. Doc A finding 3. This one is unaffected by the gold problem.
4. **A hand-written canonic can simply be wrong.** `formula_schemes_sample.json` gives `welkom` as `wordt hij welkom geheten`; the corpus majority is `is den selven verwelkomt`, and the original bootstrap accepted **0/2564** hits because of it (`DECISIONS.md`, 2026-10-19). Abstraction has to be able to recover from a wrong starting point, not just tolerate spelling drift.

Hand-enumerating variants per formula per century is the work that does not scale.

## Frequency: three different roles, not one

Rev 1 treated TF-IDF's IDF premise (rare ⇒ discriminative) as the organising idea. That was wrong as a general rule. Frequency's role depends on which question is being asked:

| Question | Role of frequency |
|---|---|
| **Which formula is this** (A vs B) | **Not a discriminator.** You cannot tell `advertentie` from `geen_resolutie` by corpus rate. Report it as a covariate; this is the only place the IDF premise could apply. |
| **Is this a formula at all** | **The criterion.** Formulaicity *is* recurrence: a phrase occurring once is not a formula; a stable phrase recurring thousands of times is. Must be measured bottom-up from repetition, not by scoring text against a canonic already assumed — which would be circular, and impossible for `welkom`. |
| **Variant or distinct type** | **Partial evidence.** A rare wording adjacent to a frequent one reads as a variant; a wording with substantial *independent* frequency reads as a candidate type. Cannot settle it alone — needs distributional evidence (context, zone, co-occurrence). The hard case. |

These are not in conflict: "rare ⇒ discriminative" answers *which* formula; "frequent ⇒ formulaic" answers *whether* it is one.

### Scaffolding vs type-deciding formulas (composition layer)

Resolution **templates** are mostly built from **standard** opening and decision formulas (high corpus rate: ontfangen / requeste / missive frames, `goedgevonden`-like closes). Those are necessary scaffolding — they do **not** decide the task type. The **less frequent** mid-body / specialised formulas usually carry the type signal.

Consequence (not a contradiction of the table above):

| Layer | Frequent openers/decisions | Rarer type-carriers |
|-------|----------------------------|---------------------|
| Catalogue risk | Statistical irrelevance if promoted as *the* type | Variant dissipation if every surface gets an id |
| Detection | Cover mass; low IDF weight by design | Often **easier to localise** once named (sparse, sharper hinge) |
| Period | Drift still hits both; period-/inventory-keyed variants, not new ids per decade | Same — wording drift ≠ new type without distributional evidence |

Human naming (ground truth) is required before a rare carrier becomes a `template_id`. Measurements propose; they do not name.

## The abstraction ladder (at formula level)

| Level | Representation of one formula | Scales? |
|---|---|---|
| L0 | Literal surface string | No — OCR + orthographic drift, and the string may be wrong (point 4) |
| L1 | Slot cloud + hand-seeded variant lists (current) | Partly — hand seeds per slot |
| L2 | **Reduced skeleton** — the minimal slot subset that still localises, slots masked | Target |
| L3 | **Recurrence-validated skeleton** — a reduced skeleton confirmed by its document frequency across the corpus | Target |
| L4 | Filler classes induced from context rather than listed | Later |

**Formula reduction (L1→L2) is the core proposal.** Ablate one slot at a time, recalibrate each configuration at its own p20 (`calibrate_cut`), and keep the minimal subset that retains localisation. **STEPT1v lesson:** making a slot *optional* via `align_dag(optional_slots=...)` is **not** ablation when the text still matches the full canonic — the DAG prefers the full path and metrics do not move. Real L1→L2 = **hard drop** (remove the slot from the cloud / score a reduced canonic), then recalibrate. Soft optional remains useful for period/OCR skip hypotheses, not for hinge discovery. **STEPT1v2 on `requeste_geleesen`:** hard-drop works (cuts/IoU move); no single-slot recall hinge (phrase is redundant for FN); **Requeste** is a specificity hinge (drop → FP 0.022→0.054, recall rises). Hinge ≠ “required for gold localisation” — distinguish FN-carriers from FP-carriers.

**L2→L3 is where frequency enters as the criterion:** a reduced skeleton is validated if it recurs at high document frequency with stable wording. That also gives a route to formulas nobody has written down yet, since it ranks candidates by recurrence rather than matching a known list. `formula_detection.FormulaSearch` (Track F dependency, STEP1 wired, STEP2+ paused) exists for exactly this.

## Retrieval arms to compare (STEPT1q)

Three ways to locate one formula's instances, measured against each other at span level:

1. **Substring** — the scheme's `search phrase`. Baseline.
2. **TF-IDF window** — cosine of candidate windows vs the canonic (`formulation/boundary/tfidf_windows.py`, STEPS1).
3. **Slot cloud + DAG** — `bootstrap_slot_cloud` + `align_dag`.

The step guide adds a fourth arm the design note missed: the deployed clouds are bootstrapped from the **stale** `*_es_gold`, so a substring win over them would not show that structure fails, only that the cloud learned from mislabelled text. Arm 3 is therefore run twice — frozen, and re-bootstrapped from the clean sample — and the verdict is read off the clean-bootstrap variant.

Span accuracy can only be measured honestly on a **hand-read sample**: the repo has no corpus-scale human span gold (only 3 synthetic cases in `formula_boundary_cases.jsonl`; ES `evidence` is a point anchor and is upstream silver). A result showing substring is as good as DAG would be valid and useful — it would say identity is carried by the hinge token after all.

## Caveats that survive rev 2

- **Input provenance.** The 31 `formula_documents` flags are themselves literal-cue detections, and `praeside_start`/`praesentibus_start` carry known attendance-list leakage (`typology_sample.py`). Abstraction over flags is only as good as the flags. Four flags (`sessie`, `handen`, `in handen`, `versonden`) have **no definition anywhere in-repo**.
- **Form vs content discipline.** Flags like `paspoort` and `betalinge` are arguably content, not form. Anything leaning on them is typing by subject matter.
- **The comparison pitfall.** A bag-of-formulas model answers "what is this resolution's formula profile", not "is this boilerplate span present here". A better recall/FP number can mean an easier question (STEPT1k worked this through for TF-IDF vs DAG).

---

## Appendix — the combination question (not this doc's purpose)

Retained from rev 1 as a finding. This is **resolution typing**, i.e. what a resolution's *mix* of formulas implies — explicitly out of scope for retrieval and discrimination, and not a basis for any claim here.

`formula_documents` (309,181 × 31 flags), each resolution as a document whose terms are its flags, TF-IDF (`norm="l2"`):

- **Known combinations separate cleanly:** within `advertentie & geen_resolutie` cosine 0.970 (n=75,713); within `welkom & sessie` 0.959 (n=336); between the two **0.068**.
- **MiniBatchKMeans k=12 recovers combinations the project established step by step:** c1 78,021 advertentie+geen_resolutie+ontfangen (info-receipt, Track L/T1f); c0 42,622 in handen+geexamineert+rapport (referral/examination, T1g); c4 36,909 vergaderinge+request+gedelibereert+goedgevonden (requeste granted, T1l); c5 28,198 gedelibereert+ontfangen+goedgevonden (decisionful missive, T1e); c6 20,230 praesentibus+praeside (the known attendance leakage, cleanly isolated); c7 13,476 geen_resolutie+ontfangen; c9 12,247 conform; c8/c11/c10/c3 requeste and pass/payment families.
- **Rare combinations are invisible:** no appointment cluster, because `welkom & sessie` is 336 of 309,181 (0.1%). This finds mass combinations only; rare ones need the human gold set.

Worth keeping for two reasons: it shows a good deal of the per-type work was recoverable from a 31-column boolean matrix, and it is the natural instrument for the combination question **when that question is actually being asked**. It says nothing about whether a given span is a formula.
