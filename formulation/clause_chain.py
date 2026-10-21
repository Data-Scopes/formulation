"""STEPT1p: clause-level chains instead of coarse type bags.

A clause node is one alignment-detected skeleton with its own cloud and cut.
`appointment_installation` is decollapsed into its two existing clouds (welkom,
sessie), whose scores `appointment_formula_type.score_text` currently throws
away via ``max()``. Chains are ordered by span start, so order and
required-vs-optional become measurable instead of declared.

Form only: no institution / NER / topical markers enter the vocabulary.
See docs/resolution-graph-design.md.
"""

from __future__ import annotations

from collections import Counter
from itertools import permutations
from typing import Any

import numpy as np
import pandas as pd

from formulation.aanstelling import LABEL_AANSTELLING
from formulation.appointment_formula_type import (
    FORMULA_TYPE_ID as APPOINTMENT_ID,
    HOLDOUT_FRAC,
    RNG,
    YEAR_MAX,
    YEAR_MIN,
    align_tokenize,
    build_appointment_clouds,
    load_selected_18c,
    split_bootstrap_holdout,
)
from formulation.boundary.align_dag import align_dag
from formulation.boundary.slot_cloud import cloud_variant_lists
from formulation.boundary.tfidf_windows import POC_YEAR
from formulation.formula_type_position import zone_from_span

DEFAULT_YEAR = POC_YEAR
DEFAULT_MIN_SUPPORT = 5
# Clause ids are form labels, not type labels: the two appointment clauses are
# siblings here, not one atomic appointment node.
CLAUSE_WELKOM = "welkom"
CLAUSE_SESSIE = "sessie"
APPOINTMENT_CLAUSES = (CLAUSE_WELKOM, CLAUSE_SESSIE)

__all__ = (
    "APPOINTMENT_CLAUSES",
    "CLAUSE_SESSIE",
    "CLAUSE_WELKOM",
    "DEFAULT_MIN_SUPPORT",
    "DEFAULT_YEAR",
    "bag_of",
    "build_appointment_clause_specs",
    "build_chain_frame",
    "chain_of",
    "detect_clauses",
    "fixture_clause_specs",
    "fixture_year_frame",
    "load_gold_appointment_frame",
    "summarize_clause_chains",
)


def _clause_spec(
    clause_id: str, cloud: dict[str, Any], cut: float, *, source: str
) -> dict[str, Any]:
    return {
        "clause_id": str(clause_id),
        "cloud": cloud,
        "cut": float(cut),
        "variant_lists": cloud.get("variant_lists") or cloud_variant_lists(cloud),
        "optional_slots": list(cloud.get("optional_slots") or []),
        "source": str(source),
    }


def build_appointment_clause_specs(
    *,
    cut: float,
    random_state: int = RNG,
    per_clause_cuts: bool = False,
) -> list[dict[str, Any]]:
    """Welkom + sessie as two separate clause nodes from the STEPT1a clouds.

    Same bootstrap as `fit_appointment_presence_model`; the only change is that
    the two clouds are kept apart instead of collapsed by ``max()``.

    ``per_clause_cuts=False`` makes both clauses inherit the frozen STEPT1a
    cut. That cut was calibrated on ``max(welkom, sessie)``, so per clause it
    is strictly harder than the type-level test ever was: DECISIONS records
    "p20 cut rises to 6.0 (perfect welkom); sessie max ~3 never clears". With
    the shared cut, sessie cannot fire and no 2-clause chain can exist — the
    first STEPT1p run measured exactly that (welkom 28/2796, sessie 0/2796).

    ``per_clause_cuts=True`` calibrates each clause on its *own* holdout score
    distribution with the same p20 rule. This does **not** touch
    `appointment_installation`'s frozen type-level cut, which stays 6.0
    everywhere else; it calibrates the two new clause nodes as their own
    objects.
    """
    gold = load_selected_18c()
    boot, hold = split_bootstrap_holdout(
        gold, holdout_frac=HOLDOUT_FRAC, random_state=random_state
    )
    welkom, sessie, _notes = build_appointment_clouds(
        boot["resolutions_text"].astype(str).tolist(),
        year_min=YEAR_MIN,
        year_max=YEAR_MAX,
    )
    specs = [
        _clause_spec(CLAUSE_WELKOM, welkom, cut, source=f"{APPOINTMENT_ID}_welkom"),
        _clause_spec(CLAUSE_SESSIE, sessie, cut, source=f"{APPOINTMENT_ID}_sessie"),
    ]
    if not per_clause_cuts:
        for spec in specs:
            spec["cut_rule"] = "frozen_stept1a_type_level_shared"
        return specs

    from formulation.appointment_formula_type import FALLBACK_CUT, calibrate_cut

    hold_texts = hold["resolutions_text"].astype(str).tolist()
    for spec in specs:
        scores = [
            float(
                align_dag(
                    spec["variant_lists"],
                    align_tokenize(t),
                    optional_slots=spec["optional_slots"],
                ).score
            )
            for t in hold_texts
        ]
        spec["cut"] = float(calibrate_cut(scores, fallback=FALLBACK_CUT))
        spec["cut_rule"] = "p20_own_clause_holdout"
        spec["holdout_score_mean"] = (
            round(float(np.mean(scores)), 4) if scores else None
        )
    return specs


def detect_clauses(
    text: str,
    clause_specs: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Align every clause cloud separately; keep per-clause span and zone.

    Returns one row per clause (present or not) so absence is explicit.
    """
    tokens = align_tokenize(str(text or ""))
    n_tokens = len(tokens)
    out: list[dict[str, Any]] = []
    for spec in clause_specs:
        res = align_dag(
            spec["variant_lists"], tokens, optional_slots=spec["optional_slots"]
        )
        score = float(res.score)
        cut = float(spec["cut"])
        start_idx = int(res.start_idx)
        end_idx = int(res.end_idx)
        mid_norm = (
            ((start_idx + end_idx) / 2.0 / n_tokens) if n_tokens > 0 else None
        )
        out.append(
            {
                "clause_id": spec["clause_id"],
                "score": round(score, 4),
                "cut": cut,
                "present": bool(score >= cut),
                "start_idx": start_idx,
                "end_idx": end_idx,
                "mid_norm": round(mid_norm, 4) if mid_norm is not None else None,
                "zone": zone_from_span(start_idx, end_idx, n_tokens),
                "n_tokens": n_tokens,
            }
        )
    return out


def chain_of(hits: list[dict[str, Any]]) -> tuple[str, ...]:
    """Ordered clause ids for the present clauses, sorted by span start.

    Ties (identical start_idx) break on clause_id so the chain is total and
    reproducible — a tie means the spans overlap, which is itself worth
    counting (see `summarize_clause_chains` -> order_stability).
    """
    present = [h for h in hits if h["present"]]
    present.sort(key=lambda h: (int(h["start_idx"]), str(h["clause_id"])))
    return tuple(str(h["clause_id"]) for h in present)


def bag_of(hits: list[dict[str, Any]]) -> tuple[str, ...]:
    """Unordered clause set (the old bag abstraction, for the comparison)."""
    return tuple(sorted(str(h["clause_id"]) for h in hits if h["present"]))


def build_chain_frame(
    frame: pd.DataFrame,
    clause_specs: list[dict[str, Any]],
    *,
    progress_every: int = 500,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Score a frame; return (per-resolution chains, per-clause-hit rows).

    Carries a ``label`` column through when present, so the same code runs on
    a year slice (unlabelled) or on ``aanstelling_labelled`` (human gold).
    """
    chain_rows: list[dict[str, Any]] = []
    hit_rows: list[dict[str, Any]] = []
    records = frame.to_dict(orient="records")
    total = len(records)
    has_label = "label" in frame.columns
    for i, rec in enumerate(records, start=1):
        rid = str(rec["id"])
        year = rec.get("year")
        year = int(year) if year is not None and not pd.isna(year) else None
        text = str(rec.get("resolutions_text") or "")
        hits = detect_clauses(text, clause_specs)
        chain = chain_of(hits)
        bag = bag_of(hits)
        row = {
            "id": rid,
            "year": year,
            "chain": list(chain),
            "bag": list(bag),
            "chain_len": len(chain),
            "n_words": len(text.split()),
        }
        if has_label:
            row["label"] = str(rec.get("label") or "")
        chain_rows.append(row)
        for h in hits:
            hit_row = {"id": rid, "year": year, **h}
            if has_label:
                hit_row["label"] = str(rec.get("label") or "")
            hit_rows.append(hit_row)
        if progress_every and i % progress_every == 0:
            print(f"  clause_chain: {i}/{total}", flush=True)
    return pd.DataFrame(chain_rows), pd.DataFrame(hit_rows)


def load_gold_appointment_frame() -> pd.DataFrame:
    """`aanstelling_labelled`: 213 human-harvested positives + overig negatives.

    This is the repo's original human-harvested delegate-appointment
    collection (`delegates_resolutie_refs` rc5 xlsx, joined to flat text in
    STEPR1). Year slices are a poor universe for appointment clause work —
    1780 holds exactly one gold positive — so clause measurement runs on this
    frame instead, with recall/FP split by the human label.
    """
    from data_io import load

    frame = load("aanstelling_labelled")
    if not isinstance(frame, pd.DataFrame):
        frame = pd.DataFrame(frame)
    out = frame.copy()
    out["id"] = out["id"].astype(str)
    out["year"] = pd.to_numeric(out["year"], errors="coerce")
    out["resolutions_text"] = out["resolutions_text"].fillna("").astype(str)
    keep = out["resolutions_text"].str.strip().ne("")
    return out.loc[keep, ["id", "year", "resolutions_text", "label"]].reset_index(
        drop=True
    )


def _by_label(
    chain_frame: pd.DataFrame,
    hit_frame: pd.DataFrame,
    *,
    positive_label: str,
    min_support: int,
) -> dict[str, Any]:
    """Per-clause and per-chain rates split by human label (recall vs FP)."""
    if "label" not in chain_frame.columns:
        return {"computed": False, "note": "frame carries no human label"}

    is_pos = chain_frame["label"].eq(positive_label)
    n_pos = int(is_pos.sum())
    n_neg = int((~is_pos).sum())

    clause_rows: list[dict[str, Any]] = []
    for cid, sub in hit_frame.groupby("clause_id", sort=True):
        pos = sub.loc[sub["label"].eq(positive_label), "present"].astype(bool)
        neg = sub.loc[~sub["label"].eq(positive_label), "present"].astype(bool)
        clause_rows.append(
            {
                "clause_id": str(cid),
                "recall_on_gold": round(float(pos.mean()), 4) if len(pos) else None,
                "fp_rate_on_overig": round(float(neg.mean()), 4) if len(neg) else None,
                "n_gold_hits": int(pos.sum()),
                "n_overig_hits": int(neg.sum()),
            }
        )

    def _chains(mask: pd.Series) -> list[dict[str, Any]]:
        counts = Counter(tuple(c) for c in chain_frame.loc[mask, "chain"])
        total = int(mask.sum())
        return [
            {
                "pattern": list(pat),
                "support": int(n),
                "frac": round(n / total, 4) if total else None,
            }
            for pat, n in counts.most_common()
            if int(n) >= int(min_support)
        ]

    return {
        "computed": True,
        "positive_label": positive_label,
        "n_gold": n_pos,
        "n_overig": n_neg,
        "clauses": clause_rows,
        "gold_chain_inventory": _chains(is_pos),
        "overig_chain_inventory": _chains(~is_pos),
        "note": (
            "Recall/FP here are measured against the human-harvested gold "
            "(delegates_resolutie_refs -> aanstelling_labelled), not against "
            "ES labels or cue regexes."
        ),
    }


def _inventory(series: pd.Series, *, min_support: int) -> list[dict[str, Any]]:
    counts = Counter(tuple(v) for v in series)
    rows = [
        {"pattern": list(pat), "support": int(n)}
        for pat, n in counts.most_common()
        if int(n) >= int(min_support)
    ]
    return rows


def _order_stability(chains: pd.Series, *, min_support: int) -> dict[str, Any]:
    """Per clause-set with >=2 members: share taking the dominant order."""
    by_set: dict[tuple[str, ...], Counter] = {}
    for chain in chains:
        tup = tuple(chain)
        if len(tup) < 2:
            continue
        key = tuple(sorted(tup))
        by_set.setdefault(key, Counter())[tup] += 1
    rows: list[dict[str, Any]] = []
    weighted_num = 0.0
    weighted_den = 0.0
    for key, orders in by_set.items():
        support = int(sum(orders.values()))
        if support < int(min_support):
            continue
        dom_order, dom_n = orders.most_common(1)[0]
        frac = dom_n / support
        rows.append(
            {
                "clause_set": list(key),
                "support": support,
                "n_distinct_orders": int(len(orders)),
                "n_possible_orders": int(len(list(permutations(key)))),
                "dominant_order": list(dom_order),
                "dominant_order_frac": round(float(frac), 4),
            }
        )
        weighted_num += frac * support
        weighted_den += support
    rows.sort(key=lambda r: -r["support"])
    return {
        "n_multiclause_sets": int(len(rows)),
        "support_weighted_dominant_order_frac": (
            round(weighted_num / weighted_den, 4) if weighted_den else None
        ),
        "note": (
            "Order measured on multi-clause chains only. Ties on identical "
            "start_idx break on clause_id, so overlapping spans register as "
            "one fixed order — inflates stability; read with n_distinct_orders."
        ),
        "sets": rows,
    }


def _collapse(chain_frame: pd.DataFrame) -> dict[str, Any]:
    """How much structure the unordered bag discards."""
    chains = [tuple(c) for c in chain_frame["chain"]]
    bags = [tuple(b) for b in chain_frame["bag"]]
    n_chains = len(set(chains))
    n_bags = len(set(bags))
    per_bag: dict[tuple[str, ...], set[tuple[str, ...]]] = {}
    for bag, chain in zip(bags, chains, strict=True):
        per_bag.setdefault(bag, set()).add(chain)
    multi = {b for b, cs in per_bag.items() if len(cs) > 1}
    n_in_multi = sum(1 for b in bags if b in multi)
    n = len(chain_frame)
    return {
        "n_distinct_bags": int(n_bags),
        "n_distinct_chains": int(n_chains),
        "collapse_factor": round(n_chains / n_bags, 4) if n_bags else None,
        "n_multi_chain_bags": int(len(multi)),
        "n_resolutions_in_multi_chain_bag": int(n_in_multi),
        "frac_resolutions_in_multi_chain_bag": (
            round(n_in_multi / n, 4) if n else None
        ),
    }


def _appointment_decollapse(
    chain_frame: pd.DataFrame,
    hit_frame: pd.DataFrame,
    *,
    review_labels: pd.DataFrame | None = None,
) -> dict[str, Any]:
    """welkom_only / sessie_only / both, with independent properties."""
    present = hit_frame.loc[hit_frame["present"].astype(bool)]
    by_id = present.groupby("id")["clause_id"].apply(set).to_dict()

    def _pattern(rid: str) -> str:
        got = by_id.get(str(rid), set())
        has_w = CLAUSE_WELKOM in got
        has_s = CLAUSE_SESSIE in got
        if has_w and has_s:
            return "both"
        if has_w:
            return "welkom_only"
        if has_s:
            return "sessie_only"
        return "neither"

    frame = chain_frame.copy()
    frame["sub_pattern"] = frame["id"].map(_pattern)

    zone_by = (
        present.groupby(["clause_id", "id"])["zone"].first().reset_index()
        if len(present)
        else pd.DataFrame(columns=["clause_id", "id", "zone"])
    )
    mid_by_clause = (
        present.groupby("clause_id")["mid_norm"].median().round(4).to_dict()
        if len(present)
        else {}
    )
    zone_mode_by_clause = (
        present.groupby("clause_id")["zone"]
        .agg(lambda s: s.value_counts().idxmax() if len(s) else None)
        .to_dict()
        if len(present)
        else {}
    )

    groups: list[dict[str, Any]] = []
    for pat, grp in frame.groupby("sub_pattern", sort=True):
        row: dict[str, Any] = {
            "sub_pattern": str(pat),
            "n": int(len(grp)),
            "frac": round(len(grp) / len(frame), 4) if len(frame) else None,
            "median_n_words": (
                int(np.median(grp["n_words"])) if len(grp) else None
            ),
        }
        if review_labels is not None and len(review_labels):
            joined = grp.merge(review_labels, on="id", how="inner")
            n_joined = int(len(joined))
            row["review_join"] = {
                "n_joined": n_joined,
                "n_keep": int((joined["review"] == "keep").sum()) if n_joined else 0,
                "n_drop": int((joined["review"] == "drop").sum()) if n_joined else 0,
                "keep_rate": (
                    round(float((joined["review"] == "keep").mean()), 4)
                    if n_joined
                    else None
                ),
            }
        groups.append(row)

    return {
        "groups": groups,
        "median_mid_norm_by_clause": mid_by_clause,
        "modal_zone_by_clause": zone_mode_by_clause,
        "zone_rows": int(len(zone_by)),
        "note": (
            "welkom/sessie were collapsed by max() in score_text; this is the "
            "same evidence kept apart. Length/zone/keep-rate are independent "
            "of the defining clause presence; group size is not."
        ),
    }


def _independence(hit_frame: pd.DataFrame) -> dict[str, Any]:
    """P(sessie|welkom) vs P(sessie|not welkom) — variant marker or partition?"""
    wide = (
        hit_frame.pivot_table(
            index="id", columns="clause_id", values="present", aggfunc="first"
        )
        if len(hit_frame)
        else pd.DataFrame()
    )
    if CLAUSE_WELKOM not in wide.columns or CLAUSE_SESSIE not in wide.columns:
        return {"computed": False, "note": "welkom/sessie not both scored"}
    w = wide[CLAUSE_WELKOM].fillna(False).astype(bool)
    s = wide[CLAUSE_SESSIE].fillna(False).astype(bool)
    p_s = float(s.mean()) if len(s) else 0.0
    p_s_given_w = float(s[w].mean()) if int(w.sum()) else None
    p_s_given_not_w = float(s[~w].mean()) if int((~w).sum()) else None
    lift = (
        round(p_s_given_w / p_s, 4)
        if p_s and p_s_given_w is not None
        else None
    )
    return {
        "computed": True,
        "n": int(len(wide)),
        "p_welkom": round(float(w.mean()), 4) if len(w) else None,
        "p_sessie": round(p_s, 4),
        "p_sessie_given_welkom": (
            round(p_s_given_w, 4) if p_s_given_w is not None else None
        ),
        "p_sessie_given_not_welkom": (
            round(p_s_given_not_w, 4) if p_s_given_not_w is not None else None
        ),
        "lift_sessie_given_welkom": lift,
        "reading": (
            "lift ~1 => presence independent => variant marker; "
            "lift >>1 or <<1 => partitions the backbone => candidate distinct type"
        ),
    }


def summarize_clause_chains(
    chain_frame: pd.DataFrame,
    hit_frame: pd.DataFrame,
    *,
    year: int,
    clause_specs: list[dict[str, Any]],
    min_support: int = DEFAULT_MIN_SUPPORT,
    review_labels: pd.DataFrame | None = None,
) -> dict[str, Any]:
    """Provenanced metrics for STEPT1p. Gates are judged in NOTES, not here."""
    n = int(len(chain_frame))
    clauses = []
    for spec in clause_specs:
        cid = spec["clause_id"]
        sub = hit_frame.loc[hit_frame["clause_id"] == cid]
        n_present = int(sub["present"].astype(bool).sum()) if len(sub) else 0
        clauses.append(
            {
                "clause_id": cid,
                "source": spec.get("source"),
                "cut": float(spec["cut"]),
                "cut_rule": spec.get("cut_rule"),
                "n": int(len(sub)),
                "n_present": n_present,
                "hit_rate": round(n_present / len(sub), 4) if len(sub) else None,
                "score_mean": (
                    round(float(sub["score"].mean()), 4) if len(sub) else None
                ),
            }
        )

    collapse = _collapse(chain_frame)
    order = _order_stability(chain_frame["chain"], min_support=min_support)
    chain_len_hist = Counter(int(v) for v in chain_frame["chain_len"])

    return {
        "step": "STEPT1p",
        "method": "clause_chain_vs_bag",
        "design_doc": "docs/resolution-graph-design.md",
        "year": int(year),
        "min_support": int(min_support),
        "form_only": True,
        "content_markers_used": [],
        "n_resolutions": n,
        "clauses": clauses,
        "chain_len_histogram": {str(k): int(v) for k, v in sorted(chain_len_hist.items())},
        "collapse": collapse,
        "order_stability": order,
        "bag_inventory": _inventory(chain_frame["bag"], min_support=min_support),
        "chain_inventory": _inventory(chain_frame["chain"], min_support=min_support),
        "appointment_decollapse": _appointment_decollapse(
            chain_frame, hit_frame, review_labels=review_labels
        ),
        "by_human_label": _by_label(
            chain_frame,
            hit_frame,
            positive_label=LABEL_AANSTELLING,
            min_support=1,
        ),
        "independence": _independence(hit_frame),
        "gates": {
            "g1_collapse_chains_gt_bags": bool(
                (collapse["n_distinct_chains"] or 0)
                > (collapse["n_distinct_bags"] or 0)
            ),
            "g1_collapse_frac_multi_ge_0_10": bool(
                (collapse["frac_resolutions_in_multi_chain_bag"] or 0.0) >= 0.10
            ),
            "g2_order_stability_ge_0_80": bool(
                (order["support_weighted_dominant_order_frac"] or 0.0) >= 0.80
            ),
            "g2_order_refuted_lt_0_60": bool(
                order["support_weighted_dominant_order_frac"] is not None
                and order["support_weighted_dominant_order_frac"] < 0.60
            ),
        },
        "notes": (
            "Clause nodes are form skeletons with their own clouds. Both "
            "appointment clauses share the frozen STEPT1a cut (calibrated "
            "together) — per-clause cuts would be a new calibration, out of "
            "scope. No vergadering/rekenkamer claim: those labels do not "
            "exist (only keep/drop)."
        ),
    }


def load_review_labels() -> pd.DataFrame | None:
    """`aanstelling_review_labels` (keep/drop) for the independent-property join."""
    from data_io import load

    try:
        rows = load("aanstelling_review_labels")
    except Exception:
        return None
    frame = rows if isinstance(rows, pd.DataFrame) else pd.DataFrame(rows)
    if frame.empty or "review" not in frame.columns:
        return None
    out = frame[["id", "review"]].copy()
    out["id"] = out["id"].astype(str)
    return out


def fixture_clause_specs() -> list[dict[str, Any]]:
    """Two tiny clause clouds from fixture texts (no parquet / gold)."""
    welkom, sessie, _notes = build_appointment_clouds(
        [
            "is den selven verwelkomt, ende heeft sessie genomen",
            "is den zelven verwellekomt, en heeft dienvolgende sessie genomen",
            "is den selve verwelkomt, en heeft sessie genomen",
        ]
    )
    return [
        _clause_spec(CLAUSE_WELKOM, welkom, 2.0, source="fixture_welkom"),
        _clause_spec(CLAUSE_SESSIE, sessie, 2.0, source="fixture_sessie"),
    ]


def fixture_year_frame() -> pd.DataFrame:
    """Tiny year slice covering both clauses, one clause, and neither."""
    return pd.DataFrame(
        [
            {
                "id": "fix-both-1",
                "year": 1780,
                "resolutions_text": (
                    "Ontfangen een missive van den Gouverneur, is den selven "
                    "verwelkomt, ende heeft sessie genomen"
                ),
            },
            {
                "id": "fix-both-2",
                "year": 1780,
                "resolutions_text": (
                    "is den zelven verwellekomt, en heeft dienvolgende sessie genomen"
                ),
            },
            {
                "id": "fix-sessie-1",
                "year": 1780,
                "resolutions_text": "ende heeft sessie genomen in deese Vergaderinge",
            },
            {
                "id": "fix-none-1",
                "year": 1780,
                "resolutions_text": "Goedgevonden ende verstaen dat men zal",
            },
        ]
    )
