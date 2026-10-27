"""Unit tests for STEPT1ag residual sweep (fixture only)."""

from __future__ import annotations

from formulation.formula_family_residual_sweep import (
    fixture_sweep,
    is_trivial_family,
    propose_truncate,
    sweep_families,
)


def test_trivial_sieve_catches_tok_and_short() -> None:
    trivial, reason = is_trivial_family(
        {
            "exemplar_norm": "van de",
            "n_members": 1,
            "overlap_cue": "other",
            "hinge_bucket": "tok:van_de",
        }
    )
    assert trivial and reason == "token_len_le3"

    trivial2, reason2 = is_trivial_family(
        {
            "exemplar_norm": "houdende dat",
            "n_members": 1,
            "overlap_cue": "other",
            "hinge_bucket": "tok:houdende_dat",
        }
    )
    assert trivial2 and reason2 == "short_tail_f1b"


def test_truncate_proposal_on_waar_straddle() -> None:
    prop = propose_truncate(
        {"exemplar_norm": "houdende advertentie waar op", "n_members": 1}
    )
    assert prop is not None
    assert prop["action"] == "truncate_or_split"
    assert "waar" in prop["suffix"]


def test_fixture_sweep_parks_trivia_caps_review() -> None:
    out = fixture_sweep()
    m = out["metrics"]
    assert m["step"] == "STEPT1ag"
    assert m["n_trivial"] >= 3
    assert m["n_review"] >= 1
    assert m["n_review"] <= m["review_cap"]
    reasons = m["trivial_reason_hist"]
    assert "token_len_le3" in reasons or "short_tail_f1b" in reasons
    # multi family never in trivial
    triv_ids = {r["family_id"] for r in out["trivial"]}
    assert "fam_m001" not in triv_ids
    # chain fragment should be reviewable (absorb into multi)
    rev_ids = {r["family_id"] for r in out["review"]}
    assert "fam_s_chain" in rev_ids or "fam_s_waar" in rev_ids
    for r in out["review"]:
        assert r.get("human_keep") is None


def test_substring_of_multi_is_trivial() -> None:
    multi_ex = ["waar op gedelibereert zynde is goedgevonden en verstaan"]
    trivial, reason = is_trivial_family(
        {
            "exemplar_norm": "gedelibereert zynde is goedgevonden",
            "n_members": 1,
            "overlap_cue": "other",
            "hinge_bucket": "tok:gedelibereert_zynde",
        },
        multi_exemplars=multi_ex,
    )
    assert trivial and reason == "substring_of_multi"


def test_review_cap_overflow_parks() -> None:
    families = [
        {
            "family_id": "fam_m",
            "exemplar": "WAAR op gedelibereert zynde is",
            "exemplar_norm": "waar op gedelibereert zynde is",
            "n_members": 4,
            "phrase_freq_max": 9000,
            "overlap_cue": "waar_op",
            "hinge_bucket": "cue:waar_op",
        }
    ]
    for i in range(10):
        families.append(
            {
                "family_id": f"fam_s{i}",
                "exemplar": f"waar op gedelibereert zynde variant {i}",
                "exemplar_norm": f"waar op gedelibereert zynde variant {i}",
                "n_members": 1,
                "phrase_freq_max": 1000 - i,
                "overlap_cue": "waar_op",
                "overlap_place": "decision",
                "hinge_bucket": "cue:waar_op",
            }
        )
    out = sweep_families(families, review_cap=3)
    assert out["metrics"]["n_review"] == 3
    assert out["metrics"]["n_review_capped_out"] == 7


def test_freq_below_min_parks_even_with_cue() -> None:
    families = [
        {
            "family_id": "fam_m",
            "exemplar": "WAAR op gedelibereert zynde is",
            "exemplar_norm": "waar op gedelibereert zynde is",
            "n_members": 4,
            "phrase_freq_max": 9000,
            "overlap_cue": "waar_op",
            "hinge_bucket": "cue:waar_op",
        },
        {
            "family_id": "fam_lonely",
            "exemplar": "in handen van hunnen Lieutenant",
            "exemplar_norm": "in handen van hunnen lieutenant",
            "n_members": 1,
            "phrase_freq_max": 1,
            "overlap_cue": "in_handen",
            "overlap_place": "decision",
            "hinge_bucket": "cue:in_handen",
        },
        {
            "family_id": "fam_mass",
            "exemplar": "waar op gedelibereert zynde verder",
            "exemplar_norm": "waar op gedelibereert zynde verder",
            "n_members": 1,
            "phrase_freq_max": 800,
            "overlap_cue": "waar_op",
            "overlap_place": "decision",
            "hinge_bucket": "cue:waar_op",
        },
    ]
    out = sweep_families(families, review_cap=10, min_review_freq=500)
    assert out["metrics"]["min_review_freq"] == 500
    assert out["metrics"]["trivial_reason_hist"].get("freq_below_min") == 1
    rev_ids = {r["family_id"] for r in out["review"]}
    assert "fam_lonely" not in rev_ids
    assert "fam_mass" in rev_ids
    for r in out["review"]:
        assert int(r["phrase_freq_max"]) >= 500
