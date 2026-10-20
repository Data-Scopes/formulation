# STEPT1k — Requeste opener formula-type measure (NOTES)

**Status:** done (2026-10-20). Recall + cloud gates PASS; FP gate FAILS but **accepted** — judgment below. `requeste_geleesen` promoted from provisional to accepted (A), measured on the slot-cloud/DAG baseline (kept consistent with appointment/advies method).

```bash
uv run python scripts/eval_requeste_formula_type.py --refresh-gold
uv run python -m data_io.check
```

## Results

Operating cut = 4.5 (p20 holdout positive scores). n_gold=74205 (n_bootstrap=59364, n_holdout=14841), n_negatives=500.

| Gate | Result |
|------|--------|
| Overall recall ≥ 0.70 | **PASS** — 0.8983 |
| FP rate ≤ 0.05 on N=500 | **FAIL** — 0.206 (103/500) |
| Cue-window accepts ≫ 0 | **PASS** — 37,939 accepted / 111,666 hits (6 slots, 248 variant types) |

| Slice | Model recall | Wording requeste/rekest/reqte | Δ |
|-------|-------------:|-------------------------------:|--:|
| Overall | 0.8983 | 0.8847 | +0.0136 |
| Pre-1731 | 0.8608 | 0.8460 | +0.0148 |
| Post-1731 | 0.9319 | 0.9194 | +0.0125 |

## Notes

- Empirical canonic: `IS ter Vergaderinge geleesen de Requeste` (STEPT1j empty-band head; Track S framing skeleton).
- Gold = ES `rekest`; formula type id = `requeste_geleesen` (opener ≠ ES type name).
- Provisional `requeste_start` presence stays provisional until gates PASS.
- **FP diagnosis (scratch, not pipeline):** cut sweep on saved scores showed no threshold clears both gates at once (best FP=0.042 only at cut=8.0, where recall crashes to 0.631, below the 0.70 floor) — not a calibration problem. Single-slot ablation (keep only `requeste`, drop `is`/`ter`/`vergaderinge`/`geleesen`/`de`) raised recall *and* FP together (0.880/0.136 vs 0.645/0.076 on a matched subsample) — so the generic slots aren't the main noise source either; the `requeste` slot itself is where negatives still get through.
- **Root cause:** FP concentrates in negatives carrying a decision-formula marker (`goedgevonden`/`goetgevonden`): FP rate 0.340 for negatives with the marker vs 0.117 without, and 66% of all false positives (68/103) come from the 40% of negatives that have it. Reading: resolution *form* in the SG is organized around **decision type** (approved / referred / deferred ...), not ES `proposition_type` (what prompted the item). A negative sharing the same decision type as a typical rekest looks structurally like one almost everywhere except the opener noun — a single-slot fuzzy match can't carry that discrimination alone.
- **TF-IDF+LR comparison, with a caveat:** a document-level char n-gram + LR baseline (same hyperparameters as R1/L2, trained/tested with no id leakage) got closer to both gates at once (recall 0.79 / FP 0.054 at cut 0.8). Initially read as "the model adds more discriminative power" — **that overclaims**. Both methods actually score the *full* document (`score_text` tokenizes the whole text, not a window), so the real difference isn't how much text each sees, it's what evidence each is licensed to use: DAG requires the slot sequence in order, roughly contiguous (answers "is the opener clause present"); TF-IDF counts character n-grams anywhere, order-blind (answers "does this document's vocabulary look like a rekest" — closer to re-deriving ES's own label from topical content than to detecting the boilerplate span). The feature-weight check (top features are literal `requeste`/`geleesen` fragments, not length) doesn't disambiguate these, since TF-IDF can't say *where* those fragments fired — consistent with both "found the opener" and "the word recurs later in the substantive text." So the TF-IDF number is an upper bound on class-separability via *some* textual signal, not evidence the opener-formula definition or DAG method under-performs at the task it's actually answering.
- **Decision:** keep the slot-cloud/DAG baseline (consistent with appointment/advies method, and the only one of the two actually measuring span presence rather than document topic) rather than switching measurement methods for one type. Accept `requeste_geleesen` as **A** on recall strength (0.898), with the FP rate and decision-type confound recorded as a known, understood limitation — not a silent gap.
- **Net-then-sieve tested and refuted (for this signal pair):** two-stage "cheap recall net → strict structural sieve" (the project's `candidate-then-structure` shape) was tried as TF-IDF proba net + DAG score sieve, 7×6 cut grid on the holdout-gold / test-negative slice. **No cut pair clears both gates**, and the sieve contributes nothing: TF-IDF@0.8 alone = 0.791/0.054, +DAG@4.5 = 0.787/0.054; TF-IDF@0.5 alone = 0.875/0.082, +DAG@4.5 = 0.859/0.072. The combination traces the same frontier as the net alone — it drops gold and negatives at the same rate rather than selectively cutting FP. Reason: the two stages are redundant, both keying on `requeste`/`geleesen` vocabulary (ordered slots vs. order-blind n-grams), so the sieve adds no orthogonal evidence. A cruder wording-substring net + DAG sieve (0.876/0.110) is strictly dominated by TF-IDF alone at 0.5. Also: the DAG cliff survives every net — at `dag>=5.0` recall collapses to ~0.64 under all TF-IDF cuts, i.e. nearly all gold sits bunched just above 4.5, so the alignment score is too coarsely graded to sieve with.
- **Open question this raises (sharper than the design question it replaces):** is the ≤0.05 FP gate reachable *at all* against ES-derived gold? Four independent signals (slot-cloud DAG, wording substring, document TF-IDF+LR, and every combination tried) hit a floor near 0.04–0.05 FP only by pushing recall below the 0.70 floor. That is the pattern expected if some share of the 500 "negatives" are genuinely requeste-opener-bearing resolutions that ES did not type as `rekest` — negatives are defined solely by ES label absence, and the proposition_type scheme was an administrative construction not always cleanly maintained. If so the gate measures label completeness as much as model error, and the ≤0.05 target may be unreachable in principle for any formula type measured this way. Worth settling before another type is gated on it.
- **Carries forward:** (1) the decision-type-vs-proposition_type tension applies beyond requeste (Track T0 typology is keyed to `proposition_type`); (2) the FP-gate-vs-label-completeness question above. Both belong to T1l / later typology work, not re-litigating per step.

## Next

- **STEPT1l** — subtype characterisation under requeste+ (mirror STEPT1f).
Clear chat before starting.
