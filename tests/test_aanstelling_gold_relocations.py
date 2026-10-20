"""The 18 non-naive gold URNs stay positives; they live under a nearby session num."""

from __future__ import annotations

import json
from pathlib import Path

FIXTURE = Path(__file__).parent / "fixtures" / "aanstelling_gold_relocations.jsonl"


def _rows() -> list[dict]:
    return [json.loads(line) for line in FIXTURE.read_text(encoding="utf-8").splitlines() if line.strip()]


def test_eighteen_unique_recovered_gold_ids() -> None:
    rows = _rows()
    assert len(rows) == 18
    recovered = [row["recovered_id"] for row in rows]
    assert len(set(recovered)) == 18
    assert all(row["recovered_id"].startswith("session-") for row in rows)


def test_seventeen_relocated_on_urn_date_same_resolution() -> None:
    relocated = [row for row in _rows() if row["recovery"] == "same_inv_date_resolution"]
    assert len(relocated) == 17
    for row in relocated:
        assert row["recovered_id"] != row["naive_id"]
        assert row["recovered_date"] == row["urn_date"]
        naive_res = row["naive_id"].rsplit("-resolution-", 1)[1]
        recovered_res = row["recovered_id"].rsplit("-resolution-", 1)[1]
        assert recovered_res == naive_res


def test_one_keep_naive_when_urn_date_absent() -> None:
    kept = [row for row in _rows() if row["recovery"] == "urn_date_absent_keep_naive_id"]
    assert len(kept) == 1
    row = kept[0]
    assert row["urn_date"] == "1685-09-23"
    assert row["recovered_id"] == row["naive_id"] == "session-3312-num-82-resolution-2"
    assert row["recovered_date"] == "1685-09-25"
