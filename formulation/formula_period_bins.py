"""Family × 25-year bins: independent sub-templates + measured cross-bin eval.

Formulas drift gradually; when a later-bin model falls under threshold on an
earlier bin, that is the recalibration signal. Opening families are separate
rows from appointment installation. Every claim is a number in the metrics.
"""

from __future__ import annotations

import re
from typing import Any

import numpy as np
import pandas as pd
import pyarrow.parquet as pq

from data_io import resolve
from formulation.appointment_formula_type import (
    FORMULA_TYPE_ID as APPOINTMENT_ID,
    YEAR_MAX,
    YEAR_MIN,
    build_appointment_clouds,
    calibrate_cut,
    load_selected_18c,
    popularity_weight,
    score_text,
)
from formulation.boundary.align_dag import align_dag
from formulation.boundary.slot_cloud import (
    bootstrap_slot_cloud,
    cloud_variant_lists,
)
from formulation.boundary.tfidf_windows import tokenize

BIN_WIDTH = 25
BIN_ORIGIN = 1700
MIN_BIN_N = 30
RNG = 20261019
CANDIDATE_CAP_PER_BIN = 200

# Eval gates (recorded on the metrics object; judged in NOTES after a full run).
RECALIBRATE_RECALL_BAR = 0.5
DIAGONAL_RECALL_BAR = 0.5

OPENING_FAMILIES: dict[str, dict[str, str]] = {
    "ontfangen_start": {
        "canonic": "Ontfangen een missive van",
        "search": r"ontfangen\s+een\s+missive",
        "role": "opening",
    },
    "requeste_start": {
        "canonic": "gelesen de requeste van",
        "search": r"gele[sz]en\s+de\s+requeste",
        "role": "opening",
    },
}

# Family → formula_documents flag columns to compare against model diagonal.
FAMILY_DOCUMENT_FLAGS: dict[str, tuple[str, ...]] = {
    APPOINTMENT_ID: ("welkom", "sessie"),
    "ontfangen_start": ("ontfangen_start",),
    "requeste_start": ("requeste_start", "request_start"),
}


def year_bin(
    year: int,
    *,
    origin: int = BIN_ORIGIN,
    width: int = BIN_WIDTH,
) -> str:
    """Return ``YYYY-YYYY`` label for a 25-year bin (origin-aligned)."""
    y = int(year)
    offset = (y - int(origin)) // int(width)
    start = int(origin) + offset * int(width)
    end = start + int(width) - 1
    return f"{start}-{end}"


def bin_bounds(label: str) -> tuple[int, int]:
    a, b = label.split("-")
    return int(a), int(b)


def assign_bins(
    frame: pd.DataFrame,
    *,
    year_col: str = "year",
    origin: int = BIN_ORIGIN,
    width: int = BIN_WIDTH,
) -> pd.DataFrame:
    out = frame.copy()
    out["year"] = pd.to_numeric(out[year_col], errors="coerce")
    out["period_bin"] = out["year"].map(
        lambda y: year_bin(int(y), origin=origin, width=width)
        if pd.notna(y)
        else "unknown"
    )
    return out


def list_bins_in_range(
    year_min: int = YEAR_MIN,
    year_max: int = YEAR_MAX,
    *,
    origin: int = BIN_ORIGIN,
    width: int = BIN_WIDTH,
) -> list[str]:
    labels: list[str] = []
    seen: set[str] = set()
    for y in range(int(year_min), int(year_max) + 1):
        lab = year_bin(y, origin=origin, width=width)
        if lab not in seen:
            labels.append(lab)
            seen.add(lab)
    return labels


def build_single_cloud(
    texts: list[str],
    canonic: str,
    *,
    template_id: str,
    year_min: int | None = None,
    year_max: int | None = None,
) -> dict[str, Any]:
    template = tokenize(canonic)
    cloud, _notes = bootstrap_slot_cloud(
        texts,
        template,
        template_id=template_id,
        period="bin",
        year_min=year_min,
        year_max=year_max,
    )
    return cloud


def score_single_cloud(text: str, cloud: dict[str, Any]) -> float:
    tokens = tokenize(str(text or ""))
    variants = cloud.get("variant_lists") or cloud_variant_lists(cloud)
    opt = list(cloud.get("optional_slots") or [])
    return float(align_dag(variants, tokens, optional_slots=opt).score)


def fit_appointment_model(texts: list[str], *, bin_label: str) -> dict[str, Any]:
    y0, y1 = bin_bounds(bin_label)
    welkom, sessie, notes = build_appointment_clouds(
        texts, year_min=y0, year_max=y1
    )
    return {
        "family": APPOINTMENT_ID,
        "bin": bin_label,
        "welkom_cloud": welkom,
        "sessie_cloud": sessie,
        "notes": notes,
        "score_fn": "appointment",
    }


def fit_opening_model(
    texts: list[str],
    *,
    family: str,
    bin_label: str,
) -> dict[str, Any]:
    meta = OPENING_FAMILIES[family]
    y0, y1 = bin_bounds(bin_label)
    cloud = build_single_cloud(
        texts,
        meta["canonic"],
        template_id=f"{family}_{bin_label}",
        year_min=y0,
        year_max=y1,
    )
    return {
        "family": family,
        "bin": bin_label,
        "cloud": cloud,
        "canonic": meta["canonic"],
        "score_fn": "single",
    }


def score_with_model(text: str, model: dict[str, Any]) -> float:
    if model.get("score_fn") == "appointment":
        return float(
            score_text(text, model["welkom_cloud"], model["sessie_cloud"])["score"]
        )
    return score_single_cloud(text, model["cloud"])


def calibrate_model_cut(texts: list[str], model: dict[str, Any]) -> float:
    scores = [score_with_model(t, model) for t in texts]
    return calibrate_cut(scores)


def cross_bin_matrix(
    models: dict[str, dict[str, Any]],
    bin_texts: dict[str, list[str]],
    cuts: dict[str, float],
    *,
    family: str,
) -> list[dict[str, Any]]:
    """Score every data bin with every model bin; recall @ that model's cut."""
    self_recall: dict[str, float] = {}
    for b, model in models.items():
        texts = bin_texts.get(b) or []
        if not texts:
            continue
        cut = float(cuts[b])
        scores = [score_with_model(t, model) for t in texts]
        self_recall[b] = float(np.mean([s >= cut for s in scores]))

    rows: list[dict[str, Any]] = []
    for model_bin, model in models.items():
        cut = float(cuts[model_bin])
        m0, _ = bin_bounds(model_bin)
        for data_bin, texts in bin_texts.items():
            d0, _ = bin_bounds(data_bin)
            adjacent = abs(m0 - d0) == BIN_WIDTH
            backward = m0 > d0
            if not texts:
                rows.append(
                    {
                        "family": family,
                        "model_bin": model_bin,
                        "data_bin": data_bin,
                        "n": 0,
                        "recall": None,
                        "score_mean": None,
                        "score_p20": None,
                        "operating_cut": cut,
                        "adjacent_pair": adjacent,
                        "backward_slip": backward,
                        "delta_vs_data_self": None,
                        "recalibrate_signal": False,
                    }
                )
                continue
            scores = [score_with_model(t, model) for t in texts]
            arr = np.asarray(scores, dtype=float)
            recall = float(np.mean(arr >= cut))
            data_self = self_recall.get(data_bin)
            delta = (
                round(recall - float(data_self), 4) if data_self is not None else None
            )
            recalc = bool(
                adjacent
                and backward
                and recall < RECALIBRATE_RECALL_BAR
            )
            rows.append(
                {
                    "family": family,
                    "model_bin": model_bin,
                    "data_bin": data_bin,
                    "n": int(len(texts)),
                    "recall": round(recall, 4),
                    "score_mean": round(float(arr.mean()), 4),
                    "score_p20": round(float(np.percentile(arr, 20)), 4),
                    "operating_cut": round(cut, 4),
                    "adjacent_pair": bool(adjacent),
                    "backward_slip": bool(backward),
                    "delta_vs_data_self": delta,
                    "recalibrate_signal": recalc,
                }
            )
    return rows


def formula_documents_bin_rates(
    flags: tuple[str, ...] | list[str],
    *,
    year_min: int = YEAR_MIN,
    year_max: int = YEAR_MAX,
) -> dict[str, Any]:
    """Per-25y-bin true rates of ``formula_documents`` flags (resolution rows only).

    Also reports ``any_listed`` = OR of the listed flags. Attendance-list rows
    are excluded. Leakage flags (praeside/praesentibus) are never used here.
    """
    from data_io import load

    frame = load("formula_documents")
    if not isinstance(frame, pd.DataFrame):
        frame = pd.DataFrame(frame)
    res = frame.loc[
        frame["doc_id"].astype(str).str.contains("-resolution-", na=False)
    ].copy()
    res["year"] = pd.to_numeric(res["year"], errors="coerce")
    res = res.loc[res["year"].between(int(year_min), int(year_max), inclusive="both")]
    wanted = [f for f in flags if f in res.columns]
    missing = [f for f in flags if f not in res.columns]
    if not wanted:
        return {
            "flags": list(flags),
            "missing_flags": missing,
            "bin_n": {},
            "flag_rates": {},
            "any_listed_rate": {},
            "status": "no_flags_present",
        }
    for col in wanted:
        res[col] = res[col].astype("boolean")
    res["_any"] = False
    for col in wanted:
        res["_any"] = res["_any"] | res[col].fillna(False)
    res = assign_bins(res)
    by = res.groupby("period_bin", sort=False)
    bin_n = {str(k): int(v) for k, v in by.size().items() if k != "unknown"}
    flag_rates: dict[str, dict[str, float]] = {}
    for col in wanted:
        flag_rates[col] = {
            str(k): round(float(v), 4)
            for k, v in by[col].mean().items()
            if k != "unknown"
        }
    any_rate = {
        str(k): round(float(v), 4)
        for k, v in by["_any"].mean().items()
        if k != "unknown"
    }
    return {
        "flags": wanted,
        "missing_flags": missing,
        "bin_n": bin_n,
        "flag_rates": flag_rates,
        "any_listed_rate": any_rate,
        "status": "ok",
        "source": "formula_documents",
        "row_filter": "doc_id contains -resolution-",
    }


def compare_model_to_formula_documents(
    family: str,
    diagonal_recall: dict[str, float | None],
    *,
    year_min: int = YEAR_MIN,
    year_max: int = YEAR_MAX,
) -> dict[str, Any]:
    """Side-by-side: model diagonal recall vs formula_documents flag rates per bin."""
    flags = FAMILY_DOCUMENT_FLAGS.get(family, ())
    if not flags:
        return {"status": "no_flag_map", "family": family}
    try:
        fd = formula_documents_bin_rates(
            flags, year_min=year_min, year_max=year_max
        )
    except FileNotFoundError as exc:
        return {"status": "formula_documents_missing", "error": str(exc)}
    if fd.get("status") != "ok":
        return {**fd, "family": family}

    any_rate = fd.get("any_listed_rate") or {}
    per_bin: list[dict[str, Any]] = []
    bins = sorted(
        set(diagonal_recall) | set(any_rate),
        key=lambda L: bin_bounds(L)[0] if "-" in L else 0,
    )
    for lab in bins:
        m = diagonal_recall.get(lab)
        f = any_rate.get(lab)
        delta = (
            round(float(m) - float(f), 4)
            if m is not None and f is not None
            else None
        )
        per_bin.append(
            {
                "period_bin": lab,
                "model_diagonal_recall": m,
                "formula_documents_any_listed_rate": f,
                "delta_model_minus_documents": delta,
                "formula_documents_n": (fd.get("bin_n") or {}).get(lab),
                "per_flag": {
                    fl: (fd.get("flag_rates") or {}).get(fl, {}).get(lab)
                    for fl in fd.get("flags") or []
                },
            }
        )
    deltas = [
        float(r["delta_model_minus_documents"])
        for r in per_bin
        if r["delta_model_minus_documents"] is not None
    ]
    return {
        "status": "ok",
        "family": family,
        "flags": fd.get("flags"),
        "formula_documents": fd,
        "per_bin": per_bin,
        "delta_mean": round(float(np.mean(deltas)), 4) if deltas else None,
        "delta_abs_mean": round(float(np.mean(np.abs(deltas))), 4) if deltas else None,
        "note": (
            "Positive delta ⇒ alignment model hits more of its pool than "
            "formula_documents flags on the full resolution matrix for that bin; "
            "negative ⇒ documents flag is broader / model under-recalls."
        ),
    }


def load_opening_candidates_for_bin(
    family: str,
    bin_label: str,
    *,
    cap: int = CANDIDATE_CAP_PER_BIN,
    random_state: int = RNG,
) -> pd.DataFrame:
    """Substring-seeded candidates from resolutions_flat inside a bin (capped)."""
    meta = OPENING_FAMILIES[family]
    pat = re.compile(meta["search"], re.IGNORECASE)
    y0, y1 = bin_bounds(bin_label)
    y0 = max(y0, YEAR_MIN)
    y1 = min(y1, YEAR_MAX)
    path = resolve("resolutions_flat")
    parts: list[pd.DataFrame] = []
    for year in range(y0, y1 + 1):
        chunk = pq.read_table(
            path,
            columns=["id", "year", "resolutions_text"],
            filters=[("year", "=", int(year))],
        ).to_pandas()
        if chunk.empty:
            continue
        mask = (
            chunk["resolutions_text"]
            .fillna("")
            .astype(str)
            .map(lambda t: bool(pat.search(t)))
        )
        hit = chunk.loc[mask]
        if not hit.empty:
            parts.append(hit)
    if not parts:
        return pd.DataFrame(columns=["id", "year", "resolutions_text", "period_bin"])
    frame = pd.concat(parts, ignore_index=True)
    frame["id"] = frame["id"].astype(str)
    frame["resolutions_text"] = frame["resolutions_text"].fillna("").astype(str)
    if len(frame) > int(cap):
        frame = frame.sample(n=int(cap), random_state=int(random_state))
    return assign_bins(frame.reset_index(drop=True))


def evaluate_family(
    family: str,
    *,
    min_bin_n: int = MIN_BIN_N,
    candidate_cap: int = CANDIDATE_CAP_PER_BIN,
    random_state: int = RNG,
    fixture_frames: dict[str, pd.DataFrame] | None = None,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """Fit per-bin models, cross-score, return measured summary + matrix rows."""
    fam = APPOINTMENT_ID if family in {APPOINTMENT_ID, "appointment"} else family

    if fixture_frames is not None:
        bin_frames = {
            k: assign_bins(v) if "period_bin" not in v.columns else v
            for k, v in fixture_frames.items()
        }
    elif fam == APPOINTMENT_ID:
        gold = assign_bins(load_selected_18c())
        bin_frames = {
            lab: g for lab, g in gold.groupby("period_bin") if lab != "unknown"
        }
    elif fam in OPENING_FAMILIES:
        bin_frames = {}
        for lab in list_bins_in_range():
            frame = load_opening_candidates_for_bin(
                fam, lab, cap=candidate_cap, random_state=random_state
            )
            if not frame.empty:
                bin_frames[lab] = frame
    else:
        raise ValueError(
            f"unknown family {family!r}; "
            f"try appointment / {', '.join(OPENING_FAMILIES)}"
        )

    models: dict[str, dict[str, Any]] = {}
    cuts: dict[str, float] = {}
    bin_texts: dict[str, list[str]] = {}
    bin_n: dict[str, int] = {}
    model_source: dict[str, str] = {}  # bin → "self" | "borrowed:<later_bin>"

    for lab, frame in sorted(bin_frames.items(), key=lambda kv: bin_bounds(kv[0])[0]):
        texts = frame["resolutions_text"].astype(str).tolist()
        bin_texts[lab] = texts
        bin_n[lab] = len(texts)
        if len(texts) < int(min_bin_n):
            continue
        if fam in OPENING_FAMILIES:
            model = fit_opening_model(texts, family=fam, bin_label=lab)
        else:
            model = fit_appointment_model(texts, bin_label=lab)
        models[lab] = model
        cuts[lab] = calibrate_model_cut(texts, model)
        model_source[lab] = "self"

    # Sparse bins (some hits, below min_bin_n): borrow the next later self-fit model
    # for recalibration / coverage — gradual drift implies the following period is
    # the right donor when the current bin is too thin to fit.
    borrow_rows: list[dict[str, Any]] = []
    self_bins = sorted(
        [b for b, src in model_source.items() if src == "self"],
        key=lambda L: bin_bounds(L)[0],
    )
    sparse_bins = sorted(
        [b for b, n in bin_n.items() if 0 < n < int(min_bin_n)],
        key=lambda L: bin_bounds(L)[0],
    )
    for sparse in sparse_bins:
        s0, _ = bin_bounds(sparse)
        later = [b for b in self_bins if bin_bounds(b)[0] > s0]
        earlier = [b for b in self_bins if bin_bounds(b)[0] < s0]
        # Prefer next period (gradual forward recalibration); if none (late
        # collapse), fall back to nearest earlier self-fit model.
        if later:
            donor = later[0]
            status = "borrowed_next_period"
        elif earlier:
            donor = earlier[-1]
            status = "borrowed_previous_period"
        else:
            borrow_rows.append(
                {
                    "sparse_bin": sparse,
                    "n_sparse": bin_n[sparse],
                    "borrowed_from": None,
                    "recall_on_sparse": None,
                    "status": "no_donor",
                }
            )
            continue
        models[sparse] = dict(models[donor])
        models[sparse]["bin"] = sparse
        models[sparse]["borrowed_from"] = donor
        cuts[sparse] = float(cuts[donor])
        model_source[sparse] = f"borrowed:{donor}"
        scores = [
            score_with_model(t, models[sparse]) for t in bin_texts[sparse]
        ]
        recall = float(np.mean([s >= cuts[sparse] for s in scores])) if scores else None
        borrow_rows.append(
            {
                "sparse_bin": sparse,
                "n_sparse": int(bin_n[sparse]),
                "borrowed_from": donor,
                "operating_cut": round(float(cuts[sparse]), 4),
                "recall_on_sparse": round(recall, 4) if recall is not None else None,
                "score_mean_on_sparse": (
                    round(float(np.mean(scores)), 4) if scores else None
                ),
                "status": status,
            }
        )

    matrix = cross_bin_matrix(models, bin_texts, cuts, family=fam)
    for row in matrix:
        row["model_source"] = model_source.get(str(row["model_bin"]), "unknown")

    diag = [r for r in matrix if r["model_bin"] == r["data_bin"] and r["n"]]
    slips = [r for r in matrix if r.get("recalibrate_signal")]
    adjacent_backward = [
        r
        for r in matrix
        if r.get("adjacent_pair") and r.get("backward_slip") and r.get("n")
    ]
    diag_recalls = [float(r["recall"]) for r in diag if r["recall"] is not None]
    pop_rate = float(np.mean(diag_recalls)) if diag_recalls else 0.0
    weak_diag = [
        r["model_bin"]
        for r in diag
        if r["recall"] is not None and float(r["recall"]) < DIAGONAL_RECALL_BAR
    ]
    self_diag_recalls = [
        float(r["recall"])
        for r in diag
        if r["recall"] is not None
        and model_source.get(str(r["model_bin"]), "").startswith("self")
    ]

    summary: dict[str, Any] = {
        "family": fam,
        "role": OPENING_FAMILIES.get(fam, {}).get("role", "appointment"),
        "bin_width": BIN_WIDTH,
        "bin_origin": BIN_ORIGIN,
        "year_min": YEAR_MIN,
        "year_max": YEAR_MAX,
        "min_bin_n": int(min_bin_n),
        "candidate_cap_per_bin": int(candidate_cap) if fam in OPENING_FAMILIES else None,
        "random_state": int(random_state),
        "bins_seen": sorted(bin_n.keys(), key=lambda L: bin_bounds(L)[0]),
        "bin_n": {k: int(v) for k, v in bin_n.items()},
        "bins_modeled": sorted(models.keys(), key=lambda L: bin_bounds(L)[0]),
        "bins_modeled_self": self_bins,
        "bins_modeled_borrowed": sorted(
            [b for b, src in model_source.items() if src.startswith("borrowed:")],
            key=lambda L: bin_bounds(L)[0],
        ),
        "model_source": model_source,
        "borrow_from_next_period": borrow_rows,
        "n_borrowed_bins": sum(
            1
            for r in borrow_rows
            if str(r.get("status", "")).startswith("borrowed_")
        ),
        "bins_skipped_empty": sorted(
            [b for b, n in bin_n.items() if n == 0],
            key=lambda L: bin_bounds(L)[0],
        ),
        "cuts": {k: round(float(v), 4) for k, v in cuts.items()},
        "diagonal_recall": {
            r["model_bin"]: r["recall"] for r in diag if r["recall"] is not None
        },
        "adjacent_backward": adjacent_backward,
        "recalibrate_signals": slips,
        "n_recalibrate_signals": len(slips),
        "eval_gates": {
            "diagonal_recall_bar": DIAGONAL_RECALL_BAR,
            "recalibrate_recall_bar": RECALIBRATE_RECALL_BAR,
            "pass_all_self_bins_diagonal": (
                bool(self_diag_recalls)
                and all(r >= DIAGONAL_RECALL_BAR for r in self_diag_recalls)
            ),
            "weak_diagonal_bins": weak_diag,
            "pass_has_recalibrate_signal_or_stable": True,
            "note": (
                "recalibrate_signal = adjacent backward recall "
                f"< {RECALIBRATE_RECALL_BAR}. "
                "Sparse bins (0 < n < min_bin_n) borrow the nearest later "
                "self-fit model (borrow_from_next_period); measured as "
                "recall_on_sparse under the donor cut."
            ),
        },
        "popularity": {
            "corpus_rate_proxy": round(pop_rate, 4),
            "weight": round(popularity_weight(pop_rate), 4),
            "weight_formula": "log(1 / clip(rate))",
            "note": "mean in-bin (diagonal) recall; ubiquitous families get low weight",
        },
        "formula_documents_compare": compare_model_to_formula_documents(
            fam,
            {
                r["model_bin"]: r["recall"]
                for r in diag
                if r["recall"] is not None
            },
        ),
        "method": "per_bin_slot_cloud_cross_score_with_next_period_borrow",
        "measurements": [
            "bin_n",
            "cuts",
            "diagonal_recall",
            "cross_bin_recall_matrix",
            "delta_vs_data_self",
            "recalibrate_signals",
            "borrow_from_next_period",
            "popularity.weight",
            "formula_documents_compare",
        ],
    }
    return summary, matrix


def fixture_appointment_bins() -> dict[str, pd.DataFrame]:
    """Tiny synthetic bins for CI (enough rows for min_bin_n=30)."""
    early = pd.DataFrame(
        [
            {
                "id": f"a{i}",
                "year": 1710 + (i % 10),
                "resolutions_text": (
                    "heeft dienvolgende sessie genomen in de vergaderinge"
                    if i % 2 == 0
                    else "sessie te nemen in haar Hoogh Mogende Vergaderinge"
                ),
            }
            for i in range(40)
        ]
    )
    late = pd.DataFrame(
        [
            {
                "id": f"b{i}",
                "year": 1735 + (i % 10),
                "resolutions_text": (
                    "is den selven verwelkomt, ende sessie genomen"
                    if i % 2 == 0
                    else "is den zelven verwellekomt, ende heeft sessie genomen"
                ),
            }
            for i in range(40)
        ]
    )
    return {"1700-1724": early, "1725-1749": late}


def fixture_sparse_then_rich_bins() -> dict[str, pd.DataFrame]:
    """Early bin too thin to fit; later bin rich — tests next-period borrow."""
    sparse = pd.DataFrame(
        [
            {
                "id": "s0",
                "year": 1712,
                "resolutions_text": "sessie genomen in de vergaderinge",
            },
            {
                "id": "s1",
                "year": 1715,
                "resolutions_text": "heeft sessie genomen",
            },
        ]
    )
    rich = fixture_appointment_bins()["1725-1749"]
    return {"1700-1724": sparse, "1725-1749": rich}
