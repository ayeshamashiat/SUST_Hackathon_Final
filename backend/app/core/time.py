"""Internally we keep every datetime naive-but-UTC (simplest for SQLite
round-trips, which silently strip tzinfo anyway). This one helper is the
single place that marks a value as UTC when it leaves the process - used by
both the API response schemas and anywhere we hand-build a JSON-ish dict
(e.g. an alert's evidence payload). Without this, a naive ISO string like
"2026-07-11T06:07:16" gets parsed by the browser as *local* time, silently
shifting every displayed timestamp by the viewer's UTC offset.
"""

from datetime import datetime, timezone


def to_utc_iso(dt: datetime) -> str:
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.isoformat()
