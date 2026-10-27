# Decision Log

Record durable methodological and architectural decisions here. Keep entries short enough to scan.

## Template

### YYYY-MM-DD: Decision title

- **Context:** What changed or what result forced a choice?
- **Decision:** What did we decide?
- **Reason:** Why is this the right tradeoff now?

## 2026-10-27: Growth edge = bubble-up (cliff-medoid); hand catalogue = later comparison

- **Context:** User dissatisfied with seed-anchored skim: word leak / one-word variants treated as different types; indicative hinge list was never meant to *define* the catalogue. Confirmed after NER-side Gemini residue handoff.
- **Decision:**
  1. **Discovery growth edge** = scoped grams → `char_wb` TF-IDF → cluster → **medoids** → **relative-gap / cliff sieve** → human steer/name. Limited **POC first** (steer before full stack).
  2. Hand hinge ledger / polarity cues / STEPT1aj skim = **comparison anchors later**, not normative types.
  3. No auto-promote to blueprints; catalogue-size band (~15–30 hinges / ~25–50 named) still a sanity check after emergence.
  4. Full EM → transition → `[SLOT]` → formula-DAG still **parked** until POC steers.
  5. Matching-only stay out (PINNED_TO, underparse axis, etc.).
- **Reason:** Surfaces must merge before typing; human names what bubbles, rather than scoring everything against a prior list.

## 2026-10-27: Gemini emergent-centroid stack — residue from `republic_ner_matching` detour

- **Context:** Accidental Gemini-style work in `republic_ner_matching` (underparse/seam inventory on n=9 flats).
- **Decision:** Accept method residue (cliff sieve, scoped windows, medoids, phrase/boundary gates). Superseded as growth-edge call by **2026-10-27 bubble-up** above. Matching helpers stay out of formulation.
- **Reason:** Controls are useful; archetypes-first-as-catalogue is not.

## 2026-10-26: STEPT1aj — near+mid hinge-witness skim (emit)

- **Context:** STEPT1ai left near (20) + mid (72) as the human triage queue; far parked.
- **Decision:** Ship **STEPT1aj** emit — `formula_hinge_witness_skim_xlsx` (blank `human_keep` ∈ {variant, split, composition, reject}) + ingest path to `formula_hinge_witness_verdicts`. No auto-mint; polarity/referral watchwords in guide only.
- **Reason:** Soft membership named the queue; typology growth still needs human band labels before ledger/template changes.

## 2026-10-26: STEPT1ai — witness adjudicate vs hinge archetypes

- **Context:** STEPT1ah seeded 20 hinges (14 with canonic); archaeology `formula_family_candidates` remain witnesses, not types.
- **Decision:** Ship **STEPT1ai** — char_wb 3–5 TF-IDF cosine soft membership → near (≥0.80) / mid (≥0.50) / far. Full run: 1261 exemplars → near 20 / mid 72 / far 1169. Mid does not auto-mint or auto-merge; pockets excluded from targets; ledger/templates untouched.
- **Reason:** Empirically separate thin variant shell (near) and triage queue (mid) from mass far-noise without turning harvest into catalogue growth.

## 2026-10-26: Decision-polarity surface cues (human)

- **Context:** Polarity pockets still null-canonic; need holdable surface signs before naming.
- **Decision:** Record (not mint):
  1. **`decision_negative`** — cue family **`afgewezen`** (+ friends). Still ≠ `geen_resolutie` (null). Canonic stays null until a naming step.
  2. **Approve-then-refer** — **`Naar Y gestuurt voor advies`** (slot Y) **especially after** `goetgevonden / goedgevonden en verstaan` is **composition** (`goedgevonden` + referral-for-advice), not one polarity type and not bare `ter_advies` scaffolding alone. Typical Y: **Raad van State**; also a **Commissie** with purpose clause **`om te … examineren`** (and kin). Slot Y / purpose are content slots, not separate hinges.
  3. **Tentative:** **`afgehandeld te worden`** (not bare `afgehandeld`) — disposed/to-be-handled surface; polarity/role TBD (≠ `afgewezen`; ≠ `geen_resolutie`). May sit nearer purpose/referral than refuse. Hunt later; do not mint.
  4. **Exposition cites execution / prior resoluties** — the exposition band (e.g. `advertentie` / houdende…) may **formulaically refer** to the same execution phrases (afgewezen / afgehandeld te worden / naar-Y-gestuurt…) **and** to **earlier resolutions**. That is **composition / cross-reference**, not a second copy of the decide hinge and not a new type minted from the citation surface. Position interprets (exposition place ≠ inventing formulaicity).
  5. **Commissorial / advice-chain cues** (record, not mint): **`resolutie commissoriaal`**; **`hebben … geexamineerd`** (past of the `om te … examineren` purpose); **`op advies van`**. Likely compose with Raad-van-State / commissie referral and with `ter_advies` / `advies` openers — do not collapse into one hinge; roles TBD.
  - **More polarity/referral cues deferred** (later chat) — do not invent.
- **Reason:** Negative refusal and post-approve referral are distinct procedural moves; collapsing either into `goedgevonden` or `ter_advies` loses the catalogue edge. Exposition can *point at* those moves and prior acts without being them.

## 2026-10-26: STEPT1ah addendum — decision polarity pockets

- **Context:** Human glance of the hinge ledger: scaffolding covers cue/form (`waar_op`, `goedgevonden`, `geen_resolutie`) but not resolution outcome polarity.
- **Decision:** Add four unnamed `pocket` rows — `decision_positive` / `decision_negative` / `decision_conditional` / `decision_deferred` (null canonic). Positive may later coincide with `goedgevonden`; deferred ≠ `geen_resolutie` and ≠ `advertentie`. No invented wording; no auto-merge.
- **Reason:** Catalogue growth saturates procedural moves; lock intent before witness adjudicate.

## 2026-10-26: STEPT1ah — seed hinge archetype ledger

- **Context:** Redesign pause locked hinge/composition/witness ontology; next empirical work is archetypes first, not more harvest patches.
- **Decision:** Ship **STEPT1ah** — hand-seed `formula_hinge_candidates` (now n=20 after polarity addendum): decision/referral scaffolding (`waar_op`, `geen_resolutie`, `goedgevonden`, `in_handen`, `advertentie`, `ter_advies`, `voldoening`, `ontfangen`), L2 of six blueprints as `from_blueprint`, STEPT1u + decision-polarity pockets unnamed. No `gedelibereert` id; no witness TF-IDF; no auto-mint.
- **Reason:** Catalogue growth starts from a holdable hinge set; harvest remains archaeology until adjudicate step.

## 2026-10-26: Formula-in-effect ontology (redesign pause)

- **Context:** STEPT1aa–ag treated 5-gram / family / residual surfaces as almost-formulas and patched with sieves, caps, and reorder flags. Skim still showed hapax “cardinals,” person strings, and no holdable concept of what a formula is. User called a redesign pause.
- **Decision:** Lock the ontology below (also in [`formula-conceptual-overview.md`](formula-conceptual-overview.md)). **Park** STEPT1aa–ag outputs as **candidate archaeology** — not the growth edge; no further residual/family patch steps. Empirical hinge work waits for a later chat after clear.
  - **Formula-in-effect** (all required): recurrence; reduced skeleton (hinge); discourse/procedural function; composition/gaps allowed; position interprets (does not invent formulaicity alone).
  - **What is real:** hinge → composition → human-named template; variants are not types. Harvest / overlap / fold / sequence rows are **witnesses**, not almost-formulas.
  - **Catalogue band (18c procedural):** ~15–30 hinges; ~25–50 named types. ~6 is too few (opener-biased); >100 named ≈ oversplit; ~2000 families is never the target count.
  - **Wide/small:** too wide → split at function boundaries, keep long string as composition evidence; too small → glue/tail/name (or F1b of an existing hinge), not a formula.
  - **Witness adjudication:** proposed **archetypes first**; post-hoc compare gathered phrases to hinge-sized canonics (prefer char n-gram TF-IDF) → near / mid / far. Mid does not auto-mint or auto-merge. Not a discovery method.
- **Reason:** Catalogue size comes from saturating procedural moves, not emptying residuals. Patches on the wrong unit cannot reach a holdable typology.

## 2026-10-26: STEPT1ag — triviality sieve before residual review

- **Context:** Post-fold skim had hundreds of thin/solo families (tok bigrams, place fillers, short tails). A full residual absorb/truncate hand-read would drown in trivia.
- **Decision:** **STEPT1ag** — Pass 0 parks trivia (token≤3, tok-hinge without cue, closed-class/place/office, substring of multi, F1b short-tail, no-signal). Pass 1 emits capped (~60) absorb/truncate **proposals** only; overflow parked; no auto-merge.
- **Reason:** Keep human judgment on formula-shaped leftovers; metrics count the mass.

## 2026-10-26: STEPT1af — overlap-first; type from place

- **Context:** Skim showed pre-overlap `suggested_role` (esp. any-hit `opener_abs`/`opener_rel`) labeling mid-text as openers; `gedelibereert` cue split decision chains; null mass swallowed by `waar_op`; person strings as exemplars.
- **Decision:** **STEPT1af** reorder: repair → nest → overlap → name-strip → assign role from place+cue. Ignore profile `suggested_role`. Drop `gedelibereert_*` cue; null wins over `waar_op`; widen WAAR/bare-`waar` split; heuristic name mask before exemplar/hinge.
- **Reason:** Type must follow formula identity (overlap + place), not early-position OR flags on raw 5-grams.

## 2026-10-26: STEPT1ad accepted → STEPT1ae wire overlap-cue into fold

- **Context:** STEPT1ad fixture prove 10/10; user accepted NOTES.
- **Decision:** Open **STEPT1ae** — optional `--overlap` on `fold_phrases` / `run_formula_family_fold` calling prove helpers (union + paradigm + F1b annotate). Default path without `--overlap` stays STEPT1ab. No auto-mint; no F1b lookahead.
- **Reason:** Prove locked the gates; wire is additive and reversible via CLI flag.

## 2026-10-26: Prove-first overlap-cue fold (STEPT1ad)

- **Context:** STEPT1ab hinge buckets leave sliding decision windows as separate families; Marijn’s overlap TSV encodes positional chains. Wiring straight into `formula_family_fold` risks opaque merges.
- **Decision:** Ship **STEPT1ad** as a **separate prove** (`overlap_cue_prove` + `prove_overlap_cue_fold`): overlap union within place bands, bottom-up cues, paradigm cardinal/plural mask, cardinal corpus substring test, short-tail F1b suppress (no lookahead). Register `phrases_5gram_overlap`. Do **not** change production fold until NOTES accept → STEPT1ae.
- **Reason:** Same prove-then-wire pattern as appointment-institution; principles are judgeable case-by-case before contaminating `formula_family_candidates`.

## 2026-10-26: Harvest artefacts — positional overlap vs real formula boundaries

- **Context:** 5-gram harvest windows often **overlap in position**. That yields (a) sliding windows of one formula and (b) windows that **straddle** two formulas (e.g. `advertentie waar op…`). Conversely, one long formula is chopped into overlapping fragments (`nomineeren te visiteeren examineeren` / `advis daar op` / …).
- **Decision:** Treat these as **harvest artefacts**, not typology. Fold **repairs** them before science: split mid-window at decision-start **`waar op`** (prefix vs decision family); **glue** known long chopped chains into one family; refuse only **straddle re-attach** (e.g. advertentie|waar op), not null-decision sliding windows that share `geen resolutie`. Bare `waar op` → decision-start family; `waar op` + `geen resolutie` → null-decision family. Canonical exemplar remains the join key.
- **Reason:** Overlapping positions are how the harvester works; formula typology must not inherit straddles or chops.

## 2026-10-26: Do science on a canonical form (family exemplar join key)

- **Context:** STEPT1ab folds sliding 5-grams / spelling variants into families. STEPT1z harvest treated nested surfaces as separate nodes and polluted the sequence matrix. Trifecta’s `canonical_pref_label` vs raw `target_word` is the same lesson.
- **Decision:** **Do science on a canonical form.** Family **exemplar** is the join key for typology, sequence-matrix nodes, counts, and harvest. **Members** stay for human skim/evidence only. Zone/length ≠ role. Skim sheets use blank `keep` / `human_role` until human fill; prefer undecided over a wrong merge. Sequence-matrix impact (STEPT1ac) rebuilds harvest from exemplars and compares to STEPT1z with hard + soft (containment) metrics.
- **Reason:** Surfaces undercount or explode graphs; false merges poison transitions worse than missing a rare phrase.

## 2026-10-26: STEPT1aa/ab — 5-gram inventory → family fold (typology bridge)

- **Context:** Track T opener treadmill paused; need a formula-level overview including decision scaffolding. Large frame is Marijn’s 5-gram occurrence dump (~26.7M rows), not `formula_documents` flags. Freq sieve alone drops rare carriers and does not settle variants.
- **Decision:** Ship **STEPT1aa** (stream + `phrase_freq` Pass A + protected/rare sidecar; legacy `lcats`/zone) and **STEPT1ab** (nest collapse + variant fold → `formula_family_candidates`; human_role empty). No auto-mint. Next after human skim = typology map and **rebuild/compare `formula_sequence_matrix`** using folded exemplars as harvest nodes.
- **Reason:** Size-safe recurrence evidence + Doc B scaffolding/carrier split; fold addresses nested surfaces that polluted STEPT1z harvest.

## 2026-10-25: opener_candidates — human merge of formula surfaces

- **Context:** STEPT1z harvest produces nested/alias surfaces (`in handen` / `handen`, variant openers). The candidate frame needs a way to collapse those without minting a new type.
- **Decision:** Add human **`merge_candidates`** on `opener_candidates`: absorb `from_ids` into survivor `into_id`; accumulate `surfaces` / `merged_from` / `seed_refs` / `n_empty_support`; absorbed rows get `status=merged` + `merged_into`. Refuses absorbing or targeting blueprints. Optional `--canonic` on merge can pocket→named. Driver CLI: `--merge … --into …`. No auto-merge from the sequence matrix.
- **Reason:** Process judgment stays human; sequence P-matrix noise is hygiene, fixed by merge in the queue before measure.

## 2026-10-25: STEPT1z — probabilistic formula sequence matrix (+ harvest)

- **Context:** After STEPT1y, hand-naming voordracht is a poor fit (surface-varied). User wants compute to propose candidates and a **probabilistic** before/after overview — not only counts or a linear queue.
- **Decision:** Ship **STEPT1z**. Primary product = **row-stochastic adjacent transition matrix** P(next=B | current=A) on year 1780 (rows sum ≈ 1; include `END`). Companion = support `n` (+ optional precedes layer P(B later|A), median gap). Nodes = six blueprints + harvested scheme/pocket surfaces. Harvest from `formula_schemes_sample` + STEPT1u pockets (substring order; presence for blueprints). Do **not** auto-mint/`named`. No full DAG re-fit this step.
- **Reason:** Conditional succession is the sequence story; raw n alone misleads; joint P(A,B) collapses back to co-presence. Human naming gate stays.

## 2026-10-25: STEPT1y — human-judged `opener_candidates` write-back loop

- **Context:** After STEPT1x (6 blueprints), each new opener still meant twin scripts (measure + promote). User asked for a pipeline plus a candidates dataframe that a human judges, with the pipeline writing evidence back into the table.
- **Decision:** Ship **STEPT1y**. Durable loop = `opener_candidates` ↔ driver phases (`measure` → `wire` → `propose-promote`) ↔ human verdicts. Pipeline writes **evidence only**; human writes names + `a_verdict` / `promote_verdict`. No auto-mint, no auto-A, no auto-promote (`--apply-promote` requires human accept). Seed: 6 blueprint audit rows + `voordracht` / `conclusie_handen` pockets. Audit adapters only for the six done types; new types refuse measure until a later adapter.
- **Reason:** Same bar as the 2026-10-22 human-naming gate; stops copy-paste STEPT1k/n/s/w twins without collapsing judgment into metrics.

## 2026-10-25: STEPT1x — `rapport_gehoord` promoted to blueprint (6-core)

- **Context:** STEPT1w accepted A; STEPT1x wired into presence + `ACCEPTED_TYPE_IDS` and re-ran 1780 composition-unknown (5-core → 6-core).
- **Decision:** Promote `rapport_gehoord` to `role: "blueprint"`. Empty **0.122→0.107** (342→300). Three rapport-bearing cores clear support≥5 (solo 42; +requeste 10; +both requestes 7), all dominant_bag_frac 1.0 — gates 1–3 PASS. Period label stays `18c`; promote evidence is 1780 — recalibrate later for other periods. Next = human-judged `opener_candidates` queue + measure→wire→propose-promote driver (or 6-core empty re-char).
- **Reason:** Unlike STEPT1t (empty flat), rapport pulls real residual empty mass; low-noise solo core confirms STEPT1u’s skeleton call under composition.

## 2026-10-25: STEPT1w — rapport opener accepted A (cleanest FP so far)

- **Context:** STEPT1u named `IS gehoord het rapport van` as the sharpest residual empty-band skeleton. Full ES `proposition_type=rapport` gold (n=13,928) + slot-cloud/DAG measured as `rapport_gehoord`.
- **Decision:** Accept A — recall **0.895** PASS; FP **0.006** PASS (3/500); cloud 10,642/12,839; cut 7.5 (= 5-slot exact ceiling). Model trails wording ~5 pts (same pattern as missive/advies). Do **not** promote this step. Next = blueprint promote (STEPT1m-style) or voordracht / L3.
- **Reason:** Stereotyped canonic on gold; mid-text `rapport` FP risk from STEPT1l did not materialise at this cut.

## 2026-10-23: STEPT1v2 — Requeste is FP/specificity hinge; no recall hinge

- **Context:** Full hard-drop on long-head `requeste_geleesen` (n=47,237; holdout 9,447): cuts move (9.0→6.5/7.5); recall flat ≈0.977 for every single drop except drop-Requeste (R 0.998 / FP 0.054). Five slots within ε for recall+FP; Requeste fails safe via FP rise +0.032.
- **Decision:** Close STEPT1v2 as **PASS**. L2 naming: **Requeste** = specificity (FP) hinge; IS/ter/Vergaderinge/geleesen/de = scaffolding for recall. Do not deploy a reduced cut; skip leave-k. Next = rapport opener A (STEPT1u) or Doc B L3.
- **Reason:** Hard-drop answers Doc B where soft optional could not. Hinge here is against negatives, not gold FN — do not mint a one-token skeleton from `l2_required_tokens_guess`.

## 2026-10-23: STEPT1v2 opened — hard-drop L1→L2

- **Context:** STEPT1v soft optional was a methodological no-op; Doc B needs forced absence.
- **Decision:** Open **STEPT1v2** — remove each slot from `variant_lists`, recalibrate p20 per config, name hinge vs scaffolding on long-head `requeste_geleesen`. Guide + eval ready; measurement only (no frozen-cut / blueprint change). Leave-k optional after single drops show signal.
- **Reason:** Hard-drop measures “identity without this token”; fixture already moves cut and span IoU where soft optional did not.

## 2026-10-23: STEPT1v — soft optional ablation is a no-op; hard-drop next

- **Context:** STEPT1v single-slot `optional_slots` ablation on long-head `requeste_geleesen` (n=47,237; holdout 9,447): every config identical (recall 0.9766, FP 0.022, cut 9.0, span IoU 1.0). No hinge; vacuous “all slots safe.”
- **Decision:** Treat STEPT1v as **inconclusive method result**, not “formula has no required slots.” Soft optional *allows* skip; gold still takes the full six-slot path. **Next = STEPT1v2 hard-drop** (remove slot from `variant_lists` / reduced canonic, recalibrate). Do not change frozen cut 4.5 from this run. Amend Doc B: L1→L2 needs forced absence, not optional alone.
- **Reason:** On a population that matches the full canonic, optional ablation cannot move scores; only removing the slot tests whether identity survives without it.

## 2026-10-23: STEPT1v opened — L2 reduction before another opener

- **Context:** After STEPT1u, user declined another opener; chose Doc B L1→L2 on a settled formula.
- **Decision:** Measure on **`requeste_geleesen`** (long-head gold only); soft `optional_slots` first pass. Rapport-A / letter / close-clause parked.
- **Reason:** Use accepted inventory to ask what a formula *is*, not grow opener coverage.

## 2026-10-22: STEPT1u — 5-core empty is no longer rekest-headed

- **Context:** After STEPT1t, empty stayed 342/2796 (0.122). STEPT1j’s empty (1329) was 53% rekest; that finding drove the requeste track. Re-ran empty-band characterisation on current 5-core scores.
- **Decision:** Treat remaining empty as **several pockets**. Rekest share collapsed to **0.105** (36). New head = **voordracht** (80, 0.234). Named residuals: rapport skeleton + conclusie+handen. Do **not** mint from n=342. (Superseded next-step call: user declined another opener; L2 opened instead.)
- **Reason:** Unknown-first says characterise before minting; the old rekest story is closed.

## 2026-10-22: STEPT1t — `requeste_op_de` promoted to blueprint (5-core)

- **Context:** STEPT1s accepted the short opener; STEPT1t wired it into presence + `ACCEPTED_TYPE_IDS` and re-ran the 1780 composition-unknown measurement (4-core → 5-core).
- **Decision:** Promote `requeste_op_de` to `role: "blueprint"`. Empty mass **unchanged** at 0.122 (gate 1 FAIL — expected: long `requeste_geleesen` at cut 4.5 already scores short texts). Three dual-opener cores clear support≥5 (`requeste_geleesen`+`requeste_op_de` 188; +missive 109; +advies 7), all dominant_bag_frac 1.0 — gates 2–3 PASS. No solo short core: all 304 short presents also fire the long model (cut collision). Downstream five modules still untouched.
- **Reason:** Typology gain is naming dual-opener composition, not further empty shrink. Gate 3 (low-noise) is the promotion call; STEPT1s cross-fire 0.02 keeps the types distinct under the short model despite long@4.5 asymmetry.

## 2026-10-22: STEPT1s — `requeste_op_de` accepted as A (cut 4.5)

- **Context:** STEPT1r named the short opener; STEPT1s measured it (slot-cloud + DAG) on head-filtered ES rekest gold (n=16,447, 22% of rekest).
- **Decision:** Accept `requeste_op_de` (canonic `Op de Requeste`) as measured A. Operating cut **4.5**. Recall 1.0 (gold definition makes this near-tautological — trust FP + cross-fire). FP **0.064** FAILS ≤0.05 but accepted (32/500; far below long opener’s accepted 0.206). Cross-fire on long-head rekest **0.02**. Do **not** promote to blueprint / wire `ACCEPTED_TYPE_IDS` in this step. Letter short-opener parallel stays parked.
- **Reason:** Split is operationally clean (low cross-fire); short canonic’s FP cost is real but modest; raising the cut cannot help (max score = 4.5).

## 2026-10-22: STEPT1r — requeste low band is `Op de Requeste`; split confirmed

- **Context:** STEPT1q’s bimodal `dag_frozen_score` on rekest gold (low ≈4.5 / high ≈9) looked like a cut tradeoff. Part A tied the low band to shorter texts and absent deliberation markers; part B hand-read + full clean-gold head tally showed it is a **second opener**, not a clipped long canonic.
- **Decision:** Split after human name. Long type stays `requeste_geleesen` (`IS ter Vergaderinge geleesen de Requeste`). Short type named **`op_de_requeste`** (id `requeste_op_de`, canonic `Op de Requeste`). Do **not** mint in STEPT1r — next step = mint + calibrate (FP risk: short canonic). Park a likely **parallel short-vs-receipt opener split for letters/missives** until after that mint; do not fold letter work into the requeste step.
- **Reason:** Clean bipartition on gold (low 0.973 `Op de Requeste`, high 0.992 long reading formula); frozen 4.5 is a three-slot collision, so one type cannot both inventory the short routine and keep a tight FP cut.

## 2026-10-22: Template ridge — naming, scaffolding vs carriers, drift

- **Context:** Direction judgment after STEPT1o–q: risk of drowning in statistical irrelevance (ubiquitous formulas) or variant dissipation (every surface a new id). User clarifications: (1) templates are mostly built from standard opening/decision formulas — **less frequent** formulas decide the type; (2) that sparsity also makes carriers **easier to find** once named; (3) formula wording **drifts** over time; (4) template **naming** needs human ground truth.
- **Decision:**
  1. **Human naming gate:** new `template_id` / blueprint names require a human NOTES call after characterisation (sample read). Auto-mint from rates, clusters, bags, or band n is forbidden.
  2. **Scaffolding ≠ type:** keep ubiquitous openers/decision glue as measured presence / covariates with low popularity weight; do not treat them as the typology instrument. Prioritise characterisation (and eventual A acceptance) of **rarer type-carrying** formulas — default against new ids still applies; human name when distributional evidence supports a split.
  3. **Drift ≠ new type:** absorb period/OCR wording via slot clouds, period keys, and discriminators; new ids only with independent distributional identity (STEPT1l pattern).
  4. **STEPT1r** = characterise requeste low-score band (part A quantitative on disk; part B hand-read when flat mounted) **before** Doc B L2 reduction; L2 is a later step, not STEPT1r.
- **Reason:** Stays on the ridge between coarse mush and catalogue explosion; matches Doc B frequency roles at formula level while correcting the composition-layer mistake of equating “frequent in bags” with “decides the template.”

## 2026-10-20: STEPT1o — missive joins the accepted core; four openers promoted to blueprint

- **Context:** STEPT1n accepted `missive_ontfangen` (frozen cut 6.0), mirroring STEPT1m's requeste wiring gap: `composition_unknown.ACCEPTED_TYPE_IDS` still only held the three prior openers, so STEPT1i/T1m's proto-blueprint measurement never saw missive.
- **Decision:** Wired `missive_ontfangen` into `formula_type_presence.py` (`fit_missive_presence_model`, mirrors requeste wiring) and `composition_unknown.ACCEPTED_TYPE_IDS`; re-ran the STEPT1m 1780 comparison (3-core → 4-core). Empty/undecided mass dropped only modestly (0.140→0.122), but `filler_star` (bag = bare `ontfangen_start` root only, no accepted type — 42.5% of the universe) **collapsed to 0.000** — that mass reclassifies to `known_sparse` now that the opener firing on it has a real accepted-type home. Five new/growing accepted_cores cleared support≥5 (`missive_ontfangen` alone 1239; `missive+requeste` 182; `appointment+missive+requeste` 20; `advies+missive` 7; `appointment+missive` 7), dominant_bag_frac 0.714–1.000 — same or better than the 3-core baseline's 0.706–0.982. **Promoted** `missive_ontfangen` to `role: "blueprint"` in `formula_templates`, joining the other three. Same five downstream modules (order/position/residual/graph-zone/cover-set) left untouched, per STEPT1m precedent — now a doubled follow-up item (requeste + missive).
- **Reason:** The filler_star collapse is the real typology finding here: a large share of the corpus that looked like "unexplained boilerplate" under the 3-core accepted set was actually missive-opened all along, just invisible because missive had no accepted-type home yet. Composition-level low-noise behavior (this step's gates) is independent of STEPT1n's own recall/FP judgment and isn't relitigated here.

## 2026-10-20: STEPT1n — missive opener as A family (STEPT1k-style, full ES gold)

- **Context:** STEPT1m closed with three accepted openers; user directed a missive track following the same measured-formula-type pattern as requeste (STEPT1k), not the parked Track L TF-IDF document-retrieval harvest (STEPL3, never opened).
- **Decision:** STEPT1n mirrors STEPT1k exactly: gold = ES `proposition_type=missive` + flat text (177,045 rows, 1705–1796 — 2.4× rekest's 74,205); formula type `missive_ontfangen` with empirical canonic `Ontfangen een missive van` (already established in `formula_period_bins.OPENING_FAMILIES`); cue-window slot-cloud + DAG; wording baseline for deltas only. Recall 0.887 **PASS** (≥0.70); FP 0.11 **FAIL but accepted** — smaller than requeste's 0.206, and expected given STEPT1e's own finding that ontfangen+ and ES-missive are strongly aligned but not identical (P(missive\|ont+)=0.928, P(ont+\|missive)=0.880 on 1780). New caveat vs requeste: model recall trails the naive wording baseline by 2.7–5.3 points across slices (real opener variation — plural `missiven`, reordered preambles — costs the DAG some gold that a bare substring still catches). No STEPT1k2-style hand-read FP adjudication run — the FP magnitude is smaller and the step guide's own gate anticipated the STEPT1e prior.
- **Reason:** Keeps formula-type acceptance on one consistent method (slot-cloud/DAG measuring span presence) across all four openers rather than switching definitions per type; records the wording-baseline shortfall honestly instead of only reporting the gates that passed.

## 2026-10-20: STEPT1m — requeste joins the accepted core; three openers promoted to blueprint

- **Context:** STEPT1k accepted `requeste_geleesen` (frozen cut 4.5), but it was never wired into the shared accepted-core machinery — `composition_unknown.ACCEPTED_TYPE_IDS` still only held `appointment_installation` + `advies_geleesen`, so STEPT1i's proto-blueprint/undecided measurement never saw it. `formula_templates` also had no rows at all for the three accepted formula types themselves (only boundary-span framing, doc_flag surface markers, and appointment institution siblings).
- **Decision:** Wired `requeste_geleesen` into `formula_type_presence.py` (new `fit_requeste_presence_model`, mirrors the advies wiring) and `composition_unknown.ACCEPTED_TYPE_IDS`; re-ran STEPT1i's composition-unknown measurement on the same comparison year (1780). Undecided/empty mass dropped from 0.475 to 0.140 (confirms STEPT1j's "empty is rekest-headed" finding quantitatively); two new accepted_cores cleared the support≥5 floor (`requeste_geleesen` alone, support 1113; `advies+requeste`, 57; `appointment+requeste`, 21), each with dominant_bag_frac 0.84–0.98 — same low-noise range as STEPT1i's 2-core baseline (0.71–0.93), and the 3-core split exactly partitions the 2-core totals (74 = 17+57 for advies; 28 = 7+21 for appointment). **Promoted** all three opener types (`appointment_installation`, `advies_geleesen`, `requeste_geleesen`) to a new `role: "blueprint"` in `formula_templates`. Left `formula_type_composition_graph.py` / `formula_type_order.py` / `formula_type_position.py` / `residual_structure.py` / `unknown_likeliness.py` untouched — each encodes its own already-closed step's zone/order/cover-set design call on top of a same-named but independent constant, not a shared one; wiring requeste into those is a separate follow-up per type, not mechanical.
- **Reason:** Closes the gap between "accepted formula type" (measured, frozen cut) and "in the registry / counted in composition measurement" that STEPT1k left open; confirms the promotion is safe (no bag proliferation) before treating these three as the typology's settled building-block inventory. Routing subtypes (STEPT1l) are explicitly excluded from promotion — they stay characteristics of `requeste_geleesen`, not new catalogue rows.

## 2026-10-20: STEPT1l — requeste+ routing subtypes separate structurally, stop

- **Context:** STEPT1k accepted `requeste_geleesen` as A. `docs/template-design-questions.md` named a structural outcome/routing lever ("goedgevonden vs handen/in handen vs advies co-occurrence") as "answerable now" for rekest sub-typology, in contrast to requester-identity sub-typology (civilian/institution/ambassador), which stays blocked because ES `proposer`/`proposer_role`/`proposition_organisation` are null corpus-wide. STEPT1l tested the answerable lever, mirroring STEPT1f's missive-subtype method.
- **Decision:** Universe = requeste+ model-detected (`formula_type_requeste_scores` `role=="gold"` & `pred` True — ES rekest gold where STEPT1k's opener score clears the accepted cut), full 1705–1796 (n=66,657; recall-miss 7,548 reported as a count only, not characterised). Three routing cuts: `referred` (`handen`/`in handen`, n=12,930, 19.4%), `granted_direct` (`goedgevonden`, not referred, n=47,274, 70.9%), `routing_unclear` (outcome joined, neither flag, n=3,335, 5.0%). **referred vs granted_direct separate structurally** on length (+93 words median, not circular with the defining flags) though only modestly on `advies` co-occurrence (0.199 vs 0.156). `routing_unclear` + outcome-unjoined together are only 9.7% — routing is effectively binary, not three-way. **Call: stop** — no new accepted formula type from routing density; `referred`/`granted_direct` stay characteristics cuts, same status as STEPT1f's `info_receipt`/`decisionful_residual`. Caveat recorded: `goedgevonden` fires at near-identical high rate inside `referred` (0.975) as inside `granted_direct` (1.0 by definition) — it marks "a resolution was taken," not specifically that the request's substance was approved, so `granted_direct` is a routing-absence label, not a "request succeeded" claim.
- **Reason:** Settles the one lever template-design-questions.md flagged as tractable without opening a new NER-frequency probe (requester identity) or re-running ES/model work; keeps the decision-type-vs-proposition_type caution from STEPT1k explicit rather than silently reading `goedgevonden` as approval.

## 2026-10-20: STEPT1k2 — requeste FP hand-read settles the gate-vs-gold-gap question

- **Context:** STEPT1k left an open question: is the ≤0.05 FP gate reachable at all against ES-derived gold, or does it partly measure ES label incompleteness (negatives are defined solely by `proposition_type` label absence)? Cheapest test, per the diagnosis note: hand-read ~20–30 of the 103 requeste-opener false positives rather than more compute.
- **Decision:** `scripts/build_requeste_fp_review_xlsx.py` wrote a workbook (`requeste_fp_review_xlsx`) stratifying 30 of the 103 FPs by score band × `goedgevonden` marker, plus 6 blind ES-rekest gold positives as a calibration self-check. Hand verdicts: calibration **6/6 (100%)** bearing — reviewer judgment reliable. to_score: 12/29 `bearing` (genuine ES gold gap), 17/29 `unrelated` (alignment noise). `scripts/ingest_requeste_fp_review_xlsx.py` computes the FP rate corrected for the `bearing` share with a Wilson 95% CI: **0.121 (CI 0.084–0.153)** vs measured 0.206 and gate 0.05 → **not_rescued**, even at the most favorable CI bound. **The gate is not reachable by crediting label gaps alone** for this type; the majority of FPs (59%) are real model imprecision on the decision-type confound already diagnosed in STEPT1k, not ES mislabeling. Keep STEPT1k's acceptance as-is; do not fold the 0.121 figure into pipeline metrics (29-case hand-read, not a recomputed gate). Full result in the STEPT1k proof NOTES addendum.
- **Reason:** Settles the open question empirically rather than deferring it to typology work; a real but minority (41%) label-gap share means future FP-gate failures should get a hand-read check like this one rather than defaulting to "probably unmeasurable," but should also not assume the gap explains most of the floor.

## 2026-10-20: STEPT1k — requeste opener as A family (then requeste+ subtypes)

- **Context:** STEPT1j empty band is rekest-headed (~half); provisional `requeste_start` presence only ~0.19 on that mass; STEPT1j2 confirmed empty ≠ R1/L1. User asked to measure/accept the requeste opener (A), then subtype characterisation under requeste+.
- **Decision:** STEPT1k mirrors STEPT1a2: gold = ES `proposition_type=rekest` + flat text; formula type `requeste_geleesen` with empirical canonic `IS ter Vergaderinge geleesen de Requeste`; cue-window slot-cloud + DAG; wording baseline `requeste`/`rekest`/`reqte` for deltas only. Provenanced `rekest_es_gold` / `formula_type_requeste_*`. Do **not** accept via `formula_documents` flags or provisional presence. After gates PASS, next = STEPT1l subtype characterisation under requeste+ (STEPT1f mirror) — not blueprint minting, not 17c period map.
- **Reason:** Closes the largest unexplained empty skeleton with the same acceptance bar as advies/appointment; keeps opener acceptance separate from later kind-shape characterisation.

## 2026-09-21: Two tracks; retrieval first

- **Context:** Formula M1 (STEP0–1) is wired, but the next useful inventory work is recovering missing whole aanstellingsresoluties, not formula spans.
- **Decision:** Split **Track R** (`STEPR0`–`STEPR4`, milestone R1) from **Track F** (`STEP0`–`STEP4`, M1 paused). Active focus is R1 until judged. Do not mix retrieval into formula STEP2.
- **Reason:** Same *why* (resolutions are formulematig), different *what they return*. One-step-per-session stays unambiguous if the prefix is `STEPR*`.

## 2026-09-21: Gold is `resolutie_refs` URNs (rc5), not a text column

- **Context:** The unique-table `delegates_1705_1795_extended` release fills `resolutie_refs` for only ~4 delegates / 6 URNs. There is no `resolutions` text field.
- **Decision:** Register `delegates_resolutie_refs` pointing at `delegates_1705_1795_v1.0-rc5.xlsx` (~196/1051 rows, ~222 URNs). Bodies come from joining those URNs onto `resolutions_flat` in STEPR1. Do not train on four unique-table positives.
- **Reason:** The spreadsheet is a label list. Inventing text from it would skip the corpus join and hide coverage failures.

## 2026-09-21: `resolutions_flat` is one row per resolution; 18c is present

- **Context:** The shared parquet is described as “paragraphs”. Track R needs whole resolutions. Gold URNs are 1685–1791; sibling NER work often slices 1626–1630.
- **Decision:** Treat each parquet row as one resolution (`type=resolution`, unique `id` `session-{inv}-num-{n}-resolution-{k}`, 692,156 rows). Do **not** collapse paragraphs before TF-IDF. Score `resolutions_text`: `paragraph_texts` is the same wording as a JSON list (`["…"]`), never exact-equal (median +4 chars). 18c coverage is adequate (322,125 rows in 1705–1795). Naive constructed ids with matching dates are gold (199/217 unique URNs). The other **18 stay gold**: they are the same aanstellingen under a drifted session `num`. Relocate by same inventory + URN date + resolution index (17 unique hits → `aanstelling_gold_relocations`). The remaining 1685-09-23 URN has no parquet row that day; keep naive `session-3312-num-82-resolution-2` (parquet date 1685-09-25). Do not invent text. Strip trailing `;` and parse URNs out of goetgevonden.nl URLs.
- **Reason:** Session numbering in `resolutions_flat` has drifted from REPUBLIC URNs (already seen in `republic_ner_matching`). Dropping the 18 would throw away known positives.

## 2026-09-21: Labelled table is one row per resolution; 10× overig

- **Context:** Several delegates can share one URN; STEPR2 needs a stratified 80/20 on labelled rows. Scoring text is whole-resolution `resolutions_text`.
- **Decision:** Freeze `aanstelling_labelled` as one row per `resolutions_flat` id. Positives keep aggregated `gold_urns` / `delegate_ids` / `delegate_fullnames`. Missing `delegate_id` falls back to `cons_id_str`. Overig is a reproducible 10× sample (`random_state=42`) from the gold year window, excluding gold ids. Missing recovered ids or naive date mismatches raise; do not invent text.
- **Reason:** Duplicate resolution texts would leak across the STEPR2 split. 10× keeps the table small enough for char n-gram TF-IDF without scoring the full 18c remainder (that is STEPR3).

## 2026-09-21: In-repo warm stays; Track R paths in local.toml

- **Context:** `resolutions_flat` lives on the 2TB warm drive used by `republic_ner_matching`. Formulation’s committed warm root is in-repo `data/warm` (formula samples).
- **Decision:** Keep `[tiers.warm] = data/warm`. Override only the `resolutions_flat` and `delegates_resolutie_refs` **dataset paths** in gitignored `data_manifest.local.toml` (absolute paths). Do not remount the whole warm tier onto `/Volumes`.
- **Reason:** Remounting warm would hide in-repo formula datasets. `data_io.resolve` already returns absolute dataset paths as-is.

## 2026-09-21: TF-IDF+LR hyperparameters frozen; no test-split tuning

- **Context:** STEPR2 needs a cheap whole-resolution baseline. Holdout on `aanstelling_labelled` (213 aanstelling / 2130 overig; 80/20 stratified, `random_state=42`) is recall **0.860** / precision **0.974** / F1 **0.914** (43 test positives; 6 FN, 1 FP). Writeup ballpark was recall ~0.97 / precision ~0.95.
- **Decision:** Keep `TfidfVectorizer(analyzer="char_wb", ngram_range=(3, 5))` + `LogisticRegression(solver="liblinear", max_iter=1000, random_state=42)`. Do **not** add `class_weight`, n-gram search, or a threshold sweep after seeing holdout numbers. STEPR3 harvests with this architecture refit on all labelled rows. STEPR4 judges a residual pass: the six FNs are mostly missive / commissie / requeste openings, not the typical *is goedgevonden … committeren* wording.
- **Reason:** Headline cost is missed aanstellingen, but retuning on the test split would invalidate the metric. A methods bake-off is out of scope unless STEPR4 chooses one residual neural pass on TF-IDF negatives.

## 2026-09-21: STEPR3 harvest cuts kept; completeness is p>0.5

- **Context:** Full remainder 691943: high/grey/low 1012/6008/684923. Holdout gold median p=0.81, so the 0.85 ingest cut demoted 24/43 gold TPs into grey. Remainder bands: 1012 >0.85, 1871 in (0.5,0.85], 4137 in (0.15,0.5], 684923 <=0.15. Almost all high (1010/1012) and most p>0.5 (2711/2883) are in 1705-1795.
- **Decision:** Keep the 0.85/0.15 bucket labels on aanstelling_tfidf_harvest. Do not rescore. Completeness list is p>0.5 (2883). Post-harvest review is (0.15,0.5] (4137), not all grey. STEPR4 residual, if any, runs only on TF-IDF negatives (p<=0.5 / odd wording), not on (0.5,0.85]. Do not treat 17c HTR as done from this 18c-trained model (160 p>0.5 before 1705).
- **Reason:** Grey mixed a threshold artifact with genuine uncertainty. Stored proba is enough to re-bucket. Headline goal is complete the historical list, so ingest-quality high is not the harvest.

## 2026-09-21: R1 stop after TF-IDF

- **Context:** Holdout@0.5 is recall 0.860 (37/43; 6 FN) / precision 0.974 / F1 0.914, below writeup ~0.97 recall. Remainder 691943: p>0.5 completeness 2883, (0.15,0.5] review 4137, p<=0.15 low 684923. Of 6 FNs, 5 sit in review; 1 is 1690 HTR at p=0.023. high_or_grey recall 0.977 (42/43). Goal is complete the historical list (Doel A).
- **Decision:** Stop after TF-IDF. No residual GysBERT or embedding pass on the 689060 TF-IDF negatives (p<=0.5). Ingest p>0.5 (2883; 2711 in 1705-1795). Human review is (0.15,0.5] (4137; 3353 in 1705-1795). Do not treat 17c HTR as done.
- **Reason:** Odd-wording FNs that residual would target are already in the review band except one 17c miss, which an 18c-trained neural model must not declare done. high_or_grey recall 0.977 meets the writeup recall ballpark once review is included. Scoring 685k lows would be a methods bake-off (Doel B), not completing the list.

## 2026-09-23: Sibling appointments out of R1, kept for later

- **Context:** Harvest review surfaces true appointments that are not *aanstelling ter Vergadering* (e.g. *commissie* into the Generaliteits Rekenkamer with oath + introduction; Zeeland multi-credential batches; Gelre *om te resideren* templates). Same missive/commissie envelope, different office or formula.
- **Decision:** Track R completeness = vergadering admissions only. In Excel `review`, use `keep` / `drop` / **`other_appointment`** (optional note: `rekenkamer`, `zeeland_multi_cred`, …). Do **not** delete `other_appointment` rows from the harvest Excel or harvest parquet. Export id+label to a sidecar when review stabilizes; later track may promote them.
- **Reason:** Throwing them away would force a second full harvest. Collapsing them into R1 gold would mix document types and hurt the vergadering list.

## 2026-09-23: R1 selection finalized with review rules + names

- **Context:** Human review covered ingest_suspect (33/33) and most review_suspect; cue rules are stable (`sessie_genomen`±`aengenaem`→keep; bare `verwelkom`→drop).
- **Decision:** Freeze `aanstelling_selected` (gold + ingest_cued + suspect keeps + review shape-ok + review_suspect keeps) and `aanstelling_review_labels`. Bulk-fill remaining sessie±aengenaem / bare verwelkom blanks by rule. Refresh rough names (17c *gecommitteert* / *opden heer* / *verwillecompt*). Leave non-rule blanks unlabeled.
- **Reason:** Completes Doel A list without re-reading the whole grey band; names support delegate matching later.

## 2026-09-24: Track R2 — pre-1705 aanstelling expansion (deferred)

- **Context:** R1 `aanstelling_selected` includes **615** pre-1705 keeps (mostly review-band, **13** overlap hand gold). Early-period resolution separation is **≤ ~70% at best**; 18c-trained scores are weak on 17c, but reviewed keeps are useful exemplars.
- **Decision:** Register **Track R2** in [`plans/milestones/R2-pre1705-aanstelling-expansion.md`](../plans/milestones/R2-pre1705-aanstelling-expansion.md). Planned method: char `char_wb` k-NN/refit on pre-1705 remainder using 615 as **soft positives / seeds**; cue + Levenshtein rerank; optional dense rerank on top-K only. **Do not execute** until explicitly chosen (active: L1, F STEP2).
- **Reason:** Separates period-specific expansion from judged R1; avoids treating 615 as gold or completeness proof; keeps vector experiments scoped without blocking current tracks.

## 2026-09-23: Track L — missive receipt (parallel to R1)

- **Context:** Need a second whole-resolution type: *Ontfangen een missive/brief …* ending in *geen resolutie is gevallen* / *vereischende* (advertentie), distinct from aanstellingen that share the opening.
- **Decision:** Start **Track L / L1** mirroring R1 (char TF-IDF + LR on `resolutions_flat`). Positives require receipt + null-decision close, not opening alone. Exclude `aanstelling_selected` ids from L positives. Seeds in `missive_receipt_seeds`. Next step STEPL0.
- **Reason:** Opening-only harvest would drown in aanstellingen and referrals; R1 machinery transfers; type filter is the new work.

## 2026-10-18: Track S — formula boundary evolution (after TF-IDF)

- **Context:** R1 char `char_wb` TF-IDF works well for whole-resolution type recovery. Formula research needs exact boilerplate boundaries and variable slots; `FormulaSearch` (Track F / M1) is not the right first harness for that cut.
- **Decision:** Register **Track S / S1** — phased TF-IDF windows → Smith-Waterman (single / slot-cloud) → DAG. GysBERT only as optional STEPS4 residual. Pause M1 FormulaSearch STEP2+ while S runs. Do not mix S scripts with L1/R1 harvest.
- **Reason:** Same research object (templated language); evolution from coarse localisation to span structure. Keeps one-step-per-session clear via `STEPS*` prefix.

## 2026-10-18: STEPS1 — TF-IDF window framing knobs

- **Context:** PDF / design thread suggested char_wb 3–5 + `sublinear_tf`, threshold ~0.35–0.40, and optional stopwords / binary cosine / `strip_accents`.
- **Decision:** STEPS1 uses `char_wb` 3–5 + `sublinear_tf=True` + `min_df=2`, cosine to the openings template from `formula_boundary_cases`, score windows of ~16 tokens (stride 2), separate align-pad for later SW. Fit IDF on the window corpus of a `resolutions_flat` year slice (default 1780). Default cut **0.35** is recorded as a **hypothesis** with score percentiles — not frozen. No stopword list, binary/BM25, `strip_accents`, or logistic regression in this step.
- **Reason:** One sharpening change on the proven R1 vectorizer family; short windows match opening formulas; Track F sample corpus is not a gate; histogram before freezing the cut.

## 2026-10-18: STEPS1 — 18c template first (17c later)

- **Context:** Fixture template *Gepraesenteert ende gelesen sijnde de Requeste* barely appears in year slices; ≥0.35 hits on 1780 were mid-doc *gepraesenteert* noise. Real 18c openings are *IS ter Vergaderinge gele(e)sen de Requeste*. 17c also has *Op de Requeste* / *Is gelesen de requeste*, but that is a later expansion.
- **Decision:** STEPS1 default query = `opening_requeste_18c` (`IS ter Vergaderinge geleesen de Requeste`). Scope framing POCs to **18th century** first. Defer 17c period templates / cloud. Keep STEPS0 `formula_boundary_cases` unchanged for SW/DAG gold.
- **Reason:** One formula family + one period; avoid mixing diachronic variants into the first threshold pass.

## 2026-10-18: STEPS1 — calibrate after framework

- **Context:** With the 18c template, 1780 framing already yields real openings at high scores, but 0.35 still pulls provincial *ter Vergaderinge … leesen* neighbours; peak dedup / cut tuning is tempting.
- **Decision:** **Do not calibrate** the cosine threshold (or related ranking knobs) until the Track S **framework** is in place: STEPS2 slot-cloud bootstrap → STEPS3 provenanced spans on real windows (SW/DAG on STEPS1 candidates). Keep 0.35 labelled hypothesis. 17c templates stay deferred.
- **Reason:** Thresholds without cloud + span output optimize the wrong stage; finish the pipeline skeleton first.

## 2026-10-18: STEPS2 — SW aggregate cloud (no MSA)

- **Context:** Slot-clouds need observed OCR/spelling variants per template position; full MSA is heavy and out of scope for the S1 scaffold.
- **Decision:** Bootstrap `formula_slot_cloud` by Smith-Waterman against the 18c canonical template on STEPS1 hits (or fixture seeds); frequency-weighted `variants` per slot; optional slots from skip-rate hypothesis (0.25). Record period/`year_*` as metadata. No MSA; no STEPS1 threshold calibration; 17c clouds still deferred.
- **Reason:** Reuses STEPS0 SW; produces `variant_lists` for `align_sw_cloud`; keeps one formula family until span harvest (STEPS3) works.

## 2026-10-18: STEPS3 — provenanced SW/DAG spans

- **Context:** STEPS1 windows + STEPS2 cloud are ready; research needs exact boilerplate `[start, end)` on real (and shortened) openings before threshold tuning or a neural residual.
- **Decision:** Harvest `formula_boundary_spans` with SW single, SW cloud, and DAG per window; map local spans to doc offsets via `token_start`; record latency / score / cloud↔DAG agreement in `formula_boundary_span_metrics`. Still **no** STEPS1 cosine calibration and **no** GysBERT (STEPS4). 18c `opening_requeste_18c` only.
- **Reason:** Completes the TF-IDF → SW → DAG skeleton on real candidates; comparative span rows enable later cut tuning and residual decision.

## 2026-10-18: STEPS4 residual named GysBERT; bake-off deferred

- **Context:** Optional neural referee for hard formula spans could be GysBERT (plan default) or GloBERTise (VOC Early Modern). A fair comparison needs shared span gold and a harness beyond the residual gate.
- **Decision:** STEPS4 remains a **written GysBERT yes/no** (mirror STEPR4). Register a later comparison/eval framework — GysBERT vs GloBERTise (+ SW/DAG baselines), IoU / boundary delta / latency on frozen gold leftovers — as [`plans/deferred/S1-neural-span-eval.md`](../plans/deferred/S1-neural-span-eval.md). Do not run that bake-off inside STEPS4.
- **Reason:** Keep the residual decision cheap; methods comparison is Doel B and reuses STEPS0 metrics when chosen.

## 2026-09-23: STEPL0 — missive-receipt cue inventory (1780)

- **Context:** Seeds registered (`missive_receipt_seeds`, 6 hand texts). Cue POC on `resolutions_flat` year 1780 via `pd.read_parquet(..., columns=[id, date, resolutions_text])`.
- **Decision:** Keep open+close conjunction as the high-precision cue. Inventory: n=2796, open=1401, close=741, both=674. Open-only (~727) is large enough that opening alone is unusable; both≈close suggests most null-decision closes co-occur with the receipt open in this year.
- **Reason:** Matches L1 type definition; STEPL1 can seed from both-hits (then exclude `aanstelling_selected`) plus hand seeds.

## 2026-10-18: S1 stop after SW/DAG — no GysBERT residual

- **Context:** STEPS0 fixture IoU=1.0 for SW single/cloud/DAG. STEPS3 on 1780 (181 windows): zero empty spans; 30 full 6-token openings at align=9; among align>=6 cloud↔DAG spans agree. Overall cloud↔DAG equal-rate 0.33 (60/181) is driven by short partial matches (mostly 'ter Vergaderinge' / single-token) on STEPS1 0.35 neighbours — not failed true openings. STEPS1 cosine still uncalibrated; neural bake-off stays deferred.
- **Decision:** Stop after TF-IDF → SW/DAG. No residual GysBERT (or other neural) pass on low-alignment leftovers. Keep deferred S1-neural-span-eval for a later GysBERT vs GloBERTise harness if chosen. Next classical work: calibrate STEPS1 threshold now that the span framework exists.
- **Reason:** Classical alignment already recovers exact boilerplate on true 18c openings; leftovers look like framing false positives. A residual neural pass would be a methods bake-off (Doel B), not completing usable spans (Doel A). Mirror STEPR4.

## 2026-10-18: S1 variable slots (proposer) after STEPS1 calibration

- **Context:** Requeste openings leave the proposer (and similar fills) after the boilerplate span ending at Requeste. Longer gappy templates or post-span rules can extract those later.
- **Decision:** Defer named variable-slot extraction (proposer, place, body) until after STEPS1 cosine threshold calibration. Keep opening_requeste_18c ending at Requeste for calibration; do not extend the template with semantic gaps in this phase.
- **Reason:** Calibration needs a stable fixed skeleton + span metrics; slot semantics are a separate cut and would mix framing noise with extraction design.

## 2026-10-19: STEPS1 freeze cosine threshold (18c)

- **Context:** STEPS3 on 1780 at hypothesis 0.35: 181 windows, cloud↔dag agree 0.33, driven by provincial ter Vergaderinge neighbours (align≈3). Re-frame + re-harvest at 0.40: 59 windows, align_mean≈7.12, cloud↔dag agree 0.61; 52/59 align≥6; 7 residual ter-only. Template opening_requeste_18c only; 1715/1670 slices barely fire this skeleton.
- **Decision:** Freeze DEFAULT_THRESHOLD at 0.40 for opening_requeste_18c (18c). Mark HYPOTHESIS_THRESHOLD=False. No peak-dedup rule. Do not treat 0.40 as a cross-century cut; 17c requeste templates stay deferred with their own calibration later.
- **Reason:** Cut removes most STEPS1 neighbour noise while keeping true IS ter Vergaderinge geleesen de Requeste openings. Earlier centuries need different templates, not this threshold.

## 2026-10-19: Multi-template registry prove-first gate

- **Context:** Scratch registry records in docs/proofs/multi-template-registry/ (opening_requeste_18c framing; dual-zone requeste/rapport; goedgevonden with outcome_signal=false; nlp_start_marker for <START> artefact; appointment_vergadering vs appointment_rekenkamer with discriminators=[institution]). Institution proof: 50 selected vs 50 harvest Rekenkamer+cue — sibling primary rekenkamer 28/50 (56%), selected FP 0/50, selected none 86%.
- **Decision:** PASS prove-first. Keep proposed formula_templates schema (including nlp_start_marker, outcome_signal, role_depends_on_place, discriminators). Appointment lookalikes: use institution/college as primary discriminator before separate TF-IDF per sibling. Schedule manifest+loader implementation as a later step; do not register scratch JSONL yet. Improve vergadering-target institution patterns before production subtype tagging.
- **Reason:** Schema encodes caveats without baking <START> or goedgevonden-as-approval into framing. Institution separates Rekenkamer siblings from R1 vergadering list with zero FP on the sample; incomplete recall/none-rate means discriminator is necessary but not yet sufficient alone.

## 2026-10-19: Formula template registry stub registered

- **Context:** Prove-first passed; next chosen step was manifest + loader stub (not STEPL2).
- **Decision:** Register `formula_templates` → `tests/fixtures/formula_templates.jsonl` (hot / explore). Loader: `formulation.formula_templates` (`load_templates`, `get_template`, role filter, schema validation). Include `unknown_residual` row. Do **not** register docs/proofs scratch JSONL. Do not harvest `institution_patterns` or rewire STEPS1 constants in this step.
- **Reason:** Promotes the gated schema into data_io without closing the catalogue or baking ORG pattern harvest into the stub.

## 2026-10-19: Appointment institution patterns from republic_ner ORG

- **Context:** Prove-first institution discriminator used hand regex. republic_ner_matching already has ORG-annotations (tag_text+inv) and ORG-entities; surfaces shift by period (e.g. 1626 Gecommitteerde Raden ter Admirt. vs 1780 Collegie ter Admiraliteit).
- **Decision:** When implementing appointment institution_patterns, harvest period/inventory-keyed variants from republic_ner ORG-annotations (+ link ORG-entities / instituten_lookup), not a single timeless regex. Keep discriminators=[institution] on appointment subtype registry rows.
- **Reason:** Same college changes wording across centuries; static patterns will miss 17c or 18c and inflate none-rate on selected.

## 2026-10-19: Registry: wide-to-narrow, recall first; open problems

- **Context:** Prove-first gate passed. User confirmed appointment discriminators=[institution] (later institution_patterns), not per-sibling TF-IDF yet. Further constraints: many templates unknown/rare; limited opening phrases branch into different templates (same for formulas); 18c known vs 17c thinner (republic_ner has some); imperfect resolution parsing especially 17c — templates may help re-separate later.
- **Decision:** Implement registry progressively: wide categories first, then finer subtypes; prioritise recall over precision. Keep unknown/residual slots. Represent branching (shared opener → subtypes by zone/institution/period). Defer 17c period map and using templates to fix misparsed resolutions to a later stage.
- **Reason:** Matches R1 sibling lesson and STEPS 18c-first cut; avoids closing the catalogue prematurely or baking precision models before coverage.

## 2026-10-19: NER committees are content subject, not template class

- **Context:** republic_ner ORG layer also covers committees/colleges. Useful for subject category of resolutions or hits. Risk of mixing that into formula_templates ids or treating committee label as template classification.
- **Decision:** Treat NER committee/ORG mentions as content/subject specification (optional later subject_hints or doc facets). Do not use them as formula-template classification. Institution discriminator for appointment siblings remains a structural subtype gate, distinct from general subject tagging.
- **Reason:** Template asks how language is shaped; committee asks what the business refers to. Collapsing them closes the catalogue wrongly and confuses framing with topic.

## 2026-10-19: STEPL2 closed gate — park L3+ harvest

- **Context:** Risk of a second R1-sized retrieval campaign (remainder score → review → selected list) with little gain for formula typology. User chose finish STEPL2 as a closed metric gate only.
- **Decision:** Run STEPL2 holdout on `missive_receipt_labelled` (char_wb 3–5 + LR, same as R1). Record metrics; **do not** open STEPL3 harvest or freeze `missive_receipt_selected` unless a later explicit decision. Track L parked after L2. Working type definition remains cue+seeds labelled table. Next sessions: registry wiring or institution_patterns.
- **Reason:** Holdout answers “is the cheap model usable?” without committing to full-corpus review. Cue-defined positives already carry the type; a completeness list is optional Doel A, not required for typology work.

## 2026-10-19: Template design questions as research north star

- **Context:** Limited catalogue coverage; user priority is how far templates get us (power/period, discrimination, formulas↔templates, harvest speed, further discrimination, detection feasibility) — with more questions expected.
- **Decision:** Keep durable list as **design questions** in [`docs/template-design-questions.md`](template-design-questions.md), not as a pipeline checklist. Prefer small empirical probes that answer a few questions; record settled answers here; leave unresolved items in that doc.
- **Reason:** Separates research framing from step execution so Track L/R ladders do not displace typology learning.

## 2026-10-19: Boundary STEPS1–3 defaults from formula_templates

- **Context:** Registry stub held `opening_requeste_18c` tokens + frozen 0.40, while `tfidf_windows` still hardcoded the same list. STEPL2 parked; user chose wire boundary→registry over institution_patterns.
- **Decision:** `resolve_framing_template` is the source for STEPS1–3 framing id/tokens/threshold (`default_opening_template`, `default_framing_threshold`, slot-cloud `default_template`). Module snapshots (`OPENING_TEMPLATE_18C`, `DEFAULT_THRESHOLD`) load from the registry at import. Do **not** harvest `institution_patterns` in this step; do not change the 0.40 cut.
- **Reason:** One edit to the framing row updates framing/scripts; avoids drift between fixture JSONL and boundary constants.

## 2026-10-19: STEPS6 institution_patterns bookkeeping (no full ORG harvest)

- **Context:** Next work after STEPS5 is period-keyed patterns from republic_ner ORG; full `ORG-annotations.json` is ~650MB on the 2TB warm drive. Session constrained to bookkeeping.
- **Decision:** Register `org_annotations`, `org_entities`, `institution_patterns` (fixture seeds + loader `formulation.institution_patterns` with year/inv filter and target→ORG-entity map). Do **not** stream-aggregate annotations or rewire the prove script in this step. Committees remain content/subject, not template ids.
- **Reason:** Unblocks schema/manifest/tests without a heavy harvest; harvest or prove-script wire-up is an explicit follow-up.

## 2026-10-19: Prove script uses institution_patterns (not templates)

- **Context:** STEPS6 registered fixture seeds; prove script still had inline regexes. User chose wire-up over full ORG stream-harvest.
- **Decision:** `scripts/prove_appointment_institution.py` loads surfaces via `formulation.institution_patterns` (`extract_institutions` / `primary_institution`). Appointment `formula_templates` keep `discriminators: ["institution"]` + `institution_targets` only — no org pattern strings in the template registry. Broad null-dated seeds added for prove recall until harvest period-keys them.
- **Reason:** One pattern store for the discriminator; templates stay structural ids, not NER surface lexicons.

## 2026-10-19: S6c stream-harvest ORG → institution_patterns

- **Context:** Full `ORG-annotations.json` (~650MB) must not be `json.load`ed; appointment targets already map to ORG-entity ids; inv needs year from inventory metadata.
- **Decision:** Stream the annotations array (`raw_decode`), filter to `TARGET_ORG_ENTITIES`, aggregate `(target, entity, inv, tag_text)` → `n`, attach `year_min`/`year_max` from `inventory_metadata`, write provenanced scratch `institution_patterns` (+ metrics) via `save_semi_structured`. Keep fixture as `institution_patterns_seeds`; merge unmapped seeds (e.g. `gecommitteerde_raaden`) by default. `load_patterns` falls back to seeds when scratch is absent. Do not put surfaces in `formula_templates`.
- **Reason:** Period-/inventory-keyed empirical spellings without memory blow-up; CI stays seed-backed; prove recall keeps seed-only targets until entity ids exist.

## 2026-10-19: S6d prove harvest vs seeds (appointment institution)

- **Context:** Locked sample (50 sibling + 50 selected; sibling pool = seed rekenkamer union). Seeds: 14 surfaces; harvest: 43 581 rows / 17 838 unique, year-scoped extract. Sibling `rekenkamer` rate 1.0 both arms (pool bias). Selected `none` 0.82 → 0.80. Harvest introduces 1 selected FP (`session-3812-num-136-resolution-10`, *Generaliteyts Reekenkaamer*); `pass_no_fp_rekenkamer_on_selected` fails on harvest.
- **Decision:** Keep harvest as default `institution_patterns` loader source. Do **not** use the unfiltered lexicon as the appointment discriminator gate. Next: tighten harvest with `--min-n` (or frequency cut) and re-run `--source compare` before changing prove defaults. Seeds stay the no-FP baseline.
- **Reason:** Lexicon size alone does not improve sibling discrimination; one OCR-ish rekenkamer surface breaks the FP gate for negligible `none` gain.

## 2026-10-19: STEPT1-period `--family all` + previous-period borrow

- **Context:** Full period-bin run for appointment, `ontfangen_start`, `requeste_start`. Ontfangen stable (diag 0.93–1.0, no recalibrate signals). Requeste early bins fine; **1750–74 n=2 / 1775–99 n=24** under `min_bin_n` and had **no later donor**, so borrow recorded `no_later_donor`.
- **Decision:** Prefer borrow from nearest **later** self-fit model; if none, fall back to nearest **earlier** (`borrowed_previous_period`). Re-run requeste/all to measure `recall_on_sparse`. Separately, widen requeste seed surfaces (`request_start` etc.) — late collapse is largely a candidate-harvest problem, not only borrow.
- **Reason:** User’s “use the period after” covers early thin bins; late opening collapse needs the symmetric previous-period donor plus better seeds.

## 2026-10-19: STEPT1a2 — advies formula type (STEPT1a-style)

- **Context:** STEPT1d left bags as fragments; next cheap step is another sharp A family. STEPT0 priors list `advies` first. Datasheet canonic is `"..."`; corpus/ES majority opener is **`geleesen het Advis van`**. Flag `formula_documents.advies` (~35k) is wording only — not gold (ES type ≈995 in 1705–1796).
- **Decision:** Mirror STEPT1a: `formulation/advies_formula_type.py` + `scripts/eval_advies_formula_type.py`; gold = ES `proposition_type=advies` → `advies_es_gold` (`--refresh-gold`); cue-window slot-cloud + DAG; wording baseline `advi[sz]`; N=500 negatives; provenanced `formula_type_advies_metrics` / `_scores`. Gates: overall recall ≥0.70, FP ≤0.05 judged, cloud accepts ≫0.
- **Full eval PASS:** recall **0.762** (n=950); FP **0.034** (17/500); cloud **686/895**; cut=4.12; Δ vs wording −0.027. Pre-1731 softer (0.60) noted, no family floor. Accept advies as formula type; next presence-bag refresh or another A / sieve.
- **Reason:** Same measured A schema as appointment on the next sharp sparse family; independent ES gold avoids circular flag detectors.

## 2026-10-20: STEPT1k — requeste opener accepted (A); FP gate questioned

- **Context:** STEPT1j left requeste as the largest unexplained skeleton in the empty band. Measure the opener as a formula type on ES `rekest` gold, same schema as STEPT1a2 advies.
- **Decision:** Accept `requeste_geleesen` as **A** on the slot-cloud/DAG baseline (method parity with appointment/advies). Recall **0.8983** (n=74205) PASS; cloud accepts 37,939 PASS; FP **0.206** (103/500) FAIL — accepted as a diagnosed limitation, not fixed, and not grounds for swapping method for one type.
- **FP diagnosis (scratch):** not calibration (no cut clears both gates; FP 0.042 only at recall 0.631). Not generic slots (single-slot ablation raised recall *and* FP: 0.880/0.136 vs 0.645/0.076). Not length (length-only barely separates; proba–length corr ~0 on random sample). Not day-order (only testable 1626–30, no overlap with 1705–1796). **Is** decision-type: FP 0.340 for negatives carrying `goedgevonden`-family markers vs 0.117 without; 66% of FPs from the 40% that have them.
- **Method-comparison caveat:** TF-IDF+LR got nearer both gates (0.79/0.054 @0.8) but answers a *different question* — order-blind document topic (≈ re-deriving the ES label) vs. ordered span presence. Both score the full document, so this is not a "more text wins" result. Treat as an upper bound on class separability, not evidence against the opener definition.
- **Net-then-sieve refuted for this signal pair:** TF-IDF-net + DAG-sieve, 7×6 cut grid — no pair clears both gates and the sieve adds nothing (TF-IDF@0.8 alone 0.791/0.054 → +DAG@4.5 0.787/0.054). Stages are redundant (same vocabulary, ordered vs. order-blind), not complementary. `candidate-then-structure` only pays when the two stages see different evidence.
- **Call:** Next = STEPT1l subtype under requeste+. **Open first:** is ≤0.05 FP reachable against ES gold at all? Four signals floor at 0.04–0.05 only below the 0.70 recall gate — the pattern expected if some "negatives" are requeste-bearing resolutions ES never typed. Cheapest test is hand-reading ~20–30 FPs, not more compute.
- **Reason:** Negatives are defined solely by ES label absence, and `proposition_type` was an administrative construction unevenly maintained; a gate built on it may measure label completeness as much as model error.

## 2026-10-20: STEPT1j2 — empty-band R1/L1 retrieval probe

- **Context:** User: prior TF-IDF type searches (R1/L1) should inform empty fingerprints. Hypothesis: contrastive vectors triage empty better than within-band clustering.
- **Decision:** `formulation/empty_band_retrieval.py` + `scripts/run_empty_band_retrieval_probe.py` — join frozen R1 harvest; L1 `fit_on_all_labelled` + score empty; P-bands × ES type. Provenanced `empty_band_retrieval_*`. Not L3; not new types.
- **1780 NOTES (PASS):** R1 **99.7% low** (med 0.022); L1 **3 high** (all missive) / 45 grey / 1281 low; empty missive soft grey (p90 0.63) but not high flood; rekest low on both. Confirms empty ≠ aanstelling/L1; fingerprints were the wrong instrument for that question.
- **Call:** Next = **requeste/rekest seeded** contrast or presence — not tighter fp clustering, not L3.
- **Reason:** Same lesson as R1/L1 design: named class needs seeds + overig, not residue clustering.

## 2026-10-20: STEPT1j — empty-band characterisation (+ fp_cut sweep)

- **Context:** STEPT1i left undecided = empty (1329); `fp_cut=0.15` one mass. Need structural characterisation before any blueprint mint; optional tighter fingerprint cuts.
- **Decision:** `formulation/empty_band.py` + `scripts/run_empty_band_characterisation.py` — join STEPT1e partition (no ES remget); type mix / length / flag catalogue; fingerprint similarity fit once, re-cluster at cuts `0.15/0.30/0.45/0.60` (operating labels @0.45); provenanced `empty_band_*`. No blueprint promotion.
- **1780 NOTES (PASS):** empty **1329**; **rekest 700** (0.53) + missive/voordracht/rapport/conclusie pockets; ontfangen_present 0; `goedgevonden`/`gedelibereert` high on rekest; conclusie sharp (`handen` 0.70). fp: 0.15 one mass; **0.45** share_largest 0.068 but 587 singletons — sample strata only. Next = **requeste/rekest opener** presence probe (or conclusie+handen) — not mint from empty n / clusters.
- **Reason:** Empty is multi-pocket, not one type; fingerprints triage sampling; largest unexplained skeleton is requeste.

## 2026-10-20: STEPT1i — formula-graph blueprints / derivatives / fingerprints

- **Context:** Unknown formulas are invisible until named; templates are combinations. Exact bags proliferate. User: object = resolution formula-graph patterns; fingerprints for variation vs different structure / derivative vs novel once blueprints exist. NER ALIGNED_TO fingerprint is the wrong instrument.
- **Decision:** STEPT1i measures (1) `accepted_core` proto-blueprints + within-core derivative mass + undecided (`empty`∪`novel_tail`); (2) content fingerprints on undecided (NN/clusters + max_sim to proto exemplars). STEPT1h cover-unknown stays auxiliary. No blueprint promotion.
- **1780 NOTES (PASS):** proto-blueprints **2** (advies 74 / appointment 28; dominant bag ~0.92); filler 1365; **empty 1329**; novel_tail **0**; only 6 exact bags. Fingerprint `fp_cut=0.15` → **one mass** (share 0.999); derivative_score p50 0.18. Next = characterise empty (T1j) and/or tighter fp cut — not mint blueprints.
- **Reason:** Thin presence inventory → no novel combinations yet; empty is the real undecided pool; loose fp cut does not split structure vs variation.

## 2026-10-20: Unknown-first doctrine + STEPT1h PASS (1780)

- **Context:** User wants resolution triage by **unknown likeliness**, then content characterisation — up-front classification from incomplete expert knowledge only rediscovers what was brought in. STEPT1g showed residual = filler mass + sparse appointment; next was not another named A from thin reading alone.
- **Decision:** Lock spine in [`plans/milestones/T1-unknown-first.md`](../plans/milestones/T1-unknown-first.md): known cover → unknown-likeliness → (fingerprints) → content characterisation → task-template promotion. STEPT1h: cover = L1 / R1 / appointment present / advies present∨gold; score `1 − hits/axes`; provenanced `resolution_unknown_*`.
- **1780 NOTES (PASS):** universe **2796**; high-unknown **2015** (0.721); cover L1 674 / R1 31 / appointment 28 / advies 76. No ≥3-axis hits. Band large because cover is thin — expected. Next = fingerprint or stratified *slice* of high-unknown, not a type from n=2015.
- **Reason:** Discovery order matches incomplete knowledge; formulas stay production support; templates become SG-task packages only after characterisation.

## 2026-10-20: STEPT1g — decisionful residual structure

- **Context:** User: STEPT1f’s info half remeasured the obvious L1 template; **probability is not typology**; formula types may have hit rates but that does not rank usefulness (ubiquitous = filler / no signal); interesting stuff is sparse; open question = structure inside ontfangen+ \\ L1.
- **Decision:** `formulation/residual_structure.py` + `scripts/run_residual_structure_probe.py` — pockets + combo catalogue + bags + stratified text sample. Provenanced `residual_structure_metrics` / `_scores` / `_sample`. No subtype ids from rates. Not STEPT1e1.
- **1780 NOTES (PASS):** residual missive **656**; solo `ontfangen_start` bag **624** (filler star); appointment pocket **26** ≈ R1 (covered); 177 flag-set combos, top-5 share 0.36 (do not mint types from head). Sample shapes: filler receipt→deliberate; creditif/install (accepted A); sparse unexplained nominations + procedural enclosures.
- **Call:** Next = named **sparse** unexplained shape (lean: provincial nomination under missive) or park Track T. Not e1; not “decisionful missive” from high-n combos.
- **Reason:** Closes the residual question with inventory + reading; frequency is not a usefulness or typology ranking.

## 2026-10-20: STEPT1f — missive subtype characterisation (circular half noted)

- **Context:** STEPT1-map named missive as not one kind structurally (info/null vs decisionful under ontfangen+). Default lean: characterise those subtypes before any A or e1 sieve.
- **Decision:** `formulation/missive_subtype_profile.py` + `scripts/run_missive_subtype_profile.py`; reuse STEPT1e scores; kind filter ES missive; subtypes = L1 `info_receipt` vs `decisionful_residual`; length from `resolutions_flat` + flag rates as characteristics. Provenanced `missive_subtype_metrics` / `_scores`. Not formula types; e1 stays parked.
- **1780 NOTES:** info 641 / decisionful 656; words med **37** vs **188.5**; flag contrast strong. **Caveat:** `info_receipt` = L1 labelled set, whose cues *are* the advertentie/geen_resolutie skeleton — that half is circular remeasurement of the obvious template. The open question was the **decisionful residual**, not L1.
- **Call (superseded):** Was rekest next; superseded by STEPT1g residual structure probe.
- **Reason:** Length split and residual focus still useful; do not treat L1 flag rates as typology evidence.

## 2026-10-20: STEPT1-map — typology before classify

- **Context:** Detectors and partitions (appointment, advies, ontfangen±, flags) outran a clear object of typing. User: without typology and characteristics, no classification. STEPT1e1 flag sieve would classify surfaces. Schemes sample is the user’s **hypothetical** sketch — resolutions may not fit fully, should usually fit partially.
- **Decision:** Docs-only map ([`STEPT1-typology-formula-map.md`](proofs/multi-template-registry/STEPT1-typology-formula-map.md)): keep resolution kind / characteristics / discourse role / formula evidence as distinct layers; schemes×STEPT0×measured crosswalk; inventory (accepted / provisional / scheme-only / overloaded). Schemes = hypothesis, not closed checklist; partial/non-fit revises the sketch. **Park STEPT1e1.** No new A until a characterisation gap from the map is chosen.
- **Call:** Next = characterisation gap (default lean: missive subtypes under ontfangen+), not flag bucketing. *(Superseded by STEPT1f PASS.)*
- **Reason:** Formula detectors support kinds/roles; they are not the typology. Map is the gate.

## 2026-10-20: STEPT1e — partition probe (ES + flags on ontfangen±)

- **Context:** STEPT1e0 left typology gaps: ES mix on ontfangen±, flag rates, residual after L1 (~724 ids). Discourse skeleton in play: opening → (expose) → decision → (defer) → (execution).
- **Decision:** Implement STEPT1e as a focused probe — `formulation/ontfangen_partition.py` + `scripts/run_ontfangen_partition_probe.py`; lean ES `mget` + `formula_documents` join + known-set tags; provenanced `ontfangen_partition_metrics` / `_scores`. Ontfangen stays provisional root/partition.
- **1780 NOTES (PASS):** P(missive\|ont+) **0.928**, P(ont+\|missive) **0.880**; residual **724** still 91% missive but decision-flag shaped (`gedelibereert`/`goedgevonden`) vs L1 null path (`geen_resolutie`+`advertentie`). Keep **opening/partition** + **decision-stage** axes. Flags = boilerplate surfaces, not outcomes; no ordered discourse spans yet.
- **Call (superseded by STEPT1-map):** Was STEPT1e1; now park e1 — typology map before classify.
- **Reason:** Closes e0 gaps with one-year measurement; residual is decisionful under the same opener, but flag sieves wait on kind characterisation.

## 2026-10-20: STEPT1e0 — ontfangen inventory before typology probe

- **Context:** T1d star + concern that formula typology needs attention. Temptation was another sparse A (rapport/…); better first inventory the composition-root population from existing 1780 artifacts.
- **Decision:** STEPT1e0 NOTES only (no new scorer, no ES): presence counts (ontfangen+ **1397/2796**), solo bags, zone, graph smoke, cheap joins (L1 673/674 under root but only ~48% of ontfangen+; R1 27/31; advies gold ∩ root **0**). Gap list: ES mix on partition, flag rates, residual after L1. **Call: STEPT1e partition probe next; no new A until then.**
- **Reason:** Half the root is unexplained by L1; datasheet/STEPT0 missive priors are untested against ontfangen±; inventory is cheaper than a wrong A or an unscoped ES join.

## 2026-10-20: STEPT1d — composition graph (co-presence)

- **Context:** T1d order parked (soft constraint only; bags still fragments). Composition should be a **graph**: nodes = types × IDF presence weight; arcs = co-presence directed by `mid_norm`. Not Track S `align_dag`. `ontfangen_start` = composition root/partition, not IDF “noise.”
- **Decision:** `formulation/formula_type_composition_graph.py` + `scripts/run_formula_type_composition_graph.py`; provenanced `formula_type_composition_graph_metrics` / `_scores`. Cheap gate: 1780 smoke `n_accepted_accepted_edges` + `graph_shape` (`provisional_root_star` vs `accepted_co_presence`). `--period-bins` only if smoke leaves dynamics open. Order CLI kept but not the composition definition.
- **1780 NOTES (PASS, `--limit 200`):** `n_accepted_accepted_edges=0`, `graph_shape=provisional_root_star` (2 spokes: ontfangen→advies, ontfangen→appointment; no advies↔appointment). **Skip `--period-bins`.** Next: another A family or sieve residual.
- **Reason:** Co-presence + relative presence is the right composition unit once sequences failed; period matrix is optional cost after the star hypothesis is tested on one year.

## 2026-10-19: STEPT1d — order / composition by start_idx

- **Context:** STEPT1c PASS — zone separates (ontfangen@opening; appointment@close) but bags remain fragments for template composition. STEPT1 §C next cheap probe is **order** (A before B).
- **Decision:** `formulation/formula_type_order.py` + `scripts/run_formula_type_order.py`: reuse T1c span scoring; per-id sort presents by `start_idx`; provenanced `formula_type_order_scores` / `_metrics` (top ordered sequences vs bags, expected opening→appointment rates, order-vs-bag diversity). Openings still provisional.
- **1780 NOTES (PASS):** n_multi=26 (0.9%); ontfangen→appointment **26/26**; only one multi bag with **one** distinct order — order does not beat bags/zone. Keep order as a soft constraint on rare multi; **stop** further sequence features. Next: another sharp A family or sieve residual.
- **Reason:** Cheapest test of sequenced composition without new detectors; T1c spans already paid for; trivial fixed order is not a template inventory.

## 2026-10-19: STEPT1c — position / zone from DAG spans

- **Context:** STEPT1b judged 1780 presence bags as **fragments** (mostly lone `ontfangen_start`); STEPT1 §C asks whether position / zone is required before templates.
- **Decision:** `formulation/formula_type_position.py` + `scripts/run_formula_type_position.py`: same models/cuts as T1b; record DAG `start_idx`/`end_idx`; `mid_norm` tertiles → `opening` / `body` / `close`; provenanced `formula_type_position_scores` + `_metrics` (per-type zone mix, `frac_in_expected_zone`, zone-tagged bags). Openings still provisional. No ES `evidence` zones in this step.
- **1780 NOTES (PASS):** ontfangen **99.6%** opening (mid_norm 0.027); appointment **0%** opening / **96%** close (mid_norm 0.90 — prior `body` wrong → set expected to `close`); zone-tagged multi bags ≈ appointment@close + ontfangen@opening (25/26). Position is a **discriminator** worth keeping on registry/scoring; bags remain fragments for template composition → next order/composition or another A family.
- **Reason:** Cheapest test of `role_depends_on_place` without new detectors; token mid-span reuses Track S alignment already paid for in presence scoring.

## 2026-10-19: STEPT1b — presence scoring + popularity bags

- **Context:** STEPT1a accepted appointment; STEPT1 §B needs corpus presence scores with IDF-style popularity weights and a judgment on whether multi-type bags look like templates.
- **Decision:** `formulation/formula_type_presence.py` + `scripts/run_formula_type_presence.py`: default POC year **1780**; freeze appointment cut from `formula_type_appointment_metrics` when present; optional provisional `ontfangen_start` / `requeste_start` for bag exploration only; provenanced `formula_type_presence_scores` (id×type, `score_weighted`) + `_metrics` (hit rates, popularity, bag size histogram + top patterns). Openings are **not** accepted types. User runs full year before NOTES judgment (templates vs fragments → STEPT1c).
- **Reason:** Weighted multi-type bags are the cheapest way to see whether presence alone composes; year POC keeps cost bounded; freezing T1a cut avoids re-litigating the appointment gate.

## 2026-10-19: T1a-fix — welkom cue-window bootstrap (full re-eval PASS)

- **Context:** STEPT1a PASS left welkom cloud at **0/2564** accepts. Root cause: datasheet canonic `wordt hij welkom geheten` ≠ corpus majority `is den selven verwelkomt,`; trailing punct on cue tokens; full texts as “hits”.
- **Decision:** Empirical canonic `is den selven verwelkomt` + ±6-token cue windows + punct-stripped align tokens + seed inject on `verwelkomt`/`selven`. Full re-eval: welkom **2251/2313** accepts; pre **0.816** / post **0.832** / FP **0**; period appointment diags **0.81–0.90**, no recalibrate signals. **Clear the 0-accept caveat.** Record side-effect: p20 cut rises to **6.0** (perfect welkom); sessie max ≈3 never clears — scoring is welkom-led; overall recall 0.829 trails wording by ~0.12. Optional later: dual-cut / length-normalize scores.
- **Reason:** Cloud now learns real OCR variants; gates still beat the 0.235 floor; stricter cut is a calibration consequence of a stronger welkom template, not a bootstrap failure.

## 2026-10-19: STEPT1a + STEPT1-period appointment eval (full run)

- **Context:** User ran `eval_appointment_formula_type.py` and `eval_formula_period_bins.py --family appointment` (not fixture).
- **Decision:** **PASS** STEPT1a gates: pre-1731 model recall 0.861 ≫ 0.235 floor; post-1731 0.937; FP 0.018 on N=500. **PASS** period-bin self-diagonals (0.86–0.95); no adjacent-backward cell under 0.5. Record caveat: welkom cloud bootstrap **accepted 0/2564** hits — live scorer is sessie-led + seed variants; fix windowed/looser welkom bootstrap before claiming welkom-variant learning. Mid-bin soft drift: 1750–74 model on 1725–49 data recall 0.613 (Δ −0.29). `formula_documents_compare` deltas are **not** same-universe (selected vs full matrix); use docs for corpus flag rarity / welkom=0 early, not as a fair bake-off.
- **Reason:** Measured bars met; caveats are explicit so next work targets welkom bootstrap and optional mid-century subtype, not re-litigating the floor test.

## 2026-10-19: STEPT1-period — family × 25y bins + measured recalibration

- **Context:** Formulas change gradually; opening-only / single-period models miss evolution. User wants independent sub-templates per family and 25-year comparison, with measurements.
- **Decision:** `formulation/formula_period_bins.py` + `scripts/eval_formula_period_bins.py`: per family (`appointment_installation`, `ontfangen_start`, `requeste_start`), fit slot-cloud/DAG per 25y bin (origin 1700), freeze in-bin p20 cut, write full **cross-bin recall matrix** with `delta_vs_data_self` and `recalibrate_signal` (adjacent backward recall < 0.5). Sparse bins (`0 < n < min_bin_n`) **borrow the nearest later self-fit model** (`borrow_from_next_period`, measured `recall_on_sparse`). Each summary includes **`formula_documents_compare`**: per-bin flag rates on resolution rows (`welkom`/`sessie`, etc.) vs model diagonal recall + deltas. Provenanced `formula_period_bin_metrics` / `_matrix`. Popularity weight from mean diagonal recall. Openings use capped substring candidate pools (seeds, not types).
- **Reason:** Makes gradual drift an evaluated claim (numbers), not a narrative; keeps families separate so one opening’s drift does not smear another; thin early opening pools still get a recalibration path from the following period; documents matrix is the wording-matcher baseline to beat or explain.

## 2026-10-19: STEPT1a — measured appointment formula type (+ popularity weight)

- **Context:** STEPT1 reframed: define formula types by slot-cloud/DAG (not regex); measure recall vs `aanstelling_selected` pre/post-1731 against wording baselines; explicit N=500 negatives. Ubiquitous formulas (*goedgevonden*, etc.) are uninformative for typology ranking.
- **Decision:** Ship `scripts/eval_appointment_formula_type.py` + `formulation/appointment_formula_type.py`: welkom+sessie clouds, DAG max score, p20-holdout cut, stratified negatives, provenanced `formula_type_appointment_metrics` / `_scores`. Report IDF-style **popularity** block: ``weight = log(1/clip(p))`` with ``p`` = hit rate on negatives at the cut; ``score_weighted = score * weight``. Single-family acceptance still uses raw cut; weighted scores reserved for multi-type ranking/composition (STEPT1b+). User runs full eval before pass/fail NOTES.
- **Reason:** Pre-1731 has no `welkom` wording — need measured cloud/DAG vs `sessie` floor; popularity punishment encodes STEPT0 lift insight (near-universal flags mean little) without changing the appointment gate.

## 2026-10-19: STEPT0 — provisional 18c proposition-type structural profile

- **Context:** Scoping surfaced two unused sources: `formula_documents` (309 181-row boolean formula-family flag matrix, 1705–1796, registered at a dead `republic_clean` path — recovered from `notebook-archive`) and the ES `full_resolutions` index's `metadata.proposition_type`/`metadata.resolution_type`/`evidence` fields, none of which `republic_es.py` requested. ES labels only the opening side (no outcome label, by design — avoids a decision-content claim); `formula_documents` carries the closing/outcome flags but stops at 1705. Composition (population proportions) and characterisation (per-type structural detail) are different questions: a strictly proportional sample vanishes the tail (e.g. `paspoort` at 0.1% of a year), so they are computed separately.
- **Decision:** New Track T (typology), one step (STEPT0): `formulation/typology_sample.py` computes (a) full-population `proposition_type` composition via ES terms agg (no sampling error) and (b) a floored-proportional characterisation sample (`DEFAULT_FLOOR=30`, `DEFAULT_SAMPLE_TOTAL=1000`), joined to `formula_documents` outcome flags on `(session_date, resolution_index)` — the only key present on both sides (ES/`resolutions_flat` key on inventory `num`; `formula_documents` doc_id is date-based with `num` constant at 1). `scripts/run_typology_profile.py` defaults to `POC_YEAR=1780` (shared with STEPS1/Track L) for a first provisional pass; `--full-18c` or explicit `--year-min`/`--year-max` widens. Output: `typology_structural_profile` (per-`proposition_type` label-zone medians/IQR from ES `evidence` offsets, length stats, `formula_documents` flag rates). This is a descriptive profile, not a model, and not a final typology — a provisional one is the explicit goal.
- **First run (1780, seed 20261019, 14 proposition_type values, 3 134 population resolutions, 1 063 sampled):** confirms the join and pipeline work end-to-end. `missive` (pop 1 489, 47.5%) and `rekest` (pop 761, 24.3%) structurally separate cleanly — e.g. `proposition_body` sits at median normalised offset 1.0 for `missive` vs ~0.40 for `rekest`/`rapport`/`voordracht`/`memorie`. Outcome-join coverage varies sharply by type: 99.8–100% for `missive`/`voordracht`/`memorie`/`advies`/`resolutie`, but only 15.6% for `onbekend` (460 resolutions, 14.7% of the year) — **expected, not a bug to chase:** `onbekend` resolutions were already unclassifiable upstream (that's why ES couldn't assign them a `proposition_type`), so low closing-formula coverage is consistent, not a signal of a join problem. Leave as-is.
- **Known caveat (flagged by user, not inferred):** `praeside_start`/`praesentibus_start` in `formula_documents` mark presidium/attendance-list openers; their small nonzero rate on resolution rows reflects upstream session-boundary parsing leakage (attendance-list text attached to an adjacent resolution), not real resolution content. Documented in `typology_sample.py`'s module docstring; do not read these two flags as resolution signal.
- **Bug fixed during this step:** the first implementation's `join_outcome_flags` lost all 31 real `formula_documents` flags after the left-merge — pandas upcasts bool columns to `object` on introduced NaN, and the downstream `dtype == bool` re-detection in `build_profile_records` silently picked up only the unrelated `outcome_joined` marker column instead. Fixed by casting joined flag columns to pandas nullable `boolean` dtype and passing the flag-column list explicitly via `joined.attrs["flag_columns"]` rather than re-deriving it from post-merge dtypes. The CLI's closing preview (`records[0]` only, always `missive` since composition is sorted by population) was also replaced with a compact per-type summary table — the underlying per-type `flag_rates`/`label_zones` were already correct in the saved jsonl; only the console preview was misleading.
- **Reason:** A provisional typology beats none; cheap single-year-first POC before any wider claim; population composition must never be read off the floored sample.

## 2026-10-21: Re-pin ES resolutions_index — id-keyed label joins were mislabelling ~31% of gold

- **Context:** User spotted that two `aanstelling_labelled` gold "appointments" are not appointments (a resolution-resumption and an advertentie receipt) and suggested URN drift against an older index. Checking the same id across index generations showed worse: resolution ids are **not stable across builds**. `session-3344-num-110-resolution-4` carries three different resolutions in `2024-11-10` / `2025-02-20` / `2025-03-15+` (onbekend missive → advertentie missive → rekest). On 150 random 1780 ids, `resolutions_flat` text matches `full_resolutions-2025-02-20` **150/150 (100%)** but the configured `full_resolutions-2026-03-25` only **101/146 (69%)**, with 4 ids absent.
- **Decision:** Pin `[elasticsearch].resolutions_index` to **`full_resolutions-2025-02-20`** (the generation `resolutions_flat` actually is), in `data_manifest.toml` and as the `republic_es` dataclass/loader default, with a comment forbidding a bump without re-checking match rate. Verified after the change: 150/150 (100%).
- **Consequence — prior measurements are contaminated, not wrong-by-method:** every `*_es_gold` set is built by fetching ids from the ES index and joining text from flat by id, so ~31% of rows had a label attached to the wrong text. Affects `rekest_es_gold` (74,205), `advies_es_gold`, `missive_es_gold` (177,045) and every metric derived from them: requeste 0.898 recall / 0.206 FP (STEPT1k), advies 0.762 / 0.034 (STEPT1a2), missive 0.887 / 0.11 (STEPT1n). **All three must be re-fetched and re-measured before their numbers are quoted again.**
- **Reason this matters beyond bookkeeping:** three separate steps hit an unreachable ≤0.05 FP floor and each explained it differently — decision-type confound (T1k), ES label incompleteness (T1k2), ontfangen+/missive boundary fuzziness (T1n). A 31% join mismatch produces exactly that signature. T1k2's hand-read found 41% of sampled FPs were genuine requeste-openers "ES had not labelled", which is what a mismatched join looks like from the inside; its conclusion that the gate is unreachable may be an artifact. Also the same root cause as the `aanstelling_gold_relocations` 18-URN patch, which treated a pervasive problem as 18 rows.

## 2026-10-21: Clean stratified recheck after the re-pin — gold contamination confirmed; FP gate left undecided

- **Context:** Rather than re-fetch 74k–177k rows per type, `scripts/recheck_es_gold_sample.py` samples 15 ES-labelled ids per year from the *pinned* index, joins flat text (same generation ⇒ exact), and verifies each sampled negative's label individually against that index. Existing frozen clouds/cuts are reused, so this isolates the gold-contamination effect rather than a retrained pipeline.
- **Result (recall / FP, clean vs stale):** requeste **0.995 / 0.171** vs 0.898 / 0.206 (n=1380, neg 374); advies **0.920 / 0.024** vs 0.762 / 0.034 (n=840, neg 499); missive **0.988 / 0.018** vs 0.887 / 0.110 (n=1380, neg 226). Wilson 95% CIs: missive FP 0.007–0.045, advies FP 0.014–0.042, requeste FP 0.136–0.213.
- **Cause of the FP collapse:** of 500 flat-sampled negatives, **274 were actually labelled `missive`** by the pinned index (126 for `rekest`, 1 for `advies`). The old negative pools excluded ids drawn from the mismatched gold set, so hundreds of genuine positives sat in the negative pool and every correct detection counted as a false positive.
- **Decision:** Gold contamination is confirmed and large: the stale negative pools held hundreds of genuine positives, so the pre-re-pin FP figures measured the join, not the model. Recall is solid on clean gold for all three (0.92–0.995) and the T1n/T1o promotions hold. STEPT1k2's "gate unreachable" conclusion is **withdrawn** — a 29-case hand-read cannot support it either way. `requeste_geleesen` fails the gate at 0.171 with a CI (0.136–0.213) well clear of 0.05, so STEPT1k's decision-type confound stands as real signal.
- **Not decided — whether the ≤0.05 FP gate is reachable.** An earlier revision of this entry claimed missive (0.018) and advies (0.024) "pass it outright". **Withdrawn as underpowered** (amended 2026-10-21 during STEPT1q): those rates rest on 4/226 and ~12/499 events, a Wilson half-width of ±0.026 against a 0.05 gate. A STEPT1q re-measurement with the same frozen cloud and cut, differing only in which negatives were drawn, gave missive FP **0.0575 (13/226)** instead of 0.018 — Fisher exact p=0.045 against the figure above. Two draws that far apart mean n≈226 cannot resolve this gate. Needs ~2,000 clean negatives (±0.009) before any pass/fail is recorded.
- **Reason:** a stratified sample with CIs cheaply answers "did the numbers move?", which is what this entry establishes. It does not answer "does the model clear a 0.05 threshold" — that needs an order of magnitude more negatives. A gate verdict resting on a handful of events is not worth recording as a decision; this project has now been burned twice that way (STEPT1k2's 29-case hand-read, and the figures above). The full re-fetch is also still owed before these datasets are used downstream.
