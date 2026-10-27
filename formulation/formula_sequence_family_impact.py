"""STEPT1ac: sequence-matrix impact — harvest from family exemplars vs STEPT1z.

Principle: do science on a canonical form (exemplar join key; members skim-only).
"""

from __future__ import annotations

from typing import Any, Sequence

from formulation.formula_family_fold import (
    MIN_SHARED_TOKEN_SPAN,
    _contiguous_token_overlap,
)
from formulation.formula_sequence_matrix import (
    BLUEPRINT_SURFACES,
    POCKET_HARVEST,
    harvest_catalog,
    run_year_matrix,
)
from formulation.phrases_5gram_profile import normalize_phrase

DEFAULT_MAX_FAMILY_HARVEST = 40


def _blueprint_surface_norms() -> set[str]:
    return {
        normalize_phrase(s)
        for surfaces in BLUEPRINT_SURFACES.values()
        for s in surfaces
    }


def family_exemplar_harvest(
    families: Sequence[dict[str, Any]],
    *,
    max_n: int = DEFAULT_MAX_FAMILY_HARVEST,
    keep_pockets: bool = True,
) -> list[dict[str, Any]]:
    """Build harvest rows from family exemplars (canonical forms)."""
    bp = _blueprint_surface_norms()
    pockets: list[dict[str, Any]] = []
    if keep_pockets:
        for row in POCKET_HARVEST:
            pockets.append(
                {
                    "formula_id": str(row["formula_id"]),
                    "surface": str(row["surface"]),
                    "source": "empty_band_1780",
                    "pocket": row.get("pocket"),
                    "family_id": None,
                    "notes": str(row.get("notes") or ""),
                    "canonical": True,
                }
            )

    budget = max(0, int(max_n) - len(pockets))
    ranked = sorted(
        (
            f
            for f in families
            if f.get("exemplar")
            and normalize_phrase(str(f["exemplar"])) not in bp
            and normalize_phrase(str(f["exemplar"]))
        ),
        key=lambda f: (
            -int(f.get("phrase_freq_max") or 0),
            -int(f.get("n_members") or 0),
            str(f.get("family_id") or ""),
        ),
    )

    by_role: dict[str, list[dict[str, Any]]] = {}
    for f in ranked:
        role = str(f.get("suggested_role") or "other")
        by_role.setdefault(role, []).append(f)

    picked: list[dict[str, Any]] = []
    seen_norm: set[str] = set()
    roles = sorted(by_role.keys())
    while len(picked) < budget and any(by_role.values()):
        progressed = False
        for role in roles:
            bucket = by_role.get(role) or []
            if not bucket:
                continue
            f = bucket.pop(0)
            ex = str(f["exemplar"])
            nrm = normalize_phrase(ex)
            if nrm in seen_norm or nrm in bp:
                continue
            seen_norm.add(nrm)
            picked.append(
                {
                    "formula_id": f"harvest_fam_{f.get('family_id')}",
                    "surface": ex,
                    "source": "formula_family_exemplar",
                    "pocket": None,
                    "family_id": f.get("family_id"),
                    "suggested_role": f.get("suggested_role"),
                    "phrase_freq_max": int(f.get("phrase_freq_max") or 0),
                    "n_members": int(f.get("n_members") or 0),
                    "notes": "canonical exemplar; members skim-only",
                    "canonical": True,
                }
            )
            progressed = True
            if len(picked) >= budget:
                break
        if not progressed:
            break

    return pockets + picked


def _family_norms(families: Sequence[dict[str, Any]]) -> list[str]:
    norms: list[str] = []
    for f in families:
        if f.get("exemplar"):
            norms.append(normalize_phrase(str(f["exemplar"])))
        for m in f.get("members") or []:
            ph = m.get("phrase") or m.get("phrase_norm")
            if ph:
                norms.append(normalize_phrase(str(ph)))
    return [n for n in norms if n]


def surface_contained(surface: str, family_norms: Sequence[str]) -> bool:
    s = normalize_phrase(surface)
    if not s:
        return False
    for fam in family_norms:
        if not fam:
            continue
        if s == fam or s in fam or fam in s:
            return True
        if _contiguous_token_overlap(s, fam) >= MIN_SHARED_TOKEN_SPAN:
            return True
    return False


def soft_containment_rate(
    old_harvest: Sequence[dict[str, Any]],
    families: Sequence[dict[str, Any]],
) -> dict[str, Any]:
    norms = _family_norms(families)
    total = 0
    hit = 0
    misses: list[str] = []
    for row in old_harvest:
        surf = str(row.get("surface") or "")
        if not surf:
            continue
        total += 1
        if surface_contained(surf, norms):
            hit += 1
        elif len(misses) < 15:
            misses.append(surf)
    return {
        "n_old_harvest": total,
        "n_contained": hit,
        "frac_contained": (hit / total) if total else None,
        "miss_examples": misses,
    }


def catalog_impact_summary(
    *,
    families: Sequence[dict[str, Any]],
    old_harvest: Sequence[dict[str, Any]] | None = None,
    max_family_harvest: int = DEFAULT_MAX_FAMILY_HARVEST,
) -> dict[str, Any]:
    old = list(old_harvest) if old_harvest is not None else harvest_catalog()
    new_h = family_exemplar_harvest(families, max_n=max_family_harvest)
    soft = soft_containment_rate(old, families)
    n_members = sum(int(f.get("n_members") or 0) for f in families)
    return {
        "step": "STEPT1ac",
        "principle": "do science on a canonical form",
        "n_families": len(families),
        "n_member_surfaces": n_members,
        "n_old_harvest_surfaces": len(old),
        "n_new_exemplar_harvest": len(new_h),
        "n_new_family_exemplars": sum(
            1 for h in new_h if h.get("source") == "formula_family_exemplar"
        ),
        "n_new_pockets": sum(1 for h in new_h if h.get("source") == "empty_band_1780"),
        "hard": {
            "old_harvest_n": len(old),
            "new_harvest_n": len(new_h),
            "family_collapse_ratio": (
                (n_members / len(families)) if families else None
            ),
        },
        "soft_containment": soft,
        "new_harvest": new_h,
        "new_harvest_preview": [
            {
                "formula_id": h["formula_id"],
                "surface": h["surface"],
                "source": h["source"],
            }
            for h in new_h[:12]
        ],
    }


def compare_matrix_summaries(
    baseline: dict[str, Any],
    family_matrix: dict[str, Any],
    *,
    catalog: dict[str, Any] | None = None,
) -> dict[str, Any]:
    def _g(m: dict[str, Any], key: str) -> Any:
        return m.get(key)

    out: dict[str, Any] = {
        "step": "STEPT1ac",
        "principle": "do science on a canonical form",
        "baseline": {
            "n_resolutions": _g(baseline, "n_resolutions"),
            "n_empty": _g(baseline, "n_empty"),
            "frac_empty": _g(baseline, "frac_empty"),
            "n_nodes": _g(baseline, "n_nodes"),
            "n_edges": _g(baseline, "n_edges"),
            "n_harvest_surfaces": _g(baseline, "n_harvest_surfaces"),
        },
        "family_exemplar_matrix": {
            "n_resolutions": _g(family_matrix, "n_resolutions"),
            "n_empty": _g(family_matrix, "n_empty"),
            "frac_empty": _g(family_matrix, "frac_empty"),
            "n_nodes": _g(family_matrix, "n_nodes"),
            "n_edges": _g(family_matrix, "n_edges"),
            "n_harvest_surfaces": _g(family_matrix, "n_harvest_surfaces"),
        },
        "delta": {
            "empty": (_g(family_matrix, "n_empty") or 0)
            - (_g(baseline, "n_empty") or 0),
            "frac_empty": (
                None
                if _g(baseline, "frac_empty") is None
                or _g(family_matrix, "frac_empty") is None
                else float(family_matrix["frac_empty"]) - float(baseline["frac_empty"])
            ),
            "nodes": (_g(family_matrix, "n_nodes") or 0)
            - (_g(baseline, "n_nodes") or 0),
            "edges": (_g(family_matrix, "n_edges") or 0)
            - (_g(baseline, "n_edges") or 0),
        },
    }
    if catalog:
        cat = dict(catalog)
        cat.pop("new_harvest", None)  # keep metrics compact
        out["catalog"] = cat
    return out


def run_year_matrix_from_families(
    families: Sequence[dict[str, Any]],
    *,
    year: int,
    max_family_harvest: int = DEFAULT_MAX_FAMILY_HARVEST,
    limit: int | None = None,
) -> tuple[dict[str, Any], list[dict[str, Any]], list[dict[str, Any]], dict[str, str]]:
    """Year matrix using family exemplar harvest instead of scheme shortlist."""
    harvest = family_exemplar_harvest(families, max_n=max_family_harvest)
    return run_year_matrix(
        year=year,
        limit=limit,
        max_harvest=None,
        harvest_rows=harvest,
    )
