"""STEPS1: char_wb TF-IDF sliding-window framing for formula candidates.

Fits IDF on the window corpus of a slice, scores cosine vs an opening template.
Does not run Smith-Waterman, DAG, GysBERT, or FormulaSearch.
"""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd
import pyarrow.parquet as pq
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from data_io import resolve
from formulation.formula_templates import (
    DEFAULT_FRAMING_ID,
    resolve_framing_template,
)

ANALYZER = "char_wb"
NGRAM_RANGE = (3, 5)
SUBLINEAR_TF = True
MIN_DF = 2
WINDOW_SIZE = 16
STRIDE = 2
ALIGN_PAD = 8
POC_YEAR = 1780
# Framing id + tokens/threshold come from formula_templates (not hardcoded).
TEMPLATE_ID_OPENING = DEFAULT_FRAMING_ID
_FRAMING = resolve_framing_template(TEMPLATE_ID_OPENING)
OPENING_TEMPLATE_18C = list(_FRAMING["tokens"])
DEFAULT_THRESHOLD = float(_FRAMING["threshold"])
HYPOTHESIS_THRESHOLD = not bool(_FRAMING["threshold_frozen"])


def tokenize(text: str) -> list[str]:
    """Whitespace tokens; matches STEPS0 fixture grain."""
    return str(text).split()


def window_text(tokens: list[str], start: int, end: int) -> str:
    return " ".join(tokens[start:end])


def sliding_windows(
    tokens: list[str],
    *,
    window_size: int = WINDOW_SIZE,
    stride: int = STRIDE,
) -> list[tuple[int, int, str]]:
    """Half-open [start, end) windows. Short texts yield one clipped window."""
    if window_size < 1:
        raise ValueError(f"window_size must be >= 1; got {window_size}")
    if stride < 1:
        raise ValueError(f"stride must be >= 1; got {stride}")
    n = len(tokens)
    if n == 0:
        return []
    if n <= window_size:
        return [(0, n, window_text(tokens, 0, n))]
    out: list[tuple[int, int, str]] = []
    start = 0
    while start + window_size <= n:
        end = start + window_size
        out.append((start, end, window_text(tokens, start, end)))
        start += stride
    last_start = n - window_size
    if not out or out[-1][0] != last_start:
        out.append((last_start, n, window_text(tokens, last_start, n)))
    return out


def make_vectorizer(*, min_df: int = MIN_DF) -> TfidfVectorizer:
    """Sharpened R1 family: char_wb 3–5 + sublinear_tf. No accents strip."""
    return TfidfVectorizer(
        analyzer=ANALYZER,
        ngram_range=NGRAM_RANGE,
        sublinear_tf=SUBLINEAR_TF,
        min_df=min_df,
    )


def default_opening_template(
    *,
    rows: list[dict[str, Any]] | None = None,
) -> tuple[str, list[str]]:
    """STEPS1 default framing tokens from ``formula_templates``.

    17c forms (*Op de Requeste*, *Is gelesen de requeste*, …) are deferred.
    STEPS0 ``formula_boundary_cases`` keeps its own span-gold template.
    """
    resolved = resolve_framing_template(TEMPLATE_ID_OPENING, rows=rows)
    return resolved["template_id"], list(resolved["tokens"])


def default_framing_threshold(
    *,
    rows: list[dict[str, Any]] | None = None,
) -> float:
    """Frozen STEPS1b cosine cut from ``formula_templates``."""
    return float(resolve_framing_template(TEMPLATE_ID_OPENING, rows=rows)["threshold"])


def opening_template_from_cases(
    cases: list[dict[str, Any]] | pd.DataFrame,
) -> tuple[str, list[str]]:
    """Optional: template tokens from STEPS0 fixtures (not the STEPS1 default)."""
    if isinstance(cases, pd.DataFrame):
        if cases.empty:
            raise ValueError("formula_boundary_cases is empty")
        row = cases.iloc[0]
        tokens = list(row["template"])
        case_id = str(row.get("case_id", "fixture"))
    else:
        if not cases:
            raise ValueError("formula_boundary_cases is empty")
        tokens = list(cases[0]["template"])
        case_id = str(cases[0].get("case_id", "fixture"))
    if not tokens:
        raise ValueError("Opening template is empty")
    return f"fixture_{case_id}", tokens


def load_resolution_slice(
    *,
    year: int | None = None,
    limit: int | None = None,
) -> pd.DataFrame:
    """Read ``resolutions_flat`` with optional year pushdown and head cap."""
    path = resolve("resolutions_flat")
    filters = None if year is None else [("year", "=", int(year))]
    frame = pq.read_table(path, filters=filters).to_pandas()
    if year is not None and frame.empty:
        raise ValueError(f"resolutions_flat has no rows for year={year}")
    if limit is not None:
        frame = frame.head(int(limit))
    return frame


def collect_windows(
    texts: pd.Series | list[str],
    ids: pd.Series | list[str],
    *,
    window_size: int = WINDOW_SIZE,
    stride: int = STRIDE,
) -> pd.DataFrame:
    """Build one row per sliding window; keeps resolution id and token offsets."""
    rows: list[dict[str, Any]] = []
    for doc_id, text in zip(map(str, ids), texts, strict=True):
        tokens = tokenize("" if text is None else str(text))
        for start, end, wtext in sliding_windows(
            tokens, window_size=window_size, stride=stride
        ):
            rows.append(
                {
                    "id": doc_id,
                    "token_start": int(start),
                    "token_end": int(end),
                    "n_tokens_doc": int(len(tokens)),
                    "window_text": wtext,
                }
            )
    return pd.DataFrame(rows)


def score_windows(
    windows: pd.DataFrame,
    template_tokens: list[str],
    *,
    template_id: str = TEMPLATE_ID_OPENING,
    threshold: float = DEFAULT_THRESHOLD,
    align_pad: int = ALIGN_PAD,
    min_df: int = MIN_DF,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Fit TF-IDF on window texts; cosine vs template; keep archival fields.

    Returns ``(all_scored_windows, threshold_notes)``. Candidates are rows with
    ``score >= threshold``; notes always cover the full score distribution.
    """
    if windows.empty:
        raise ValueError("No windows to score")
    if "window_text" not in windows.columns:
        raise ValueError("windows missing window_text")
    required = ("id", "token_start", "token_end")
    missing = [c for c in required if c not in windows.columns]
    if missing:
        raise ValueError(f"windows missing columns: {missing}")

    corpus = windows["window_text"].fillna("").astype(str)
    # Ensure template n-grams enter the vocabulary even if rare in the slice.
    fit_texts = pd.concat(
        [corpus, pd.Series([" ".join(template_tokens)], dtype="string")],
        ignore_index=True,
    )
    effective_min_df = min(int(min_df), max(1, len(fit_texts)))
    vectorizer = make_vectorizer(min_df=effective_min_df)
    matrix = vectorizer.fit_transform(fit_texts)
    window_matrix = matrix[:-1]
    template_vector = matrix[-1]
    scores = cosine_similarity(window_matrix, template_vector).ravel()

    scored = windows.copy()
    scored["score"] = scores.astype(np.float64)
    scored["template_id"] = template_id
    scored["above_threshold"] = scored["score"] >= float(threshold)
    n_doc = scored.get("n_tokens_doc")
    if n_doc is None:
        n_doc = scored["token_end"]
    scored["align_start"] = (scored["token_start"] - int(align_pad)).clip(lower=0)
    scored["align_end"] = (scored["token_end"] + int(align_pad)).clip(
        upper=n_doc.astype(int)
    )

    notes = threshold_notes(
        scored["score"],
        threshold=threshold,
        template_id=template_id,
        n_windows=len(scored),
        n_docs=int(scored["id"].nunique()),
        window_size=int(
            (scored["token_end"] - scored["token_start"]).median()
            if len(scored)
            else WINDOW_SIZE
        ),
        stride=None,
        align_pad=align_pad,
        min_df=effective_min_df,
        n_features=int(len(vectorizer.get_feature_names_out())),
    )
    return scored, notes


def select_candidates(scored: pd.DataFrame) -> pd.DataFrame:
    """Rows at or above the recorded threshold."""
    if "above_threshold" not in scored.columns:
        raise ValueError("scored windows missing above_threshold")
    return scored.loc[scored["above_threshold"]].reset_index(drop=True)


def threshold_notes(
    scores: pd.Series | np.ndarray,
    *,
    threshold: float,
    template_id: str,
    n_windows: int,
    n_docs: int,
    window_size: int,
    stride: int | None,
    align_pad: int,
    min_df: int,
    n_features: int,
) -> dict[str, Any]:
    """Score distribution + settings. Threshold hypothesis flag follows HYPOTHESIS_THRESHOLD."""
    arr = np.asarray(scores, dtype=np.float64)
    if arr.size == 0:
        percentiles: dict[str, float] = {}
    else:
        percentiles = {
            f"p{p}": float(np.percentile(arr, p)) for p in (50, 75, 90, 95, 99)
        }
    return {
        "template_id": template_id,
        "threshold": float(threshold),
        "threshold_is_hypothesis": HYPOTHESIS_THRESHOLD,
        "n_windows": int(n_windows),
        "n_docs": int(n_docs),
        "n_above_threshold": int((arr >= float(threshold)).sum()) if arr.size else 0,
        "score_min": float(arr.min()) if arr.size else None,
        "score_max": float(arr.max()) if arr.size else None,
        "score_mean": float(arr.mean()) if arr.size else None,
        **percentiles,
        "analyzer": ANALYZER,
        "ngram_range": f"{NGRAM_RANGE[0]}-{NGRAM_RANGE[1]}",
        "sublinear_tf": SUBLINEAR_TF,
        "min_df": int(min_df),
        "n_features": int(n_features),
        "window_size": int(window_size),
        "stride": stride,
        "align_pad": int(align_pad),
        "strip_accents": False,
        "stopwords": False,
        "classifier": None,
        "vectorizer": "TfidfVectorizer",
        "score_kind": "cosine_to_template",
    }


def frame_documents(
    frame: pd.DataFrame,
    template_tokens: list[str],
    *,
    template_id: str = TEMPLATE_ID_OPENING,
    text_col: str = "resolutions_text",
    id_col: str = "id",
    window_size: int = WINDOW_SIZE,
    stride: int = STRIDE,
    threshold: float = DEFAULT_THRESHOLD,
    align_pad: int = ALIGN_PAD,
    min_df: int = MIN_DF,
) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, Any]]:
    """Windows → scores → candidates for a resolutions-like table."""
    if text_col not in frame.columns:
        raise ValueError(f"Frame missing {text_col}")
    if id_col not in frame.columns:
        raise ValueError(f"Frame missing {id_col}")
    windows = collect_windows(
        frame[text_col],
        frame[id_col],
        window_size=window_size,
        stride=stride,
    )
    scored, notes = score_windows(
        windows,
        template_tokens,
        template_id=template_id,
        threshold=threshold,
        align_pad=align_pad,
        min_df=min_df,
    )
    notes["stride"] = int(stride)
    notes["window_size"] = int(window_size)
    candidates = select_candidates(scored)
    return scored, candidates, notes


def candidates_records(candidates: pd.DataFrame) -> list[dict[str, Any]]:
    """JSON-serialisable candidate rows (drop bulky full-slice scores)."""
    cols = [
        "id",
        "token_start",
        "token_end",
        "align_start",
        "align_end",
        "score",
        "template_id",
        "window_text",
        "n_tokens_doc",
    ]
    keep = [c for c in cols if c in candidates.columns]
    rows: list[dict[str, Any]] = []
    for row in candidates[keep].to_dict(orient="records"):
        out: dict[str, Any] = {}
        for key, value in row.items():
            if isinstance(value, (np.floating, float)):
                out[key] = float(value)
            elif isinstance(value, (np.integer, int)) and not isinstance(value, bool):
                out[key] = int(value)
            elif isinstance(value, np.bool_):
                out[key] = bool(value)
            else:
                out[key] = value
        rows.append(out)
    return rows
