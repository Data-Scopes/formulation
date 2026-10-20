"""STEPS3: SW/DAG span harvest on windows + slot-cloud."""

from __future__ import annotations

from formulation.boundary.slot_cloud import bootstrap_slot_cloud, fixture_hit_texts
from formulation.boundary.span_harvest import (
    METHOD_DAG,
    METHOD_SW_CLOUD,
    METHOD_SW_SINGLE,
    FIXTURE_SHORTENED_TEXTS,
    cloud_align_inputs,
    fixture_windows,
    harvest_spans,
    harvest_window,
    normalize_cloud,
    windows_from_records,
)
from formulation.boundary.tfidf_windows import OPENING_TEMPLATE_18C, tokenize


def _fixture_cloud() -> dict:
    template = list(OPENING_TEMPLATE_18C)
    cloud, _notes = bootstrap_slot_cloud(
        fixture_hit_texts(),
        template,
        template_id="opening_requeste_18c",
        period="18c",
    )
    return cloud


def test_normalize_and_cloud_inputs() -> None:
    cloud = _fixture_cloud()
    wrapped = normalize_cloud([cloud])
    tid, template, lists, optional = cloud_align_inputs(wrapped)
    assert tid == "opening_requeste_18c"
    assert template == OPENING_TEMPLATE_18C
    assert len(lists) == len(template)
    assert isinstance(optional, list)


def test_harvest_window_emits_three_methods() -> None:
    cloud = _fixture_cloud()
    tid, template, lists, optional = cloud_align_inputs(cloud)
    window = {
        "id": "w1",
        "token_start": 10,
        "token_end": 20,
        "score": 0.9,
        "window_text": "noise IS ter Vergaderinge geleesen de Requeste van Jan",
        "template_id": tid,
    }
    rows = harvest_window(
        window,
        template=template,
        variant_lists=lists,
        optional_slots=optional,
        template_id=tid,
    )
    methods = {r["method"] for r in rows}
    assert methods == {METHOD_SW_SINGLE, METHOD_SW_CLOUD, METHOD_DAG}
    for row in rows:
        assert row["align_score"] > 0
        assert row["local_end"] > row["local_start"]
        # Document offsets = window base + local.
        assert row["doc_start"] == 10 + row["local_start"]
        assert row["doc_end"] == 10 + row["local_end"]
        assert "Requeste" in row["span_text"] or "requeste" in row["span_text"].lower()


def test_harvest_shortened_fixture_windows() -> None:
    cloud = _fixture_cloud()
    windows = fixture_windows()
    assert any(
        w["window_text"] in FIXTURE_SHORTENED_TEXTS for w in windows
    )
    spans, notes = harvest_spans(windows, cloud)
    assert notes["n_windows"] == len(windows)
    assert notes["n_span_rows"] == len(windows) * 3
    assert notes["threshold_calibrated"] is True
    assert notes["gysbert"] is False
    dag_rows = [r for r in spans if r["method"] == METHOD_DAG]
    assert any(r["align_score"] > 0 and r["n_matched_tokens"] >= 3 for r in dag_rows)
    agree = notes["sw_cloud_dag_span_agreement"]
    assert agree["n_compared"] == len(windows)


def test_windows_from_records_joins_ocr_tokens() -> None:
    rows = windows_from_records(
        [
            {
                "id": "c1",
                "ocr_tokens": ["IS", "ter", "Vergaderinge", "geleesen", "de", "Requeste"],
                "token_start": 0,
                "gt_start": 0,
                "gt_end": 6,
            }
        ]
    )
    assert len(rows) == 1
    assert rows[0]["window_text"].startswith("IS ter")
    assert rows[0]["gt_end"] == 6


def test_gold_iou_on_clean_opening() -> None:
    cloud = _fixture_cloud()
    tid, template, lists, optional = cloud_align_inputs(cloud)
    text = "IS ter Vergaderinge geleesen de Requeste van Jan"
    tokens = tokenize(text)
    window = {
        "id": "gold",
        "token_start": 0,
        "token_end": len(tokens),
        "score": 1.0,
        "window_text": text,
        "gt_start": 0,
        "gt_end": 6,
    }
    rows = harvest_window(
        window,
        template=template,
        variant_lists=lists,
        optional_slots=optional,
        template_id=tid,
    )
    for row in rows:
        assert row["iou"] >= 0.8
