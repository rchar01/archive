from __future__ import annotations

import json
from collections import defaultdict
from typing import Any, Iterable

from scripts.core.index_builder import IndexEntry, section_title


def build_sidebar_data(entries: Iterable[IndexEntry]) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, dict[str, list[IndexEntry]]] = defaultdict(lambda: defaultdict(list))
    labels: dict[str, str] = {}

    for entry in sorted(entries, key=lambda item: (item.workflow_root, item.section, item.title.lower(), item.link)):
        grouped[entry.workflow_root][entry.section].append(entry)
        labels[entry.workflow_root] = entry.workflow_label

    sidebar: dict[str, list[dict[str, Any]]] = {}
    for workflow_root, sections in grouped.items():
        items: list[dict[str, Any]] = []
        for section, section_entries in sections.items():
            items.append(
                {
                    "text": section_title(section),
                    "items": [{"text": entry.display_title, "link": entry.link} for entry in section_entries],
                }
            )
        sidebar[f"/{workflow_root}/"] = [{"text": labels[workflow_root], "items": items}]
    return sidebar


def build_nav_data(entries: Iterable[IndexEntry]) -> list[dict[str, str]]:
    labels: dict[str, str] = {}
    for entry in entries:
        labels[entry.workflow_root] = entry.workflow_label

    nav = [{"text": "Home", "link": "/"}]
    for workflow_root in sorted(labels):
        nav.append({"text": labels[workflow_root], "link": f"/{workflow_root}/"})
    return nav


def render_sidebar_ts(sidebar: dict[str, list[dict[str, Any]]]) -> str:
    content = json.dumps(sidebar, indent=2, ensure_ascii=True)
    return f"export default {content}\n"


def render_nav_ts(nav: list[dict[str, str]]) -> str:
    content = json.dumps(nav, indent=2, ensure_ascii=True)
    return f"export default {content}\n"
