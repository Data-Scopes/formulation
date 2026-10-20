---
cursor:
  subagentId: "bc-aa0292ab-2695-5200-ab9c-6b0029c23ea2"
---

# S4 opening phrase candidates — sample

**Path found:** `/Users/rikhoekstra/develop/republic_ner_matching/output/s4_opening_phrase_candidates.jsonl`  
(`~/republic_ner_matching/republic_ner_matching/output/...` was missing.)

**Line count:** 1 (single JSON object on one line; not one-record-per-line JSONL)

**Top-level fields:** `tier1_unique_flat_rows`, `excluded_gold_dates`, `minimum_frequency`, `candidates`

**Per-candidate fields:** `phrase`, `count`, `word_count`  
(no span/offset/position fields)

**Envelope:** `tier1_unique_flat_rows=3817`, `excluded_gold_dates=50`, `minimum_frequency=5`, `candidates` length=271 (counts 5–1015; word_count 2–5)

**Example candidates:**

| phrase | count | word_count |
|--------|------:|-----------:|
| ontfangen een | 1015 | 2 |
| ontfangen een missive | 716 | 3 |
| is gelesen | 635 | 2 |
| is gelesen de | 434 | 3 |
| ontfangen een missive van | 342 | 4 |

**What they appear to be:** Frequency-ranked n-gram openings (Dutch States-General formulaic starters such as “ontfangen een missive…”, “is gelesen…”) harvested from tier-1 resolution text after excluding gold dates, kept only if they occur at least five times.
