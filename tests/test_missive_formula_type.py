"""Unit smoke for STEPT1n missive opener formula-type scoring (no ES / parquet)."""

from __future__ import annotations

from formulation.missive_formula_type import (
    MISSIVE_CANONIC,
    build_missive_cloud,
    calibrate_cut,
    fixture_smoke_frames,
    missive_bootstrap_texts,
    score_text,
    wording_flags,
)


def test_wording_flags_and_canonic():
    assert "missive" in MISSIVE_CANONIC.casefold()
    assert wording_flags("Ontfangen een Missive van den ambassadeur")["missive_wording"]
    assert wording_flags("ontfangen eene missiue van den resident")["missive_wording"]
    assert wording_flags("Ontfangen een brieff van den gouverneur")["missive_wording"]
    assert not wording_flags("IS ter Vergaderinge geleesen de Requeste")["missive_wording"]


def test_cue_windows_around_missive():
    text = "Ontfangen een missive van den Gouverneur van Suriname"
    wins, meta = missive_bootstrap_texts([text], pad=3)
    assert meta["mode"] == "cue_windows"
    assert wins
    assert "missive" in wins[0].casefold()


def test_cloud_accepts_empirical_windows():
    texts = [
        "Ontfangen een missive van den Gouverneur van Suriname",
        "ontfangen eene missive van den ambassadeur tot Londen",
        "Ontfangen een missive van den Resident tot Hamburg",
    ]
    cloud, notes = build_missive_cloud(texts)
    assert notes["n_hits_accepted"] >= 2
    assert notes["bootstrap_input"]["mode"] == "cue_windows"
    missive_slot = next(
        s
        for s in cloud["slots"]
        if str(s["canonical"]).casefold() in {"missive", "brief", "missiue"}
    )
    learned = {
        v["token"] for v in missive_slot["variants"] if int(v.get("count") or 0) > 0
    }
    assert learned


def test_cloud_scores_fixture_positive_above_negative():
    gold, neg = fixture_smoke_frames()
    cloud, _notes = build_missive_cloud(gold["resolutions_text"].tolist())
    pos = score_text(gold.iloc[0]["resolutions_text"], cloud)
    neg_s = score_text(neg.iloc[0]["resolutions_text"], cloud)
    assert pos["score"] > neg_s["score"]
    assert pos["score"] > 0


def test_calibrate_cut_fallback():
    assert calibrate_cut([]) == 2.0
