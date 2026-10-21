"""Clean ES gold sampling against the *pinned* resolutions index.

After the 2026-10-21 re-pin, resolution ids are known not to be stable across
index generations: the stale ``*_es_gold`` sets have ~31% of rows labelled from
the wrong resolution (``docs/DECISIONS.md``). These helpers avoid that by
sampling ids from the pinned index and joining text from the same generation,
so the join is exact, and by verifying each sampled negative's label
individually rather than assuming label absence.

Extracted from ``scripts/recheck_es_gold_sample.py`` (2026-10-21) so STEPT1q
can reuse the validated sampler instead of importing one script from another.
"""

from __future__ import annotations

import math
from typing import Any

import pandas as pd

from data_io import resolve
from formulation.appointment_formula_type import YEAR_MAX, YEAR_MIN, sample_negatives
from formulation.republic_es import RepublicEsClient


def wilson(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    """Wilson score interval (default 95%)."""
    if n == 0:
        return (0.0, 0.0)
    p = k / n
    d = 1 + z * z / n
    c = p + z * z / (2 * n)
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return (max(0.0, (c - h) / d), min(1.0, (c + h) / d))


def gold_query_body(
    proposition_type: str,
    year: int,
    *,
    size: int,
    random_within_year: bool = False,
    random_seed: int | None = None,
) -> dict[str, Any]:
    """ES query body for one (proposition_type, year) gold slice.

    Default (``random_within_year=False``) is the systematic, lowest-id-first
    body used to produce the recorded recheck numbers in ``docs/DECISIONS.md``
    (``2026-10-21``): sorted by ``_id`` ascending. When
    ``random_within_year=True`` the same bool/filter query is wrapped in a
    ``function_score`` with ``random_score`` and the ``sort`` key is omitted
    so the default ``_score`` descending order (now random) controls
    selection.
    """
    filter_clauses = [
        {"term": {"metadata.proposition_type.keyword": proposition_type}},
        {"term": {"metadata.session_year": int(year)}},
    ]
    if random_within_year:
        return {
            "size": int(size),
            "_source": ["metadata.id", "metadata.session_year"],
            "query": {
                "function_score": {
                    "query": {"bool": {"filter": filter_clauses}},
                    "random_score": {
                        "seed": int(random_seed),
                        "field": "_seq_no",
                    },
                }
            },
        }
    return {
        "size": int(size),
        "sort": [{"_id": "asc"}],
        "_source": ["metadata.id", "metadata.session_year"],
        "query": {"bool": {"filter": filter_clauses}},
    }


def stratified_gold_ids(
    client: RepublicEsClient,
    proposition_type: str,
    *,
    per_year: int,
    random_within_year: bool = False,
    random_seed: int | None = None,
) -> list[dict[str, Any]]:
    """Up to `per_year` ids per session_year, from the pinned index.

    Default is SYSTEMATIC within year (lowest ids first, ``sort`` by
    ``_id`` ascending) — not random. The recorded clean recheck numbers in
    ``docs/DECISIONS.md`` were produced this way, so this default must not
    change. Pass ``random_within_year=True`` (with a ``random_seed``) to
    opt into random-within-year sampling for comparison.
    """
    rows: list[dict[str, Any]] = []
    index = client.config.resolutions_index
    for year in range(YEAR_MIN, YEAR_MAX + 1):
        body = gold_query_body(
            proposition_type,
            year,
            size=per_year,
            random_within_year=random_within_year,
            random_seed=random_seed,
        )
        hits = client.search(index, body).get("hits", {}).get("hits") or []
        for hit in hits:
            src = hit.get("_source") or {}
            meta = src.get("metadata") or {}
            rid = meta.get("id") or hit.get("_id")
            if rid:
                rows.append({"id": str(rid), "year": int(year)})
    return rows


def flat_texts(ids_years: list[dict[str, Any]]) -> pd.DataFrame:
    """Join text from resolutions_flat (same generation as the pinned index)."""
    import pyarrow.parquet as pq

    path = resolve("resolutions_flat")
    meta = pd.DataFrame(ids_years)
    if meta.empty:
        return meta
    out: list[dict[str, Any]] = []
    for year, grp in meta.groupby("year"):
        want = set(grp["id"].astype(str))
        chunk = pq.read_table(
            path,
            columns=["id", "resolutions_text"],
            filters=[("year", "=", int(year))],
        ).to_pandas()
        chunk["id"] = chunk["id"].astype(str)
        for rec in chunk.loc[chunk["id"].isin(want)].to_dict("records"):
            out.append(
                {
                    "id": rec["id"],
                    "year": int(year),
                    "resolutions_text": str(rec.get("resolutions_text") or ""),
                }
            )
    return pd.DataFrame(out)


def verified_negatives(
    client: RepublicEsClient,
    exclude: set[str],
    *,
    n: int,
    proposition_type: str,
    random_state: int,
) -> tuple[pd.DataFrame, int]:
    """Flat-sampled negatives, minus any the pinned index labels as the target."""
    neg = sample_negatives(
        exclude_ids=exclude,
        n=n,
        random_state=random_state,
        year_min=YEAR_MIN,
        year_max=YEAR_MAX,
    )
    got = client.mget(
        client.config.resolutions_index,
        neg["id"].astype(str).tolist(),
        ["metadata.proposition_type"],
    )
    bad = {
        rid
        for rid, src in got.items()
        if str(((src.get("metadata") or {}).get("proposition_type")) or "")
        == proposition_type
    }
    clean = neg.loc[~neg["id"].astype(str).isin(bad)].reset_index(drop=True)
    return clean, len(bad)


__all__ = [
    "flat_texts",
    "gold_query_body",
    "stratified_gold_ids",
    "verified_negatives",
    "wilson",
]
