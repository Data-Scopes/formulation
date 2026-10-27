"""Unit smoke for STEPT1s short requeste opener (no ES / parquet)."""

from __future__ import annotations

from formulation.requeste_op_de_formula_type import (
    REQUESTE_OP_DE_CANONIC,
    build_requeste_op_de_cloud,
    calibrate_cut,
    fixture_smoke_frames,
    is_long_requeste_head,
    is_op_de_requeste_head,
    requeste_op_de_bootstrap_texts,
    score_text,
    wording_flags,
)


def test_wording_flags_and_canonic():
    assert REQUESTE_OP_DE_CANONIC == "Op de Requeste"
    assert wording_flags("Op de Requeste van den suppliant")["op_de_requeste_wording"]
    assert wording_flags("OP de rekest van den coopman")["op_de_requeste_wording"]
    assert not wording_flags(
        "IS ter Vergaderinge geleesen de Requeste van den suppliant"
    )["op_de_requeste_wording"]
    assert not wording_flags("Ontfangen een missive")["op_de_requeste_wording"]


def test_head_classifiers():
    short = "Op de Requeste van den suppliant IS goedgevonden"
    long = "IS ter Vergaderinge geleesen de Requeste van den suppliant"
    assert is_op_de_requeste_head(short)
    assert not is_op_de_requeste_head(long)
    assert is_long_requeste_head(long)
    assert not is_long_requeste_head(short)


def test_head_classifier_short_and_trailing_op():
    """Regression: exact 3-token text and trailing Op must not IndexError."""
    assert is_op_de_requeste_head("Op de Requeste")
    assert is_op_de_requeste_head("OP de rekest")
    assert not is_op_de_requeste_head("Op de")
    assert not is_op_de_requeste_head("")
    # "op" near the end with fewer than 2 tokens after it
    assert not is_op_de_requeste_head("goedgevonden en verstaan Op")
    assert not is_op_de_requeste_head("goedgevonden Op de")


def test_cue_windows_around_requeste():
    text = "Op de Requeste van den suppliant"
    wins, meta = requeste_op_de_bootstrap_texts([text], pad=3)
    assert meta["mode"] == "cue_windows"
    assert wins
    assert "requeste" in wins[0].casefold()


def test_cloud_accepts_empirical_windows():
    texts = [
        "Op de Requeste van den suppliant",
        "OP de requeste van den coopman",
        "Op de Rekest van Jan Jansen",
    ]
    cloud, notes = build_requeste_op_de_cloud(texts)
    assert notes["n_hits_accepted"] >= 2
    assert notes["bootstrap_input"]["mode"] == "cue_windows"
    requeste_slot = next(
        s
        for s in cloud["slots"]
        if str(s["canonical"]).casefold() in {"requeste", "rekest", "request"}
    )
    learned = {
        v["token"] for v in requeste_slot["variants"] if int(v.get("count") or 0) > 0
    }
    assert learned


def test_cloud_scores_fixture_positive_above_negative():
    gold, neg = fixture_smoke_frames()
    cloud, _notes = build_requeste_op_de_cloud(gold["resolutions_text"].tolist())
    pos = score_text(gold.iloc[0]["resolutions_text"], cloud)
    neg_s = score_text(neg.iloc[0]["resolutions_text"], cloud)
    assert pos["score"] > neg_s["score"]
    assert pos["score"] > 0


def test_calibrate_cut_fallback():
    assert calibrate_cut([]) == 2.0
