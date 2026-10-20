"""Unit smoke for STEPT1a appointment formula-type scoring (no parquet)."""

from __future__ import annotations

from formulation.appointment_formula_type import (
    WELKOM_CANONIC,
    apply_popularity,
    build_appointment_clouds,
    calibrate_cut,
    fixture_smoke_frames,
    popularity_weight,
    score_text,
    welkom_bootstrap_texts,
    wording_flags,
)


def test_wording_flags_and_canonic():
    assert "verwelkomt" in WELKOM_CANONIC
    flags = wording_flags("is den selven verwelkomt, ende sessie genomen")
    assert flags["welkom"] and flags["sessie"] and flags["welkom_or_sessie"]
    assert not wording_flags("Ontfangen een missive")["welkom_or_sessie"]


def test_cue_windows_strip_punct_around_verwelkomt():
    text = "was, is den selven verwelkomt, en heeft dienvolgende sessie genomen"
    wins, meta = welkom_bootstrap_texts([text], pad=3)
    assert meta["mode"] == "cue_windows"
    assert wins
    assert "verwelkomt" in wins[0]
    assert "verwelkomt," not in wins[0]


def test_welkom_cloud_accepts_empirical_windows():
    texts = [
        "was, is den selven verwelkomt, en heeft dienvolgende sessie genomen",
        "is den zelven verwellekomt, ende heeft sessie genomen",
        "is den selve verwelkomt, en heeft sessie genomen",
    ]
    welkom_cloud, _sessie, notes = build_appointment_clouds(texts)
    w_notes = notes["welkom"]
    assert w_notes["n_hits_accepted"] >= 2
    assert w_notes["bootstrap_input"]["mode"] == "cue_windows"
    # Learned OCR surface present (not seed-only).
    welkom_slot = next(
        s for s in welkom_cloud["slots"] if s["canonical"] == "verwelkomt"
    )
    learned = {v["token"] for v in welkom_slot["variants"] if int(v.get("count") or 0) > 0}
    assert "verwelkomt" in learned or "verwellekomt" in learned


def test_cloud_scores_fixture_positive_above_negative():
    gold, neg = fixture_smoke_frames()
    texts = gold["resolutions_text"].tolist()
    welkom_cloud, sessie_cloud, _notes = build_appointment_clouds(texts)
    pos = score_text(gold.iloc[1]["resolutions_text"], welkom_cloud, sessie_cloud)
    neg_s = score_text(neg.iloc[0]["resolutions_text"], welkom_cloud, sessie_cloud)
    assert pos["score"] > neg_s["score"]
    assert pos["score"] > 0


def test_calibrate_cut_fallback():
    assert calibrate_cut([]) == 2.0
    assert calibrate_cut([1.0, 2.0, 3.0, 4.0, 5.0]) <= 3.0


def test_popularity_punishes_ubiquitous_formulas():
    # goedgevonden-like (~0.60 corpus) weighs much less than rare (~0.02).
    w_common = popularity_weight(0.60)
    w_rare = popularity_weight(0.02)
    assert w_rare > w_common
    assert apply_popularity(4.0, 0.60) < apply_popularity(4.0, 0.02)
    assert popularity_weight(1.0) < 0.01 or popularity_weight(0.999) < 1.0
