"""Unit smoke for STEPT1w rapport formula-type scoring (no ES / parquet)."""

from __future__ import annotations

from formulation.rapport_formula_type import (
    RAPPORT_CANONIC,
    build_rapport_cloud,
    calibrate_cut,
    fixture_smoke_frames,
    rapport_bootstrap_texts,
    score_text,
    wording_flags,
)


def test_wording_flags_and_canonic():
    assert "rapport" in RAPPORT_CANONIC.casefold()
    assert "gehoord" in RAPPORT_CANONIC.casefold()
    assert wording_flags("IS gehoord het rapport van de Heeren")["rapport_wording"]
    assert wording_flags("gehoort het rapport van de gecommitteerden")["rapport_wording"]
    assert not wording_flags("Ontfangen een missive")["rapport_wording"]


def test_cue_windows_around_rapport():
    text = "IS gehoord het rapport van de Heeren Gedeputeerden van Holland"
    wins, meta = rapport_bootstrap_texts([text], pad=3)
    assert meta["mode"] == "cue_windows"
    assert wins
    assert "rapport" in wins[0].casefold()


def test_cloud_accepts_empirical_windows():
    texts = [
        "IS gehoord het rapport van de Heeren Gedeputeerden van Holland",
        "is gehoort het rapport van de gecommitteerden rakende de saeck",
        "IS gehoord het rapport van de Heeren ter Generaliteit geëxamineert",
    ]
    cloud, notes = build_rapport_cloud(texts)
    assert notes["n_hits_accepted"] >= 2
    assert notes["bootstrap_input"]["mode"] == "cue_windows"
    rapport_slot = next(
        s for s in cloud["slots"] if str(s["canonical"]).casefold() == "rapport"
    )
    learned = {
        v["token"] for v in rapport_slot["variants"] if int(v.get("count") or 0) > 0
    }
    assert learned


def test_cloud_scores_fixture_positive_above_negative():
    gold, neg = fixture_smoke_frames()
    cloud, _notes = build_rapport_cloud(gold["resolutions_text"].tolist())
    pos = score_text(gold.iloc[0]["resolutions_text"], cloud)
    neg_s = score_text(neg.iloc[0]["resolutions_text"], cloud)
    assert pos["score"] > neg_s["score"]
    assert pos["score"] > 0


def test_calibrate_cut_fallback():
    assert calibrate_cut([]) == 2.0
