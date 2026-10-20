"""STEPS2: slot-cloud bootstrap from SW-aligned hits (no MSA)."""

from __future__ import annotations

from formulation.boundary.align_sw import align_sw_cloud, align_sw_pairs
from formulation.boundary.slot_cloud import (
    FIXTURE_HIT_TEXTS,
    OPTIONAL_SKIP_RATE,
    bootstrap_slot_cloud,
    cloud_variant_lists,
    default_template,
    fixture_hit_texts,
    observe_hit,
)
from formulation.boundary.tfidf_windows import OPENING_TEMPLATE_18C, tokenize


def test_default_template_is_18c() -> None:
    tid, tokens = default_template()
    assert tid == "opening_requeste_18c"
    assert tokens == OPENING_TEMPLATE_18C


def test_align_sw_pairs_maps_slots() -> None:
    template = list(OPENING_TEMPLATE_18C)
    ocr = tokenize("noise IS ter Vergaderinge geleesen de Requeste van Jan")
    result, pairs = align_sw_pairs(template, ocr)
    assert result.score > 0
    matched = {s: j for s, j in pairs if j is not None}
    assert len(matched) >= 4
    # First template slot should land on "IS"
    assert ocr[matched[0]].lower() == "is"


def test_observe_hit_rejects_noise() -> None:
    template = list(OPENING_TEMPLATE_18C)
    assert observe_hit(template, tokenize("de coopman tot Amsterdam")) is None
    hit = observe_hit(
        template,
        tokenize("IS ter Vergaderinge geleesen de Requeste van Jan"),
    )
    assert hit is not None
    assert hit["n_matched"] >= 5


def test_bootstrap_collects_ocr_variants() -> None:
    template = list(OPENING_TEMPLATE_18C)
    cloud, notes = bootstrap_slot_cloud(
        fixture_hit_texts(),
        template,
        template_id="opening_requeste_18c",
        period="18c",
    )
    assert notes["msa"] is False
    assert notes["n_hits_accepted"] >= 4
    assert notes["optional_skip_rate"] == OPTIONAL_SKIP_RATE
    assert len(cloud["slots"]) == len(template)
    # "Is" / "gelesen" / "d'" / "Reqveste" style drift should appear somewhere.
    all_tokens = {
        v["token"]
        for slot in cloud["slots"]
        for v in slot["variants"]
    }
    assert "IS" in all_tokens or "Is" in all_tokens
    assert any(t.lower().startswith("geles") for t in all_tokens)

    lists = cloud_variant_lists(cloud)
    assert len(lists) == len(template)
    assert all(lists[i][0] == template[i] for i in range(len(template)))

    # Cloud must be usable by STEPS0 SW cloud aligner.
    ocr = tokenize(FIXTURE_HIT_TEXTS[2])
    aligned = align_sw_cloud(lists, ocr)
    assert aligned.score > 0
    assert aligned.end_idx > aligned.start_idx


def test_optional_skip_rate_hypothesis_flag() -> None:
    template = ["A", "opt", "B"]
    # Hits that often skip middle token.
    texts = [
        "A B rest",
        "A B more",
        "A opt B rest",
        "A B again",
    ]
    cloud, notes = bootstrap_slot_cloud(
        texts,
        template,
        template_id="toy",
        period=None,
        optional_skip_rate=0.5,
        min_matched_ratio=0.5,
    )
    assert notes["optional_skip_rate_is_hypothesis"] is True
    assert 1 in cloud["optional_slots"] or cloud["slots"][1]["skip_rate"] >= 0.5
