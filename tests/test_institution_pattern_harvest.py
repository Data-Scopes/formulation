"""Unit tests for ORG annotation → institution_patterns stream harvest."""

from __future__ import annotations

import json
from pathlib import Path

from formulation.institution_pattern_harvest import (
    aggregate_mentions,
    entity_to_targets,
    harvest_institution_patterns,
    iter_json_array,
    merge_with_seeds,
    normalize_entity_id,
    stream_target_mentions,
)
from formulation.institution_patterns import (
    SEEDS_LOGICAL_NAME,
    load_patterns,
    validate_patterns,
)


def test_normalize_entity_id_strips_urn():
    assert normalize_entity_id("urn:republic:entity:O0000072") == "O0000072"
    assert normalize_entity_id("O0000072") == "O0000072"


def test_iter_json_array_streams(tmp_path: Path):
    path = tmp_path / "arr.json"
    path.write_text(
        json.dumps(
            [
                {"entity": "O0000072", "reference": {"tag_text": "Rekenkamer", "inv": "3835"}},
                {"entity": "O0000167", "reference": {"tag_text": "Raad van State", "inv": 3835}},
            ]
        ),
        encoding="utf-8",
    )
    objs = list(iter_json_array(path))
    assert len(objs) == 2
    assert objs[0]["entity"] == "O0000072"


def test_stream_and_aggregate_maps_targets(tmp_path: Path):
    path = tmp_path / "org.json"
    path.write_text(
        json.dumps(
            [
                {
                    "entity": "urn:republic:entity:O0000072",
                    "reference": {"tag_text": "Generaliteits  Rekenkamer", "inv": "3835"},
                },
                {
                    "entity": "O0000072",
                    "reference": {"tag_text": "Generaliteits Rekenkamer", "inv": 3835},
                },
                {
                    "entity": "O0000005",
                    "reference": {
                        "tag_text": "Gecommitteerde Raden ter Admirt. tot Rotterdam",
                        "inv": "3185",
                    },
                },
                {
                    "entity": "O9999999",
                    "reference": {"tag_text": "ignored other org", "inv": "3835"},
                },
            ]
        ),
        encoding="utf-8",
    )
    mentions = list(stream_target_mentions(path))
    assert len(mentions) == 3
    rows = aggregate_mentions(
        mentions,
        entity_names={
            "O0000072": "Generaliteitsrekenkamer",
            "O0000005": "Admiraliteit van Rotterdam",
        },
        inventory_years={3835: (1780, 1780), 3185: (1626, 1626)},
        min_n=1,
    )
    validate_patterns(rows)
    rek = [r for r in rows if r["institution_target"] == "rekenkamer"]
    assert len(rek) == 1
    assert rek[0]["n"] == 2
    assert rek[0]["pattern"] == "Generaliteits Rekenkamer"
    assert rek[0]["year_min"] == 1780
    assert rek[0]["source"] == "org_annotations"
    adm = [r for r in rows if r["institution_target"] == "admirality"]
    assert len(adm) == 1
    assert adm[0]["inv"] == 3185
    assert adm[0]["year_max"] == 1626


def test_merge_with_seeds_keeps_unique_surfaces():
    harvest = [
        {
            "institution_target": "rekenkamer",
            "org_entity_id": "O0000072",
            "org_entity_name": "Generaliteitsrekenkamer",
            "pattern": "Rekenkamer",
            "inv": None,
            "year_min": None,
            "year_max": None,
            "n": 10,
            "source": "org_annotations",
        }
    ]
    seeds = [
        dict(harvest[0], source="fixture", n=1),
        {
            "institution_target": "gecommitteerde_raaden",
            "org_entity_id": None,
            "org_entity_name": None,
            "pattern": "Gecommitteerde Raaden",
            "inv": None,
            "year_min": None,
            "year_max": None,
            "n": 1,
            "source": "fixture",
        },
    ]
    merged = merge_with_seeds(harvest, seeds)
    assert len(merged) == 2
    assert {r["source"] for r in merged} == {"org_annotations", "fixture"}


def test_entity_to_targets_covers_map():
    rev = entity_to_targets()
    assert rev["O0000072"] == "rekenkamer"
    assert rev["O0000003"] == "admirality"


def test_load_patterns_falls_back_to_seeds():
    """Scratch harvest may be absent; seeds must still load."""
    rows = load_patterns()
    assert len(rows) >= 5
    # Explicit seeds logical name always works
    from data_io import load

    seeds = load(SEEDS_LOGICAL_NAME)
    assert isinstance(seeds, list) and len(seeds) >= 5


def test_harvest_with_injected_paths(tmp_path: Path):
    ann = tmp_path / "ann.json"
    ann.write_text(
        json.dumps(
            [
                {
                    "entity": "O0000167",
                    "reference": {"tag_text": "Raad van State", "inv": 3835},
                }
            ]
        ),
        encoding="utf-8",
    )
    rows, metrics = harvest_institution_patterns(
        annotations_path=ann,
        entity_names={"O0000167": "Raad van State"},
        inventory_years={3835: (1780, 1780)},
        with_seeds=False,
        min_n=1,
    )
    assert metrics["n_harvest_rows"] == 1
    assert rows[0]["institution_target"] == "raad_van_state"
    assert rows[0]["year_min"] == 1780
