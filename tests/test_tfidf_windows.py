"""STEPS1: char_wb sublinear TF-IDF window framing smoke."""

from __future__ import annotations

from formulation.boundary.tfidf_windows import (
    ANALYZER,
    DEFAULT_THRESHOLD,
    NGRAM_RANGE,
    OPENING_TEMPLATE_18C,
    SUBLINEAR_TF,
    TEMPLATE_ID_OPENING,
    collect_windows,
    default_opening_template,
    frame_documents,
    make_vectorizer,
    opening_template_from_cases,
    select_candidates,
    sliding_windows,
    tokenize,
)


TEMPLATE = list(OPENING_TEMPLATE_18C)


def test_vectorizer_is_char_wb_3_to_5_sublinear() -> None:
    vec = make_vectorizer(min_df=1)
    assert vec.analyzer == ANALYZER == "char_wb"
    assert vec.ngram_range == NGRAM_RANGE == (3, 5)
    assert vec.sublinear_tf is SUBLINEAR_TF is True


def test_sliding_windows_cover_short_and_strided() -> None:
    tokens = tokenize("a b c d e f g h i j")
    short = sliding_windows(tokens[:3], window_size=8, stride=2)
    assert short == [(0, 3, "a b c")]
    wins = sliding_windows(tokens, window_size=4, stride=2)
    starts = [s for s, _, _ in wins]
    assert starts[0] == 0
    assert starts[-1] == 6


def test_opening_hit_scores_above_background() -> None:
    import pandas as pd

    opening = " ".join(TEMPLATE + ["van", "Jan", "Jansen"])
    noise = "de coopman tot Amsterdam verzoekt vrijdom van licenten ende convoyen"
    frame = pd.DataFrame(
        {
            "id": ["hit", "noise"],
            "resolutions_text": [opening, noise],
        }
    )
    scored, candidates, notes = frame_documents(
        frame,
        TEMPLATE,
        window_size=8,
        stride=2,
        threshold=0.2,
        min_df=1,
    )
    hit_max = float(scored.loc[scored["id"].eq("hit"), "score"].max())
    noise_max = float(scored.loc[scored["id"].eq("noise"), "score"].max())
    assert hit_max > noise_max
    assert hit_max >= DEFAULT_THRESHOLD or notes["n_above_threshold"] >= 1
    assert notes["threshold_is_hypothesis"] is False
    assert notes["sublinear_tf"] is True
    assert notes["analyzer"] == "char_wb"
    assert len(select_candidates(scored)) == notes["n_above_threshold"]
    assert not candidates.empty
    assert "align_start" in candidates.columns
    assert "align_end" in candidates.columns


def test_default_opening_template_is_18c() -> None:
    tid, tokens = default_opening_template()
    assert tid == TEMPLATE_ID_OPENING == "opening_requeste_18c"
    assert tokens == OPENING_TEMPLATE_18C


def test_opening_template_from_fixture_shape() -> None:
    legacy = [
        "Gepraesenteert",
        "ende",
        "gelesen",
        "sijnde",
        "de",
        "Requeste",
    ]
    cases = [
        {
            "case_id": "opening_clean",
            "template": legacy,
            "ocr_tokens": legacy + ["van"],
        }
    ]
    tid, tokens = opening_template_from_cases(cases)
    assert tid == "fixture_opening_clean"
    assert tokens == legacy


def test_collect_windows_keeps_offsets() -> None:
    import pandas as pd

    windows = collect_windows(
        pd.Series(["one two three four five six"]),
        pd.Series(["doc-1"]),
        window_size=4,
        stride=2,
    )
    assert set(windows.columns) >= {"id", "token_start", "token_end", "window_text"}
    assert windows.iloc[0]["token_start"] == 0
    assert windows.iloc[0]["id"] == "doc-1"
