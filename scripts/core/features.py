from __future__ import annotations

import os


DISABLED_VALUES = {"0", "false", "no", "off"}


def env_flag_enabled(name: str, *, default: bool = True) -> bool:
    value = str(os.environ.get(name) or "").strip().lower()
    if not value:
        return default
    return value not in DISABLED_VALUES


def knowledge_graph_enabled() -> bool:
    return env_flag_enabled("ARCHIVE_KNOWLEDGE_GRAPH", default=True)
