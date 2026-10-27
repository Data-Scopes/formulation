"""Unit tests for STEPT1ab formula family fold (fixture only)."""

from __future__ import annotations

from formulation.formula_family_fold import fold_phrases, fixture_fold, nest_collapse
from formulation.phrases_5gram_profile import normalize_phrase


def test_nest_collapse_attaches_substring_child() -> None:
    rows = [
        {
            "phrase": "Ontfangen een Missive van den Heere",
            "phrase_norm": normalize_phrase("Ontfangen een Missive van den Heere"),
            "phrase_freq": 49000,
        },
        {
            "phrase": "Ontfangen een Missive van den",
            "phrase_norm": normalize_phrase("Ontfangen een Missive van den"),
            "phrase_freq": 90000,
        },
    ]
    kept, n = nest_collapse(rows)
    assert n == 1
    assert len(kept) == 1
    assert "heere" in kept[0]["phrase_norm"]
    nested = kept[0].get("_nested_members") or []
    assert len(nested) == 1
    assert nested[0]["phrase_norm"] == normalize_phrase(
        "Ontfangen een Missive van den"
    )


def test_normalize_end_makes_null_decision_a_substring() -> None:
    assert normalize_phrase("geen resolutie is gevallen <END>") == (
        "geen resolutie is gevallen"
    )
    assert "geen resolutie is gevallen" in "op geen resolutie is gevallen"


def test_fixture_fold_produces_families() -> None:
    result = fixture_fold()
    m = result["metrics"]
    assert m["n_families"] >= 1
    assert m["n_input_phrases"] >= m["n_after_nest"]
    fam = result["families"][0]
    assert fam["family_id"].startswith("fam_")
    assert fam["human_role"] is None
    assert fam["variant_of"] is None
    assert fam["n_members"] >= 1


def test_positional_straddle_splits_advertentie_waar_op() -> None:
    from formulation.formula_family_fold import repair_harvest_segments

    parts = repair_harvest_segments("advertentie waar op geen resolutie")
    assert parts == ["advertentie", "waar op geen resolutie"]
    # Already at decision start — no split
    assert repair_harvest_segments("waar op geen resolutie is") == [
        "waar op geen resolutie is"
    ]


def test_fold_splits_straddle_and_glues_long_formula() -> None:
    rows = [
        {
            "phrase": "advertentie WAAR op geen resolutie",
            "phrase_freq": 50000,
            "zone": "close",
            "lcats": "small",
            "suggested_role": "null_decision",
            "source": "high_freq",
        },
        {
            "phrase": "WAAR op geen resolutie is",
            "phrase_freq": 60000,
            "zone": "close",
            "lcats": "small",
            "suggested_role": "null_decision",
            "source": "high_freq",
        },
        {
            "phrase": "nomineeren te visiteeren examineeren en",
            "phrase_freq": 800,
            "zone": "body",
            "lcats": "medium",
            "suggested_role": "carrier",
            "source": "high_freq",
        },
        {
            "phrase": "der selver advis daar op",
            "phrase_freq": 700,
            "zone": "body",
            "lcats": "medium",
            "suggested_role": "carrier",
            "source": "high_freq",
        },
    ]
    result = fold_phrases(rows)
    norms = {normalize_phrase(str(f.get("exemplar_norm") or f.get("exemplar") or "")): f for f in result["families"]}
    # waar op + geen resolutie → null_decision family; not glued to advertentie
    waar = [f for f in result["families"] if "waar op" in normalize_phrase(str(f.get("exemplar_norm") or ""))]
    assert waar
    assert all(f.get("suggested_role") == "null_decision" for f in waar)
    assert all("advertentie" not in normalize_phrase(str(f.get("exemplar_norm") or "")) for f in waar)
    glue = [f for f in result["families"] if str(f.get("hinge_bucket") or "").startswith("glue:")]
    assert len(glue) == 1, [f.get("exemplar_norm") for f in glue]
    assert glue[0]["n_members"] >= 2
    # advertentie segment is its own family (not under waar op)
    adv = [
        f
        for f in result["families"]
        if normalize_phrase(str(f.get("exemplar_norm") or "")) == "advertentie"
        or (
            "advertentie" in normalize_phrase(str(f.get("exemplar_norm") or ""))
            and "waar op" not in normalize_phrase(str(f.get("exemplar_norm") or ""))
        )
    ]
    assert adv


def test_sliding_window_null_decision_variants_merge() -> None:
    """Adjacent 5-grams of one formula must fold (user skim: geen resolutie)."""
    rows = [
        {
            "phrase": "op geen resolutie is gevallen",
            "phrase_norm": "op geen resolutie is gevallen",
            "phrase_freq": 80000,
            "zone": "close",
            "lcats": "small",
            "suggested_role": "null_decision",
            "source": "high_freq",
        },
        {
            "phrase": "geen resolutie is gevallen <END>",
            "phrase_norm": normalize_phrase("geen resolutie is gevallen <END>"),
            "phrase_freq": 79000,
            "zone": "close",
            "lcats": "small",
            "suggested_role": "null_decision",
            "source": "high_freq",
        },
        {
            "phrase": "WAAR op geen resolutie is",
            "phrase_norm": "waar op geen resolutie is",
            "phrase_freq": 66000,
            "zone": "close",
            "lcats": "small",
            "suggested_role": "null_decision",
            "source": "high_freq",
        },
    ]
    result = fold_phrases(rows)
    assert result["metrics"]["n_families"] == 1
    assert result["families"][0]["n_members"] == 3


def test_fold_does_not_merge_different_zone_high_freq() -> None:
    rows = [
        {
            "phrase": "alpha hinge one two three",
            "phrase_norm": "alpha hinge one two three",
            "phrase_freq": 5000,
            "zone": "opening",
            "lcats": "medium",
            "suggested_role": "scaffolding_opener",
            "source": "high_freq",
        },
        {
            "phrase": "alpha hinge one two four",
            "phrase_norm": "alpha hinge one two four",
            "phrase_freq": 4800,
            "zone": "close",
            "lcats": "medium",
            "suggested_role": "scaffolding_decision",
            "source": "high_freq",
        },
    ]
    result = fold_phrases(rows, variant_ratio=50.0)
    # Same hinge bucket but incompatible zone + independent freq → 2 families
    assert result["metrics"]["n_families"] == 2


def test_handen_not_attendance_hinge() -> None:
    from formulation.formula_family_fold import _hinge_bucket

    assert _hinge_bucket("handen van de heeren van") == "decision_ish:handen"
    assert _hinge_bucket("in handen van de heeren") == "decision_ish:handen"
    assert "attendance" not in _hinge_bucket("handen van de heeren van")
    # Pure delegate name still attendance
    assert _hinge_bucket("de heeren van lynden van").startswith("attendance:")


def test_overlap_cue_pass_unites_gedelibereert_chain() -> None:
    """STEPT1ae: overlap edges collapse decision windows that hinge buckets split."""
    import json
    from pathlib import Path

    edges = [
        json.loads(line)
        for line in (
            Path(__file__).parent / "fixtures" / "overlap_cue_prove_edges.jsonl"
        )
        .read_text(encoding="utf-8")
        .splitlines()
        if line.strip()
    ]
    rows = [
        {
            "phrase": "WAAR op gedelibereert zynde is",
            "phrase_freq": 9000,
            "zone": "close",
            "lcats": "small",
            "source": "high_freq",
        },
        {
            "phrase": "op gedelibereert zynde is goedgevonden",
            "phrase_freq": 8500,
            "zone": "close",
            "lcats": "small",
            "source": "high_freq",
        },
        {
            "phrase": "gedelibereert zynde is goedgevonden en",
            "phrase_freq": 8000,
            "zone": "close",
            "lcats": "small",
            "source": "high_freq",
        },
        {
            "phrase": "zynde is goedgevonden en verstaan",
            "phrase_freq": 7800,
            "zone": "close",
            "lcats": "small",
            "source": "high_freq",
        },
    ]
    without = fold_phrases(rows)
    with_ov = fold_phrases(rows, overlap_edges=edges)
    assert with_ov["metrics"]["overlap_enabled"] is True
    assert with_ov["metrics"]["step"] == "STEPT1af"
    assert with_ov["metrics"]["type_after_overlap"] is True
    assert with_ov["metrics"]["n_families"] < without["metrics"]["n_families"]
    assert with_ov["metrics"]["n_families"] == 1
    fam = with_ov["families"][0]
    assert fam["human_role"] is None
    assert fam.get("overlap_cue") == "waar_op"
    assert fam["suggested_role"] == "scaffolding_decision"
    assert fam["n_members"] >= 4


def test_bare_waar_midphrase_splits() -> None:
    from formulation.formula_family_fold import repair_harvest_segments

    parts = repair_harvest_segments("griffier fagel houdende advertentie waar")
    assert parts[0] == "griffier fagel houdende advertentie"
    assert parts[1].startswith("waar")


def test_null_wins_over_waar_op_cue() -> None:
    edges = [
        {
            "phrase1": "WAAR op geen resolutie is",
            "phrase2": "op geen resolutie is gevallen",
            "overlap_freq": 50000,
            "phrase1_frac": 0.85,
            "phrase2_frac": 0.88,
        }
    ]
    rows = [
        {
            "phrase": "WAAR op geen resolutie is",
            "phrase_freq": 66000,
            "zone": "close",
            "source": "high_freq",
            "suggested_role": "scaffolding_opener",  # poison — must be ignored
        },
        {
            "phrase": "op geen resolutie is gevallen",
            "phrase_freq": 80000,
            "zone": "close",
            "source": "high_freq",
            "suggested_role": "scaffolding_opener",
        },
    ]
    out = fold_phrases(rows, overlap_edges=edges)
    assert out["metrics"]["n_families"] == 1
    fam = out["families"][0]
    assert fam["suggested_role"] == "null_decision"
    assert fam.get("overlap_cue") == "geen_resolutie"


def test_name_strip_not_exemplar_hinge() -> None:
    from formulation.overlap_cue_prove import strip_incidental_names

    skel, stripped = strip_incidental_names("griffier fagel houdende advertentie")
    assert "NAME" in skel
    assert stripped
    rows = [
        {
            "phrase": "Griffier Fagel houdende advertentie",
            "phrase_freq": 10000,
            "zone": "body",
            "mean_rel_mid": 0.45,
            "source": "high_freq",
            "opener_abs": True,
            "suggested_role": "scaffolding_opener",
        }
    ]
    out = fold_phrases(rows)
    fam = out["families"][0]
    assert "fagel" not in normalize_phrase(str(fam.get("exemplar_norm") or ""))
    assert fam["suggested_role"] != "scaffolding_opener"


def test_body_not_opener_from_profile_flags() -> None:
    """Place/type after fold — body zone must not become opener via opener_abs."""
    rows = [
        {
            "phrase": "Gedeputeerden van de Provincie van",
            "phrase_freq": 20000,
            "zone": "body",
            "mean_rel_mid": 0.48,
            "opener_abs": True,
            "opener_rel": True,
            "suggested_role": "scaffolding_opener",
            "source": "high_freq",
        }
    ]
    out = fold_phrases(rows)
    assert out["families"][0]["suggested_role"] == "carrier"
