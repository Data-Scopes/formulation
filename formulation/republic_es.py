"""Lean REPUBLIC Elasticsearch lookups (Track R enrichment).

Uses stdlib HTTP only. Always requests a narrow ``_source`` include list —
never pull full resolution / text-region documents.
"""

from __future__ import annotations

import json
import re
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any

import pandas as pd

from data_io.manifest import load_manifest_dict

RESOLUTION_ID_RE = re.compile(
    r"^(?P<session>session-\d+-num-\d+)-resolution-\d+$"
)

RESOLUTION_SOURCE = [
    "id",
    "metadata.session_id",
    "metadata.session_date",
    "metadata.session_weekday",
    "metadata.inventory_num",
    "metadata.page_ids",
    "metadata.scan_ids",
    "metadata.president",
    "metadata.resolution_type",
    "metadata.proposition_type",
    "metadata.session_year",
    "evidence",
    "stats",
]

SESSION_SOURCE = [
    "id",
    "metadata.session_id",
    "metadata.session_date",
    "metadata.session_weekday",
    "metadata.president",
    "metadata.inventory_num",
    "metadata.resolution_ids",
    "metadata.attendants_list_id",
    "metadata.page_ids",
    "metadata.scan_ids",
]

TEXT_REGION_SOURCE = [
    "id",
    "metadata.session_id",
    "metadata.scan_id",
    "metadata.page_id",
    "metadata.iiif_url",
]

DEFAULT_BATCH = 100
DEFAULT_TIMEOUT = 60


@dataclass(frozen=True)
class ElasticsearchConfig:
    host: str
    scheme: str = "https"
    port: int = 443
    url_prefix: str = "elasticsearch"
    resolutions_index: str = "full_resolutions-2026-03-25"
    session_metadata_index: str = "session_metadata-2026-03-25"
    session_text_regions_index: str = "session_text_regions-2026-03-25"
    timeout: int = DEFAULT_TIMEOUT

    @property
    def base_url(self) -> str:
        prefix = self.url_prefix.strip("/")
        root = f"{self.scheme}://{self.host}"
        if self.port not in (80, 443):
            root = f"{root}:{self.port}"
        return f"{root}/{prefix}" if prefix else root


def load_elasticsearch_config() -> ElasticsearchConfig:
    """Read ``[elasticsearch]`` from the merged manifest (+ local.toml)."""
    raw = load_manifest_dict().get("elasticsearch") or {}
    if not isinstance(raw, dict):
        raise ValueError("[elasticsearch] in the manifest must be a table")
    host = str(raw.get("host") or "").strip()
    if not host:
        raise ValueError(
            "Missing [elasticsearch].host — set it in data_manifest.toml "
            "or data_manifest.local.toml"
        )
    return ElasticsearchConfig(
        host=host,
        scheme=str(raw.get("scheme") or "https"),
        port=int(raw.get("port") or 443),
        url_prefix=str(raw.get("url_prefix") or "elasticsearch"),
        resolutions_index=str(
            raw.get("resolutions_index") or "full_resolutions-2026-03-25"
        ),
        session_metadata_index=str(
            raw.get("session_metadata_index") or "session_metadata-2026-03-25"
        ),
        session_text_regions_index=str(
            raw.get("session_text_regions_index")
            or "session_text_regions-2026-03-25"
        ),
        timeout=int(raw.get("timeout") or DEFAULT_TIMEOUT),
    )


def session_id_from_resolution_id(resolution_id: object) -> str | None:
    if resolution_id is None or (isinstance(resolution_id, float) and pd.isna(resolution_id)):
        return None
    match = RESOLUTION_ID_RE.match(str(resolution_id).strip())
    return match.group("session") if match else None


class RepublicEsClient:
    """Minimal client: mget + terms search with forced ``_source`` includes."""

    def __init__(self, config: ElasticsearchConfig | None = None) -> None:
        self.config = config or load_elasticsearch_config()

    def mget(
        self,
        index: str,
        ids: list[str],
        source_includes: list[str],
        *,
        batch_size: int = DEFAULT_BATCH,
    ) -> dict[str, dict[str, Any]]:
        """Return ``{id: _source}`` for found docs only."""
        out: dict[str, dict[str, Any]] = {}
        unique = list(dict.fromkeys(i for i in ids if i))
        step = max(int(batch_size), 1)
        for start in range(0, len(unique), step):
            chunk = unique[start : start + step]
            body = {
                "docs": [
                    {"_id": doc_id, "_source": source_includes} for doc_id in chunk
                ]
            }
            response = self._request_json("POST", f"{index}/_mget", body=body)
            for doc in response.get("docs") or []:
                if not doc.get("found"):
                    continue
                doc_id = str(doc.get("_id") or "")
                source = doc.get("_source")
                if doc_id and isinstance(source, dict):
                    out[doc_id] = source
        return out

    def search_text_regions_by_session(
        self,
        session_ids: list[str],
        *,
        batch_size: int = 50,
        size_per_batch: int = 500,
    ) -> dict[str, list[dict[str, Any]]]:
        """Map session_id → lean text-region sources (no line/word trees)."""
        out: dict[str, list[dict[str, Any]]] = {}
        unique = list(dict.fromkeys(i for i in session_ids if i))
        step = max(int(batch_size), 1)
        index = self.config.session_text_regions_index
        for start in range(0, len(unique), step):
            chunk = unique[start : start + step]
            body = {
                "size": int(size_per_batch),
                "query": {"terms": {"metadata.session_id.keyword": chunk}},
                "_source": TEXT_REGION_SOURCE,
            }
            response = self._request_json("POST", f"{index}/_search", body=body)
            for hit in response.get("hits", {}).get("hits") or []:
                source = hit.get("_source")
                if not isinstance(source, dict):
                    continue
                meta = source.get("metadata") or {}
                sid = meta.get("session_id")
                if not sid:
                    continue
                out.setdefault(str(sid), []).append(source)
        return out

    def search(self, index: str, body: dict[str, Any]) -> dict[str, Any]:
        """Raw ``_search`` passthrough — caller controls query/aggs/_source."""
        return self._request_json("POST", f"{index}/_search", body=body)

    def _request_json(
        self,
        method: str,
        path: str,
        *,
        body: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        url = f"{self.config.base_url}/{path.lstrip('/')}"
        data = None if body is None else json.dumps(body).encode("utf-8")
        headers = {"Accept": "application/json"}
        if data is not None:
            headers["Content-Type"] = "application/json"
        request = urllib.request.Request(
            url, data=data, headers=headers, method=method
        )
        try:
            with urllib.request.urlopen(
                request, timeout=self.config.timeout
            ) as response:
                return json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")[:500]
            raise RuntimeError(
                f"Elasticsearch {method} {url} failed: {exc.code} {detail}"
            ) from exc


def _join_list(values: Any, *, limit: int = 20) -> str:
    if values is None:
        return ""
    if isinstance(values, str):
        return values
    if not isinstance(values, (list, tuple)):
        return str(values)
    parts = [str(v) for v in values if v is not None and str(v).strip()]
    if len(parts) > limit:
        parts = parts[:limit] + [f"…(+{len(values) - limit})"]
    return "; ".join(parts)


def _meta(source: dict[str, Any] | None) -> dict[str, Any]:
    if not source:
        return {}
    meta = source.get("metadata")
    return meta if isinstance(meta, dict) else {}


def _region_summary(regions: list[dict[str, Any]]) -> dict[str, Any]:
    page_ids: list[str] = []
    scan_ids: list[str] = []
    iiif_urls: list[str] = []
    for region in regions:
        rmeta = region.get("metadata") or {}
        if rmeta.get("page_id"):
            page_ids.append(str(rmeta["page_id"]))
        if rmeta.get("scan_id"):
            scan_ids.append(str(rmeta["scan_id"]))
        if rmeta.get("iiif_url"):
            iiif_urls.append(str(rmeta["iiif_url"]))
    page_ids = list(dict.fromkeys(page_ids))
    scan_ids = list(dict.fromkeys(scan_ids))
    iiif_urls = list(dict.fromkeys(iiif_urls))
    return {
        "es_tr_page_ids": _join_list(page_ids),
        "es_tr_scan_ids": _join_list(scan_ids),
        "es_tr_iiif_urls": _join_list(iiif_urls, limit=8),
        "es_tr_n": len(regions),
    }


def enrich_resolution_rows(
    frame: pd.DataFrame,
    client: RepublicEsClient,
    *,
    batch_size: int = DEFAULT_BATCH,
    with_text_regions: bool = True,
) -> pd.DataFrame:
    """Add session / ES columns to a frame that has an ``id`` column."""
    if "id" not in frame.columns:
        raise ValueError("Frame needs an id column")
    out = frame.copy()
    ids = out["id"].astype(str)
    session_ids = ids.map(session_id_from_resolution_id)
    out["session_id"] = session_ids

    resolutions = client.mget(
        client.config.resolutions_index,
        ids.tolist(),
        RESOLUTION_SOURCE,
        batch_size=batch_size,
    )
    unique_sessions = [s for s in session_ids.dropna().unique().tolist()]
    sessions = client.mget(
        client.config.session_metadata_index,
        unique_sessions,
        SESSION_SOURCE,
        batch_size=batch_size,
    )
    regions_by_session: dict[str, list[dict[str, Any]]] = {}
    if with_text_regions and unique_sessions:
        regions_by_session = client.search_text_regions_by_session(
            unique_sessions,
            batch_size=min(batch_size, 50),
        )

    res_lookup = pd.DataFrame.from_dict(
        {
            rid: {
                "es_resolution_found": True,
                "es_inventory_num": _meta(src).get("inventory_num"),
                "es_res_session_id": _meta(src).get("session_id"),
                "es_res_session_date": _meta(src).get("session_date"),
                "es_res_president": _meta(src).get("president"),
                "es_res_page_ids": _join_list(_meta(src).get("page_ids")),
                "es_res_scan_ids": _join_list(_meta(src).get("scan_ids")),
            }
            for rid, src in resolutions.items()
        },
        orient="index",
    )
    if res_lookup.empty:
        res_lookup = pd.DataFrame(
            columns=[
                "es_resolution_found",
                "es_inventory_num",
                "es_res_session_id",
                "es_res_session_date",
                "es_res_president",
                "es_res_page_ids",
                "es_res_scan_ids",
            ]
        )

    sess_records = {}
    for sid, src in sessions.items():
        meta = _meta(src)
        summary = _region_summary(regions_by_session.get(sid, []))
        sess_records[sid] = {
            "es_session_found": True,
            "es_session_date": meta.get("session_date"),
            "es_session_weekday": meta.get("session_weekday"),
            "es_president": meta.get("president"),
            "es_attendants_list_id": meta.get("attendants_list_id"),
            "es_session_resolution_ids": _join_list(meta.get("resolution_ids")),
            **summary,
        }
    # sessions found only via text regions
    for sid, regions in regions_by_session.items():
        if sid in sess_records:
            continue
        sess_records[sid] = {
            "es_session_found": False,
            "es_session_date": None,
            "es_session_weekday": None,
            "es_president": None,
            "es_attendants_list_id": None,
            "es_session_resolution_ids": "",
            **_region_summary(regions),
        }
    sess_lookup = pd.DataFrame.from_dict(sess_records, orient="index")
    if sess_lookup.empty:
        sess_lookup = pd.DataFrame(
            columns=[
                "es_session_found",
                "es_session_date",
                "es_session_weekday",
                "es_president",
                "es_attendants_list_id",
                "es_session_resolution_ids",
                "es_tr_page_ids",
                "es_tr_scan_ids",
                "es_tr_iiif_urls",
                "es_tr_n",
            ]
        )

    out = out.join(res_lookup, on="id", how="left")
    out = out.join(sess_lookup, on="session_id", how="left")
    out["es_resolution_found"] = out["es_resolution_found"].fillna(False).astype(bool)
    out["es_session_found"] = out["es_session_found"].fillna(False).astype(bool)
    out["es_tr_n"] = out["es_tr_n"].fillna(0).astype(int)
    return out
