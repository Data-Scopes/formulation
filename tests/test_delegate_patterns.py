"""Unique-delegate OCR pattern matching against resolution text."""

from __future__ import annotations

import pandas as pd

from formulation.delegate_patterns import (
    PatternEntry,
    add_delegate_matches,
    build_pattern_index,
    match_delegates_in_text,
)


def _toy_index() -> list[PatternEntry]:
    delegates = pd.DataFrame(
        [
            {
                "delegate_id": "15065",
                "fullname": "Reede tot Renswoude, Frederik van",
                "patterns": "van Renswoude;vande Lier;Renswoude",
                "pattern": "van Renswoude",
                "minjaar": 1680,
                "maxjaar": 1730,
            },
            {
                "delegate_id": "999",
                "fullname": "Holland Fake",
                "patterns": "van Holland;Gelderlandt",
                "pattern": "",
                "minjaar": 1700,
                "maxjaar": 1790,
            },
        ]
    )
    return build_pattern_index(delegates, min_len=10)


def test_blacklist_drops_province_patterns() -> None:
    index = _toy_index()
    ids = {e.delegate_id for e in index}
    assert "15065" in ids
    assert "999" not in ids  # only geo patterns


def test_match_prefers_renswoude_in_cue_window() -> None:
    index = _toy_index()
    text = (
        "Is ter Vergaderinge gelesen seeckere Commissie op den heer "
        "Frederick van Rheede van Renswoude heer vande Lier om wegen "
        "de provincie van Holland"
    )
    matches = match_delegates_in_text(text, 1695, index, top_k=2)
    assert matches
    assert matches[0].delegate_id == "15065"
    assert matches[0].in_cue_window is True


def test_year_gate_excludes_out_of_range() -> None:
    index = _toy_index()
    text = "op den heer van Renswoude te committeren"
    assert match_delegates_in_text(text, 1600, index) == []
    assert match_delegates_in_text(text, 1695, index)


def test_add_delegate_matches_skips_suspects() -> None:
    index = _toy_index()
    frame = pd.DataFrame(
        [
            {
                "id": "a",
                "year": 1695,
                "date": "1695-06-06",
                "suspect": False,
                "resolutions_text": "op den heer van Renswoude te committeren tot gedeputeerde",
            },
            {
                "id": "b",
                "year": 1695,
                "date": "1695-06-06",
                "suspect": True,
                "resolutions_text": "op den heer van Renswoude te committeren tot gedeputeerde",
            },
        ]
    )
    out = add_delegate_matches(frame, index)
    assert out.loc[0, "matched_delegate_id"] == "15065"
    assert out.loc[1, "matched_delegate_id"] == ""


def test_attendance_date_gate_filters_inactive() -> None:
    from formulation.attendance_activity import AttendanceSpan

    index = _toy_index()
    text = "op den heer van Renswoude te committeren tot gedeputeerde"
    # Without attendance: match ok at 1695
    assert match_delegates_in_text(text, 1695, index, resolution_date="1695-06-06")
    # With attendance career only in 1720s: blocked
    spans = {
        "15065": AttendanceSpan(
            first=pd.Timestamp("1720-01-01"),
            last=pd.Timestamp("1725-01-01"),
            n=10,
        )
    }
    assert (
        match_delegates_in_text(
            text,
            1695,
            index,
            resolution_date="1695-06-06",
            attendance=spans,
            require_attendance_active=True,
        )
        == []
    )
    # Active on that day: allowed
    spans = {
        "15065": AttendanceSpan(
            first=pd.Timestamp("1690-01-01"),
            last=pd.Timestamp("1700-01-01"),
            n=10,
        )
    }
    hits = match_delegates_in_text(
        text,
        1695,
        index,
        resolution_date="1695-06-06",
        attendance=spans,
    )
    assert hits and hits[0].delegate_id == "15065"
