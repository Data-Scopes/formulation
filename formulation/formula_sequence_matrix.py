"""STEPT1z: probabilistic formula sequence matrix + harvest shortlist.

Primary product: row-stochastic adjacent transition matrix
P(next=B | current=A), including END. Companion: support n (+ precedes, gaps).

Order = token start_idx from canonic/substring matches (presence-gated for
blueprints). Not a full DAG re-fit.
"""

from __future__ import annotations

import json
import math
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from data_io import load
from formulation.advies_formula_type import ADVIES_CANONIC
from formulation.advies_formula_type import FORMULA_TYPE_ID as ADVIES_ID
from formulation.appointment_formula_type import FORMULA_TYPE_ID as APPOINTMENT_ID
from formulation.appointment_formula_type import SESSIE_CANONIC, WELKOM_CANONIC
from formulation.boundary.tfidf_windows import POC_YEAR, tokenize
from formulation.composition_unknown import ACCEPTED_TYPE_IDS
from formulation.missive_formula_type import FORMULA_TYPE_ID as MISSIVE_ID
from formulation.missive_formula_type import MISSIVE_CANONIC
from formulation.rapport_formula_type import FORMULA_TYPE_ID as RAPPORT_ID
from formulation.rapport_formula_type import RAPPORT_CANONIC
from formulation.requeste_formula_type import FORMULA_TYPE_ID as REQUESTE_ID
from formulation.requeste_formula_type import REQUESTE_CANONIC
from formulation.requeste_op_de_formula_type import FORMULA_TYPE_ID as REQUESTE_OP_DE_ID
from formulation.requeste_op_de_formula_type import REQUESTE_OP_DE_CANONIC

DEFAULT_YEAR = POC_YEAR
EMPTY_ID = "EMPTY"
END_ID = "END"
ROW_SUM_EPS = 1e-6
EXAMPLES_PER_NODE = 3
TEXT_TRUNC_CHARS = 280
TOP_EDGE_EXAMPLES = 20
MIN_EDGE_N_ADJACENT = 5
PICK_RULE = "shortest_hit"

_REPO_ROOT = Path(__file__).resolve().parents[1]
SCHEMES_PATH = (
    _REPO_ROOT / "docs/proofs/multi-template-registry/formula_schemes_sample.json"
)

# Blueprint positioning surfaces (substring; first hit). Appointment uses sessie
# as the span anchor (STEPT1p: sessie backbone).
BLUEPRINT_SURFACES: dict[str, tuple[str, ...]] = {
    APPOINTMENT_ID: (SESSIE_CANONIC, WELKOM_CANONIC),
    ADVIES_ID: (ADVIES_CANONIC, "geleesen het Advis", "Advis van"),
    REQUESTE_ID: (REQUESTE_CANONIC, "geleesen de Requeste"),
    MISSIVE_ID: (MISSIVE_CANONIC, "Ontfangen een missive", "Ontfangen een Missive"),
    REQUESTE_OP_DE_ID: (REQUESTE_OP_DE_CANONIC, "Op de Requeste"),
    RAPPORT_ID: (RAPPORT_CANONIC, "gehoord het rapport", "gehoort het rapport"),
}

# STEPT1u residual pocket surfaces (harvest; not named).
POCKET_HARVEST: tuple[dict[str, Any], ...] = (
    {
        "formula_id": "harvest_voordracht_voorgedragen",
        "surface": "voorgedragen",
        "source": "empty_band_1780",
        "pocket": "voordracht",
        "notes": "STEPT1u praeses/provincial bring-in surface",
    },
    {
        "formula_id": "harvest_voordracht_ingebragt",
        "surface": "ingebragt",
        "source": "empty_band_1780",
        "pocket": "voordracht",
        "notes": "STEPT1u provincial Gedeputeerden surface",
    },
    {
        "formula_id": "harvest_conclusie_handen",
        "surface": "in handen",
        "source": "empty_band_1780",
        "pocket": "conclusie_handen",
        "notes": "STEPT1u conclusie+handen residual",
    },
    {
        "formula_id": "harvest_conclusie_handen_bare",
        "surface": "handen",
        "source": "empty_band_1780",
        "pocket": "conclusie_handen",
        "notes": "broader handen cue (noisier)",
    },
)


def _norm_canonic(raw: Any) -> str | None:
    if raw is None:
        return None
    s = str(raw).strip()
    if not s or s in {".", "...", "…"}:
        return None
    # schemes sometimes glue alternatives with /
    if "/" in s and len(s) > 40:
        s = s.split("/")[0].strip()
    return s or None


def load_scheme_harvest(path: Path | None = None) -> list[dict[str, Any]]:
    """Usable canonic / search-phrase surfaces from formula_schemes_sample."""
    raw = json.loads((path or SCHEMES_PATH).read_text(encoding="utf-8"))
    out: list[dict[str, Any]] = []
    seen: set[str] = set()
    for row in raw:
        name = str(row.get("phrasename") or "").strip()
        if not name:
            continue
        surface = _norm_canonic(row.get("canonic_formula"))
        if surface is None:
            sp = row.get("search phrase")
            if isinstance(sp, str) and sp.strip() and not re.search(r"[\[\\\*\+\?]", sp):
                surface = sp.strip()
        if surface is None:
            continue
        fid = f"harvest_scheme_{name}"
        if fid in seen:
            continue
        seen.add(fid)
        out.append(
            {
                "formula_id": fid,
                "surface": surface,
                "source": "formula_schemes_sample",
                "pocket": None,
                "scheme_phrasename": name,
                "notes": str(row.get("intention") or row.get("function") or ""),
            }
        )
    return out


def harvest_catalog() -> list[dict[str, Any]]:
    """Scheme surfaces + STEPT1u pocket surfaces (dedup by formula_id)."""
    rows = list(POCKET_HARVEST) + load_scheme_harvest()
    # Drop scheme rows that collide with blueprint canonics (exact surface).
    blueprint_surfaces = {
        s.lower() for surfaces in BLUEPRINT_SURFACES.values() for s in surfaces
    }
    out: list[dict[str, Any]] = []
    for row in rows:
        if str(row["surface"]).lower() in blueprint_surfaces:
            continue
        out.append(dict(row))
    return out


def _find_surface(tokens: list[str], surface: str) -> tuple[int, int] | None:
    """First whitespace-token span matching surface (casefold)."""
    needle = tokenize(surface)
    if not needle or not tokens:
        return None
    n = len(needle)
    needle_l = [t.casefold() for t in needle]
    toks_l = [t.casefold() for t in tokens]
    for i in range(0, len(toks_l) - n + 1):
        if toks_l[i : i + n] == needle_l:
            return i, i + n
    # Fallback: joined substring on casefold text with space markers
    hay = " ".join(toks_l)
    needle_s = " ".join(needle_l)
    pos = hay.find(needle_s)
    if pos < 0:
        return None
    # map char offset back to approx token index
    prefix = hay[:pos]
    start = prefix.count(" ") if prefix else 0
    return start, start + n


def _blueprint_hit(
    text: str,
    formula_id: str,
    *,
    present: bool,
) -> dict[str, Any] | None:
    if not present:
        return None
    tokens = tokenize(text)
    for surface in BLUEPRINT_SURFACES.get(formula_id, ()):
        span = _find_surface(tokens, surface)
        if span is not None:
            return {
                "formula_id": formula_id,
                "role": "blueprint",
                "start_idx": span[0],
                "end_idx": span[1],
                "surface": surface,
            }
    # Present by DAG/presence but canonic miss — park at start so it still
    # participates in bags/order weakly (start 0).
    return {
        "formula_id": formula_id,
        "role": "blueprint",
        "start_idx": 0,
        "end_idx": 0,
        "surface": None,
        "position_fallback": True,
    }


def _harvest_hit(text: str, row: dict[str, Any]) -> dict[str, Any] | None:
    tokens = tokenize(text)
    span = _find_surface(tokens, str(row["surface"]))
    if span is None:
        return None
    return {
        "formula_id": str(row["formula_id"]),
        "role": "harvest",
        "start_idx": span[0],
        "end_idx": span[1],
        "surface": str(row["surface"]),
        "pocket": row.get("pocket"),
        "source": row.get("source"),
    }


def ordered_hits_for_text(
    text: str,
    *,
    present_blueprint_ids: set[str],
    harvest_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    hits: list[dict[str, Any]] = []
    for fid in sorted(present_blueprint_ids):
        h = _blueprint_hit(text, fid, present=True)
        if h is not None:
            hits.append(h)
    for row in harvest_rows:
        h = _harvest_hit(text, row)
        if h is not None:
            hits.append(h)
    hits.sort(
        key=lambda h: (int(h["start_idx"]), int(h["end_idx"]), str(h["formula_id"]))
    )
    # Dedup identical formula_id keeping earliest span
    seen: set[str] = set()
    out: list[dict[str, Any]] = []
    for h in hits:
        fid = str(h["formula_id"])
        if fid in seen:
            continue
        seen.add(fid)
        out.append(h)
    return out


def load_presence_presents(*, year: int) -> dict[str, set[str]]:
    """id → set of accepted blueprint formula_type_ids with present=True."""
    presence = pd.DataFrame(load("formula_type_presence_scores"))
    presence["id"] = presence["id"].astype(str)
    presence["year"] = pd.to_numeric(presence["year"], errors="coerce")
    slice_ = presence.loc[presence["year"] == int(year)].copy()
    slice_["present"] = slice_["present"].astype(bool)
    accepted = {str(x) for x in ACCEPTED_TYPE_IDS}
    slice_ = slice_.loc[
        slice_["present"] & slice_["formula_type_id"].astype(str).isin(accepted)
    ]
    out: dict[str, set[str]] = defaultdict(set)
    for rec in slice_.to_dict(orient="records"):
        out[str(rec["id"])].add(str(rec["formula_type_id"]))
    return dict(out)


def build_sequences(
    texts: pd.DataFrame,
    *,
    present_by_id: dict[str, set[str]],
    harvest_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Per-resolution ordered hit list (+ EMPTY flag)."""
    rows: list[dict[str, Any]] = []
    for rec in texts.to_dict(orient="records"):
        rid = str(rec["id"])
        year = int(rec["year"]) if rec.get("year") is not None else None
        text = str(rec.get("resolutions_text") or "")
        present = present_by_id.get(rid, set())
        hits = ordered_hits_for_text(
            text, present_blueprint_ids=present, harvest_rows=harvest_rows
        )
        rows.append(
            {
                "id": rid,
                "year": year,
                "n_hits": len(hits),
                "ordered_ids": [h["formula_id"] for h in hits],
                "hits": hits,
                "is_empty": len(hits) == 0,
            }
        )
    return rows


def _quantile(vals: list[float], q: float) -> float | None:
    if not vals:
        return None
    return float(np.quantile(np.asarray(vals, dtype=float), q))


def build_transition_counts(
    sequences: list[dict[str, Any]],
) -> tuple[Counter[tuple[str, str]], Counter[str], dict[tuple[str, str], list[float]], Counter[tuple[str, str]], Counter[str]]:
    """Adjacent transitions (+ END), precedes pairs, gaps, from-counts."""
    adjacent: Counter[tuple[str, str]] = Counter()
    n_from: Counter[str] = Counter()
    gaps: dict[tuple[str, str], list[float]] = defaultdict(list)
    precedes: Counter[tuple[str, str]] = Counter()
    n_empty = 0

    for seq in sequences:
        hits = list(seq.get("hits") or [])
        if not hits:
            n_empty += 1
            n_from[EMPTY_ID] += 1
            adjacent[(EMPTY_ID, END_ID)] += 1
            continue
        ids = [str(h["formula_id"]) for h in hits]
        for i, hid in enumerate(ids):
            n_from[hid] += 1
            if i + 1 < len(ids):
                nxt = ids[i + 1]
                adjacent[(hid, nxt)] += 1
                gap = float(hits[i + 1]["start_idx"] - hits[i]["end_idx"])
                gaps[(hid, nxt)].append(gap)
            else:
                adjacent[(hid, END_ID)] += 1
            for j in range(i + 1, len(ids)):
                precedes[(hid, ids[j])] += 1
    n_from[EMPTY_ID] = n_from.get(EMPTY_ID, 0) + 0  # ensure key if unused
    if n_empty and EMPTY_ID not in n_from:
        n_from[EMPTY_ID] = n_empty
    return adjacent, n_from, gaps, precedes, Counter({EMPTY_ID: n_empty})


def build_probabilistic_matrix(
    sequences: list[dict[str, Any]],
    *,
    node_meta: dict[str, dict[str, Any]],
    year: int,
) -> dict[str, Any]:
    """Row-stochastic adjacent P + companion n / precedes / gaps."""
    adjacent, n_from, gaps, precedes, empty_counts = build_transition_counts(sequences)
    n_empty = int(empty_counts.get(EMPTY_ID, 0))
    if n_empty:
        n_from[EMPTY_ID] = n_empty

    # Node universe: observed from/to + catalog meta + sentinels
    nodes = sorted(
        set(node_meta)
        | set(n_from)
        | {b for a, b in adjacent}
        | {END_ID, EMPTY_ID}
    )
    # Column set for stochastic rows = all possible next states seen or END
    columns = sorted(set(nodes) | {END_ID})

    edge_rows: list[dict[str, Any]] = []
    wide_p: dict[str, dict[str, float]] = {}
    wide_n: dict[str, dict[str, int]] = {}

    for a in nodes:
        if a == END_ID:
            continue  # END has no outgoing distribution
        row_n_from = int(n_from.get(a, 0))
        row_p: dict[str, float] = {}
        row_n: dict[str, int] = {}
        # collect outgoing
        targets = {b for (x, b) in adjacent if x == a} | {END_ID}
        for b in sorted(targets):
            n_ab = int(adjacent.get((a, b), 0))
            p = (n_ab / row_n_from) if row_n_from else 0.0
            if n_ab == 0 and b != END_ID:
                continue
            if n_ab == 0 and b == END_ID and row_n_from == 0:
                continue
            row_p[b] = p
            row_n[b] = n_ab
            gap_list = gaps.get((a, b), [])
            n_prec = int(precedes.get((a, b), 0))
            p_prec = (n_prec / row_n_from) if row_n_from else 0.0
            edge_rows.append(
                {
                    "from_id": a,
                    "to_id": b,
                    "p_adjacent": round(p, 6),
                    "n_adjacent": n_ab,
                    "n_from": row_n_from,
                    "p_precedes": round(p_prec, 6) if b != END_ID else None,
                    "n_precedes": n_prec if b != END_ID else None,
                    "gap_median": (
                        None
                        if not gap_list
                        else round(_quantile(gap_list, 0.5) or 0.0, 4)
                    ),
                    "gap_p25": (
                        None
                        if not gap_list
                        else round(_quantile(gap_list, 0.25) or 0.0, 4)
                    ),
                    "gap_p75": (
                        None
                        if not gap_list
                        else round(_quantile(gap_list, 0.75) or 0.0, 4)
                    ),
                    "from_role": (node_meta.get(a) or {}).get("role"),
                    "to_role": (
                        "sentinel"
                        if b in {END_ID, EMPTY_ID}
                        else (node_meta.get(b) or {}).get("role")
                    ),
                }
            )
        # ensure row sums to 1 when n_from > 0: if missing mass, it means
        # we skipped zero cells — mass already on observed targets only.
        # Renormalize if floating dust; if row empty but n_from>0, put on END.
        mass = sum(row_p.values())
        if row_n_from > 0:
            if mass <= 0:
                row_p[END_ID] = 1.0
                row_n[END_ID] = row_n.get(END_ID, 0)
            elif not math.isclose(mass, 1.0, abs_tol=ROW_SUM_EPS):
                row_p = {k: v / mass for k, v in row_p.items()}
        wide_p[a] = {c: round(float(row_p.get(c, 0.0)), 6) for c in columns if c != a or c == END_ID}
        # keep full column set for matrix consumers
        wide_p[a] = {c: round(float(row_p.get(c, 0.0)), 6) for c in columns}
        wide_n[a] = {c: int(row_n.get(c, 0)) for c in columns}

    node_rows: list[dict[str, Any]] = []
    for nid in nodes:
        meta = node_meta.get(nid, {})
        role = meta.get("role")
        if nid in {END_ID, EMPTY_ID}:
            role = "sentinel"
        node_rows.append(
            {
                "formula_id": nid,
                "role": role,
                "n_from": int(n_from.get(nid, 0)),
                "surface": meta.get("surface"),
                "source": meta.get("source"),
                "pocket": meta.get("pocket"),
                "notes": meta.get("notes"),
            }
        )

    # Row-sum check
    row_sum_ok = True
    row_sums: dict[str, float] = {}
    for a, dist in wide_p.items():
        s = float(sum(dist.values()))
        row_sums[a] = round(s, 6)
        if int(n_from.get(a, 0)) > 0 and not math.isclose(s, 1.0, abs_tol=1e-4):
            row_sum_ok = False

    return {
        "year": int(year),
        "n_resolutions": int(len(sequences)),
        "n_empty": n_empty,
        "frac_empty": round(n_empty / len(sequences), 4) if sequences else None,
        "primary": "p_adjacent_row_stochastic",
        "row_sum_ok": row_sum_ok,
        "row_sums": row_sums,
        "nodes": node_rows,
        "columns": columns,
        "edges": edge_rows,
        "P_adjacent": wide_p,
        "N_adjacent": wide_n,
        "n_edges": len(edge_rows),
        "n_nodes": len(node_rows),
    }


def node_meta_catalog(
    harvest_rows: list[dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    meta: dict[str, dict[str, Any]] = {}
    for fid, surfaces in BLUEPRINT_SURFACES.items():
        meta[fid] = {
            "role": "blueprint",
            "surface": surfaces[0],
            "source": "accepted_core",
            "pocket": None,
            "notes": "STEPT1 accepted opener",
        }
    for row in harvest_rows:
        meta[str(row["formula_id"])] = {
            "role": "harvest",
            "surface": row.get("surface"),
            "source": row.get("source"),
            "pocket": row.get("pocket"),
            "notes": row.get("notes"),
        }
    meta[EMPTY_ID] = {
        "role": "sentinel",
        "surface": None,
        "source": "sentinel",
        "pocket": None,
        "notes": "no formula hits",
    }
    meta[END_ID] = {
        "role": "sentinel",
        "surface": None,
        "source": "sentinel",
        "pocket": None,
        "notes": "after last hit",
    }
    return meta


def fixture_sequences() -> list[dict[str, Any]]:
    """Tiny deterministic sequences (no parquet)."""
    # missive → goedgevonden-harvest → END
    # requeste → requeste_op_de → END
    # empty
    # rapport → END
    # voordracht harvest alone → END
    h_goed = {
        "formula_id": "harvest_scheme_goedgevonden",
        "role": "harvest",
        "start_idx": 40,
        "end_idx": 42,
        "surface": "goedgevonden",
    }
    h_voor = {
        "formula_id": "harvest_voordracht_voorgedragen",
        "role": "harvest",
        "start_idx": 5,
        "end_idx": 6,
        "surface": "voorgedragen",
    }

    def seq(rid: str, hits: list[dict[str, Any]]) -> dict[str, Any]:
        return {
            "id": rid,
            "year": 1780,
            "n_hits": len(hits),
            "ordered_ids": [h["formula_id"] for h in hits],
            "hits": hits,
            "is_empty": len(hits) == 0,
        }

    return [
        seq(
            "f1",
            [
                {
                    "formula_id": MISSIVE_ID,
                    "role": "blueprint",
                    "start_idx": 0,
                    "end_idx": 4,
                    "surface": MISSIVE_CANONIC,
                },
                h_goed,
            ],
        ),
        seq(
            "f2",
            [
                {
                    "formula_id": MISSIVE_ID,
                    "role": "blueprint",
                    "start_idx": 0,
                    "end_idx": 4,
                    "surface": MISSIVE_CANONIC,
                },
                h_goed,
            ],
        ),
        seq(
            "f3",
            [
                {
                    "formula_id": REQUESTE_ID,
                    "role": "blueprint",
                    "start_idx": 0,
                    "end_idx": 6,
                    "surface": REQUESTE_CANONIC,
                },
                {
                    "formula_id": REQUESTE_OP_DE_ID,
                    "role": "blueprint",
                    "start_idx": 10,
                    "end_idx": 13,
                    "surface": REQUESTE_OP_DE_CANONIC,
                },
            ],
        ),
        seq("f4", []),
        seq(
            "f5",
            [
                {
                    "formula_id": RAPPORT_ID,
                    "role": "blueprint",
                    "start_idx": 0,
                    "end_idx": 5,
                    "surface": RAPPORT_CANONIC,
                }
            ],
        ),
        seq("f6", [h_voor]),
        seq("f7", [h_voor]),
        seq(
            "f8",
            [
                {
                    "formula_id": MISSIVE_ID,
                    "role": "blueprint",
                    "start_idx": 0,
                    "end_idx": 4,
                    "surface": MISSIVE_CANONIC,
                }
            ],
        ),
    ]


def fixture_matrix() -> dict[str, Any]:
    harvest = harvest_catalog()
    meta = node_meta_catalog(harvest)
    return build_probabilistic_matrix(
        fixture_sequences(), node_meta=meta, year=DEFAULT_YEAR
    )


def run_year_matrix(
    *,
    year: int = DEFAULT_YEAR,
    limit: int | None = None,
    max_harvest: int | None = 40,
    harvest_rows: list[dict[str, Any]] | None = None,
) -> tuple[dict[str, Any], list[dict[str, Any]], list[dict[str, Any]], dict[str, str]]:
    """Full year: sequences + matrix + harvest + texts_by_id for examples.

    Pass ``harvest_rows`` to override the default scheme+pocket catalog
    (STEPT1ac: family exemplars).
    """
    from formulation.formula_type_presence import load_year_slice

    texts = load_year_slice(year)
    if limit is not None:
        texts = texts.head(int(limit)).copy()
    present_by_id = load_presence_presents(year=year)
    if harvest_rows is not None:
        harvest = list(harvest_rows)
    else:
        harvest = harvest_catalog()
        if max_harvest is not None:
            # Keep all pocket harvests; cap scheme tail
            pockets = [h for h in harvest if h.get("source") == "empty_band_1780"]
            schemes = [h for h in harvest if h.get("source") != "empty_band_1780"]
            harvest = pockets + schemes[: max(0, int(max_harvest) - len(pockets))]
    sequences = build_sequences(
        texts, present_by_id=present_by_id, harvest_rows=harvest
    )
    meta = node_meta_catalog(harvest)
    matrix = build_probabilistic_matrix(sequences, node_meta=meta, year=year)
    matrix["limit"] = limit
    matrix["n_harvest_surfaces"] = len(harvest)
    texts_by_id = {
        str(r["id"]): str(r.get("resolutions_text") or "")
        for r in texts.to_dict(orient="records")
    }
    return matrix, sequences, harvest, texts_by_id


def matrix_edges_records(matrix: dict[str, Any]) -> list[dict[str, Any]]:
    return list(matrix.get("edges") or [])


def matrix_nodes_records(matrix: dict[str, Any]) -> list[dict[str, Any]]:
    return list(matrix.get("nodes") or [])


def sequence_score_records(sequences: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Compact per-id rows (no full text)."""
    out: list[dict[str, Any]] = []
    for seq in sequences:
        out.append(
            {
                "id": seq["id"],
                "year": seq.get("year"),
                "n_hits": seq.get("n_hits"),
                "ordered_ids": seq.get("ordered_ids"),
                "is_empty": seq.get("is_empty"),
            }
        )
    return out


def harvest_records(
    harvest: list[dict[str, Any]],
    matrix: dict[str, Any],
) -> list[dict[str, Any]]:
    """Harvest shortlist with n_from from the matrix nodes."""
    n_from = {
        str(n["formula_id"]): int(n.get("n_from") or 0)
        for n in matrix.get("nodes") or []
    }
    out: list[dict[str, Any]] = []
    for row in harvest:
        fid = str(row["formula_id"])
        out.append(
            {
                **row,
                "n_from": n_from.get(fid, 0),
                "status": "harvest",
            }
        )
    out.sort(key=lambda r: (-int(r.get("n_from") or 0), str(r["formula_id"])))
    return out


def truncate_around_tokens(
    text: str,
    start_idx: int,
    end_idx: int,
    *,
    max_chars: int = TEXT_TRUNC_CHARS,
) -> str:
    """Ellipsis window around a token span (illustrative, not a gold span)."""
    tokens = tokenize(text)
    if not tokens:
        raw = str(text).strip()
        if len(raw) <= max_chars:
            return raw
        return raw[: max_chars - 1] + "…"
    n = len(tokens)
    s = max(0, min(int(start_idx), n))
    e = max(s, min(int(end_idx), n))
    # Grow token window until char budget roughly filled
    left, right = s, e
    while left > 0 or right < n:
        cand_l = left - 1 if left > 0 else left
        cand_r = right + 1 if right < n else right
        trial = tokens[cand_l:cand_r]
        if len(" ".join(trial)) > max_chars and (right - left) > max(1, e - s):
            break
        left, right = cand_l, cand_r
        if left == 0 and right == n:
            break
    piece = " ".join(tokens[left:right])
    if left > 0:
        piece = "…" + piece
    if right < n:
        piece = piece + "…"
    if len(piece) > max_chars + 2:
        piece = piece[: max_chars - 1] + "…"
    return piece


def _hit_for_formula(seq: dict[str, Any], formula_id: str) -> dict[str, Any] | None:
    for h in seq.get("hits") or []:
        if str(h.get("formula_id")) == formula_id:
            return h
    return None


def _n_tokens_text(text: str) -> int:
    return len(tokenize(text))


def build_node_examples(
    sequences: list[dict[str, Any]],
    texts_by_id: dict[str, str],
    matrix: dict[str, Any],
    *,
    per_node: int = EXAMPLES_PER_NODE,
    max_chars: int = TEXT_TRUNC_CHARS,
) -> list[dict[str, Any]]:
    """Archetypal examples per node: shortest texts among hits (cap per_node)."""
    n_from = {
        str(n["formula_id"]): int(n.get("n_from") or 0)
        for n in matrix.get("nodes") or []
    }
    roles = {
        str(n["formula_id"]): n.get("role") for n in matrix.get("nodes") or []
    }
    formula_ids = [
        fid
        for fid, n in n_from.items()
        if n > 0 and fid not in {END_ID}
    ]
    out: list[dict[str, Any]] = []
    for fid in sorted(formula_ids):
        cands: list[tuple[int, int, str, dict[str, Any], dict[str, Any]]] = []
        for seq in sequences:
            if fid == EMPTY_ID:
                if not seq.get("is_empty"):
                    continue
                rid = str(seq["id"])
                text = texts_by_id.get(rid, "")
                cands.append((_n_tokens_text(text), 0, rid, seq, {}))
                continue
            hit = _hit_for_formula(seq, fid)
            if hit is None:
                continue
            rid = str(seq["id"])
            text = texts_by_id.get(rid, "")
            cands.append(
                (
                    _n_tokens_text(text),
                    int(hit.get("start_idx") or 0),
                    rid,
                    seq,
                    hit,
                )
            )
        cands.sort(key=lambda t: (t[0], t[1], t[2]))
        for rank, (n_tok, start_idx, rid, _seq, hit) in enumerate(
            cands[: int(per_node)], start=1
        ):
            text = texts_by_id.get(rid, "")
            if fid == EMPTY_ID:
                trunc = truncate_around_tokens(text, 0, min(12, _n_tokens_text(text)), max_chars=max_chars)
                surface = None
                end_idx = 0
            else:
                end_idx = int(hit.get("end_idx") or start_idx)
                trunc = truncate_around_tokens(
                    text, start_idx, end_idx, max_chars=max_chars
                )
                surface = hit.get("surface")
            out.append(
                {
                    "kind": "node",
                    "formula_id": fid,
                    "role": roles.get(fid),
                    "example_rank": rank,
                    "id": rid,
                    "n_tokens": n_tok,
                    "start_idx": start_idx if fid != EMPTY_ID else None,
                    "end_idx": end_idx if fid != EMPTY_ID else None,
                    "surface": surface,
                    "text_trunc": trunc,
                    "pick_rule": PICK_RULE,
                    "n_from": n_from.get(fid, 0),
                }
            )
    return out


def build_edge_examples(
    sequences: list[dict[str, Any]],
    texts_by_id: dict[str, str],
    matrix: dict[str, Any],
    *,
    top_n: int = TOP_EDGE_EXAMPLES,
    min_n: int = MIN_EDGE_N_ADJACENT,
    max_chars: int = TEXT_TRUNC_CHARS,
) -> list[dict[str, Any]]:
    """One archetypal example for each top adjacent edge (n_adjacent >= min_n)."""
    edges = [
        e
        for e in matrix.get("edges") or []
        if e.get("to_id") != END_ID
        and int(e.get("n_adjacent") or 0) >= int(min_n)
        and float(e.get("p_adjacent") or 0) > 0
    ]
    edges.sort(
        key=lambda e: (-float(e["p_adjacent"]), -int(e["n_adjacent"]), e["from_id"])
    )
    out: list[dict[str, Any]] = []
    for edge in edges[: int(top_n)]:
        a = str(edge["from_id"])
        b = str(edge["to_id"])
        cands: list[tuple[int, int, str, dict[str, Any], dict[str, Any]]] = []
        for seq in sequences:
            ids = [str(x) for x in (seq.get("ordered_ids") or [])]
            # adjacent pair a then b
            ok = False
            for i in range(len(ids) - 1):
                if ids[i] == a and ids[i + 1] == b:
                    ok = True
                    break
            if not ok:
                continue
            hit_a = _hit_for_formula(seq, a) or {}
            hit_b = _hit_for_formula(seq, b) or {}
            rid = str(seq["id"])
            text = texts_by_id.get(rid, "")
            cands.append(
                (
                    _n_tokens_text(text),
                    int(hit_a.get("start_idx") or 0),
                    rid,
                    hit_a,
                    hit_b,
                )
            )
        if not cands:
            continue
        cands.sort(key=lambda t: (t[0], t[1], t[2]))
        n_tok, start_a, rid, hit_a, hit_b = cands[0]
        text = texts_by_id.get(rid, "")
        s0 = int(hit_a.get("start_idx") or 0)
        e1 = int(hit_b.get("end_idx") or hit_b.get("start_idx") or s0)
        out.append(
            {
                "kind": "edge",
                "from_id": a,
                "to_id": b,
                "p_adjacent": edge.get("p_adjacent"),
                "n_adjacent": edge.get("n_adjacent"),
                "n_from": edge.get("n_from"),
                "example_rank": 1,
                "id": rid,
                "n_tokens": n_tok,
                "start_idx": s0,
                "end_idx": e1,
                "surface_from": hit_a.get("surface"),
                "surface_to": hit_b.get("surface"),
                "text_trunc": truncate_around_tokens(
                    text, s0, e1, max_chars=max_chars
                ),
                "pick_rule": PICK_RULE,
            }
        )
    return out


def build_archetypal_examples(
    sequences: list[dict[str, Any]],
    texts_by_id: dict[str, str],
    matrix: dict[str, Any],
    *,
    per_node: int = EXAMPLES_PER_NODE,
    top_edges: int = TOP_EDGE_EXAMPLES,
    min_edge_n: int = MIN_EDGE_N_ADJACENT,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Node + edge example tables for the human workbook."""
    nodes = build_node_examples(
        sequences, texts_by_id, matrix, per_node=per_node
    )
    edges = build_edge_examples(
        sequences,
        texts_by_id,
        matrix,
        top_n=top_edges,
        min_n=min_edge_n,
    )
    return nodes, edges


def fixture_texts_by_id() -> dict[str, str]:
    """Short texts aligned with fixture_sequences hit surfaces."""
    return {
        "f1": (
            "Ontfangen een missive van den Heere X houdende advertentie "
            "waarop is goedgevonden en verstaan te doen."
        ),
        "f2": (
            "Ontfangen een missive van Y en daarna is goedgevonden "
            "het versoek te accorderen."
        ),
        "f3": (
            "IS ter Vergaderinge geleesen de Requeste van Z. "
            "Op de Requeste is gedelibereert."
        ),
        "f4": "Korte resolutie zonder herkende opener hier.",
        "f5": "IS gehoord het rapport van de gecommitteerden over de saake.",
        "f6": "DE Heer praesideerende heeft voorgedragen de saake van A.",
        "f7": "Kort: heeft voorgedragen.",
        "f8": "Ontfangen een missive van den ambassadeur alleen.",
    }


def wide_frame(wide: dict[str, dict[str, Any]], *, value_name: str) -> pd.DataFrame:
    """Row-stochastic (or count) dict → DataFrame indexed by from_id."""
    if not wide:
        return pd.DataFrame()
    frame = pd.DataFrame.from_dict(wide, orient="index")
    frame.index.name = "from_id"
    frame = frame.sort_index()
    # stable column order: formulas then END/EMPTY
    cols = [c for c in frame.columns if c not in {END_ID, EMPTY_ID}]
    cols = sorted(cols)
    for sentinel in (EMPTY_ID, END_ID):
        if sentinel in frame.columns:
            cols.append(sentinel)
    frame = frame.reindex(columns=cols)
    frame.attrs["value_name"] = value_name
    return frame


def write_human_xlsx(
    matrix: dict[str, Any],
    *,
    harvest: list[dict[str, Any]] | None = None,
    node_examples: list[dict[str, Any]] | None = None,
    edge_examples: list[dict[str, Any]] | None = None,
    path: Path | None = None,
) -> Path:
    """Excel workbook for humans: P, N, edges, nodes, harvest, examples."""
    from data_io import resolve

    out_path = Path(path) if path is not None else resolve("formula_sequence_matrix_xlsx")
    out_path.parent.mkdir(parents=True, exist_ok=True)

    p_df = wide_frame(matrix.get("P_adjacent") or {}, value_name="p_adjacent")
    n_df = wide_frame(matrix.get("N_adjacent") or {}, value_name="n_adjacent")
    edges = pd.DataFrame(matrix.get("edges") or [])
    if len(edges):
        edges = edges.sort_values(
            ["p_adjacent", "n_adjacent"], ascending=[False, False]
        )
    nodes = pd.DataFrame(matrix.get("nodes") or [])
    if len(nodes):
        nodes = nodes.sort_values("n_from", ascending=False)
    if not harvest:
        harvest_df = pd.DataFrame()
    elif "n_from" in harvest[0]:
        harvest_df = pd.DataFrame(harvest)
    else:
        harvest_df = pd.DataFrame(harvest_records(harvest, matrix))

    ex_df = pd.DataFrame(node_examples or [])
    if len(ex_df):
        ex_df = ex_df.sort_values(["formula_id", "example_rank"])
    edge_ex_df = pd.DataFrame(edge_examples or [])
    if len(edge_ex_df):
        edge_ex_df = edge_ex_df.sort_values(
            ["p_adjacent", "n_adjacent"], ascending=[False, False]
        )

    readme = pd.DataFrame(
        [
            {
                "sheet": "P_adjacent",
                "meaning": "Primary: P(next=column | current=row); rows sum ≈ 1",
            },
            {
                "sheet": "N_adjacent",
                "meaning": "Companion support counts for the same cells",
            },
            {
                "sheet": "edges",
                "meaning": "Long form: p_adjacent + n + precedes + gap",
            },
            {
                "sheet": "nodes",
                "meaning": "Blueprint / harvest / EMPTY / END with n_from",
            },
            {
                "sheet": "harvest",
                "meaning": "Harvest shortlist (not auto-named)",
            },
            {
                "sheet": "examples",
                "meaning": (
                    "Archetypal snippets per node (shortest hits); "
                    "illustrative — not a completeness claim"
                ),
            },
            {
                "sheet": "edge_examples",
                "meaning": "One archetypal snippet per top adjacent edge",
            },
            {
                "sheet": "(meta)",
                "meaning": (
                    f"year={matrix.get('year')} n={matrix.get('n_resolutions')} "
                    f"row_sum_ok={matrix.get('row_sum_ok')}"
                ),
            },
        ]
    )

    with pd.ExcelWriter(out_path, engine="openpyxl") as writer:
        readme.to_excel(writer, sheet_name="readme", index=False)
        p_df.to_excel(writer, sheet_name="P_adjacent")
        n_df.to_excel(writer, sheet_name="N_adjacent")
        edges.to_excel(writer, sheet_name="edges", index=False)
        nodes.to_excel(writer, sheet_name="nodes", index=False)
        harvest_df.to_excel(writer, sheet_name="harvest", index=False)
        ex_df.to_excel(writer, sheet_name="examples", index=False)
        edge_ex_df.to_excel(writer, sheet_name="edge_examples", index=False)
    return out_path


__all__ = (
    "BLUEPRINT_SURFACES",
    "DEFAULT_YEAR",
    "EMPTY_ID",
    "END_ID",
    "EXAMPLES_PER_NODE",
    "MIN_EDGE_N_ADJACENT",
    "PICK_RULE",
    "POCKET_HARVEST",
    "TEXT_TRUNC_CHARS",
    "TOP_EDGE_EXAMPLES",
    "build_archetypal_examples",
    "build_edge_examples",
    "build_node_examples",
    "build_probabilistic_matrix",
    "build_sequences",
    "fixture_matrix",
    "fixture_sequences",
    "fixture_texts_by_id",
    "harvest_catalog",
    "harvest_records",
    "load_presence_presents",
    "load_scheme_harvest",
    "matrix_edges_records",
    "matrix_nodes_records",
    "node_meta_catalog",
    "ordered_hits_for_text",
    "run_year_matrix",
    "sequence_score_records",
    "truncate_around_tokens",
    "wide_frame",
    "write_human_xlsx",
)
