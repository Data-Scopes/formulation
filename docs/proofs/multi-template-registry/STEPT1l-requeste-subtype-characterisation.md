# STEPT1l — Requeste+ routing subtype characterisation (NOTES)

**Status:** done (2026-10-20). Structural separation **PASS**; `routing_unclear` small as expected.

```bash
uv run python scripts/run_requeste_subtype_profile.py
uv run python -m data_io.check
```

## Results

Universe = requeste+ model-detected (`formula_type_requeste_scores`, `role=="gold"` & `pred` True — ES rekest gold where the STEPT1k slot-cloud/DAG opener score clears the accepted cut 4.5), full 1705–1796. n_requeste_plus = 66,657; n_recall_miss = 7,548 (= the STEPT1k 0.898 recall gap, not characterised here); outcome_join_coverage 0.953.

| Subtype | n | frac of requeste+ | n_words median (q1–q3) |
|---|---:|---:|---|
| `referred` (handen / in handen) | 12,930 | 0.194 | 227 (135–373) |
| `granted_direct` (goedgevonden, not referred) | 47,274 | 0.709 | 134 (90–230) |
| `routing_unclear` (outcome joined, neither flag) | 3,335 | 0.050 | 154 (100–271) |
| (outcome not joined — ES/parsing gap) | 3,118 | 0.047 | — |

## Contrast

| Metric | referred | granted_direct | routing_unclear |
|---|---:|---:|---:|
| n_words median | 227 | 134 | 154 |
| advies co-occurrence rate | 0.199 | 0.156 | 0.086 |

Delta (referred − granted_direct): **+93 words** median, a ~70% length increase. This is not circular with the subtype definition (length wasn't used to define the split).

## Eval gates

1. **Do `referred` vs `granted_direct` separate structurally? PASS.** Length separates clearly (+93 words median, referred longer) — consistent with a referred request carrying an extra referral/examination clause (`rapport_start`/`geexamineert` appear in referred's top combos, never in granted_direct's) before the resolution proper. `advies` co-occurrence is higher for referred (0.199 vs 0.156) but the gap is modest, not sharp — advies-seeking is not exclusive to the referred path.
2. **Is `routing_unclear` a small residual or a large third mass? PASS (small).** 0.050 of requeste+ (plus 0.047 outcome-unjoined) — the referred/granted_direct two-way split covers 90.3% of requeste+. Routing is effectively binary, not a three-way structure.
3. **Call: stop.** No new A from routing density alone; `referred` / `granted_direct` stay characteristics cuts, not accepted formula types.

## Caveats

- **`goedgevonden` is not exclusively "request granted."** It fires at near-identical high rate inside `referred` (0.975) as it does by definition inside `granted_direct` (1.0, tautological since it's the subtype's defining flag). Reading: `goedgevonden` marks *a resolution was taken* (procedural "it was resolved that..."), not specifically that the request's substance was approved outright — a referral ("goedgevonden ... te stellen in handen van...") is itself a resolution and also carries the marker. The `granted_direct` label should be read as "resolved, no referral marker present" — a structural routing cut, not a semantic "request succeeded" claim. This is the same decision-type-vs-proposition_type caution carried forward from STEPT1k.
- **Requester-identity sub-typology (civilian / institution / ambassador) stays out of scope**, confirming the `docs/template-design-questions.md` framing: ES `proposer`/`proposer_role`/`proposition_organisation` are null corpus-wide; that lever needs a separate NER-mention-frequency probe (not opened here).
- `n_outcome_unjoined` (3,118; 4.7%) is `formula_documents` join miss (likely session-boundary / parsing gaps already known from STEPT0), not a routing category — excluded from the subtype denominators' numerators but left in `n_requeste_plus`.
- Flags describe boilerplate surfaces, not archival outcomes — not a decision-correctness claim.

## Next

Track T1 requeste+ characterisation closed at this level of detail. No further routing-axis split opened (would need a kind-support probe per the step guide's do-not list). Clear chat before the next step.
