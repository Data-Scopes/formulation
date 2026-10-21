"""STEPT1q: compare retrieval arms for ONE formula on clean post-re-pin gold.

Four arms locate the same formula over the same rows:

1. ``substring_wording`` — the type's ``wording_flags()`` regex (the baseline
   STEPT1n actually reported, so the only apples-to-apples comparison against
   its 0.915).
2. ``substring_scheme``  — the scheme's ``search phrase`` from
   ``formula_schemes_sample.json`` (Doc B's nominated arm 1).
3. ``tfidf_window``      — ``boundary.tfidf_windows`` cosine of sliding windows
   vs the canonic.
4. ``dag_frozen`` / ``dag_clean_boot`` — slot cloud + ``align_dag``. The frozen
   model's cloud was bootstrapped from the *stale* ``*_es_gold``, so a second
   variant re-bootstraps from a split of the clean sample and recalibrates its
   cut at p20. G1 is judged on ``dag_clean_boot``; ``dag_frozen`` is reported as
   the deployed number.

Gold is NOT the stale ``*_es_gold`` sets (~31% mislabelled, see DECISIONS.md
2026-10-21). It is sampled per year from the *pinned* index with text joined
from the same generation, reusing the validated sampler in
``scripts/recheck_es_gold_sample.py``.

Spans from every arm live on one grid: ``align_tokenize(text)`` joined with
single spaces, so ``tfidf_windows.tokenize`` (whitespace split) reproduces it.
Substring arms are *anchor* matchers (a few characters), so they are measured by
containment, never by IoU.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

import pandas as pd

from formulation.appointment_formula_type import (
    FALLBACK_CUT,
    HOLDOUT_FRAC,
    RNG,
    YEAR_MAX,
    YEAR_MIN,
    align_tokenize,
    calibrate_cut,
    split_bootstrap_holdout,
)
from formulation.boundary import tfidf_windows as tw
from formulation.es_gold_sample import wilson

_REPO_ROOT = Path(__file__).resolve().parents[1]
# A repo doc, not a dataset: the schemes sample is the hand-written source of
# the ``search phrase`` arm and is not registered in data_manifest.toml.
SCHEMES_PATH = (
    _REPO_ROOT / "docs/proofs/multi-template-registry/formula_schemes_sample.json"
)

# Per-type wiring. ``scheme`` is the phrasename in formula_schemes_sample.json.
TYPES: dict[str, dict[str, Any]] = {
    "missive": {
        "proposition_type": "missive",
        "formula_type_id": "missive_ontfangen",
        "scheme": "ontfangen_start",
        "module": "formulation.missive_formula_type",
        "canonic": "MISSIVE_CANONIC",
        "token_re": "_MISSIVE_TOKEN_RE",
        "build_cloud": "build_missive_cloud",
        "presence": "fit_missive_presence_model",
    },
    "requeste": {
        "proposition_type": "rekest",
        "formula_type_id": "requeste_geleesen",
        "scheme": "requeste_start",
        "module": "formulation.requeste_formula_type",
        "canonic": "REQUESTE_CANONIC",
        "token_re": "_REQUESTE_TOKEN_RE",
        "build_cloud": "build_requeste_cloud",
        "presence": "fit_requeste_presence_model",
    },
    "advies": {
        "proposition_type": "advies",
        "formula_type_id": "advies_geleesen",
        "scheme": "advies",
        "module": "formulation.advies_formula_type",
        "canonic": "ADVIES_CANONIC",
        "token_re": "_ADVIES_TOKEN_RE",
        "build_cloud": "build_advies_cloud",
        "presence": "fit_advies_presence_model",
    },
}

SPAN_ARMS = ("tfidf_window", "tfidf_window_p20", "dag_frozen", "dag_clean_boot")
ANCHOR_ARMS = ("substring_wording", "substring_scheme")


def load_type_api(type_key: str) -> dict[str, Any]:
    """Resolve a type's canonic / cloud builder / scorer / wording regex."""
    import importlib

    spec = TYPES[type_key]
    mod = importlib.import_module(spec["module"])
    presence = importlib.import_module("formulation.formula_type_presence")
    return {
        **spec,
        "canonic_text": getattr(mod, spec["canonic"]),
        "build_cloud": getattr(mod, spec["build_cloud"]),
        "score_text": mod.score_text,
        "wording_flags": mod.wording_flags,
        "token_re": getattr(mod, spec["token_re"]),
        "fit_presence": getattr(presence, spec["presence"]),
    }


def scheme_search_phrase(phrasename: str, *, path: str | Path | None = None) -> str:
    """The scheme's ``search phrase`` regex fragment (Doc B arm 1)."""
    src = Path(path) if path else SCHEMES_PATH
    with open(src, encoding="utf-8") as fh:
        rows = json.load(fh)
    for row in rows:
        if str(row.get("phrasename")) == phrasename:
            phrase = row.get("search phrase")
            if not phrase:
                raise ValueError(f"scheme {phrasename!r} has no search phrase")
            return str(phrase)
    raise KeyError(f"no scheme named {phrasename!r} in {src}")


def normalized_tokens(text: str) -> list[str]:
    """The common span grid for every arm."""
    return align_tokenize(str(text or ""))


def anchor_span(
    tokens: list[str], pattern: re.Pattern[str]
) -> tuple[int, int] | None:
    """First token matching the anchor regex, as a half-open token span."""
    for idx, tok in enumerate(tokens):
        if pattern.search(tok):
            return (idx, idx + 1)
    return None


def iou(a: tuple[int, int] | None, b: tuple[int, int] | None) -> float | None:
    """Token-span intersection over union; None if either span is absent."""
    if a is None or b is None:
        return None
    inter = max(0, min(a[1], b[1]) - max(a[0], b[0]))
    union = (a[1] - a[0]) + (b[1] - b[0]) - inter
    return float(inter / union) if union > 0 else None


def contained(
    anchor: tuple[int, int] | None, span: tuple[int, int] | None
) -> bool | None:
    """Is the anchor token inside the span? None if either is absent."""
    if anchor is None or span is None:
        return None
    return bool(anchor[0] >= span[0] and anchor[1] <= span[1])


def tfidf_arm_scores(
    frame: pd.DataFrame,
    canonic: str,
    *,
    template_id: str,
    threshold: float,
) -> pd.DataFrame:
    """Best window per row: score + token span on the normalized grid.

    Windows are built over ``normalized_tokens`` joined with spaces, so the
    returned ``token_start``/``token_end`` index the same grid the DAG uses.
    """
    norm = frame["resolutions_text"].astype(str).map(
        lambda t: " ".join(normalized_tokens(t))
    )
    windows = tw.collect_windows(norm, frame["id"].astype(str))
    if windows.empty:
        return pd.DataFrame(
            columns=["id", "tfidf_score", "tfidf_start", "tfidf_end"]
        )
    scored, _notes = tw.score_windows(
        windows,
        normalized_tokens(canonic),
        template_id=template_id,
        threshold=float(threshold),
    )
    best = scored.loc[scored.groupby("id")["score"].idxmax()].reset_index(drop=True)
    return best.rename(
        columns={
            "score": "tfidf_score",
            "token_start": "tfidf_start",
            "token_end": "tfidf_end",
        }
    )[["id", "tfidf_score", "tfidf_start", "tfidf_end"]]


def score_arms(
    gold: pd.DataFrame,
    neg: pd.DataFrame,
    *,
    api: dict[str, Any],
    clouds: dict[str, Any],
    cuts: dict[str, float],
    tfidf_threshold: float,
) -> tuple[pd.DataFrame, float]:
    """One row per resolution with every arm's fire flag and token span.

    Gold and negatives are scored in a **single** pass so the TF-IDF arm fits
    one vocabulary/IDF over all rows. Fitting gold and negatives separately
    would put recall and FP on different scales and make the arm's threshold
    meaningless.

    The TF-IDF window is reported at two thresholds on the SAME scores (no
    refit): ``tfidf_window`` at the frozen ``tfidf_threshold`` (calibrated for
    ``opening_requeste_18c``, not this template), and ``tfidf_window_p20`` at
    a threshold calibrated on this sample's own gold best-window scores (p20,
    via ``calibrate_cut``). Returns the scored frame plus that p20 threshold.
    """
    frames = []
    for role, frame in (("gold", gold), ("negative", neg)):
        if frame is None or frame.empty:
            continue
        f = frame.copy()
        f["role"] = role
        frames.append(f)
    if not frames:
        return pd.DataFrame()
    combined = pd.concat(frames, ignore_index=True)

    anchor_patterns = {
        "substring_wording": api["token_re"],
        "substring_scheme": re.compile(
            scheme_search_phrase(api["scheme"]), re.IGNORECASE
        ),
    }

    tfidf = tfidf_arm_scores(
        combined,
        api["canonic_text"],
        template_id=api["formula_type_id"],
        threshold=tfidf_threshold,
    ).set_index("id")

    # p20 of GOLD rows' best-window scores on *this* sample - the frozen
    # tfidf_threshold belongs to a different template, so it is reported
    # alongside, not relied on alone.
    gold_ids = (
        set(gold["id"].astype(str)) if gold is not None and not gold.empty else set()
    )
    gold_tfidf_scores = (
        tfidf.loc[tfidf.index.isin(gold_ids), "tfidf_score"].astype(float).tolist()
        if not tfidf.empty
        else []
    )
    tfidf_threshold_p20 = calibrate_cut(gold_tfidf_scores, fallback=tfidf_threshold)

    rows: list[dict[str, Any]] = []
    for rec in combined.to_dict("records"):
        rid = str(rec["id"])
        text = str(rec.get("resolutions_text") or "")
        tokens = normalized_tokens(text)
        out: dict[str, Any] = {
            "id": rid,
            "year": rec.get("year"),
            "role": rec.get("role"),
            "n_tokens": len(tokens),
        }

        # Anchor arms. wording_flags() decides the fire; the token scan only
        # locates it, so a fire with no locatable token is recorded honestly.
        out["substring_wording_fire"] = bool(
            any(api["wording_flags"](text).values())
        )
        for arm, pattern in anchor_patterns.items():
            span = anchor_span(tokens, pattern)
            if arm == "substring_scheme":
                out[f"{arm}_fire"] = span is not None
            out[f"{arm}_start"] = span[0] if span else None
            out[f"{arm}_end"] = span[1] if span else None

        # TF-IDF window arm, at two thresholds on the same best-window score.
        if rid in tfidf.index:
            trow = tfidf.loc[rid]
            score = float(trow["tfidf_score"])
            start, end = int(trow["tfidf_start"]), int(trow["tfidf_end"])
            out["tfidf_window_score"] = score
            out["tfidf_window_fire"] = bool(score >= float(tfidf_threshold))
            out["tfidf_window_start"] = start
            out["tfidf_window_end"] = end
            out["tfidf_window_p20_score"] = score
            out["tfidf_window_p20_fire"] = bool(score >= float(tfidf_threshold_p20))
            out["tfidf_window_p20_start"] = start
            out["tfidf_window_p20_end"] = end
        else:
            out["tfidf_window_score"] = None
            out["tfidf_window_fire"] = False
            out["tfidf_window_start"] = None
            out["tfidf_window_end"] = None
            out["tfidf_window_p20_score"] = None
            out["tfidf_window_p20_fire"] = False
            out["tfidf_window_p20_start"] = None
            out["tfidf_window_p20_end"] = None

        # DAG arms.
        for arm in ("dag_frozen", "dag_clean_boot"):
            cloud = clouds.get(arm)
            if cloud is None:
                out[f"{arm}_score"] = None
                out[f"{arm}_fire"] = None
                out[f"{arm}_start"] = None
                out[f"{arm}_end"] = None
                continue
            res = api["score_text"](text, cloud)
            out[f"{arm}_score"] = float(res["score"])
            out[f"{arm}_fire"] = bool(float(res["score"]) >= float(cuts[arm]))
            out[f"{arm}_start"] = int(res["start_idx"])
            out[f"{arm}_end"] = int(res["end_idx"])
        rows.append(out)
    return pd.DataFrame(rows), float(tfidf_threshold_p20)


def _span(row: dict[str, Any], arm: str) -> tuple[int, int] | None:
    s, e = row.get(f"{arm}_start"), row.get(f"{arm}_end")
    if s is None or e is None or pd.isna(s) or pd.isna(e):
        return None
    return (int(s), int(e))


def arm_rates(
    gold: pd.DataFrame, neg: pd.DataFrame, arms: list[str]
) -> list[dict[str, Any]]:
    """Recall + FP with Wilson CIs per arm, on identical rows."""
    out: list[dict[str, Any]] = []
    for arm in arms:
        col = f"{arm}_fire"
        if col not in gold.columns or gold[col].isna().all():
            continue
        g_hits = int(gold[col].fillna(False).astype(bool).sum())
        n_hits = int(neg[col].fillna(False).astype(bool).sum()) if len(neg) else 0
        recall = round(g_hits / len(gold), 4) if len(gold) else None
        rec: dict[str, Any] = {
            "arm": arm,
            "n_gold": int(len(gold)),
            "recall": recall,
            "recall_ci95": [round(x, 4) for x in wilson(g_hits, len(gold))],
            "n_negatives": int(len(neg)),
            "fp": round(n_hits / len(neg), 4) if len(neg) else None,
            "fp_ci95": [round(x, 4) for x in wilson(n_hits, len(neg))],
        }
        # A regex tuned for a different period/type can go 0/N on gold - that
        # is not a measured recall, it is inapplicability. Flag it so callers
        # (deltas, reports) do not treat the zero as a real result.
        if recall == 0.0:
            rec["applicable"] = False
            rec["applicability_note"] = (
                f"0/{rec['n_gold']} gold hits - treat as inapplicable to this "
                "type/period, not as a measured result"
            )
        else:
            rec["applicable"] = True
        out.append(rec)
    return out


def recall_matched_fp(
    gold_scores: list[float], neg_scores: list[float], target_recall: float
) -> dict[str, Any]:
    """FP at a cut chosen to hit ``target_recall`` on gold, for cross-arm comparison.

    Two score arms compared at their own independently-chosen cuts are
    answering "how loose is this arm", not "which arm discriminates better" -
    e.g. ``dag_frozen`` at 4.5 vs ``dag_clean_boot`` at 3.0 is a cut
    difference, not a quality difference. Anchoring both arms to the SAME
    gold recall removes that confound.

    The cut is the ``(1 - target_recall)`` quantile of ``gold_scores`` (so
    that fraction of gold sits at or above it); ``fp`` is then the share of
    ``neg_scores`` at or above that same cut, and ``achieved_recall`` is the
    actual gold share at or above it (may differ slightly from
    ``target_recall`` with small/discrete samples).
    """
    if not gold_scores or not neg_scores:
        return {
            "target_recall": float(target_recall),
            "cut": None,
            "fp": None,
            "achieved_recall": None,
        }
    gold_s = pd.Series(gold_scores, dtype=float)
    neg_s = pd.Series(neg_scores, dtype=float)
    cut = float(gold_s.quantile(1.0 - float(target_recall)))
    return {
        "target_recall": float(target_recall),
        "cut": round(cut, 4),
        "fp": round(float((neg_s >= cut).mean()), 4),
        "achieved_recall": round(float((gold_s >= cut).mean()), 4),
    }


def midpoint_delta(
    a: tuple[int, int] | None, b: tuple[int, int] | None
) -> float | None:
    """Absolute distance between span midpoints, in tokens."""
    if a is None or b is None:
        return None
    return abs(((a[0] + a[1]) / 2) - ((b[0] + b[1]) / 2))


def span_agreement(gold: pd.DataFrame) -> dict[str, Any]:
    """Span agreement, measured per pair by a geometry the pair admits.

    IoU is only meaningful between arms whose spans have comparable length, so
    it is used for DAG-vs-DAG alone. A TF-IDF window is a fixed 16-token
    locator while a DAG span is the formula itself (~5-7 tokens), which caps
    their IoU near 0.35 **by construction** — so that pair is measured by
    whether the window contains the DAG span, plus midpoint distance. Anchor
    arms are a few characters wide and are measured by containment only.
    """
    recs = gold.to_dict("records")

    # Comparable-length spans only.
    ious: dict[str, list[float]] = {}
    vals = [
        v
        for row in recs
        if row.get("dag_frozen_fire") and row.get("dag_clean_boot_fire")
        if (v := iou(_span(row, "dag_frozen"), _span(row, "dag_clean_boot")))
        is not None
    ]
    if vals:
        ious["dag_frozen__dag_clean_boot"] = vals

    containment: dict[str, Any] = {}
    offsets: dict[str, Any] = {}

    def _containment(inner: str, outer: str) -> None:
        hits, deltas_ = [], []
        for row in recs:
            if not (row.get(f"{inner}_fire") and row.get(f"{outer}_fire")):
                continue
            c = contained(_span(row, inner), _span(row, outer))
            if c is None:
                continue
            hits.append(c)
            d = midpoint_delta(_span(row, inner), _span(row, outer))
            if d is not None:
                deltas_.append(d)
        if hits:
            containment[f"{inner}__in__{outer}"] = {
                "n": len(hits),
                "rate": round(sum(hits) / len(hits), 4),
            }
        if deltas_:
            offsets[f"{inner}__vs__{outer}"] = {
                "n": len(deltas_),
                "median_tokens": round(float(pd.Series(deltas_).median()), 2),
                "p90_tokens": round(float(pd.Series(deltas_).quantile(0.90)), 2),
            }

    # The DAG span should sit inside the window the TF-IDF arm picked.
    for dag in ("dag_frozen", "dag_clean_boot"):
        _containment(dag, "tfidf_window")
    # Anchors inside every span arm.
    for anchor in ANCHOR_ARMS:
        for span_arm in SPAN_ARMS:
            _containment(anchor, span_arm)

    iou_summary = {
        pair: {
            "n": len(vals),
            "median": round(float(pd.Series(vals).median()), 4),
            "p10": round(float(pd.Series(vals).quantile(0.10)), 4),
            "disjoint_share": round(
                sum(1 for v in vals if v == 0.0) / len(vals), 4
            ),
        }
        for pair, vals in ious.items()
    }
    return {
        "iou": iou_summary,
        "containment": containment,
        "midpoint_offset": offsets,
        "note": (
            "IoU is reported for DAG-vs-DAG only: a 16-token TF-IDF window vs "
            "a ~6-token DAG span caps IoU near 0.35 by construction, so that "
            "pair is judged by containment + midpoint distance instead."
        ),
    }


def fp_overlap(neg: pd.DataFrame, arms: list[str]) -> dict[str, Any]:
    """How many arms fire per false positive; unanimous share.

    ``arms`` must already be filtered to applicable arms (``arm_rates``'
    ``applicable`` flag) - an inapplicable arm never fires, so including it
    would understate unanimity among the arms that can actually fire.
    """
    arms_counted = [a for a in arms if f"{a}_fire" in neg.columns]
    cols = [f"{a}_fire" for a in arms_counted]
    if not cols or neg.empty:
        return {"arms_counted": arms_counted}
    fired = neg[cols].fillna(False).astype(bool)
    per_row = fired.sum(axis=1)
    any_fire = int((per_row > 0).sum())
    return {
        "n_arms": len(cols),
        "arms_counted": arms_counted,
        "n_negatives": int(len(neg)),
        "n_negatives_any_arm_fires": any_fire,
        "by_n_arms_firing": {
            str(k): int(v) for k, v in per_row.value_counts().sort_index().items()
        },
        "unanimous_share_of_fp": (
            round(int((per_row == len(cols)).sum()) / any_fire, 4)
            if any_fire
            else None
        ),
    }


def deltas(rates: list[dict[str, Any]]) -> dict[str, Any]:
    """Substring-minus-DAG recall/FP deltas; G1 is judged on dag_clean_boot."""
    by_arm = {r["arm"]: r for r in rates}
    out: dict[str, Any] = {}
    for dag in ("dag_clean_boot", "dag_frozen"):
        if dag not in by_arm or by_arm[dag].get("applicable") is False:
            continue
        for sub in ANCHOR_ARMS:
            if sub not in by_arm or by_arm[sub].get("applicable") is False:
                continue
            d_recall = (by_arm[sub]["recall"] or 0) - (by_arm[dag]["recall"] or 0)
            d_fp = (by_arm[sub]["fp"] or 0) - (by_arm[dag]["fp"] or 0)
            if d_recall >= 0 and d_fp <= 0:
                verdict = "substring_wins"
            elif d_recall <= 0 and d_fp >= 0:
                verdict = "substring_loses"
            else:
                verdict = "trades"
            out[f"{sub}__vs__{dag}"] = {
                "d_recall": round(d_recall, 4),
                "d_fp": round(d_fp, 4),
                "verdict": verdict,
            }
    out["g1_judged_on"] = "substring_* vs dag_clean_boot"
    return out


def build_clean_boot_cloud(
    gold: pd.DataFrame,
    *,
    api: dict[str, Any],
    pool: pd.DataFrame | None = None,
    random_state: int = RNG,
) -> tuple[dict[str, Any], float, dict[str, Any]]:
    """Re-bootstrap the cloud from a split of CLEAN text; p20 cut.

    If ``pool`` is given (non-empty), the cloud is bootstrapped from a split
    of ``pool`` instead of ``gold``: the pool's bootstrap split builds the
    cloud and the pool's holdout split calibrates the p20 cut. ``gold`` is
    then never touched by the cloud or the cut, so the eval rows stay
    genuinely unseen and the comparison against ``dag_frozen`` is not
    confounded by bootstrap volume as well as gold quality.

    If ``pool`` is ``None`` or empty, falls back to today's behaviour: split
    ``gold`` itself into bootstrap/holdout (the eval rows do inform the cloud
    and cut in that case).
    """
    if pool is not None and not pool.empty:
        source = pool
        bootstrap_source = "disjoint_pool"
    else:
        source = gold
        bootstrap_source = "eval_gold"
    boot, hold = split_bootstrap_holdout(
        source, holdout_frac=HOLDOUT_FRAC, random_state=random_state
    )
    cloud, notes = api["build_cloud"](
        boot["resolutions_text"].astype(str).tolist(),
        year_min=YEAR_MIN,
        year_max=YEAR_MAX,
    )
    hold_scores = [
        api["score_text"](t, cloud)["score"]
        for t in hold["resolutions_text"].astype(str).tolist()
    ]
    cut = float(calibrate_cut(hold_scores, fallback=FALLBACK_CUT))
    return (
        cloud,
        cut,
        {
            **notes,
            "n_bootstrap": int(len(boot)),
            "n_holdout": int(len(hold)),
            "cut_rule": "p20_holdout_positive_scores_clean_sample",
            "bootstrap_source": bootstrap_source,
        },
    )


def summarize(
    *,
    type_key: str,
    gold: pd.DataFrame,
    neg: pd.DataFrame,
    arms: list[str],
    cuts: dict[str, float],
    tfidf_threshold: float,
    index: str,
    sampling: str,
    n_gold_requested: int,
    n_negatives_dropped: int,
) -> dict[str, Any]:
    rates = arm_rates(gold, neg, arms)
    # fp_overlap's unanimity is only meaningful over arms that can actually
    # fire, so an arm arm_rates flagged inapplicable (0/N gold hits) is
    # dropped here before counting FP overlap.
    applicable_arms = [r["arm"] for r in rates if r.get("applicable", True)]
    return {
        "step": "STEPT1q",
        "type": type_key,
        "formula_type_id": TYPES[type_key]["formula_type_id"],
        "proposition_type": TYPES[type_key]["proposition_type"],
        "index": index,
        "sampling": sampling,
        "gold_definition": "clean_stratified_pinned_index_join",
        "n_gold_requested": int(n_gold_requested),
        "n_gold_joined": int(len(gold)),
        "n_negatives": int(len(neg)),
        "n_negatives_dropped_as_target_type": int(n_negatives_dropped),
        "cuts": {k: round(float(v), 4) for k, v in cuts.items()},
        "tfidf_threshold": round(float(tfidf_threshold), 4),
        "arms": rates,
        "deltas": deltas(rates),
        "span_agreement": span_agreement(gold),
        "fp_overlap": fp_overlap(neg, applicable_arms),
        "caveats": [
            "dag_frozen's cloud was bootstrapped from the stale *_es_gold "
            "(~31% mislabelled); dag_clean_boot is the fair comparison for G1.",
            "Substring arms are anchor matchers: containment, never IoU.",
            "Absolute rates carry sampling error - read the Wilson CIs, and "
            "the full *_es_gold re-fetch is still owed.",
        ],
    }


def _fmt_num(x: Any) -> str:
    """Compact fixed-width-ish number for a terminal table; ``-`` for None."""
    if x is None or (isinstance(x, float) and pd.isna(x)):
        return "-"
    if isinstance(x, bool):
        return str(x)
    if isinstance(x, float):
        return f"{x:.4f}"
    return str(x)


def _fmt_ci(ci: Any) -> str:
    if not ci or len(ci) != 2:
        return "-"
    return f"[{_fmt_num(ci[0])}, {_fmt_num(ci[1])}]"


def _pad_table(rows: list[tuple[str, ...]]) -> list[str]:
    """Left-justify each column to the widest cell, two spaces between."""
    if not rows:
        return []
    widths = [max(len(str(r[i])) for r in rows) for i in range(len(rows[0]))]
    return [
        "  ".join(str(cell).ljust(widths[i]) for i, cell in enumerate(row))
        for row in rows
    ]


def format_summary(metrics: dict[str, Any]) -> str:
    """Plain-text, terminal-aligned summary of a ``summarize()`` metrics dict.

    A raw ``json.dumps`` dump of this metrics dict is unreadable at a
    terminal; this renders the header, per-arm table, cuts, recall-matched
    FP table, span-agreement line, and FP-overlap line a human can scan in
    one pass. No external dependencies.
    """
    lines: list[str] = []

    boot_source = metrics.get("bootstrap_source", "?")
    boot_pool = metrics.get("n_bootstrap_pool")
    lines.append(
        f"STEPT1q  type={metrics.get('type')}  "
        f"formula_type_id={metrics.get('formula_type_id')}  "
        f"index={metrics.get('index')}"
    )
    lines.append(
        f"sampling_mode={metrics.get('sampling_mode')}  "
        f"n_gold_joined={metrics.get('n_gold_joined')}  "
        f"n_negatives={metrics.get('n_negatives')}  "
        f"bootstrap_source={boot_source} (pool={boot_pool})"
    )
    lines.append("")

    arms = metrics.get("arms") or []
    arm_rows: list[tuple[str, ...]] = [
        ("arm", "recall", "recall_ci95", "fp", "fp_ci95", "applicable")
    ]
    for a in arms:
        arm_rows.append(
            (
                str(a.get("arm")),
                _fmt_num(a.get("recall")),
                _fmt_ci(a.get("recall_ci95")),
                _fmt_num(a.get("fp")),
                _fmt_ci(a.get("fp_ci95")),
                str(a.get("applicable", True)),
            )
        )
    lines.append("Arms:")
    lines.extend("  " + row for row in _pad_table(arm_rows))
    lines.append("")

    cuts = metrics.get("cuts") or {}
    lines.append(
        "Cuts: "
        + (", ".join(f"{k}={_fmt_num(v)}" for k, v in cuts.items()) or "-")
    )
    lines.append("")

    recall_matched = metrics.get("recall_matched") or {}
    rm_arms = {k: v for k, v in recall_matched.items() if k != "note"}
    lines.append("Recall-matched FP:")
    if rm_arms:
        rm_rows: list[tuple[str, ...]] = [
            ("arm", "target_recall", "cut", "fp", "achieved_recall")
        ]
        for arm, vals in rm_arms.items():
            rm_rows.append(
                (
                    arm,
                    _fmt_num(vals.get("target_recall")),
                    _fmt_num(vals.get("cut")),
                    _fmt_num(vals.get("fp")),
                    _fmt_num(vals.get("achieved_recall")),
                )
            )
        lines.extend("  " + row for row in _pad_table(rm_rows))
    else:
        lines.append("  (no scored arms)")
    if recall_matched.get("note"):
        lines.append(f"  note: {recall_matched['note']}")
    lines.append("")

    span_agreement_ = metrics.get("span_agreement") or {}
    iou = span_agreement_.get("iou") or {}
    containment = span_agreement_.get("containment") or {}
    dag_iou_median = next(iter(iou.values()), {}).get("median") if iou else None
    dag_window = next(
        (
            v
            for k, v in containment.items()
            if k.split("__in__")[0].startswith("dag_") and k.endswith("__in__tfidf_window")
        ),
        None,
    )
    anchor_dag = next(
        (
            v
            for k, v in containment.items()
            if k.split("__in__")[0] in ANCHOR_ARMS and "__in__dag_" in k
        ),
        None,
    )
    lines.append(
        "Span agreement: "
        f"DAG-DAG IoU median={_fmt_num(dag_iou_median)}  "
        f"DAG-in-window containment="
        f"{_fmt_num(dag_window.get('rate') if dag_window else None)}  "
        f"anchor-in-DAG containment="
        f"{_fmt_num(anchor_dag.get('rate') if anchor_dag else None)}"
    )
    lines.append("")

    fp_overlap_ = metrics.get("fp_overlap") or {}
    lines.append(
        "FP overlap: "
        f"n_any_arm_fires={fp_overlap_.get('n_negatives_any_arm_fires')}  "
        f"unanimous_share={_fmt_num(fp_overlap_.get('unanimous_share_of_fp'))}  "
        f"arms_counted={fp_overlap_.get('arms_counted')}"
    )

    return "\n".join(lines)


def fixture_frames() -> tuple[pd.DataFrame, pd.DataFrame]:
    """Tiny in-memory smoke rows (no ES, no resolutions_flat)."""
    gold = pd.DataFrame(
        [
            {
                "id": "g1",
                "year": 1780,
                "resolutions_text": (
                    "Ontfangen een missive van den Heer Raadpensionaris, "
                    "houdende advertentie. Waarop geen resolutie is gevallen."
                ),
            },
            {
                "id": "g2",
                "year": 1781,
                "resolutions_text": (
                    "ONtfangen eene Missiue van de Gedeputeerden, houdende "
                    "advertentie van hunne aankomst."
                ),
            },
            {
                "id": "g3",
                "year": 1782,
                "resolutions_text": (
                    "Ontfangen een brief van den Commandeur, waarop is "
                    "gedelibereert en goedgevonden."
                ),
            },
        ]
    )
    neg = pd.DataFrame(
        [
            {
                "id": "n1",
                "year": 1780,
                "resolutions_text": (
                    "IS ter Vergaderinge geleesen de Requeste van eenige "
                    "ingezetenen, waarop geen resolutie is gevallen."
                ),
            },
            {
                "id": "n2",
                "year": 1781,
                "resolutions_text": (
                    "Geleesen het Advis van de Generaliteits Rekenkamer op "
                    "de voorgaande requeste."
                ),
            },
        ]
    )
    return gold, neg


__all__ = [
    "ANCHOR_ARMS",
    "SPAN_ARMS",
    "TYPES",
    "anchor_span",
    "arm_rates",
    "build_clean_boot_cloud",
    "contained",
    "deltas",
    "fixture_frames",
    "format_summary",
    "fp_overlap",
    "iou",
    "load_type_api",
    "midpoint_delta",
    "normalized_tokens",
    "recall_matched_fp",
    "scheme_search_phrase",
    "score_arms",
    "span_agreement",
    "summarize",
    "tfidf_arm_scores",
    "wilson",
]
