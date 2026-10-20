#!/usr/bin/env python3
"""Generic ES provenance export: flat/resolution ids -> inventory_num, page_ids, scan_ids.

Reusable fallback for any case needing real archival provenance (inventory identity,
page/scan location) that a project's own derived datasets don't carry -- e.g. checking
whether two resolution ids sitting under the same calendar-date label are genuinely
adjacent pages of one register or an unrelated register that happens to share the date.
Not scoped to any one caller's id list: pass whatever ids need provenance.

Pulls only the already-lean `RESOLUTION_SOURCE` fields from `full_resolutions` (no
coordinates, no full text) -- see `formulation.republic_es` module docstring.

Usage:
    uv run python scripts/export_resolution_es_provenance.py --ids-file path/to/ids.txt --output output/name.jsonl
    cat ids.txt | uv run python scripts/export_resolution_es_provenance.py --output output/name.jsonl
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from formulation.republic_es import RESOLUTION_SOURCE, RepublicEsClient


def read_ids(ids_file: str | None) -> list[str]:
    if ids_file:
        lines = Path(ids_file).read_text().splitlines()
    else:
        lines = sys.stdin.read().splitlines()
    return [line.strip() for line in lines if line.strip()]


def provenance_row(flat_id: str, source: dict) -> dict:
    meta = source.get("metadata") or {}
    return {
        "flat_id": flat_id,
        "found": True,
        "inventory_num": meta.get("inventory_num"),
        "session_id": meta.get("session_id"),
        "session_date": meta.get("session_date"),
        "page_ids": meta.get("page_ids") or [],
        "scan_ids": meta.get("scan_ids") or [],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ids-file", default=None, help="One flat/resolution id per line; omit to read stdin.")
    parser.add_argument("--output", required=True, help="Output JSONL path.")
    parser.add_argument("--batch-size", type=int, default=100)
    args = parser.parse_args()

    ids = read_ids(args.ids_file)
    client = RepublicEsClient()
    found = client.mget(
        client.config.resolutions_index, ids, RESOLUTION_SOURCE, batch_size=args.batch_size
    )

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    n_found = 0
    with out_path.open("w") as f:
        meta = {
            "record_type": "meta",
            "n_requested": len(ids),
            "n_found": len(found),
            "index": client.config.resolutions_index,
            "source_fields": RESOLUTION_SOURCE,
        }
        f.write(json.dumps(meta) + "\n")
        for flat_id in ids:
            source = found.get(flat_id)
            if source is None:
                f.write(json.dumps({"flat_id": flat_id, "found": False}) + "\n")
                continue
            f.write(json.dumps(provenance_row(flat_id, source)) + "\n")
            n_found += 1

    print(f"requested={len(ids)} found={n_found} missing={len(ids) - n_found}")
    print(f"wrote {out_path}")


if __name__ == "__main__":
    main()
