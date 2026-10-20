"""Unit smoke for STEPT1a2 advies formula-type scoring (no ES / parquet)."""

from __future__ import annotations

from formulation.advies_formula_type import (
    ADVIES_CANONIC,
    advies_bootstrap_texts,
    build_advies_cloud,
    calibrate_cut,
    fixture_smoke_frames,
    score_text,
    wording_flags,
)


def test_wording_flags_and_canonic():
    assert "Advis" in ADVIES_CANONIC
    assert wording_flags("geleesen het Advis van")["advies_wording"]
    assert wording_flags("consideratien en advis")["advies_wording"]
    assert not wording_flags("Ontfangen een missive")["advies_wording"]


def test_cue_windows_around_advis():
    text = "IS ter Vergaderinge geleesen het Advis van 's Lands Advocaten"
    wins, meta = advies_bootstrap_texts([text], pad=3)
    assert meta["mode"] == "cue_windows"
    assert wins
    assert "Advis" in wins[0] or "advis" in wins[0].casefold()


def test_cloud_accepts_empirical_windows():
    texts = [
        "IS ter Vergaderinge geleesen het Advis van 's Lands Advocaten",
        "is ter Vergaderinge gelesen het advies van de Heeren",
        "IS ter Vergaderinge geleesen het Advis van de 's Lands Advocaaten",
    ]
    cloud, notes = build_advies_cloud(texts)
    assert notes["n_hits_accepted"] >= 2
    assert notes["bootstrap_input"]["mode"] == "cue_windows"
    advis_slot = next(
        s
        for s in cloud["slots"]
        if str(s["canonical"]).casefold() in {"advis", "advies"}
    )
    learned = {
        v["token"] for v in advis_slot["variants"] if int(v.get("count") or 0) > 0
    }
    assert learned


def test_cloud_scores_fixture_positive_above_negative():
    gold, neg = fixture_smoke_frames()
    cloud, _notes = build_advies_cloud(gold["resolutions_text"].tolist())
    pos = score_text(gold.iloc[0]["resolutions_text"], cloud)
    neg_s = score_text(neg.iloc[0]["resolutions_text"], cloud)
    assert pos["score"] > neg_s["score"]
    assert pos["score"] > 0


def test_calibrate_cut_fallback():
    assert calibrate_cut([]) == 2.0
