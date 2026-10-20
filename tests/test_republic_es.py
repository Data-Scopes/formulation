"""Lean ES helpers: session_id parse + enrich join (mocked HTTP)."""

from __future__ import annotations

import pandas as pd

from formulation.republic_es import (
    ElasticsearchConfig,
    RepublicEsClient,
    enrich_resolution_rows,
    session_id_from_resolution_id,
)


def test_session_id_from_resolution_id() -> None:
    assert (
        session_id_from_resolution_id("session-3778-num-292-resolution-5")
        == "session-3778-num-292"
    )
    assert session_id_from_resolution_id("not-a-resolution") is None


def test_enrich_joins_mocked_mget(monkeypatch) -> None:
    config = ElasticsearchConfig(
        host="example.test",
        resolutions_index="full_resolutions-test",
        session_metadata_index="session_metadata-test",
        session_text_regions_index="session_text_regions-test",
    )
    client = RepublicEsClient(config)

    def fake_mget(index, ids, source_includes, *, batch_size=100):
        if index == config.resolutions_index:
            return {
                "session-1-num-2-resolution-3": {
                    "id": "session-1-num-2-resolution-3",
                    "metadata": {
                        "session_id": "session-1-num-2",
                        "session_date": "1780-01-02",
                        "inventory_num": 1,
                        "page_ids": ["p1"],
                        "scan_ids": ["s1"],
                        "president": None,
                    },
                }
            }
        if index == config.session_metadata_index:
            return {
                "session-1-num-2": {
                    "id": "session-1-num-2",
                    "metadata": {
                        "session_id": "session-1-num-2",
                        "session_date": "1780-01-02",
                        "session_weekday": "vrijdag",
                        "president": "X",
                        "attendants_list_id": "session-1-num-2-attendance_list",
                        "resolution_ids": ["session-1-num-2-resolution-3"],
                    },
                }
            }
        return {}

    def fake_regions(session_ids, *, batch_size=50, size_per_batch=500):
        return {
            "session-1-num-2": [
                {
                    "id": "tr-1",
                    "metadata": {
                        "session_id": "session-1-num-2",
                        "page_id": "page-a",
                        "scan_id": "scan-a",
                        "iiif_url": "https://example/iiif/a",
                    },
                }
            ]
        }

    monkeypatch.setattr(client, "mget", fake_mget)
    monkeypatch.setattr(client, "search_text_regions_by_session", fake_regions)

    frame = pd.DataFrame(
        [
            {
                "id": "session-1-num-2-resolution-3",
                "resolutions_text": "is goedgevonden",
                "proba_aanstelling": 0.9,
            },
            {
                "id": "session-9-num-9-resolution-9",
                "resolutions_text": "missing in es",
                "proba_aanstelling": 0.2,
            },
        ]
    )
    enriched = enrich_resolution_rows(frame, client)
    assert enriched.loc[0, "session_id"] == "session-1-num-2"
    assert bool(enriched.loc[0, "es_resolution_found"]) is True
    assert bool(enriched.loc[0, "es_session_found"]) is True
    assert enriched.loc[0, "es_session_weekday"] == "vrijdag"
    assert enriched.loc[0, "es_president"] == "X"
    assert "https://example/iiif/a" in enriched.loc[0, "es_tr_iiif_urls"]
    assert bool(enriched.loc[1, "es_resolution_found"]) is False
    assert bool(enriched.loc[1, "es_session_found"]) is False
    assert "resolutions_text" in enriched.columns
