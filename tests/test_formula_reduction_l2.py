"""Unit smoke for STEPT1v L1→L2 formula reduction (no ES / parquet)."""

from __future__ import annotations

from formulation.formula_reduction_l2 import (
    REQUESTE_CANONIC,
    ablation_configs,
    exhaustive_configs,
    fixture_smoke,
    metrics_at_cut,
    score_text_with_optional,
    slot_labels,
    summarize_reduction,
)


def test_slot_labels_match_canonic():
    labels = slot_labels()
    assert len(labels) == 6
    assert " ".join(labels) == REQUESTE_CANONIC or labels[-1].casefold() == "requeste"


def test_ablation_configs_cover_each_slot():
    configs = ablation_configs(6, bootstrap_optional=[2])
    ids = {c["config_id"] for c in configs}
    assert "full" in ids
    assert "all_required" in ids
    assert configs[0]["optional_slots"] == [2]
    assert {c["config_id"] for c in configs if c["kind"] == "single_slot_optional"} == {
        f"ablate_{i}" for i in range(6)
    }


def test_exhaustive_count():
    assert len(exhaustive_configs(3)) == 8


def test_fixture_ablation_scores():
    gold, neg, cloud, notes = fixture_smoke()
    labels = slot_labels(cloud)
    full = score_text_with_optional(
        gold.iloc[0]["resolutions_text"],
        cloud,
        list(cloud.get("optional_slots") or []),
    )
    ablate_de = score_text_with_optional(
        gold.iloc[0]["resolutions_text"],
        cloud,
        [labels.index("de")] if "de" in labels else [4],
    )
    assert full["score"] > 0
    assert ablate_de["score"] >= 0
    assert notes["n_hits_accepted"] >= 1


def test_summarize_marks_safe_or_hinge():
    labels = ["IS", "ter", "Vergaderinge", "geleesen", "de", "Requeste"]
    rows = [
        {
            "config_id": "all_required",
            "kind": "baseline_required",
            "optional_slots": [],
            "recall": 0.90,
            "fp_rate": 0.05,
            "cut": 6.0,
        },
        {
            "config_id": "ablate_4",
            "kind": "single_slot_optional",
            "optional_slots": [4],
            "ablated_slot": 4,
            "recall": 0.89,
            "fp_rate": 0.06,
            "cut": 5.5,
        },
        {
            "config_id": "ablate_5",
            "kind": "single_slot_optional",
            "optional_slots": [5],
            "ablated_slot": 5,
            "recall": 0.50,
            "fp_rate": 0.20,
            "cut": 3.0,
        },
    ]
    summary = summarize_reduction(
        rows,
        labels=labels,
        cloud_notes={},
        n_gold_universe=100,
        n_bootstrap=80,
        n_holdout=20,
        random_state=0,
        mode="single_slot_ablation",
    )
    assert any(s["token"] == "de" for s in summary["safe_ablate_slots"])
    assert any(s["token"] == "Requeste" for s in summary["hinge_slots"])
    assert "Requeste" in summary["l2_required_tokens_guess"]


def test_metrics_at_cut_shape():
    import pandas as pd

    gold = pd.DataFrame({"score": [9.0, 8.0, 4.0]})
    neg = pd.DataFrame({"score": [1.0, 5.0]})
    m = metrics_at_cut(gold, neg, cut=5.0)
    assert m["recall"] == round(2 / 3, 4)
    assert m["fp_rate"] == 0.5
