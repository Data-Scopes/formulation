"""Unit smoke for STEPT1v2 hard-drop L1→L2 (no ES / parquet)."""

from __future__ import annotations

from formulation.formula_reduction_hard_drop import (
    REQUESTE_CANONIC,
    fixture_smoke,
    hard_drop_configs,
    hard_drop_variants,
    leave_k_configs,
    score_text_hard_drop,
    slot_labels,
    summarize_hard_drop,
)


def test_hard_drop_configs_cover_each_slot():
    configs = hard_drop_configs(6)
    ids = {c["config_id"] for c in configs}
    assert "full" in ids
    assert configs[0]["drop_slots"] == []
    assert {c["config_id"] for c in configs if c["kind"] == "single_slot_hard_drop"} == {
        f"drop_{i}" for i in range(6)
    }
    drop0 = next(c for c in configs if c["config_id"] == "drop_0")
    assert drop0["kept_slots"] == [1, 2, 3, 4, 5]


def test_hard_drop_variants_removes_slot():
    _, _, cloud, _ = fixture_smoke()
    labels = slot_labels(cloud)
    full = hard_drop_variants(cloud, [])
    assert len(full) == len(labels)
    dropped = hard_drop_variants(cloud, [0])
    assert len(dropped) == len(labels) - 1
    # First remaining slot should still be original slot 1's canonical family
    assert dropped[0][0].casefold() == labels[1].casefold() or labels[1].casefold() in {
        v.casefold() for v in dropped[0]
    }


def test_leave_k_count():
    # C(4,2) = 6
    assert len(leave_k_configs(4, 2)) == 6


def test_hard_drop_changes_score_vs_soft_optional():
    """Forced absence of a hinge-ish token should not match soft-optional no-op."""
    gold, _neg, cloud, _notes = fixture_smoke()
    text = gold.iloc[0]["resolutions_text"]
    full = score_text_hard_drop(text, cloud, [])
    # Drop "Requeste" (last slot) — still finds the rest, but fewer layers
    labels = slot_labels(cloud)
    req_i = next(
        (i for i, t in enumerate(labels) if t.casefold() == "requeste"),
        len(labels) - 1,
    )
    dropped = score_text_hard_drop(text, cloud, [req_i])
    assert full["n_slots_scored"] == len(labels)
    assert dropped["n_slots_scored"] == len(labels) - 1
    assert dropped["score"] <= full["score"]


def test_summarize_marks_safe_or_hinge():
    labels = ["IS", "ter", "Vergaderinge", "geleesen", "de", "Requeste"]
    rows = [
        {
            "config_id": "full",
            "kind": "baseline_full",
            "drop_slots": [],
            "recall": 0.90,
            "fp_rate": 0.05,
            "cut": 9.0,
        },
        {
            "config_id": "drop_4",
            "kind": "single_slot_hard_drop",
            "drop_slots": [4],
            "ablated_slot": 4,
            "recall": 0.89,
            "fp_rate": 0.06,
            "cut": 7.5,
        },
        {
            "config_id": "drop_5",
            "kind": "single_slot_hard_drop",
            "drop_slots": [5],
            "ablated_slot": 5,
            "recall": 0.50,
            "fp_rate": 0.20,
            "cut": 4.0,
        },
    ]
    summary = summarize_hard_drop(
        rows,
        labels=labels,
        cloud_notes={},
        n_gold_universe=100,
        n_bootstrap=80,
        n_holdout=20,
        random_state=0,
        mode="single_slot_hard_drop",
    )
    assert any(s["token"] == "de" for s in summary["safe_drop_slots"])
    assert any(s["token"] == "Requeste" for s in summary["hinge_slots"])
    assert "Requeste" in summary["l2_required_tokens_guess"]
    assert summary["step"] == "STEPT1v2"
    assert summary["canonic"] == REQUESTE_CANONIC
