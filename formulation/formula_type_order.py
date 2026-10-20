"""STEPT1d: order / composition of formula-type hits (A before B by start_idx).

STEPT1c showed zone separates families but bags stay fragments. This step
orders presents by DAG span start and asks whether sequenced types look like
resolution templates.
"""

from __future__ import annotations

from collections import Counter
from typing import Any

import pandas as pd

from formulation.advies_formula_type import FORMULA_TYPE_ID as ADVIES_ID
from formulation.appointment_formula_type import FORMULA_TYPE_ID as APPOINTMENT_ID
from formulation.boundary.tfidf_windows import POC_YEAR
from formulation.formula_type_position import (
    CLOSE_CUT,
    OPENING_CUT,
    fixture_position_frames,
    fixture_position_models,
    score_position_frame,
)

# Re-export zone cuts for CLI (same tertiles as STEPT1c).
__all__ = (
    "CLOSE_CUT",
    "DEFAULT_YEAR",
    "EXPECTED_ORDERS",
    "OPENING_CUT",
    "composition_rows",
    "expected_order_holds",
    "fixture_order_frames",
    "fixture_order_models",
    "ordered_presents",
    "score_order_frame",
    "summarize_order",
)

DEFAULT_YEAR = POC_YEAR

# When both ends are present, earlier type should precede later (document order).
# T1d-refresh: ontfangen → advies (T1c-refresh zone already hints later on the 6).
EXPECTED_ORDERS: tuple[tuple[str, str], ...] = (
    ("ontfangen_start", APPOINTMENT_ID),
    ("requeste_start", APPOINTMENT_ID),
    ("ontfangen_start", ADVIES_ID),
)


def _sort_key(row: Any) -> tuple[int, int, str]:
    return (
        int(row.start_idx),
        int(row.end_idx),
        str(row.formula_type_id),
    )


def ordered_presents(group: pd.DataFrame) -> list[dict[str, Any]]:
    """Present hits sorted by document order (start_idx ascending)."""
    present = group.loc[group["present"]]
    if present.empty:
        return []
    rows = list(present.itertuples(index=False))
    rows.sort(key=_sort_key)
    out: list[dict[str, Any]] = []
    for r in rows:
        out.append(
            {
                "formula_type_id": str(r.formula_type_id),
                "zone": str(r.zone) if r.zone is not None else None,
                "start_idx": int(r.start_idx),
                "end_idx": int(r.end_idx),
                "mid_norm": (
                    float(r.mid_norm) if r.mid_norm is not None else None
                ),
                "score": float(r.score),
                "provisional": bool(r.provisional),
            }
        )
    return out


def expected_order_holds(
    ordered_types: list[str],
    earlier: str,
    later: str,
) -> bool | None:
    """True if earlier precedes later when both present; None if either missing."""
    if earlier not in ordered_types or later not in ordered_types:
        return None
    return ordered_types.index(earlier) < ordered_types.index(later)


def composition_rows(scores: pd.DataFrame) -> pd.DataFrame:
    """One row per resolution: unordered bag + ordered sequence of presents."""
    if scores.empty:
        return pd.DataFrame(
            columns=[
                "id",
                "year",
                "n_present",
                "bag_types",
                "ordered_types",
                "ordered_zones",
                "ordered_typed_zones",
                "matches_any_expected_order",
            ]
        )

    rows: list[dict[str, Any]] = []
    for rid, grp in scores.groupby("id", sort=False):
        year_val = grp["year"].iloc[0]
        year = int(year_val) if year_val is not None and pd.notna(year_val) else None
        ordered = ordered_presents(grp)
        types = [h["formula_type_id"] for h in ordered]
        zones = [h["zone"] for h in ordered]
        typed_zones = [
            {"formula_type_id": h["formula_type_id"], "zone": h["zone"]}
            for h in ordered
        ]
        bag = tuple(sorted(set(types)))
        expected_flags = [
            expected_order_holds(types, a, b) for a, b in EXPECTED_ORDERS
        ]
        applicable = [f for f in expected_flags if f is not None]
        matches_any = (
            any(applicable) if applicable else None
        )
        rows.append(
            {
                "id": str(rid),
                "year": year,
                "n_present": int(len(ordered)),
                "bag_types": list(bag),
                "ordered_types": types,
                "ordered_zones": zones,
                "ordered_typed_zones": typed_zones,
                "hits": ordered,
                "matches_any_expected_order": matches_any,
            }
        )
    return pd.DataFrame(rows)


def summarize_order(
    compositions: pd.DataFrame,
    *,
    year: int,
    models: list[dict[str, Any]],
    random_state: int,
    limit: int | None,
    opening_cut: float = OPENING_CUT,
    close_cut: float = CLOSE_CUT,
) -> dict[str, Any]:
    """Provenanced metrics: ordered sequences vs bags + expected-order rates."""
    n_ids = int(len(compositions))
    multi = (
        compositions.loc[compositions["n_present"] >= 2]
        if n_ids
        else compositions
    )
    n_multi = int(len(multi))

    bag_counter: Counter[tuple[str, ...]] = Counter()
    ordered_counter: Counter[tuple[str, ...]] = Counter()
    zone_ordered_counter: Counter[tuple[tuple[str, str | None], ...]] = Counter()
    size_hist: Counter[int] = Counter()

    if n_ids:
        for rec in compositions.to_dict(orient="records"):
            n = int(rec["n_present"])
            size_hist[n] += 1
            bag = tuple(rec.get("bag_types") or [])
            ordered = tuple(rec.get("ordered_types") or [])
            if bag:
                bag_counter[bag] += 1
            if ordered:
                ordered_counter[ordered] += 1
            typed = rec.get("ordered_typed_zones") or []
            if typed:
                zone_key = tuple(
                    (str(t["formula_type_id"]), t.get("zone")) for t in typed
                )
                zone_ordered_counter[zone_key] += 1

    expected_out: list[dict[str, Any]] = []
    for earlier, later in EXPECTED_ORDERS:
        n_both = 0
        n_ok = 0
        if n_ids:
            for rec in compositions.to_dict(orient="records"):
                types = list(rec.get("ordered_types") or [])
                flag = expected_order_holds(types, earlier, later)
                if flag is None:
                    continue
                n_both += 1
                if flag:
                    n_ok += 1
        expected_out.append(
            {
                "earlier": earlier,
                "later": later,
                "n_both_present": n_both,
                "n_expected_order": n_ok,
                "frac_expected_order": (
                    round(n_ok / n_both, 4) if n_both else None
                ),
            }
        )

    def _top_seqs(
        counter: Counter[tuple[Any, ...]],
        *,
        as_typed_zones: bool = False,
        min_len: int = 1,
    ) -> list[dict[str, Any]]:
        out: list[dict[str, Any]] = []
        for pat, cnt in counter.most_common(20):
            if len(pat) < min_len:
                continue
            if as_typed_zones:
                payload: dict[str, Any] = {
                    "ordered_typed_zones": [
                        {"formula_type_id": a, "zone": b} for a, b in pat
                    ],
                }
            else:
                payload = {"types": list(pat)}
            out.append(
                {
                    **payload,
                    "n": int(cnt),
                    "rate": round(cnt / n_ids, 4) if n_ids else 0.0,
                }
            )
        return out

    # How often unordered multi bags have >1 distinct order among those ids.
    order_vs_bag: list[dict[str, Any]] = []
    if n_multi:
        by_bag: dict[tuple[str, ...], Counter[tuple[str, ...]]] = {}
        for rec in multi.to_dict(orient="records"):
            bag = tuple(sorted(rec.get("bag_types") or []))
            ordered = tuple(rec.get("ordered_types") or [])
            by_bag.setdefault(bag, Counter())[ordered] += 1
        for bag, orders in sorted(by_bag.items(), key=lambda x: -sum(x[1].values())):
            order_vs_bag.append(
                {
                    "bag": list(bag),
                    "n": int(sum(orders.values())),
                    "n_distinct_orders": int(len(orders)),
                    "top_orders": [
                        {"types": list(o), "n": int(c)}
                        for o, c in orders.most_common(5)
                    ],
                }
            )

    return {
        "step": "STEPT1d",
        "method": "order_composition_by_start_idx",
        "year": int(year),
        "random_state": int(random_state),
        "limit": limit,
        "n_resolutions": n_ids,
        "n_types": int(len(models)),
        "n_multi": n_multi,
        "zone_cuts": {
            "opening_lt": float(opening_cut),
            "body_lt": float(close_cut),
            "close_ge": float(close_cut),
            "rule": "mid_norm = (start_idx+end_idx)/2 / n_tokens",
        },
        "order_rule": "sort presents by start_idx, then end_idx, then type id",
        "appointment_accepted": any(
            m.get("formula_type_id") == APPOINTMENT_ID and not m.get("provisional")
            for m in models
        ),
        "advies_accepted": any(
            m.get("formula_type_id") == ADVIES_ID and not m.get("provisional")
            for m in models
        ),
        "openings_provisional": any(bool(m.get("provisional")) for m in models),
        "expected_orders": expected_out,
        "sequences": {
            "n_ids": n_ids,
            "n_multi": n_multi,
            "size_histogram": {
                str(k): int(v) for k, v in sorted(size_hist.items())
            },
            "frac_zero": (
                round(size_hist.get(0, 0) / n_ids, 4) if n_ids else None
            ),
            "frac_one": (
                round(size_hist.get(1, 0) / n_ids, 4) if n_ids else None
            ),
            "frac_multi": (
                round(
                    sum(v for k, v in size_hist.items() if k >= 2) / n_ids,
                    4,
                )
                if n_ids
                else None
            ),
            "top_bags": _top_seqs(bag_counter),
            "top_ordered": _top_seqs(ordered_counter),
            "top_ordered_multi": _top_seqs(ordered_counter, min_len=2),
            "top_ordered_zones": _top_seqs(
                zone_ordered_counter, as_typed_zones=True
            ),
            "order_vs_bag": order_vs_bag[:20],
            "judgment_prompt": (
                "Do ordered formula-type sequences look like recognisable "
                "resolution templates, or still fragments? "
                "If still fragments → another A family or sieve residual; "
                "if order composes templates → keep sequence on registry."
            ),
        },
    }


def score_order_frame(
    frame: pd.DataFrame,
    models: list[dict[str, Any]],
    *,
    opening_cut: float = OPENING_CUT,
    close_cut: float = CLOSE_CUT,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Return (long position scores, per-id composition rows)."""
    scores = score_position_frame(
        frame,
        models,
        opening_cut=opening_cut,
        close_cut=close_cut,
    )
    return scores, composition_rows(scores)


def fixture_order_frames() -> pd.DataFrame:
    """Opening phrase first, appointment phrase after padding (expected order)."""
    pad = " ".join(["woord"] * 40)
    base = fixture_position_frames()
    rows = []
    for rec in base.to_dict(orient="records"):
        rid = str(rec["id"])
        text = str(rec["resolutions_text"])
        if rid == "fix-appt-1":
            # Ontfangen-like opener is already in other fixtures; for appt-only
            # keep late appointment. Combined order is tested via multi ids.
            text = f"{pad} {text}"
        elif rid.startswith("fix-ont") or rid.startswith("fix-req"):
            text = f"{text} {pad}"
        else:
            text = f"{pad} {text} {pad}"
        rows.append({**rec, "resolutions_text": text})

    # Synthetic multi-hit: opening then appointment in document order.
    ont = next(
        r for r in base.to_dict(orient="records") if str(r["id"]).startswith("fix-ont")
    )
    appt = next(
        r for r in base.to_dict(orient="records") if str(r["id"]) == "fix-appt-1"
    )
    adv = next(
        r for r in base.to_dict(orient="records") if str(r["id"]).startswith("fix-adv")
    )
    rows.append(
        {
            "id": "fix-order-1",
            "year": 1780,
            "resolutions_text": (
                f"{ont['resolutions_text']} {pad} {appt['resolutions_text']}"
            ),
        }
    )
    # Reverse order (appointment then opening) — expected-order fail.
    rows.append(
        {
            "id": "fix-order-rev",
            "year": 1780,
            "resolutions_text": (
                f"{appt['resolutions_text']} {pad} {ont['resolutions_text']}"
            ),
        }
    )
    # Ontfangen then advies (T1d-refresh primary pair).
    rows.append(
        {
            "id": "fix-order-adv",
            "year": 1780,
            "resolutions_text": (
                f"{ont['resolutions_text']} {pad} {adv['resolutions_text']}"
            ),
        }
    )
    # Advies then ontfangen — expected ontfangen→advies fail.
    rows.append(
        {
            "id": "fix-order-adv-rev",
            "year": 1780,
            "resolutions_text": (
                f"{adv['resolutions_text']} {pad} {ont['resolutions_text']}"
            ),
        }
    )
    return pd.DataFrame(rows)


def fixture_order_models() -> list[dict[str, Any]]:
    return fixture_position_models()
