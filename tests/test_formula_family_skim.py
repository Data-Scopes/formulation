"""STEPT1ac family skim workbook tests."""

from __future__ import annotations

from formulation.formula_family_fold import fixture_fold
from formulation.formula_family_skim import family_skim_rows, write_family_skim_xlsx


def test_skim_rows_blank_keep() -> None:
    fams = fixture_fold()["families"]
    rows = family_skim_rows(fams)
    assert rows
    assert rows[0]["keep"] == ""
    assert "family_id" in rows[0]
    assert "exemplar" in rows[0]


def test_write_skim_xlsx(tmp_path) -> None:
    fams = fixture_fold()["families"]
    path = write_family_skim_xlsx(tmp_path / "skim.xlsx", fams, metrics={"n": len(fams)})
    assert path.exists()
    assert path.stat().st_size > 0
