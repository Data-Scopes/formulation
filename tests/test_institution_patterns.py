"""Smoke tests for period-keyed institution_patterns fixture seeds."""

from __future__ import annotations

import pytest

from data_io import load
from formulation.institution_patterns import (
    LOGICAL_NAME,
    SEEDS_LOGICAL_NAME,
    TARGET_ORG_ENTITIES,
    dedupe_pattern_rows,
    extract_institutions,
    load_patterns,
    org_entity_ids_for_target,
    pattern_to_regex,
    patterns_for_target,
    primary_institution,
    validate_pattern,
)


def _seed_rows():
    return load_patterns(rows=load(SEEDS_LOGICAL_NAME))


def test_manifest_load_and_targets():
    rows = _seed_rows()
    assert len(rows) >= 5
    assert LOGICAL_NAME == "institution_patterns"
    targets = {r["institution_target"] for r in rows}
    assert "rekenkamer" in targets
    assert "admirality" in targets
    assert "staten_generael_vergadering" in targets


def test_year_filter_separates_admiralty_surfaces():
    seeds = _seed_rows()
    early = patterns_for_target("admirality", year=1626, rows=seeds)
    late = patterns_for_target("admirality", year=1780, rows=seeds)
    assert any("Admirt" in r["pattern"] or "Gecommitteerde" in r["pattern"] for r in early)
    assert any("Collegie ter Admiraliteit" in r["pattern"] for r in late)
    dated_early = [r for r in early if r.get("year_min") is not None]
    dated_late = [r for r in late if r.get("year_min") is not None]
    assert dated_early and all(
        r["year_min"] <= 1626 <= r["year_max"] for r in dated_early
    )
    assert dated_late and all(
        r["year_min"] <= 1780 <= r["year_max"] for r in dated_late
    )


def test_inv_filter():
    seeds = _seed_rows()
    rows = patterns_for_target("rekenkamer", inv=3835, rows=seeds)
    dated = [r for r in rows if r.get("inv") == 3835]
    assert len(dated) == 1
    assert dated[0]["year_min"] == 1780


def test_target_org_entity_map():
    assert "O0000072" in org_entity_ids_for_target("rekenkamer")
    assert org_entity_ids_for_target("gecommitteerde_raaden") == ()
    assert "rekenkamer" in TARGET_ORG_ENTITIES


def test_validate_rejects_empty_pattern():
    bad = dict(_seed_rows()[0])
    bad["pattern"] = ""
    with pytest.raises(ValueError, match="pattern"):
        validate_pattern(bad)


def test_extract_and_primary_from_fixture_surfaces():
    seeds = _seed_rows()
    text = (
        "commissie inde Generaliteits Rekenkamer ende voorts "
        "naer de Vergaderinge van haer Hoog Mogende"
    )
    hits = extract_institutions(text, rows=seeds)
    labels = {lab for lab, _ in hits}
    assert "rekenkamer" in labels
    assert primary_institution(hits) == "rekenkamer"
    assert pattern_to_regex("Raad van State").search("den Raad  van State")


def test_dedupe_pattern_rows_keeps_max_n():
    base = {
        "institution_target": "rekenkamer",
        "org_entity_id": "O0000072",
        "pattern": "Rekenkamer",
        "inv": 3835,
        "year_min": 1780,
        "year_max": 1780,
        "source": "org_annotations",
    }
    rows = [
        {**base, "n": 2, "inv": 3835},
        {**base, "n": 9, "inv": 3185, "year_min": 1626, "year_max": 1626},
        {**base, "pattern": "REKENKAMER", "n": 3, "inv": 4000},
        {
            **base,
            "institution_target": "admirality",
            "pattern": "Admiraliteit",
            "n": 1,
            "inv": None,
            "year_min": None,
            "year_max": None,
        },
    ]
    out = dedupe_pattern_rows(rows)
    assert len(out) == 2
    rek = next(r for r in out if r["institution_target"] == "rekenkamer")
    assert rek["n"] == 9
    assert rek["inv"] == 3185
