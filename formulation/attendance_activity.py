"""Attendance-derived activity windows for date-constrained delegate matching.

Builds first/last sitting dates per ``delegate_id`` from the 1705–1795
attendance-long table (``class=delegate`` only). Used to gate pattern matches
to people who actually sit around the resolution date.
"""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd
import pyarrow.parquet as pq

from data_io import resolve

LOGICAL_ATTENDANCE = "attendance_long_1705_1795"
# Allow a little slack around the observed career (travel / missing days).
ACTIVE_SLACK_DAYS = 30
# Boost when first attendance falls near the aanstelling (new seat).
NEW_SEAT_BEFORE_DAYS = 7
NEW_SEAT_AFTER_DAYS = 365
NEW_SEAT_BOOST = 1.5


@dataclass(frozen=True)
class AttendanceSpan:
    first: pd.Timestamp
    last: pd.Timestamp
    n: int


def load_attendance_spans(
    path: str | None = None,
    *,
    class_name: str = "delegate",
) -> dict[str, AttendanceSpan]:
    """Return ``delegate_id → first/last attendance date`` from attendance-long."""
    resolved = resolve(LOGICAL_ATTENDANCE) if path is None else path
    cols = ["delegate_id", "d", "m", "j", "class"]
    frame = pq.read_table(resolved, columns=cols).to_pandas()
    if class_name:
        frame = frame.loc[frame["class"].astype(str).eq(class_name)]
    frame = frame.dropna(subset=["delegate_id", "d", "m", "j"]).copy()
    frame["delegate_id"] = frame["delegate_id"].astype(str)
    # 1705–1795: pandas Timestamp is safe (post-1678).
    frame["date"] = pd.to_datetime(
        {
            "year": pd.to_numeric(frame["j"], errors="coerce"),
            "month": pd.to_numeric(frame["m"], errors="coerce"),
            "day": pd.to_numeric(frame["d"], errors="coerce"),
        },
        errors="coerce",
    )
    frame = frame.dropna(subset=["date"])
    grouped = frame.groupby("delegate_id", sort=False).agg(
        first=("date", "min"),
        last=("date", "max"),
        n=("date", "size"),
    )
    return {
        did: AttendanceSpan(
            first=pd.Timestamp(row["first"]),
            last=pd.Timestamp(row["last"]),
            n=int(row["n"]),
        )
        for did, row in grouped.iterrows()
    }


def parse_resolution_date(value: object) -> pd.Timestamp | None:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    if isinstance(value, pd.Timestamp):
        return value if not pd.isna(value) else None
    text = str(value).strip()[:10]
    if not text:
        return None
    ts = pd.to_datetime(text, errors="coerce")
    return ts if not pd.isna(ts) else None


def is_active_on(
    date: pd.Timestamp,
    span: AttendanceSpan,
    *,
    slack_days: int = ACTIVE_SLACK_DAYS,
) -> bool:
    slack = pd.Timedelta(days=int(slack_days))
    return (span.first - slack) <= date <= (span.last + slack)


def new_seat_boost(
    date: pd.Timestamp,
    span: AttendanceSpan,
    *,
    before_days: int = NEW_SEAT_BEFORE_DAYS,
    after_days: int = NEW_SEAT_AFTER_DAYS,
    boost: float = NEW_SEAT_BOOST,
) -> float:
    """Return score multiplier if first attendance looks like a new seat."""
    delta = (span.first - date).days
    if -int(before_days) <= delta <= int(after_days):
        return float(boost)
    return 1.0
