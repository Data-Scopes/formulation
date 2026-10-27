"""Unit tests for STEPT1aa phrases_5gram profile (fixture only)."""

from __future__ import annotations

from formulation.phrases_5gram_profile import (
    fixture_profile,
    is_protected,
    keyword_role,
    lcats_from_doc_len,
    load_protected_seeds,
    normalize_phrase,
    zone_from_rel,
)


def test_normalize_strips_nlp_sentinels() -> None:
    assert normalize_phrase("geen resolutie is gevallen <END>") == (
        "geen resolutie is gevallen"
    )
    assert normalize_phrase("<START> Ontfangen een Missive") == (
        "ontfangen een missive"
    )


def test_lcats_and_zone() -> None:
    assert lcats_from_doc_len(40) == "very_small"
    assert lcats_from_doc_len(80) == "small"
    assert zone_from_rel(0.1, 0.2) == "opening"
    assert zone_from_rel(0.5, 0.55) == "body"
    assert zone_from_rel(0.8, 0.9) == "close"


def test_protected_seeds_cover_rapport() -> None:
    seeds = load_protected_seeds(include_opener_candidates=False)
    assert is_protected(normalize_phrase("IS gehoord het rapport van"), seeds)


def test_fixture_profile_has_high_and_sidecar() -> None:
    prof = fixture_profile()
    m = prof["metrics"]
    assert m["n_high_freq"] >= 3
    assert m["n_protected_below_gate"] >= 1
    assert m["n_rare_sidecar"] >= 1
    roles = {r["suggested_role"] for r in prof["high_freq"]}
    assert "scaffolding_opener" in roles or "scaffolding_decision" in roles
    assert keyword_role("geen resolutie is gevallen") == "null_decision"
    # Referral windows that also say ``heeren van`` are not attendance junk.
    assert keyword_role("handen van de heeren van") == "decision_ish"
    assert keyword_role("in handen van de heeren") == "decision_ish"
    from formulation.phrases_5gram_profile import suggested_role

    assert (
        suggested_role(
            "handen van de heeren van",
            zone="body",
            pos_start=40.0,
            opener_abs=False,
            opener_rel=False,
        )
        == "scaffolding_decision"
    )
