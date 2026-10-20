"""STEPT1b: score a year slice for formula-type presence + popularity weights.

Runs accepted appointment + advies + requeste models (frozen STEPT1a /
STEPT1a2 / STEPT1k cuts when available) and optional provisional opening
families so co-occurrence bags can be inspected.
"""

from __future__ import annotations

from collections import Counter
from typing import Any

import pandas as pd
import pyarrow.parquet as pq

from data_io import load, resolve
from formulation.advies_formula_type import (
    FORMULA_TYPE_ID as ADVIES_ID,
    build_advies_cloud,
    load_advies_gold_18c,
    score_text as score_advies_text,
)
from formulation.appointment_formula_type import (
    FALLBACK_CUT,
    FORMULA_TYPE_ID as APPOINTMENT_ID,
    HOLDOUT_FRAC,
    RNG,
    YEAR_MAX,
    YEAR_MIN,
    apply_popularity,
    build_appointment_clouds,
    calibrate_cut,
    load_selected_18c,
    popularity_weight,
    score_text as score_appointment_text,
    split_bootstrap_holdout,
)
from formulation.boundary.tfidf_windows import POC_YEAR
from formulation.formula_period_bins import (
    CANDIDATE_CAP_PER_BIN,
    OPENING_FAMILIES,
    bin_bounds,
    build_single_cloud,
    score_single_cloud,
    year_bin,
)
from formulation.requeste_formula_type import (
    FORMULA_TYPE_ID as REQUESTE_ID,
    build_requeste_cloud,
    load_rekest_gold_18c,
    score_text as score_requeste_text,
)

DEFAULT_YEAR = POC_YEAR
APPOINTMENT_CUT_FALLBACK = FALLBACK_CUT
ADVIES_CUT_FALLBACK = FALLBACK_CUT
REQUESTE_CUT_FALLBACK = FALLBACK_CUT


def load_year_slice(
    year: int,
    *,
    limit: int | None = None,
) -> pd.DataFrame:
    """Load ``id`` / ``year`` / ``resolutions_text`` for one calendar year."""
    path = resolve("resolutions_flat")
    frame = pq.read_table(
        path,
        columns=["id", "year", "resolutions_text"],
        filters=[("year", "=", int(year))],
    ).to_pandas()
    frame["id"] = frame["id"].astype(str)
    frame["year"] = pd.to_numeric(frame["year"], errors="coerce").astype("Int64")
    frame["resolutions_text"] = frame["resolutions_text"].fillna("").astype(str)
    if limit is not None:
        frame = frame.head(int(limit)).copy()
    return frame.reset_index(drop=True)


def _load_frozen_cut(logical_name: str) -> float | None:
    """Read ``operating_cut`` from a provenanced metrics JSONL when present."""
    try:
        path = resolve(logical_name)
        if not path.exists():
            return None
        rows = load(logical_name)
    except (KeyError, FileNotFoundError, OSError):
        return None
    if isinstance(rows, pd.DataFrame):
        if rows.empty or "operating_cut" not in rows.columns:
            return None
        return float(rows.iloc[0]["operating_cut"])
    if isinstance(rows, list) and rows:
        cut = rows[0].get("operating_cut")
        return float(cut) if cut is not None else None
    return None


def load_frozen_appointment_cut() -> float | None:
    """Read ``operating_cut`` from STEPT1a metrics when present on disk."""
    return _load_frozen_cut("formula_type_appointment_metrics")


def load_frozen_advies_cut() -> float | None:
    """Read ``operating_cut`` from STEPT1a2 metrics when present on disk."""
    return _load_frozen_cut("formula_type_advies_metrics")


def load_frozen_requeste_cut() -> float | None:
    """Read ``operating_cut`` from STEPT1k metrics when present on disk."""
    return _load_frozen_cut("formula_type_requeste_metrics")


def fit_appointment_presence_model(
    *,
    random_state: int = RNG,
    cut: float | None = None,
) -> dict[str, Any]:
    """Bootstrap welkom+sessie from 18c gold; freeze cut from T1a or recalibrate."""
    gold = load_selected_18c()
    boot, hold = split_bootstrap_holdout(
        gold, holdout_frac=HOLDOUT_FRAC, random_state=random_state
    )
    welkom, sessie, notes = build_appointment_clouds(
        boot["resolutions_text"].astype(str).tolist(),
        year_min=YEAR_MIN,
        year_max=YEAR_MAX,
    )
    frozen = load_frozen_appointment_cut() if cut is None else None
    if cut is not None:
        operating_cut = float(cut)
        cut_rule = "cli_override"
    elif frozen is not None:
        operating_cut = float(frozen)
        cut_rule = "frozen_stept1a_metrics"
    else:
        hold_scores = [
            score_appointment_text(t, welkom, sessie)["score"]
            for t in hold["resolutions_text"].astype(str).tolist()
        ]
        operating_cut = float(calibrate_cut(hold_scores, fallback=APPOINTMENT_CUT_FALLBACK))
        cut_rule = "p20_holdout_positive_scores"
    return {
        "formula_type_id": APPOINTMENT_ID,
        "role": "appointment",
        "provisional": False,
        "welkom_cloud": welkom,
        "sessie_cloud": sessie,
        "notes": notes,
        "operating_cut": operating_cut,
        "operating_cut_rule": cut_rule,
        "score_fn": "appointment",
        "n_bootstrap": int(len(boot)),
        "n_holdout": int(len(hold)),
    }


def fit_advies_presence_model(
    *,
    random_state: int = RNG,
    cut: float | None = None,
) -> dict[str, Any]:
    """Bootstrap advies cloud from ES gold; freeze cut from T1a2 or recalibrate."""
    gold = load_advies_gold_18c()
    boot, hold = split_bootstrap_holdout(
        gold, holdout_frac=HOLDOUT_FRAC, random_state=random_state
    )
    cloud, notes = build_advies_cloud(
        boot["resolutions_text"].astype(str).tolist(),
        year_min=YEAR_MIN,
        year_max=YEAR_MAX,
    )
    frozen = load_frozen_advies_cut() if cut is None else None
    if cut is not None:
        operating_cut = float(cut)
        cut_rule = "cli_override"
    elif frozen is not None:
        operating_cut = float(frozen)
        cut_rule = "frozen_stept1a2_metrics"
    else:
        hold_scores = [
            score_advies_text(t, cloud)["score"]
            for t in hold["resolutions_text"].astype(str).tolist()
        ]
        operating_cut = float(calibrate_cut(hold_scores, fallback=ADVIES_CUT_FALLBACK))
        cut_rule = "p20_holdout_positive_scores"
    return {
        "formula_type_id": ADVIES_ID,
        "role": "advies",
        "provisional": False,
        "cloud": cloud,
        "notes": notes,
        "operating_cut": operating_cut,
        "operating_cut_rule": cut_rule,
        "score_fn": "advies",
        "n_bootstrap": int(len(boot)),
        "n_holdout": int(len(hold)),
    }


def fit_requeste_presence_model(
    *,
    random_state: int = RNG,
    cut: float | None = None,
) -> dict[str, Any]:
    """Bootstrap requeste cloud from ES rekest gold; freeze cut from T1k or recalibrate."""
    gold = load_rekest_gold_18c()
    boot, hold = split_bootstrap_holdout(
        gold, holdout_frac=HOLDOUT_FRAC, random_state=random_state
    )
    cloud, notes = build_requeste_cloud(
        boot["resolutions_text"].astype(str).tolist(),
        year_min=YEAR_MIN,
        year_max=YEAR_MAX,
    )
    frozen = load_frozen_requeste_cut() if cut is None else None
    if cut is not None:
        operating_cut = float(cut)
        cut_rule = "cli_override"
    elif frozen is not None:
        operating_cut = float(frozen)
        cut_rule = "frozen_stept1k_metrics"
    else:
        hold_scores = [
            score_requeste_text(t, cloud)["score"]
            for t in hold["resolutions_text"].astype(str).tolist()
        ]
        operating_cut = float(calibrate_cut(hold_scores, fallback=REQUESTE_CUT_FALLBACK))
        cut_rule = "p20_holdout_positive_scores"
    return {
        "formula_type_id": REQUESTE_ID,
        "role": "requeste",
        "provisional": False,
        "cloud": cloud,
        "notes": notes,
        "operating_cut": operating_cut,
        "operating_cut_rule": cut_rule,
        "score_fn": "requeste",
        "n_bootstrap": int(len(boot)),
        "n_holdout": int(len(hold)),
    }


def fit_opening_presence_model(
    family: str,
    year: int,
    *,
    candidate_cap: int = CANDIDATE_CAP_PER_BIN,
    random_state: int = RNG,
) -> dict[str, Any] | None:
    """Fit a single-cloud opening model from capped substring candidates in the year bin."""
    if family not in OPENING_FAMILIES:
        raise ValueError(f"unknown opening family {family!r}")
    meta = OPENING_FAMILIES[family]
    label = year_bin(int(year))
    y0, y1 = bin_bounds(label)
    y0 = max(y0, YEAR_MIN)
    y1 = min(y1, YEAR_MAX)
    # Reuse period-bin candidate loader without importing the heavy evaluate path.
    from formulation.formula_period_bins import load_opening_candidates_for_bin

    cand = load_opening_candidates_for_bin(
        family, label, cap=candidate_cap, random_state=random_state
    )
    if cand.empty:
        return None
    texts = cand["resolutions_text"].astype(str).tolist()
    cloud = build_single_cloud(
        texts,
        meta["canonic"],
        template_id=f"{family}_{label}",
        year_min=y0,
        year_max=y1,
    )
    scores = [score_single_cloud(t, cloud) for t in texts]
    cut = float(calibrate_cut(scores, fallback=APPOINTMENT_CUT_FALLBACK))
    return {
        "formula_type_id": family,
        "role": "opening",
        "provisional": True,
        "cloud": cloud,
        "canonic": meta["canonic"],
        "operating_cut": cut,
        "operating_cut_rule": "p20_candidate_pool",
        "score_fn": "single",
        "period_bin": label,
        "n_candidates": int(len(cand)),
    }


def score_with_presence_model(text: str, model: dict[str, Any]) -> float:
    score_fn = model.get("score_fn")
    if score_fn == "appointment":
        return float(
            score_appointment_text(
                text, model["welkom_cloud"], model["sessie_cloud"]
            )["score"]
        )
    if score_fn == "advies":
        return float(score_advies_text(text, model["cloud"])["score"])
    if score_fn == "requeste":
        return float(score_requeste_text(text, model["cloud"])["score"])
    return float(score_single_cloud(text, model["cloud"]))


def score_presence_frame(
    frame: pd.DataFrame,
    models: list[dict[str, Any]],
) -> pd.DataFrame:
    """Long scores: one row per resolution × formula type (no full text kept)."""
    rows: list[dict[str, Any]] = []
    records = frame.to_dict(orient="records")
    # Pass 1: raw scores + presence at frozen cuts.
    raw: dict[str, list[dict[str, Any]]] = {m["formula_type_id"]: [] for m in models}
    for rec in records:
        text = str(rec.get("resolutions_text") or "")
        rid = str(rec["id"])
        year = int(rec["year"]) if rec.get("year") is not None else None
        for model in models:
            ft = str(model["formula_type_id"])
            score = score_with_presence_model(text, model)
            cut = float(model["operating_cut"])
            raw[ft].append(
                {
                    "id": rid,
                    "year": year,
                    "formula_type_id": ft,
                    "role": model.get("role"),
                    "provisional": bool(model.get("provisional")),
                    "score": score,
                    "operating_cut": cut,
                    "present": bool(score >= cut),
                }
            )
    # Pass 2: popularity from year-slice hit rate; attach weighted scores.
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
            r["score"] = round(float(r["score"]), 4)
            rows.append(r)
    return pd.DataFrame(rows)


def summarize_presence(
    scores: pd.DataFrame,
    *,
    year: int,
    models: list[dict[str, Any]],
    random_state: int,
    limit: int | None,
) -> dict[str, Any]:
    """Provenanced metrics: per-type rates + bag co-occurrence."""
    types_out: list[dict[str, Any]] = []
    for model in models:
        ft = str(model["formula_type_id"])
        sub = scores.loc[scores["formula_type_id"] == ft]
        n = int(len(sub))
        n_present = int(sub["present"].sum()) if n else 0
        hit_rate = (n_present / n) if n else 0.0
        types_out.append(
            {
                "formula_type_id": ft,
                "role": model.get("role"),
                "provisional": bool(model.get("provisional")),
                "operating_cut": float(model["operating_cut"]),
                "operating_cut_rule": model.get("operating_cut_rule"),
                "n": n,
                "n_present": n_present,
                "hit_rate": round(float(hit_rate), 4),
                "popularity": {
                    "corpus_rate": round(float(hit_rate), 4),
                    "weight": round(float(popularity_weight(hit_rate)), 4),
                    "weight_formula": "log(1 / clip(rate))",
                },
                "score_mean": (
                    round(float(sub["score"].mean()), 4) if n else None
                ),
                "score_weighted_mean": (
                    round(float(sub["score_weighted"].mean()), 4) if n else None
                ),
                "score_weighted_present_mean": (
                    round(float(sub.loc[sub["present"], "score_weighted"].mean()), 4)
                    if n_present
                    else None
                ),
            }
        )

    # Bags: one set of present types per id.
    if scores.empty:
        bag_sizes: Counter[int] = Counter()
        top_patterns: list[dict[str, Any]] = []
        n_ids = 0
    else:
        present = scores.loc[scores["present"]]
        by_id = (
            present.groupby("id")["formula_type_id"]
            .apply(lambda s: tuple(sorted(set(s.astype(str)))))
            if len(present)
            else pd.Series(dtype=object)
        )
        all_ids = scores["id"].astype(str).unique()
        n_ids = int(len(all_ids))
        patterns = []
        for rid in all_ids:
            pat = by_id.get(rid, ()) if len(by_id) else ()
            if not isinstance(pat, tuple):
                pat = tuple(pat) if pat is not None else ()
            patterns.append(pat)
        bag_sizes = Counter(len(p) for p in patterns)
        pat_counts = Counter(patterns)
        top_patterns = [
            {
                "types": list(pat),
                "n": int(cnt),
                "rate": round(cnt / n_ids, 4) if n_ids else 0.0,
            }
            for pat, cnt in pat_counts.most_common(20)
            if pat  # skip empty bags in top list
        ]

    return {
        "step": "STEPT1b",
        "method": "presence_score_popularity_bags",
        "year": int(year),
        "year_min": YEAR_MIN,
        "year_max": YEAR_MAX,
        "random_state": int(random_state),
        "limit": limit,
        "n_resolutions": n_ids,
        "n_types": int(len(models)),
        "appointment_accepted": any(
            m.get("formula_type_id") == APPOINTMENT_ID and not m.get("provisional")
            for m in models
        ),
        "advies_accepted": any(
            m.get("formula_type_id") == ADVIES_ID and not m.get("provisional")
            for m in models
        ),
        "requeste_accepted": any(
            m.get("formula_type_id") == REQUESTE_ID and not m.get("provisional")
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
            "judgment_prompt": (
                "Do co-occurring formula-type hits look like recognisable "
                "resolution templates, or only a bag of fragments? "
                "If fragments → STEPT1c (position / more)."
            ),
        },
    }


def fixture_presence_frames() -> pd.DataFrame:
    """Tiny year-slice stand-in for CI (no resolutions_flat)."""
    return pd.DataFrame(
        [
            {
                "id": "fix-appt-1",
                "year": 1780,
                "resolutions_text": (
                    "is den selven verwelkomt, ende heeft sessie genomen"
                ),
            },
            {
                "id": "fix-adv-1",
                "year": 1780,
                "resolutions_text": (
                    "IS ter Vergaderinge geleesen het Advis van 's Lands Advocaten"
                ),
            },
            {
                "id": "fix-ont-1",
                "year": 1780,
                "resolutions_text": "Ontfangen een missive van den ambassadeur",
            },
            {
                "id": "fix-req-1",
                "year": 1780,
                "resolutions_text": "Is ter Vergaderinge gelesen de requeste van",
            },
            {
                "id": "fix-plain-1",
                "year": 1780,
                "resolutions_text": "Goedgevonden ende verstaen dat men zal",
            },
        ]
    )


def fixture_presence_models() -> list[dict[str, Any]]:
    """Appointment + advies + two openings from fixture texts (no parquet)."""
    frame = fixture_presence_frames()
    appt_texts = [
        frame.iloc[0]["resolutions_text"],
        "is den zelven verwellekomt, en heeft dienvolgende sessie genomen",
        "is den selve verwelkomt, en heeft sessie genomen",
    ]
    welkom, sessie, notes = build_appointment_clouds(appt_texts)
    appt = {
        "formula_type_id": APPOINTMENT_ID,
        "role": "appointment",
        "provisional": False,
        "welkom_cloud": welkom,
        "sessie_cloud": sessie,
        "notes": notes,
        "operating_cut": 2.0,
        "operating_cut_rule": "fixture",
        "score_fn": "appointment",
    }
    adv_texts = [
        frame.iloc[1]["resolutions_text"],
        "is ter Vergaderinge gelesen het advies van de Heeren Gecommitteerden",
        "IS ter Vergaderinge geleesen het Advis van de 's Lands Advocaaten",
    ]
    adv_cloud, adv_notes = build_advies_cloud(adv_texts)
    advies = {
        "formula_type_id": ADVIES_ID,
        "role": "advies",
        "provisional": False,
        "cloud": adv_cloud,
        "notes": adv_notes,
        "operating_cut": 2.0,
        "operating_cut_rule": "fixture",
        "score_fn": "advies",
    }
    req_texts = [
        frame.iloc[3]["resolutions_text"],
        "IS ter Vergaderinge geleesen de Requeste van",
        "is ter vergaderinge gelesen het rekest van",
    ]
    req_cloud, req_notes = build_requeste_cloud(req_texts)
    requeste = {
        "formula_type_id": REQUESTE_ID,
        "role": "requeste",
        "provisional": False,
        "cloud": req_cloud,
        "notes": req_notes,
        "operating_cut": 2.0,
        "operating_cut_rule": "fixture",
        "score_fn": "requeste",
    }
    models = [appt, advies, requeste]
    for family, text_idx in (("ontfangen_start", 2), ("requeste_start", 3)):
        meta = OPENING_FAMILIES[family]
        texts = [frame.iloc[text_idx]["resolutions_text"], meta["canonic"]]
        cloud = build_single_cloud(
            texts, meta["canonic"], template_id=f"{family}_fixture"
        )
        models.append(
            {
                "formula_type_id": family,
                "role": "opening",
                "provisional": True,
                "cloud": cloud,
                "canonic": meta["canonic"],
                "operating_cut": 1.0,
                "operating_cut_rule": "fixture",
                "score_fn": "single",
            }
        )
    return models
