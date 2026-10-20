# STEPT1i — Composition unknown (1780)

**Goal:** Proto-blueprints / derivatives / undecided + fingerprints on undecided.  
**Status:** **PASS** (measurement); fingerprint cut too loose for structure split.

**Doctrine:** blueprint = canonical formula-graph pattern; derivative = variation; novel = not a derivative. Presence inventory is thin (few types) → exact-bag proliferation not observed here.

## 1. Graph layer

| Motif | n | frac |
|-------|--:|-----:|
| filler_star | **1365** | 0.488 |
| known_sparse | **102** | 0.036 |
| empty | **1329** | 0.475 |
| novel_tail | **0** | 0.0 |

| Metric | Value |
|--------|------:|
| n_universe | **2796** |
| n_unique_exact_bags | **6** |
| n_unique_accepted_cores | **3** |
| n_proto_blueprints (support ≥ 5) | **2** |
| n_undecided | **1329** (all `empty`) |

### Proto-blueprints (cores)

| accepted_core | support | n_unique_exact_bags | dominant_bag_frac |
|---------------|--------:|--------------------:|------------------:|
| advies_geleesen | 74 | 2 | 0.919 |
| appointment_installation | 28 | 2 | 0.929 |

Within-core derivative noise is **low** (dominant bag ~92–93%). No appointment∩advies core with support ≥ 5 (third core empty or below floor).

**novel_tail = 0:** with only these presence types, there are no rare non-filler combinations to name — undecided is purely **no known formula hit**.

## 2. Fingerprint layer (undecided = empty)

| Metric | Value |
|--------|------:|
| n_undecided_scored | 1329 |
| nn_sim p50 / p90 | **0.494** / **0.810** |
| n_clusters / n_singletons | 2 / 1 |
| share_largest_cluster | **0.999** |
| derivative_score (max_sim to proto) p50 | **0.183** |

At `fp_cut=0.15` the empty band collapses to **one mass**. Fingerprints do **not** yet separate variation vs different structures here — cut too low and/or empty texts are broadly similar at this grain. Derivative_score ~0.18 = soft proximity to proto exemplars, not a clear derivative call.

## 3. STEPT1h crosstab (diagnostic)

| Metric | Value |
|--------|------:|
| joined | 2796 |
| composition_unknown ∩ high_unknown | 1324 |

Almost all empty bags are also cover-unknown — expected (no accepted hits).

## 4. Call

**PASS** as inventory + measurement.

1. Proto-blueprints are few and stable; bag-level derivatives are not the proliferation problem on this type inventory.
2. Undecided ≈ half the year and is **empty**, not novel combinations — need more formula types in presence (or characterisation of empty) before “novel graph patterns” appear.
3. Fingerprints at 0.15 are not discriminative on empty; next = **characterise empty** (T1j) and/or raise `fp_cut` / score derivative tails — not mint blueprints from cluster n=1.
