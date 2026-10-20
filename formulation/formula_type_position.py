"""STEPT1c: position / zone for formula-type hits (opening vs body vs close).

Presence bags from STEPT1b were fragments. This step records DAG span offsets
on the same models (appointment + advies accepted; openings provisional), maps
mid-span to coarse zones, and asks whether zone-conditioned patterns look more
like resolution templates.
"""

from __future__ import annotations

from collections import Counter
from typing import Any

import pandas as pd

from formulation.advies_formula_type import (
    FORMULA_TYPE_ID as ADVIES_ID,
    score_text as score_advies_text,
)
from formulation.appointment_formula_type import (
    FORMULA_TYPE_ID as APPOINTMENT_ID,
    align_tokenize,
    apply_popularity,
    popularity_weight,
    score_text as score_appointment_text,
)
from formulation.boundary.align_dag import align_dag
from formulation.boundary.slot_cloud import cloud_variant_lists
from formulation.boundary.tfidf_windows import POC_YEAR, tokenize
from formulation.formula_type_presence import (
    fixture_presence_frames,
    fixture_presence_models,
)

DEFAULT_YEAR = POC_YEAR
# Mid-span fraction of document tokens → coarse zone (STEPT1 §C).
OPENING_CUT = 1.0 / 3.0
CLOSE_CUT = 2.0 / 3.0
ZONES = ("opening", "body", "close")

# Home zone per formula type (STEPT1c 1780: appointment mid_norm≈0.90 → close).
# Advies prior: reading formula ("geleesen het Advis…") → opening; re-judge after run.
EXPECTED_ZONE: dict[str, str] = {
    "ontfangen_start": "opening",
    "requeste_start": "opening",
    ADVIES_ID: "opening",
    APPOINTMENT_ID: "close",
}


def zone_from_span(
    start_idx: int,
    end_idx: int,
    n_tokens: int,
    *,
    opening_cut: float = OPENING_CUT,
    close_cut: float = CLOSE_CUT,
) -> str:
    """Map span midpoint to opening / body / close (or unknown if empty)."""
    n = int(n_tokens)
    if n <= 0:
        return "unknown"
    mid = (float(start_idx) + float(end_idx)) / 2.0 / float(n)
    if mid < float(opening_cut):
        return "opening"
    if mid < float(close_cut):
        return "body"
    return "close"


def score_with_span(text: str, model: dict[str, Any]) -> dict[str, Any]:
    """Align score plus token span for one presence model."""
    raw = str(text or "")
    score_fn = model.get("score_fn")
    if score_fn == "appointment":
        detail = score_appointment_text(
            raw, model["welkom_cloud"], model["sessie_cloud"]
        )
        n_tokens = len(align_tokenize(raw))
        return {
            "score": float(detail["score"]),
            "start_idx": int(detail["start_idx"]),
            "end_idx": int(detail["end_idx"]),
            "n_tokens": int(n_tokens),
            "best_cloud": detail.get("best_cloud"),
        }
    if score_fn == "advies":
        detail = score_advies_text(raw, model["cloud"])
        n_tokens = len(align_tokenize(raw))
        return {
            "score": float(detail["score"]),
            "start_idx": int(detail["start_idx"]),
            "end_idx": int(detail["end_idx"]),
            "n_tokens": int(n_tokens),
            "best_cloud": None,
        }
    tokens = tokenize(raw)
    variants = model["cloud"].get("variant_lists") or cloud_variant_lists(
        model["cloud"]
    )
    opt = list(model["cloud"].get("optional_slots") or [])
    res = align_dag(variants, tokens, optional_slots=opt)
    return {
        "score": float(res.score),
        "start_idx": int(res.start_idx),
        "end_idx": int(res.end_idx),
        "n_tokens": int(len(tokens)),
        "best_cloud": None,
    }


def score_position_frame(
    frame: pd.DataFrame,
    models: list[dict[str, Any]],
    *,
    opening_cut: float = OPENING_CUT,
    close_cut: float = CLOSE_CUT,
) -> pd.DataFrame:
    """Long scores with span + zone (one row per resolution × type)."""
    raw: dict[str, list[dict[str, Any]]] = {m["formula_type_id"]: [] for m in models}
    for rec in frame.to_dict(orient="records"):
        text = str(rec.get("resolutions_text") or "")
        rid = str(rec["id"])
        year = int(rec["year"]) if rec.get("year") is not None else None
        for model in models:
            ft = str(model["formula_type_id"])
            detail = score_with_span(text, model)
            cut = float(model["operating_cut"])
            present = bool(detail["score"] >= cut)
            zone = (
                zone_from_span(
                    detail["start_idx"],
                    detail["end_idx"],
                    detail["n_tokens"],
                    opening_cut=opening_cut,
                    close_cut=close_cut,
                )
                if present
                else None
            )
            mid_norm = None
            n_tok = int(detail["n_tokens"])
            if present and n_tok > 0:
                mid_norm = round(
                    (detail["start_idx"] + detail["end_idx"]) / 2.0 / n_tok,
                    4,
                )
            raw[ft].append(
                {
                    "id": rid,
                    "year": year,
                    "formula_type_id": ft,
                    "role": model.get("role"),
                    "provisional": bool(model.get("provisional")),
                    "score": round(float(detail["score"]), 4),
                    "operating_cut": cut,
                    "present": present,
                    "start_idx": int(detail["start_idx"]),
                    "end_idx": int(detail["end_idx"]),
                    "n_tokens": n_tok,
                    "mid_norm": mid_norm,
                    "zone": zone,
                    "expected_zone": EXPECTED_ZONE.get(ft),
                    "best_cloud": detail.get("best_cloud"),
                }
            )

    rows: list[dict[str, Any]] = []
    for model in models:
        ft = str(model["formula_type_id"])
        chunk = raw[ft]
        n = len(chunk)
        hit_rate = (sum(1 for r in chunk if r["present"]) / n) if n else 0.0
        weight = popularity_weight(hit_rate)
        for r in chunk:
            r["corpus_rate"] = round(float(hit_rate), 6)
            r["popularity_weight"] = round(float(weight), 4)
            r["score_weighted"] = round(
                apply_popularity(float(r["score"]), hit_rate), 4
            )
            rows.append(r)
    return pd.DataFrame(rows)


def _zone_histogram(zones: list[str]) -> dict[str, Any]:
    counts = Counter(z for z in zones if z)
    n = sum(counts.values())
    hist = {z: int(counts.get(z, 0)) for z in ZONES}
    hist["unknown"] = int(counts.get("unknown", 0))
    rates = {
        z: round(hist[z] / n, 4) if n else 0.0
        for z in (*ZONES, "unknown")
    }
    return {"n": n, "counts": hist, "rates": rates}


def summarize_position(
    scores: pd.DataFrame,
    *,
    year: int,
    models: list[dict[str, Any]],
    random_state: int,
    limit: int | None,
    opening_cut: float = OPENING_CUT,
    close_cut: float = CLOSE_CUT,
) -> dict[str, Any]:
    """Provenanced metrics: per-type zone mix + zone-tagged co-occurrence bags."""
    types_out: list[dict[str, Any]] = []
    for model in models:
        ft = str(model["formula_type_id"])
        sub = scores.loc[scores["formula_type_id"] == ft]
        present = sub.loc[sub["present"]]
        n = int(len(sub))
        n_present = int(len(present))
        hit_rate = (n_present / n) if n else 0.0
        zones = present["zone"].dropna().astype(str).tolist() if n_present else []
        zone_hist = _zone_histogram(zones)
        expected = EXPECTED_ZONE.get(ft)
        frac_expected = None
        if expected and zone_hist["n"]:
            frac_expected = round(
                zone_hist["counts"].get(expected, 0) / zone_hist["n"], 4
            )
        types_out.append(
            {
                "formula_type_id": ft,
                "role": model.get("role"),
                "provisional": bool(model.get("provisional")),
                "operating_cut": float(model["operating_cut"]),
                "operating_cut_rule": model.get("operating_cut_rule"),
                "expected_zone": expected,
                "n": n,
                "n_present": n_present,
                "hit_rate": round(float(hit_rate), 4),
                "popularity": {
                    "corpus_rate": round(float(hit_rate), 4),
                    "weight": round(float(popularity_weight(hit_rate)), 4),
                    "weight_formula": "log(1 / clip(rate))",
                },
                "zone": zone_hist,
                "frac_in_expected_zone": frac_expected,
                "mid_norm_median": (
                    round(float(present["mid_norm"].median()), 4)
                    if n_present and present["mid_norm"].notna().any()
                    else None
                ),
            }
        )

    # Zone-tagged bags: present (type, zone) pairs per id.
    if scores.empty:
        bag_sizes: Counter[int] = Counter()
        top_patterns: list[dict[str, Any]] = []
        top_zone_patterns: list[dict[str, Any]] = []
        n_ids = 0
    else:
        present = scores.loc[scores["present"]].copy()
        all_ids = scores["id"].astype(str).unique()
        n_ids = int(len(all_ids))

        type_by_id: dict[str, tuple[str, ...]] = {}
        zone_by_id: dict[str, tuple[tuple[str, str], ...]] = {}
        if len(present):
            for rid, grp in present.groupby("id"):
                types = tuple(sorted(set(grp["formula_type_id"].astype(str))))
                typed_zones = tuple(
                    sorted(
                        {
                            (str(r.formula_type_id), str(r.zone))
                            for r in grp.itertuples(index=False)
                            if r.zone
                        }
                    )
                )
                type_by_id[str(rid)] = types
                zone_by_id[str(rid)] = typed_zones

        type_patterns: list[tuple[str, ...]] = []
        zone_patterns: list[tuple[tuple[str, str], ...]] = []
        for rid in all_ids:
            key = str(rid)
            type_patterns.append(type_by_id.get(key, ()))
            zone_patterns.append(zone_by_id.get(key, ()))

        bag_sizes = Counter(len(p) for p in type_patterns)
        top_patterns = [
            {
                "types": list(pat),
                "n": int(cnt),
                "rate": round(cnt / n_ids, 4) if n_ids else 0.0,
            }
            for pat, cnt in Counter(type_patterns).most_common(20)
            if pat
        ]
        top_zone_patterns = [
            {
                "typed_zones": [{"formula_type_id": a, "zone": b} for a, b in pat],
                "n": int(cnt),
                "rate": round(cnt / n_ids, 4) if n_ids else 0.0,
            }
            for pat, cnt in Counter(zone_patterns).most_common(20)
            if pat
        ]

    return {
        "step": "STEPT1c",
        "method": "position_zone_from_dag_span",
        "year": int(year),
        "random_state": int(random_state),
        "limit": limit,
        "n_resolutions": n_ids,
        "n_types": int(len(models)),
        "zone_cuts": {
            "opening_lt": float(opening_cut),
            "body_lt": float(close_cut),
            "close_ge": float(close_cut),
            "rule": "mid_norm = (start_idx+end_idx)/2 / n_tokens",
        },
        "appointment_accepted": any(
            m.get("formula_type_id") == APPOINTMENT_ID and not m.get("provisional")
            for m in models
        ),
        "advies_accepted": any(
            m.get("formula_type_id") == ADVIES_ID and not m.get("provisional")
            for m in models
        ),
        "openings_provisional": any(bool(m.get("provisional")) for m in models),
        "types": types_out,
        "bags": {
            "n_ids": n_ids,
            "size_histogram": {
                str(k): int(v) for k, v in sorted(bag_sizes.items())
            },
            "frac_zero": (
                round(bag_sizes.get(0, 0) / n_ids, 4) if n_ids else None
            ),
            "frac_one": (
                round(bag_sizes.get(1, 0) / n_ids, 4) if n_ids else None
            ),
            "frac_multi": (
                round(
                    sum(v for k, v in bag_sizes.items() if k >= 2) / n_ids,
                    4,
                )
                if n_ids
                else None
            ),
            "top_patterns": top_patterns,
            "top_zone_patterns": top_zone_patterns,
            "judgment_prompt": (
                "Do zone-conditioned formula-type hits look like recognisable "
                "resolution templates, or still fragments? "
                "If still fragments → order/composition or another family; "
                "if position separates families → keep zone on registry rows."
            ),
        },
    }


def fixture_position_frames() -> pd.DataFrame:
    """Long texts so opening vs close spans land in different tertiles."""
    pad = " ".join(["woord"] * 40)
    base = fixture_presence_frames()
    rows = []
    for rec in base.to_dict(orient="records"):
        rid = str(rec["id"])
        text = str(rec["resolutions_text"])
        if rid == "fix-appt-1":
            # Appointment phrase after a long opening pad → body/close.
            text = f"{pad} {text}"
        elif rid.startswith("fix-ont") or rid.startswith("fix-req") or rid.startswith(
            "fix-adv"
        ):
            # Opening / advies reading phrase first, then padding → opening zone.
            text = f"{text} {pad}"
        else:
            text = f"{pad} {text} {pad}"
        rows.append({**rec, "resolutions_text": text})
    return pd.DataFrame(rows)


def fixture_position_models() -> list[dict[str, Any]]:
    return fixture_presence_models()
