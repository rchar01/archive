from __future__ import annotations

import re


def slugify(value: str, fallback: str = "note") -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.strip().lower()).strip("-")
    return slug or fallback
