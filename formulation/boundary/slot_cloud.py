"""STEPS2: bootstrap frequency-weighted slot-clouds from TF-IDF hit windows.

Aligns each hit to a canonical template with Smith-Waterman (no MSA). Aggregates
OCR tokens per template slot. Optional slots are hypothesized from skip rates.
"""

from __future__ import annotations

from collections import Counter
from typing import Any

from formulation.boundary.align_sw import align_sw_pairs
from formulation.boundary.tfidf_windows import (
    TEMPLATE_ID_OPENING,
    default_opening_template,
    tokenize,
)

# Hypothesis: mark a slot optional when skips exceed this share of accepted hits.
OPTIONAL_SKIP_RATE = 0.25
# Hypothesis: accept a hit when at least this fraction of slots are matched (not skipped).
MIN_MATCHED_SLOT_RATIO = 0.5
# Drop rare OCR spellings below this count (still keep canonical).
MIN_VARIANT_COUNT = 1

# Tiny 18c OCR-noise seeds for --fixture-only smoke (no resolutions_flat).
FIXTURE_HIT_TEXTS: list[str] = [
    "IS ter Vergaderinge geleesen de Requeste van Jan Jansen",
    "Is ter Vergaderinge gelesen de Requeste van Pieter Claesz",
    "IS ter Vergaderinge geleesen d' Requeste van de weduwe",
    "IS ter Vergaderinge geleesen de Requeste van den coopman",
    "Is ter Vergaderinge geleesen de Reqveste van Anna de Vries",
    "IS ter Vergaderinge gelesen de Requeste van Hendrick",
]


def default_template(
    *,
    rows: list[dict[str, Any]] | None = None,
) -> tuple[str, list[str]]:
    """Same framing row as STEPS1 (``formula_templates``); 17c clouds deferred."""
    return default_opening_template(rows=rows)


def hit_texts_from_windows(rows: list[dict[str, Any]] | Any) -> list[str]:
    """Prefer ``window_text``; fall back to joining token lists."""
    if hasattr(rows, "to_dict"):
        records = rows.to_dict(orient="records")
    else:
        records = list(rows)
    texts: list[str] = []
    for row in records:
        if row.get("window_text"):
            texts.append(str(row["window_text"]))
        elif row.get("ocr_tokens") is not None:
            texts.append(" ".join(str(t) for t in row["ocr_tokens"]))
        elif row.get("resolutions_text"):
            texts.append(str(row["resolutions_text"]))
    return texts


def observe_hit(
    template: list[str],
    ocr_tokens: list[str],
    *,
    gap_penalty: float = 1.0,
    min_matched_ratio: float = MIN_MATCHED_SLOT_RATIO,
) -> dict[str, Any] | None:
    """Align one hit; return per-slot observations or ``None`` if too weak."""
    if not template or not ocr_tokens:
        return None
    result, pairs = align_sw_pairs(
        template, ocr_tokens, gap_penalty=gap_penalty
    )
    if result.score <= 0.0 or not pairs:
        return None

    matched: dict[int, str] = {}
    skipped: set[int] = set()
    for slot_idx, ocr_idx in pairs:
        if ocr_idx is None:
            skipped.add(int(slot_idx))
        else:
            matched[int(slot_idx)] = ocr_tokens[int(ocr_idx)]

    n_slots = len(template)
    n_matched = len(matched)
    if n_matched / n_slots < float(min_matched_ratio):
        return None

    return {
        "score": float(result.score),
        "start_idx": int(result.start_idx),
        "end_idx": int(result.end_idx),
        "matched": matched,
        "skipped": sorted(skipped),
        "n_matched": n_matched,
    }


def bootstrap_slot_cloud(
    hit_texts: list[str],
    template: list[str],
    *,
    template_id: str = TEMPLATE_ID_OPENING,
    period: str | None = "18c",
    year_min: int | None = None,
    year_max: int | None = None,
    gap_penalty: float = 1.0,
    min_matched_ratio: float = MIN_MATCHED_SLOT_RATIO,
    optional_skip_rate: float = OPTIONAL_SKIP_RATE,
    min_variant_count: int = MIN_VARIANT_COUNT,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Aggregate SW slot observations into a frequency-weighted cloud + notes.

    Does **not** run MSA. Period fields are metadata only (filter upstream).
    """
    if not template:
        raise ValueError("template must be non-empty")

    n_slots = len(template)
    variant_counts: list[Counter[str]] = [Counter() for _ in range(n_slots)]
    skip_counts = [0] * n_slots
    accepted = 0
    rejected = 0
    scores: list[float] = []

    for text in hit_texts:
        tokens = tokenize("" if text is None else str(text))
        obs = observe_hit(
            template,
            tokens,
            gap_penalty=gap_penalty,
            min_matched_ratio=min_matched_ratio,
        )
        if obs is None:
            rejected += 1
            continue
        accepted += 1
        scores.append(float(obs["score"]))
        for slot_idx, token in obs["matched"].items():
            variant_counts[int(slot_idx)][str(token)] += 1
        for slot_idx in obs["skipped"]:
            skip_counts[int(slot_idx)] += 1

    slots: list[dict[str, Any]] = []
    optional_slots: list[int] = []
    for i, canonical in enumerate(template):
        counts = variant_counts[i]
        variants = [
            {"token": tok, "count": int(cnt)}
            for tok, cnt in counts.most_common()
            if int(cnt) >= int(min_variant_count) or tok == canonical
        ]
        # Always expose the canonical spelling (count 0 if never observed).
        if not any(v["token"] == canonical for v in variants):
            variants.insert(0, {"token": canonical, "count": 0})
        skip_rate = (skip_counts[i] / accepted) if accepted else 0.0
        optional = bool(accepted and skip_rate >= float(optional_skip_rate))
        if optional:
            optional_slots.append(i)
        slots.append(
            {
                "index": i,
                "canonical": canonical,
                "optional": optional,
                "skip_count": int(skip_counts[i]),
                "skip_rate": float(skip_rate),
                "variants": variants,
            }
        )

    cloud = {
        "template_id": template_id,
        "period": period,
        "year_min": year_min,
        "year_max": year_max,
        "n_hits_in": int(len(hit_texts)),
        "n_hits_accepted": int(accepted),
        "n_hits_rejected": int(rejected),
        "optional_slots": optional_slots,
        "slots": slots,
        "variant_lists": cloud_variant_lists({"slots": slots}),
    }
    notes = {
        "template_id": template_id,
        "period": period,
        "year_min": year_min,
        "year_max": year_max,
        "n_hits_in": int(len(hit_texts)),
        "n_hits_accepted": int(accepted),
        "n_hits_rejected": int(rejected),
        "n_slots": n_slots,
        "n_optional_slots": len(optional_slots),
        "optional_slots": optional_slots,
        "optional_skip_rate": float(optional_skip_rate),
        "optional_skip_rate_is_hypothesis": True,
        "min_matched_slot_ratio": float(min_matched_ratio),
        "min_matched_slot_ratio_is_hypothesis": True,
        "min_variant_count": int(min_variant_count),
        "method": "sw_single_aggregate",
        "msa": False,
        "score_min": float(min(scores)) if scores else None,
        "score_max": float(max(scores)) if scores else None,
        "score_mean": float(sum(scores) / len(scores)) if scores else None,
        "n_variant_types": int(
            sum(len(s["variants"]) for s in slots)
        ),
    }
    return cloud, notes


def cloud_variant_lists(cloud: dict[str, Any]) -> list[list[str]]:
    """Convert rich cloud JSON to ``list[list[str]]`` for ``align_sw_cloud``."""
    slots = cloud.get("slots") or []
    out: list[list[str]] = []
    for slot in slots:
        canonical = str(slot["canonical"])
        tokens = [canonical]
        for var in slot.get("variants") or []:
            tok = str(var["token"] if isinstance(var, dict) else var)
            if tok not in tokens:
                tokens.append(tok)
        out.append(tokens)
    return out


def fixture_hit_texts() -> list[str]:
    """OCR-noisy 18c openings for fixture-only smoke."""
    return list(FIXTURE_HIT_TEXTS)
