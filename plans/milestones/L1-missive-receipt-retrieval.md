# L1 — Missive receipt retrieval (whole resolutions)

**Status:** STEPL2 done (closed gate); **L3+ parked**  
**Steps:** STEPL0–STEPL4 under [`plans/steps/`](../steps/)  
**Parallel to R1** — same machinery (char TF-IDF + LR on `resolutions_flat`), different document type. Do not mix into formula STEP2 or aanstelling scripts.

## Goal

Find whole resolutions whose act is **receiving a missive/brief** and recording that **no substantive resolution** was taken (info / *advertentie* only). Output a ranked candidate list, not formula spans.

**Closed after STEPL2:** holdout metrics only (recall 0.934 / precision 0.907 / F1 0.920 on 1780 labelled). No remainder harvest. Working type definition remains `missive_receipt_labelled` (cues + seeds). Optional later: L3→`missive_receipt_selected` only with an explicit decision.

Typical skeleton (orthography varies):

1. Opening: *Ontfangen een missive/brief van …* (writer, place, date)
2. Content cue: *houdende advertentie* / *advisen* / similar
3. Close: *WAAR op geen resolutie is gevallen* / *geen resolutie vereischende* / equivalent

## Not this type

| Looks similar | Why exclude |
|---------------|-------------|
| *Ontfangen een missive* → *aangenaam* / *sessie genomen* | Track R aanstelling |
| *Ontfangen een missive* → *in handen van* / referral | different act |
| *Ontfangen een missive* → *is goedgevonden* / real decision | substantive resolution |
| Rekenkamer / other *commissie* appointments | sibling appointment (`other_appointment`) |

Shared opening *Ontfangen een missive* is **not** enough; the **null-decision close** (or equivalent “no resolution required”) is the type discriminator.

## Done when

- Type definition + seed examples registered (STEPL0).
- Provenanced labelled table (positives + overig) exists (STEPL1).
- Holdout recall / precision / F1 recorded (STEPL2).
- Unlabelled remainder bucketed high / grey / low (STEPL3).
- Written stop-or-residual decision (STEPL4).

## Method (mirror R1)

1. **Seeds** — hand examples (no URN gold table like `resolutie_refs`). Expand with high-precision cues, then human/rule review.
2. **Baseline** — `TfidfVectorizer(analyzer="char_wb", ngram_range=(3, 5))` + `LogisticRegression` (same frozen hyperparameters as R1 unless STEPL2 metrics force a rethink).
3. **Harvest** — score remainder; ingest / review bands; cue + shape filters as needed.
4. **Residual** — optional; only on TF-IDF negatives if odd-wording FNs dominate.

## Sources

- Corpus: `resolutions_flat` (reuse Track R wiring).
- Seeds: [`tests/fixtures/missive_receipt_seeds.jsonl`](../../tests/fixtures/missive_receipt_seeds.jsonl) (hand texts).
- Negatives: sample from non-matching resolutions; **exclude** `aanstelling_selected` ids from the positive class (they may share the opening).

## Decision points

- Opening-only keyword harvest → too many aanstellingen / referrals; require close cue or model.
- 17c *brieff* / *geen resolutie vereyschende* vs 18c *Missive* / *geen resolutie is gevallen* → expect orthographic drift; do not declare one century done from the other.
- No external URN gold → STEPL1 quality depends on seed + cue precision; budget a short review pass before freezing labels.
