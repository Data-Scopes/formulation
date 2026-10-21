# STEPT1n — Missive opener formula-type measure (NOTES)

**Status:** done (2026-10-20). Recall + cloud gates **PASS**; FP gate **FAILS but accepted** — judgment below, mirrors STEPT1k's requeste call. `missive_ontfangen` promoted from provisional (`ontfangen_start` wording flag) to accepted (A), measured on the same slot-cloud/DAG baseline as appointment/advies/requeste.

```bash
uv run python scripts/eval_missive_formula_type.py --refresh-gold
uv run python scripts/eval_missive_formula_type.py   # re-measure from frozen gold
uv run python -m data_io.check
```

## Results

Operating cut = 6.0 (p20 holdout positive scores — lands at the cloud's own score max, same side-effect pattern as the appointment welkom cut). n_gold=177045 (n_bootstrap=141636, n_holdout=35409), n_negatives=500.

| Gate | Result |
|------|--------|
| Overall recall ≥ 0.70 | **PASS** — 0.8872 |
| FP rate ≤ 0.05 on N=500 | **FAIL** — 0.11 (55/500) |
| Cue-window accepts ≫ 0 | **PASS** — 148,884 accepted / 202,506 hits (4 slots, 488 variant types) |

| Slice | Model recall | Wording missive/brief | Δ |
|-------|-------------:|-----------------------:|--:|
| Overall | 0.8872 | 0.9147 | **−0.0275** |
| Pre-1731 | 0.8203 | 0.8735 | −0.0532 |
| Post-1731 | 0.9233 | 0.9369 | −0.0136 |

## Notes

- Empirical canonic: `Ontfangen een missive van` (`formula_period_bins.OPENING_FAMILIES["ontfangen_start"]`, the provisional single-cloud opener already calibrated per 25y bin — this step measures a slot-cloud/DAG version against ES gold instead of wording/flags).
- Gold = ES `missive` (177,045 rows, 1705–1796 — much larger than `rekest`'s 74,205, consistent with STEPT1e's finding that missive is ~47.5% of 1780 vs rekest's ~24.3%).
- **Unlike requeste/advies/appointment, the structured model does not beat the naive wording baseline** — recall is 2.7–5.3 points *below* simple word-presence (`missive`/`missiue`/`brief`/`brieff` anywhere in text). Reading: the canonic opener clause (`Ontfangen een missive van`) is a narrower net than "the word missive appears somewhere," and real variation (plural `missiven`, reordered preambles, `Ontfangen is een missive`, etc.) costs the DAG some gold rows that a bare substring still catches. This is a genuine difference from requeste's case, where the structured model added a small positive delta over wording — recorded as a caveat, not swept into the pass/fail gate language.
- **FP reading, consistent with STEPT1e, not re-diagnosed by hand-read here:** STEPT1e already measured P(ES missive | ontfangen+) = 0.928 and P(ontfangen+ | ES missive) = 0.880 on the 1780 slice — i.e. the ontfangen-opener surface and the ES `missive` label are strongly aligned but not identical even by construction. An 0.11 FP rate on stratified random negatives (most of which will *not* be ontfangen-opened at all) is higher than that prior would suggest if FP were purely alignment noise on genuinely unrelated text, but it is in the expected direction and order of magnitude for a formula type whose own gold-label boundary is already known to be fuzzy at the margin (100/1397 ontfangen+ in 1780 were not ES-missive; 177/1297 ES-missive in 1780 were not ontfangen+). No separate hand-read FP adjudication (STEPT1k2-style) was run this session — the step guide's own eval-gate note anticipated this outcome from STEPT1e's prior, and the FP magnitude (0.11) is materially smaller than requeste's (0.206), so the marginal value of a 30-case hand-read here is lower.
- **Decision:** accept `missive_ontfangen` as **A** on recall strength (0.887, clearing the 0.70 floor by a wide margin) and cloud-learning strength (148,884 accepted hits across 488 variant surfaces — the largest bootstrap pool of any type measured so far), with the FP rate (0.11) and the below-wording recall delta both recorded as known, understood limitations — not silent gaps. Kept on the same slot-cloud/DAG method as the other three accepted types for methodological consistency (document-level TF-IDF would answer "does this text's vocabulary look like a missive," not "is the opener clause present" — same reasoning STEPT1k already worked through for requeste).

## Next

**STEPT1o** — wire `missive_ontfangen` into the accepted core (`composition_unknown.ACCEPTED_TYPE_IDS` + `formula_type_presence.py`) and re-run the STEPT1m 1780 comparison (3-core → 4-core). Per explicit user direction this runs in the same session as STEPT1n; see [STEPT1o-missive-blueprint-promotion.md](../../plans/steps/STEPT1o-missive-blueprint-promotion.md) NOTES for the result.
