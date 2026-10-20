"""STEPT0: 18c structural profile by proposition type (Track T).

Composition (full-population ES terms aggregation) and the characterisation
sample (floored per-type draw) answer different questions and must not be
conflated — the sample deliberately over-represents rare types, so it is
*never* the source for population proportions; ``composition_by_type`` is.

``evidence`` entries from ``full_resolutions`` are themselves ``PhraseMatch``
output (ngram/Levenshtein/char scores) — silver, not gold. Offsets are
normalised by the max offset seen within a resolution's own evidence, a proxy
for text length since full resolution text is deliberately not pulled (see
``formulation.republic_es.RESOLUTION_SOURCE``); treat normalised zone
positions as approximate.

Outcome flags come from ``formula_documents`` (1705-1796 only) and are
reported as observed closing boilerplate, never as a claim about what was
decided — see STEPT0 plan scope guards. Per-type formula structure is
``top_flag_combinations`` (co-occurring flag *sets*, the actual boilerplate
unit), not ``flag_rates`` (marginal per-flag rates) — a formula is a fixed
combination of markers, not any one marker independently.

Known data-quality caveat on two ``formula_documents`` flags: ``praeside_start``
and ``praesentibus_start`` mark presidium/attendance-list openers, not
resolution content. Small nonzero rates for them on resolution rows in a
profile reflect session-boundary parsing leakage upstream (attendance-list
text attached to an adjacent resolution), not a real resolution feature —
confirmed on the first STEPT0 run (1780).
"""

from __future__ import annotations

import re
from typing import Any

import pandas as pd

from data_io import load
from formulation.boundary.tfidf_windows import POC_YEAR
from formulation.republic_es import RESOLUTION_SOURCE, RepublicEsClient

YEAR_MIN_18C = 1705
YEAR_MAX_18C = 1796

# Start on one year (shared with STEPS1/Track L: same POC_YEAR) before
# widening — other years become comparisons/extensions, not the first pass.
POC_YEAR_MIN = POC_YEAR
POC_YEAR_MAX = POC_YEAR

DEFAULT_SAMPLE_TOTAL = 1000
DEFAULT_FLOOR = 30
DEFAULT_SEED = 20261019

NONE_TYPE_KEY = "(none)"

_RESOLUTION_INDEX_RE = re.compile(r"-resolution-(\d+)$")
_DOC_ID_RE = re.compile(
    r"^session-(?P<session_date>\d{4}-\d{2}-\d{2})-num-\d+-resolution-(?P<resolution_index>\d+)$"
)


def composition_by_type(
    client: RepublicEsClient,
    *,
    year_min: int = YEAR_MIN_18C,
    year_max: int = YEAR_MAX_18C,
) -> pd.DataFrame:
    """Full-population ``proposition_type`` proportions for the year range.

    Authoritative composition table. Never derive proportions from
    :func:`draw_typed_sample` — that draw is floored, not proportional.
    """
    body = {
        "size": 0,
        "track_total_hits": True,
        "query": {
            "range": {
                "metadata.session_year": {"gte": year_min, "lte": year_max}
            }
        },
        "aggs": {
            "ptype": {
                "terms": {
                    "field": "metadata.proposition_type.keyword",
                    "size": 100,
                    "missing": NONE_TYPE_KEY,
                }
            }
        },
    }
    response = client.search(client.config.resolutions_index, body)
    total = response["hits"]["total"]["value"]
    buckets = response["aggregations"]["ptype"]["buckets"]
    rows = [
        {
            "proposition_type": bucket["key"],
            "population_n": bucket["doc_count"],
            "population_pct": bucket["doc_count"] / total if total else 0.0,
        }
        for bucket in buckets
    ]
    frame = pd.DataFrame(rows).sort_values(
        "population_n", ascending=False
    ).reset_index(drop=True)
    frame.attrs["total_resolutions"] = total
    frame.attrs["year_min"] = year_min
    frame.attrs["year_max"] = year_max
    return frame


def allocate_sample_sizes(
    composition: pd.DataFrame,
    *,
    total_target: int = DEFAULT_SAMPLE_TOTAL,
    floor: int = DEFAULT_FLOOR,
) -> pd.DataFrame:
    """Proportional allocation with a per-type floor, capped at population.

    Deliberately over-samples the tail relative to true proportions (see
    ``composition_by_type``). ``capped_by_population`` marks types whose
    population is below ``floor`` — the whole population is drawn instead.
    """
    out = composition.copy()
    total_population = out["population_n"].sum()
    proportional = (
        out["population_n"] / total_population * total_target
    ).round().astype(int)
    target = proportional.clip(lower=floor)
    out["sample_n"] = pd.concat([target, out["population_n"]], axis=1).min(axis=1)
    out["capped_by_population"] = out["sample_n"] < floor
    out["inclusion_prob"] = out["sample_n"] / out["population_n"]
    return out


def draw_typed_sample(
    client: RepublicEsClient,
    allocation: pd.DataFrame,
    *,
    year_min: int = YEAR_MIN_18C,
    year_max: int = YEAR_MAX_18C,
    seed: int = DEFAULT_SEED,
) -> list[dict[str, Any]]:
    """Randomised per-type draw at the sizes in ``allocation['sample_n']``.

    Returns raw ES ``_source`` dicts (one per hit) tagged with the type the
    allocation targeted and that type's inclusion probability, so findings
    can be reweighted to population scale later if needed.
    """
    rows: list[dict[str, Any]] = []
    for record in allocation.to_dict(orient="records"):
        ptype = record["proposition_type"]
        size = int(record["sample_n"])
        if size <= 0:
            continue
        type_filter: dict[str, Any]
        if ptype == NONE_TYPE_KEY:
            type_filter = {
                "bool": {
                    "must_not": {
                        "exists": {"field": "metadata.proposition_type"}
                    }
                }
            }
        else:
            type_filter = {
                "term": {"metadata.proposition_type.keyword": ptype}
            }
        body = {
            "size": size,
            "_source": RESOLUTION_SOURCE,
            "query": {
                "function_score": {
                    "query": {
                        "bool": {
                            "filter": [
                                {
                                    "range": {
                                        "metadata.session_year": {
                                            "gte": year_min,
                                            "lte": year_max,
                                        }
                                    }
                                },
                                type_filter,
                            ]
                        }
                    },
                    "random_score": {"seed": seed, "field": "_seq_no"},
                }
            },
        }
        response = client.search(client.config.resolutions_index, body)
        for hit in response["hits"]["hits"]:
            source = dict(hit.get("_source") or {})
            source["_sampled_proposition_type"] = ptype
            source["_inclusion_prob"] = record["inclusion_prob"]
            rows.append(source)
    return rows


def _resolution_index_from_id(resolution_id: Any) -> int | None:
    match = _RESOLUTION_INDEX_RE.search(str(resolution_id or ""))
    return int(match.group(1)) if match else None


def normalize_sample_rows(raw_rows: list[dict[str, Any]]) -> pd.DataFrame:
    """Flatten raw ``_source`` dicts from :func:`draw_typed_sample`."""
    records: list[dict[str, Any]] = []
    for source in raw_rows:
        meta = source.get("metadata") or {}
        resolution_id = meta.get("id") or source.get("id")
        records.append(
            {
                "id": resolution_id,
                "session_date": meta.get("session_date"),
                "resolution_index": _resolution_index_from_id(resolution_id),
                "resolution_type": meta.get("resolution_type"),
                "proposition_type": meta.get("proposition_type"),
                "sampled_proposition_type": source.get(
                    "_sampled_proposition_type"
                ),
                "inclusion_prob": source.get("_inclusion_prob"),
                "session_year": meta.get("session_year"),
                "evidence": source.get("evidence") or [],
                "stats": source.get("stats") or {},
            }
        )
    return pd.DataFrame.from_records(records)


def load_outcome_flags() -> pd.DataFrame:
    """``formula_documents`` resolution rows keyed by (date, resolution_index).

    ``doc_id`` is date-based (``session-YYYY-MM-DD-num-1-resolution-N``) —
    unlike ``resolutions_flat`` / ES, which key by inventory ``num``. The
    ``num`` segment here is constant ``1`` and carries no information; see
    the ``formula_documents`` manifest entry.
    """
    frame = load("formula_documents")
    frame = frame[frame["doc_id"].str.contains("-resolution-")].copy()
    extracted = frame["doc_id"].str.extract(_DOC_ID_RE)
    frame["session_date"] = extracted["session_date"]
    frame["resolution_index"] = extracted["resolution_index"].astype("Int64")
    return frame


def _flag_columns(frame: pd.DataFrame) -> list[str]:
    return [col for col in frame.columns if frame[col].dtype == bool]


def join_outcome_flags(sample: pd.DataFrame) -> pd.DataFrame:
    """Left-join ``formula_documents`` outcome flags onto a resolution sample.

    Join key is (``session_date``, ``resolution_index``) — the only key
    present on both sides. Unmatched rows are kept (flags null) and marked
    via ``outcome_joined`` rather than dropped.

    The flag columns are cast to pandas' nullable ``boolean`` dtype after the
    merge: a plain left-join on bool columns silently upcasts them to
    ``object`` wherever NaN is introduced for unmatched rows, which breaks
    any later ``dtype == bool`` detection (and ``.mean()``) on them. The
    realised flag-column list is attached via ``.attrs["flag_columns"]``
    rather than re-derived from the joined frame's dtypes downstream.
    """
    outcomes = load_outcome_flags()
    flag_cols = _flag_columns(outcomes)
    out = sample.merge(
        outcomes[["session_date", "resolution_index", *flag_cols]],
        on=["session_date", "resolution_index"],
        how="left",
    )
    if flag_cols:
        out[flag_cols] = out[flag_cols].astype("boolean")
    out["outcome_joined"] = (
        out[flag_cols[0]].notna() if flag_cols else False
    )
    out.attrs["flag_columns"] = flag_cols
    return out


def _top_flag_combinations(
    group: pd.DataFrame,
    flag_cols: list[str],
    *,
    top_k: int = 5,
) -> list[dict[str, Any]]:
    """Most frequent co-occurring flag *sets* — the formula signature.

    Marginal per-flag rates (``flag_rates``) can't show that a formula is a
    fixed combination of markers, not any one marker alone — e.g. the
    "information resolution" pattern is ``ontfangen_start`` AND
    ``advertentie`` AND ``geen_resolutie`` together, not any single flag at
    0.5 marginal rate. Restricted to rows with a known outcome join
    (``outcome_joined``); unmatched rows have no flag information to combine.
    """
    known = group[group["outcome_joined"]] if "outcome_joined" in group else group
    known_n = len(known)
    if not known_n or not flag_cols:
        return []
    patterns: dict[tuple[str, ...], int] = {}
    for row in known[flag_cols].itertuples(index=False):
        combo = tuple(sorted(col for col, val in zip(flag_cols, row) if val))
        patterns[combo] = patterns.get(combo, 0) + 1
    ranked = sorted(patterns.items(), key=lambda kv: -kv[1])[:top_k]
    return [
        {"flags": list(combo), "n": n, "rate": n / known_n}
        for combo, n in ranked
    ]


def build_profile_records(
    joined: pd.DataFrame,
    composition: pd.DataFrame,
) -> list[dict[str, Any]]:
    """One record per ``proposition_type``: zones, lengths, outcome rates.

    Carries ``population_n`` / ``population_pct`` from ``composition`` (3a)
    onto every record, so no sampled type is ever read against the wrong
    (floored) denominator.
    """
    flag_cols = joined.attrs.get("flag_columns") or []
    joined = joined.copy()
    joined["n_words"] = joined["stats"].apply(lambda s: (s or {}).get("words"))
    joined["n_paragraphs"] = joined["stats"].apply(
        lambda s: (s or {}).get("paragraphs")
    )

    label_rows: list[dict[str, Any]] = []
    for row in joined.itertuples():
        evidence = row.evidence or []
        offsets = [
            entry.get("offset")
            for entry in evidence
            if isinstance(entry, dict) and entry.get("offset") is not None
        ]
        max_offset = max(offsets) if offsets else None
        for entry in evidence:
            if not isinstance(entry, dict):
                continue
            offset = entry.get("offset")
            norm_offset = (
                offset / max_offset
                if max_offset and offset is not None
                else None
            )
            for label in entry.get("label") or []:
                label_rows.append(
                    {
                        "proposition_type": row.sampled_proposition_type,
                        "label": label,
                        "norm_offset": norm_offset,
                    }
                )
    label_frame = pd.DataFrame.from_records(
        label_rows, columns=["proposition_type", "label", "norm_offset"]
    )

    records: list[dict[str, Any]] = []
    for comp_row in composition.to_dict(orient="records"):
        ptype = comp_row["proposition_type"]
        group = joined[joined["sampled_proposition_type"] == ptype]
        sample_n = len(group)

        label_zones: list[dict[str, Any]] = []
        type_labels = label_frame[label_frame["proposition_type"] == ptype]
        for label, label_group in type_labels.groupby("label"):
            offsets = label_group["norm_offset"].dropna()
            label_zones.append(
                {
                    "label": label,
                    "n": int(len(label_group)),
                    "median_offset": float(offsets.median())
                    if not offsets.empty
                    else None,
                    "q1_offset": float(offsets.quantile(0.25))
                    if not offsets.empty
                    else None,
                    "q3_offset": float(offsets.quantile(0.75))
                    if not offsets.empty
                    else None,
                }
            )

        flag_rates = {}
        if sample_n and flag_cols:
            for col in flag_cols:
                rate = group[col].mean()
                flag_rates[col] = None if pd.isna(rate) else float(rate)
        top_flag_combinations = _top_flag_combinations(group, flag_cols)

        words = group["n_words"].dropna()
        paragraphs = group["n_paragraphs"].dropna()

        records.append(
            {
                "proposition_type": ptype,
                "population_n": int(comp_row["population_n"]),
                "population_pct": float(comp_row["population_pct"]),
                "sample_n": sample_n,
                "inclusion_prob": float(group["inclusion_prob"].iloc[0])
                if sample_n
                else None,
                "outcome_join_coverage": float(group["outcome_joined"].mean())
                if sample_n
                else None,
                "n_words_median": float(words.median()) if not words.empty else None,
                "n_words_q1": float(words.quantile(0.25)) if not words.empty else None,
                "n_words_q3": float(words.quantile(0.75)) if not words.empty else None,
                "n_paragraphs_median": float(paragraphs.median())
                if not paragraphs.empty
                else None,
                "flag_rates": flag_rates,
                "top_flag_combinations": top_flag_combinations,
                "label_zones": sorted(
                    label_zones, key=lambda z: -z["n"]
                ),
            }
        )
    return records
