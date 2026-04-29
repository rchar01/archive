from __future__ import annotations

from datetime import datetime, timezone


def generate_entry_id(now: datetime | None = None) -> str:
    timestamp = now or datetime.now(timezone.utc)
    return timestamp.strftime("%Y%m%dT%H%M%S%f")
