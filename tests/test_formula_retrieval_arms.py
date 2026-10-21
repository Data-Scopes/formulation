"""STEPT1q: retrieval-arm comparison unit tests (no ES, no resolutions_flat)."""

from __future__ import annotations

import re

import pandas as pd
import pytest

from formulation.formula_retrieval_arms import (
    ANCHOR_ARMS,
    TYPES,
    anchor_span,
    arm_rates,
    build_clean_boot_cloud,
    contained,
    deltas,
    fixture_frames,
    format_summary,
    fp_overlap,
    iou,
    load_type_api,
    normalized_tokens,
    recall_matched_fp,
    scheme_search_phrase,
    span_agreement,
    tfidf_arm_scores,
)


def test_gold_query_body_default_is_systematic_id_asc():
    from formulation.es_gold_sample import gold_query_body

    body = gold_query_body("missive", 1705, size=15)
    assert body["sort"] == [{"_id": "asc"}]
    assert "function_score" not in body["query"]
    filters = body["query"]["bool"]["filter"]
    assert {"term": {"metadata.proposition_type.keyword": "missive"}} in filters
    assert {"term": {"metadata.session_year": 1705}} in filters


def test_gold_query_body_random_within_year_omits_sort():
    from formulation.es_gold_sample import gold_query_body

    body = gold_query_body(
        "missive", 1705, size=15, random_within_year=True, random_seed=42
    )
    assert "sort" not in body
    fs = body["query"]["function_score"]
    assert fs["random_score"] == {"seed": 42, "field": "_seq_no"}
    filters = fs["query"]["bool"]["filter"]
    assert {"term": {"metadata.proposition_type.keyword": "missive"}} in filters
    assert {"term": {"metadata.session_year": 1705}} in filters


def test_scheme_search_phrases_resolve():
    assert scheme_search_phrase("ontfangen_start") == "tfange"
    assert scheme_search_phrase("requeste_start") == r"op\s?[td]+e reques"
    with pytest.raises(KeyError):
        scheme_search_phrase("no_such_scheme")


@pytest.mark.parametrize("type_key", sorted(TYPES))
def test_every_type_api_resolves(type_key):
    api = load_type_api(type_key)
    assert isinstance(api["canonic_text"], str) and api["canonic_text"]
    assert callable(api["score_text"])
    assert callable(api["wording_flags"])
    # token_re must be the type's own cue regex: it has to fire on a token of
    # that type's own canonic, which catches a copy-paste wiring mistake.
    assert any(
        api["token_re"].search(tok)
        for tok in normalized_tokens(api["canonic_text"])
    )
    assert scheme_search_phrase(api["scheme"])


def test_iou_and_containment():
    assert iou((0, 10), (0, 10)) == 1.0
    assert iou((0, 5), (5, 10)) == 0.0
    assert iou((0, 10), (5, 15)) == pytest.approx(5 / 15)
    assert iou((0, 5), None) is None
    assert contained((3, 4), (0, 10)) is True
    assert contained((11, 12), (0, 10)) is False
    assert contained(None, (0, 10)) is None


def test_anchor_span_finds_first_match_only():
    tokens = ["Ontfangen", "een", "missive", "van", "een", "missive"]
    pattern = re.compile(r"(?i)^missiv[ei]?$")
    assert anchor_span(tokens, pattern) == (2, 3)
    assert anchor_span(tokens, re.compile("zzz")) is None


def test_normalized_grid_matches_tfidf_tokenizer():
    """Arms must share one token grid, or spans are not comparable."""
    from formulation.boundary.tfidf_windows import tokenize

    text = "Ontfangen een missive van den Heer, houdende advertentie."
    norm = normalized_tokens(text)
    assert tokenize(" ".join(norm)) == norm


def test_tfidf_arm_spans_index_the_normalized_grid():
    gold, _neg = fixture_frames()
    best = tfidf_arm_scores(
        gold,
        "Ontfangen een missive van",
        template_id="missive_ontfangen",
        threshold=0.40,
    )
    assert set(best["id"]) == set(gold["id"])
    for rec in best.to_dict("records"):
        text = gold.loc[gold["id"] == rec["id"], "resolutions_text"].iloc[0]
        n = len(normalized_tokens(text))
        assert 0 <= rec["tfidf_start"] < rec["tfidf_end"] <= n


def test_arm_rates_reports_wilson_cis():
    gold = pd.DataFrame({"a_fire": [True, True, False, True]})
    neg = pd.DataFrame({"a_fire": [False, True, False, False]})
    (row,) = arm_rates(gold, neg, ["a"])
    assert row["recall"] == 0.75
    assert row["fp"] == 0.25
    lo, hi = row["recall_ci95"]
    assert lo < 0.75 < hi


def test_arm_rates_skips_arms_that_did_not_run():
    gold = pd.DataFrame({"a_fire": [True], "b_fire": [None]})
    neg = pd.DataFrame({"a_fire": [False], "b_fire": [None]})
    assert [r["arm"] for r in arm_rates(gold, neg, ["a", "b"])] == ["a"]


def test_deltas_verdicts():
    rates = [
        {"arm": "substring_wording", "recall": 0.95, "fp": 0.02},
        {"arm": "substring_scheme", "recall": 0.80, "fp": 0.30},
        {"arm": "dag_clean_boot", "recall": 0.90, "fp": 0.05},
    ]
    out = deltas(rates)
    assert out["substring_wording__vs__dag_clean_boot"]["verdict"] == "substring_wins"
    assert out["substring_scheme__vs__dag_clean_boot"]["verdict"] == "substring_loses"
    assert out["g1_judged_on"].endswith("dag_clean_boot")


def test_deltas_trades_when_mixed():
    rates = [
        {"arm": "substring_wording", "recall": 0.99, "fp": 0.40},
        {"arm": "dag_clean_boot", "recall": 0.90, "fp": 0.05},
    ]
    assert (
        deltas(rates)["substring_wording__vs__dag_clean_boot"]["verdict"] == "trades"
    )


def test_span_agreement_restricts_iou_to_comparable_spans():
    gold = pd.DataFrame(
        [
            {
                "substring_wording_fire": True,
                "substring_wording_start": 2,
                "substring_wording_end": 3,
                "tfidf_window_fire": True,
                "tfidf_window_start": 0,
                "tfidf_window_end": 16,
                "dag_frozen_fire": True,
                "dag_frozen_start": 1,
                "dag_frozen_end": 7,
                "dag_clean_boot_fire": True,
                "dag_clean_boot_start": 0,
                "dag_clean_boot_end": 6,
            }
        ]
    )
    out = span_agreement(gold)
    # Only the DAG-vs-DAG pair admits IoU.
    assert list(out["iou"]) == ["dag_frozen__dag_clean_boot"]
    assert out["iou"]["dag_frozen__dag_clean_boot"]["median"] == pytest.approx(
        5 / 7, abs=1e-4
    )
    # Window/anchor pairs go through containment instead.
    assert out["containment"]["dag_clean_boot__in__tfidf_window"]["rate"] == 1.0
    assert (
        out["containment"]["substring_wording__in__dag_clean_boot"]["rate"] == 1.0
    )
    assert out["midpoint_offset"]["dag_clean_boot__vs__tfidf_window"][
        "median_tokens"
    ] == pytest.approx(5.0)
    # Neither anchors nor the window may ever appear as an IoU pair.
    assert not any(
        label in pair
        for pair in out["iou"]
        for label in (*ANCHOR_ARMS, "tfidf_window")
    )


def test_render_span_marks_the_span_with_context():
    from scripts.build_span_review_xlsx import render_span

    tokens = "a b c d e f g h i j k l m n".split()
    out = render_span(tokens, 6, 8)
    assert "«g h»" in out
    assert out.startswith("a b c d e f")
    assert render_span(tokens, None, 8) == ""


def test_agreement_stratum_classifies_each_disagreement_shape():
    from scripts.build_span_review_xlsx import agreement_stratum

    agree = {
        "tfidf_window_fire": True,
        "tfidf_window_start": 0,
        "tfidf_window_end": 16,
        "dag_frozen_fire": True,
        "dag_frozen_start": 1,
        "dag_frozen_end": 7,
        "dag_clean_boot_fire": True,
        "dag_clean_boot_start": 1,
        "dag_clean_boot_end": 7,
    }
    assert agreement_stratum(agree) == "arms_agree"
    assert agreement_stratum({**agree, "dag_clean_boot_end": 9}) == "dags_disagree"
    assert (
        agreement_stratum({**agree, "tfidf_window_start": 10, "tfidf_window_end": 26})
        == "window_misses_dag"
    )
    assert agreement_stratum({}) == "no_span_arm_fired"
    assert (
        agreement_stratum(
            {"dag_frozen_fire": True, "dag_frozen_start": 1, "dag_frozen_end": 7}
        )
        == "only_dag_frozen"
    )


def test_build_clean_boot_cloud_without_pool_uses_eval_gold():
    gold, _neg = fixture_frames()
    api = load_type_api("missive")
    _cloud, _cut, notes = build_clean_boot_cloud(gold, api=api, random_state=0)
    assert notes["bootstrap_source"] == "eval_gold"
    assert notes["n_bootstrap"] + notes["n_holdout"] == len(gold)


def test_build_clean_boot_cloud_with_pool_bootstraps_from_pool_not_gold():
    gold, _neg = fixture_frames()
    api = load_type_api("missive")
    pool = pd.DataFrame(
        [
            {
                "id": "p1",
                "year": 1783,
                "resolutions_text": (
                    "Ontfangen een missive van de Heeren Staten, houdende "
                    "advertentie van het voorgevallene."
                ),
            },
            {
                "id": "p2",
                "year": 1784,
                "resolutions_text": (
                    "Ontfangen eene missive van den Raad van State, houdende "
                    "communicatie van resolutien."
                ),
            },
            {
                "id": "p3",
                "year": 1785,
                "resolutions_text": (
                    "Ontfangen een missive van den Gouverneur, houdende "
                    "berigt van den staat der zaken."
                ),
            },
            {
                "id": "p4",
                "year": 1786,
                "resolutions_text": (
                    "Ontfangen een missive van den Admiraliteyt, houdende "
                    "bericht van de equipagie."
                ),
            },
            {
                "id": "p5",
                "year": 1787,
                "resolutions_text": (
                    "Ontfangen een missive van de Magistraat, houdende "
                    "verzoek om assistentie."
                ),
            },
        ]
    )
    assert len(pool) != len(gold)
    _cloud, _cut, notes = build_clean_boot_cloud(
        gold, api=api, pool=pool, random_state=0
    )
    assert notes["bootstrap_source"] == "disjoint_pool"
    # n_bootstrap is derived from the 5-row pool split, not the 3-row gold.
    assert notes["n_bootstrap"] + notes["n_holdout"] == len(pool)
    assert notes["n_bootstrap"] != len(gold)


def test_merge_runs_replaces_same_key_keeps_others(monkeypatch):
    from scripts.run_formula_retrieval_arms import merge_runs

    existing = [
        {"type": "missive", "sampling_mode": "systematic_id_asc", "v": "old"},
        {"type": "requeste", "sampling_mode": "systematic_id_asc", "v": "old"},
    ]
    monkeypatch.setattr(
        "scripts.run_formula_retrieval_arms.load", lambda logical: existing
    )
    new_records = [{"type": "missive", "sampling_mode": "systematic_id_asc", "v": "new"}]
    out = merge_runs(
        "formula_retrieval_arms_metrics",
        new_records,
        key=("missive", "systematic_id_asc"),
    )
    assert len(out) == 2
    missive = next(r for r in out if r["type"] == "missive")
    assert missive["v"] == "new"
    requeste = next(r for r in out if r["type"] == "requeste")
    assert requeste["v"] == "old"


def test_merge_runs_fresh_returns_only_new_records(monkeypatch):
    from scripts.run_formula_retrieval_arms import merge_runs

    existing = [{"type": "missive", "sampling_mode": "systematic_id_asc", "v": "old"}]
    monkeypatch.setattr(
        "scripts.run_formula_retrieval_arms.load", lambda logical: existing
    )
    new_records = [{"type": "requeste", "sampling_mode": "systematic_id_asc", "v": "new"}]
    out = merge_runs(
        "formula_retrieval_arms_metrics",
        new_records,
        key=("requeste", "systematic_id_asc"),
        fresh=True,
    )
    assert out == new_records


def test_merge_runs_treats_missing_dataset_as_empty(monkeypatch):
    from scripts.run_formula_retrieval_arms import merge_runs

    def _raise(logical):
        raise FileNotFoundError(logical)

    monkeypatch.setattr("scripts.run_formula_retrieval_arms.load", _raise)
    new_records = [{"type": "missive", "sampling_mode": "systematic_id_asc", "v": "new"}]
    out = merge_runs(
        "formula_retrieval_arms_metrics",
        new_records,
        key=("missive", "systematic_id_asc"),
    )
    assert out == new_records


def test_fp_overlap_counts_unanimity():
    neg = pd.DataFrame(
        {
            "a_fire": [True, True, False],
            "b_fire": [True, False, False],
        }
    )
    out = fp_overlap(neg, ["a", "b"])
    assert out["n_negatives_any_arm_fires"] == 2
    assert out["unanimous_share_of_fp"] == 0.5
    assert out["by_n_arms_firing"]["0"] == 1
    assert out["arms_counted"] == ["a", "b"]


def test_fp_overlap_arms_counted_drops_arms_with_no_column():
    neg = pd.DataFrame({"a_fire": [True, False]})
    out = fp_overlap(neg, ["a", "b"])
    assert out["arms_counted"] == ["a"]
    assert out["n_arms"] == 1


# --- DEFECT 1: recall-matched FP (cross-arm comparison at the same cut) ---


def test_recall_matched_fp_anchors_cut_to_target_recall():
    gold_scores = [1.0, 2.0, 3.0, 4.0, 5.0]
    neg_scores = [0.5, 2.5, 4.5]
    out = recall_matched_fp(gold_scores, neg_scores, target_recall=0.8)
    # p20 of gold scores (the 20th percentile, linear interpolation) is the
    # cut for 80% recall: quantile(0.2) of [1..5] == 1.8.
    assert out["target_recall"] == 0.8
    assert out["cut"] == pytest.approx(1.8, abs=1e-6)
    assert out["achieved_recall"] == pytest.approx(0.8, abs=1e-6)
    assert out["fp"] == pytest.approx(2 / 3, abs=1e-4)


def test_recall_matched_fp_empty_inputs_returns_nones():
    out = recall_matched_fp([], [1.0, 2.0], target_recall=0.8)
    assert out == {
        "target_recall": 0.8,
        "cut": None,
        "fp": None,
        "achieved_recall": None,
    }
    out2 = recall_matched_fp([1.0, 2.0], [], target_recall=0.8)
    assert out2["cut"] is None
    assert out2["fp"] is None
    assert out2["achieved_recall"] is None


# --- DEFECT 3: an arm with 0/N gold hits is inapplicable, not a result ---


def test_arm_rates_flags_zero_recall_as_inapplicable():
    gold = pd.DataFrame({"a_fire": [False, False, False], "b_fire": [True, False, True]})
    neg = pd.DataFrame({"a_fire": [False, False], "b_fire": [True, False]})
    rows = {r["arm"]: r for r in arm_rates(gold, neg, ["a", "b"])}
    assert rows["a"]["recall"] == 0.0
    assert rows["a"]["applicable"] is False
    assert "0/3 gold hits" in rows["a"]["applicability_note"]
    assert rows["b"]["applicable"] is True
    assert "applicability_note" not in rows["b"]


def test_deltas_skips_inapplicable_arm():
    rates = [
        {
            "arm": "substring_scheme",
            "recall": 0.0,
            "fp": 0.0,
            "applicable": False,
            "applicability_note": "0/10 gold hits - treat as inapplicable",
        },
        {"arm": "substring_wording", "recall": 0.95, "fp": 0.02, "applicable": True},
        {"arm": "dag_clean_boot", "recall": 0.90, "fp": 0.05, "applicable": True},
    ]
    out = deltas(rates)
    assert "substring_scheme__vs__dag_clean_boot" not in out
    assert "substring_wording__vs__dag_clean_boot" in out


# --- DEFECT 4: readable summary ---


def test_format_summary_contains_every_arm_name():
    metrics = {
        "type": "missive",
        "formula_type_id": "missive_ontfangen",
        "index": "fixture",
        "sampling_mode": "systematic_id_asc",
        "n_gold_joined": 3,
        "n_negatives": 2,
        "bootstrap_source": "eval_gold",
        "n_bootstrap_pool": 0,
        "arms": [
            {
                "arm": "substring_wording",
                "recall": 1.0,
                "recall_ci95": [0.4, 1.0],
                "fp": 0.0,
                "fp_ci95": [0.0, 0.6],
                "applicable": True,
            },
            {
                "arm": "substring_scheme",
                "recall": 0.0,
                "recall_ci95": [0.0, 0.5],
                "fp": 0.0,
                "fp_ci95": [0.0, 0.6],
                "applicable": False,
                "applicability_note": "0/3 gold hits",
            },
            {
                "arm": "tfidf_window",
                "recall": 1.0,
                "recall_ci95": [0.4, 1.0],
                "fp": 0.0,
                "fp_ci95": [0.0, 0.6],
                "applicable": True,
            },
            {
                "arm": "tfidf_window_p20",
                "recall": 0.67,
                "recall_ci95": [0.2, 0.9],
                "fp": 0.0,
                "fp_ci95": [0.0, 0.6],
                "applicable": True,
            },
            {
                "arm": "dag_clean_boot",
                "recall": 1.0,
                "recall_ci95": [0.4, 1.0],
                "fp": 0.0,
                "fp_ci95": [0.0, 0.6],
                "applicable": True,
            },
        ],
        "cuts": {"dag_clean_boot": 5.25, "tfidf_window": 0.4, "tfidf_window_p20": 0.44},
        "recall_matched": {
            "note": "anchors excluded",
            "tfidf_window": {
                "target_recall": 1.0,
                "cut": 0.44,
                "fp": 0.0,
                "achieved_recall": 1.0,
            },
        },
        "span_agreement": {
            "iou": {"dag_frozen__dag_clean_boot": {"median": 0.8}},
            "containment": {
                "dag_clean_boot__in__tfidf_window": {"rate": 1.0},
                "substring_wording__in__dag_clean_boot": {"rate": 1.0},
            },
        },
        "fp_overlap": {
            "n_negatives_any_arm_fires": 0,
            "unanimous_share_of_fp": None,
            "arms_counted": ["substring_wording", "tfidf_window"],
        },
    }
    out = format_summary(metrics)
    assert isinstance(out, str)
    for arm in (
        "substring_wording",
        "substring_scheme",
        "tfidf_window",
        "tfidf_window_p20",
        "dag_clean_boot",
    ):
        assert arm in out
