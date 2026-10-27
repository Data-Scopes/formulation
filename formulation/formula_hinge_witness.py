"""STEPT1ai: adjudicate archaeology witnesses vs hinge archetypes.

Char_wb 3–5 TF-IDF cosine → near / mid / far. Soft membership only.
Does not mint hinges, merge families, or mutate formula_templates.
"""

from __future__ import annotations

from collections import Counter
from pathlib import Path
from typing import Any, Sequence

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from data_io import load_jsonl
from formulation.formula_hinge_ledger import (
    FIXTURE_PATH as HINGE_FIXTURE_PATH,
    default_seed_rows,
    load_fixture_rows as load_hinge_fixture_rows,
)

LOGICAL_NAME = "formula_hinge_witness_adjudication"
METRICS_NAME = "formula_hinge_witness_metrics"
WITNESS_FIXTURE_PATH = (
    Path(__file__).resolve().parents[1]
    / "tests"
    / "fixtures"
    / "formula_hinge_witnesses.jsonl"
)

ANALYZER = "char_wb"
NGRAM_RANGE = (3, 5)
SUBLINEAR_TF = True

# Provisional soft-membership cuts (CLI-overridable).
NEAR_CUT = 0.80
MID_CUT = 0.50

BANDS = frozenset({"near", "mid", "far"})

ADJUDICATION_COLUMNS = (
    "witness_id",
    "witness_text",
    "witness_norm",
    "phrase_freq",
    "source",
    "best_hinge_id",
    "best_sim",
    "second_hinge_id",
    "second_sim",
    "band",
    "human_keep",
    "human_note",
)


def _norm_text(s: str | None) -> str:
    t = (s or "").strip().lower()
    return t if t else " "


def hinge_targets(rows: Sequence[dict[str, Any]]) -> list[dict[str, Any]]:
    """Archetypes with a canonic string (pockets excluded)."""
    out: list[dict[str, Any]] = []
    for r in rows:
        can = r.get("canonic")
        if not can or not str(can).strip():
            continue
        out.append(
            {
                "hinge_id": str(r.get("hinge_id") or ""),
                "canonic": str(can).strip(),
                "canonic_norm": _norm_text(str(can)),
                "place_band": r.get("place_band"),
                "move": r.get("move"),
                "layer": r.get("layer"),
                "status": r.get("status"),
            }
        )
    return out


def band_for_sim(
    sim: float,
    *,
    near_cut: float = NEAR_CUT,
    mid_cut: float = MID_CUT,
) -> str:
    if float(sim) >= float(near_cut):
        return "near"
    if float(sim) >= float(mid_cut):
        return "mid"
    return "far"


def make_vectorizer() -> TfidfVectorizer:
    return TfidfVectorizer(
        analyzer=ANALYZER,
        ngram_range=NGRAM_RANGE,
        sublinear_tf=SUBLINEAR_TF,
        min_df=1,
    )


def adjudicate_witnesses(
    hinges: Sequence[dict[str, Any]],
    witnesses: Sequence[dict[str, Any]],
    *,
    near_cut: float = NEAR_CUT,
    mid_cut: float = MID_CUT,
) -> list[dict[str, Any]]:
    """Score each witness against hinge canonics; return adjudication rows.

    Fits IDF on the union of canonic + witness strings. Argmax cosine → band.
    """
    targets = hinge_targets(hinges)
    if not targets:
        raise ValueError("need >= 1 hinge with canonic")
    if not witnesses:
        return []

    canonic_texts = [t["canonic_norm"] for t in targets]
    wit_texts: list[str] = []
    wit_meta: list[dict[str, Any]] = []
    for i, w in enumerate(witnesses):
        raw = str(w.get("witness_text") or w.get("exemplar") or w.get("phrase") or "")
        norm = str(
            w.get("witness_norm")
            or w.get("exemplar_norm")
            or w.get("phrase_norm")
            or _norm_text(raw)
        )
        if not norm.strip():
            continue
        wit_texts.append(_norm_text(norm))
        wid = w.get("witness_id") or w.get("family_id") or f"wit_{i:04d}"
        wit_meta.append(
            {
                "witness_id": str(wid),
                "witness_text": raw or norm,
                "witness_norm": _norm_text(norm),
                "phrase_freq": int(w.get("phrase_freq") or w.get("phrase_freq_max") or 0),
                "source": str(w.get("source") or "formula_family_candidates"),
            }
        )
    if not wit_texts:
        return []

    corpus = canonic_texts + wit_texts
    vec = make_vectorizer()
    mat = vec.fit_transform(corpus)
    n_h = len(canonic_texts)
    hinge_mat = mat[:n_h]
    wit_mat = mat[n_h:]
    sim = cosine_similarity(wit_mat, hinge_mat)

    rows: list[dict[str, Any]] = []
    for i, meta in enumerate(wit_meta):
        scores = sim[i]
        order = np.argsort(-scores)
        best_i = int(order[0])
        best_sim = float(scores[best_i])
        second_i = int(order[1]) if len(order) > 1 else best_i
        second_sim = float(scores[second_i]) if len(order) > 1 else 0.0
        band = band_for_sim(best_sim, near_cut=near_cut, mid_cut=mid_cut)
        rows.append(
            {
                "witness_id": meta["witness_id"],
                "witness_text": meta["witness_text"],
                "witness_norm": meta["witness_norm"],
                "phrase_freq": meta["phrase_freq"],
                "source": meta["source"],
                "best_hinge_id": targets[best_i]["hinge_id"],
                "best_sim": round(best_sim, 6),
                "second_hinge_id": targets[second_i]["hinge_id"]
                if len(order) > 1
                else None,
                "second_sim": round(second_sim, 6) if len(order) > 1 else None,
                "band": band,
                "human_keep": None,
                "human_note": None,
            }
        )
    return rows


def adjudication_metrics(
    rows: Sequence[dict[str, Any]],
    *,
    n_hinge_targets: int,
    near_cut: float = NEAR_CUT,
    mid_cut: float = MID_CUT,
) -> dict[str, Any]:
    by_band = Counter(str(r.get("band")) for r in rows)
    by_hinge_near: Counter[str] = Counter()
    for r in rows:
        if r.get("band") == "near":
            by_hinge_near[str(r.get("best_hinge_id"))] += 1
    sims = [float(r.get("best_sim") or 0.0) for r in rows]
    return {
        "step": "STEPT1ai",
        "n_witnesses": len(rows),
        "n_hinge_targets": int(n_hinge_targets),
        "by_band": {b: int(by_band.get(b, 0)) for b in ("near", "mid", "far")},
        "by_hinge_near": dict(sorted(by_hinge_near.items())),
        "best_sim_p50": float(np.median(sims)) if sims else None,
        "best_sim_p90": float(np.percentile(sims, 90)) if sims else None,
        "near_cut": float(near_cut),
        "mid_cut": float(mid_cut),
        "vectorizer": {
            "analyzer": ANALYZER,
            "ngram_range": list(NGRAM_RANGE),
            "sublinear_tf": SUBLINEAR_TF,
        },
        "note": (
            "Soft membership only. Mid does not auto-mint or auto-merge. "
            "Hinge ledger and formula_templates untouched."
        ),
    }


def load_witness_fixture(path: Path | None = None) -> list[dict[str, Any]]:
    return list(load_jsonl(path or WITNESS_FIXTURE_PATH))


def witnesses_from_families(families: Sequence[dict[str, Any]]) -> list[dict[str, Any]]:
    """Map formula_family_candidates rows → witness dicts."""
    out: list[dict[str, Any]] = []
    for f in families:
        ex = f.get("exemplar") or f.get("exemplar_norm")
        if not ex:
            continue
        out.append(
            {
                "witness_id": str(f.get("family_id") or ""),
                "witness_text": str(ex),
                "witness_norm": str(f.get("exemplar_norm") or _norm_text(str(ex))),
                "phrase_freq": int(f.get("phrase_freq_max") or 0),
                "source": "formula_family_candidates",
            }
        )
    return out


def default_hinge_rows() -> list[dict[str, Any]]:
    if HINGE_FIXTURE_PATH.is_file():
        return load_hinge_fixture_rows()
    return default_seed_rows()
