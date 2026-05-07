from __future__ import annotations

import json
from collections import defaultdict
from collections.abc import Mapping
from typing import Any, Iterable

from scripts.core.index_builder import IndexEntry
from scripts.core.sections import (
    SectionOverride,
    load_section_overrides,
    resolve_section_collapsed,
    resolve_section_title,
    section_parts,
)


def _new_section_node() -> dict[str, Any]:
    return {"entries": [], "children": {}}


def _insert_section_entry(tree: dict[str, Any], entry: IndexEntry) -> None:
    node = tree
    for part in section_parts(entry.section):
        children = node["children"]
        if part not in children:
            children[part] = _new_section_node()
        node = children[part]
    node["entries"].append(entry)


def _sorted_links(entries: list[IndexEntry]) -> list[dict[str, str]]:
    return [{"text": entry.display_title, "link": entry.link} for entry in entries]


def _render_section_nodes(
    children: dict[str, Any],
    overrides: Mapping[str, SectionOverride],
    *,
    prefix: tuple[str, ...] = (),
    depth: int = 0,
    default_section: str = "general",
) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    def sort_key(value: str) -> tuple[str, str]:
        path = "/".join((*prefix, value))
        return (resolve_section_title(path, overrides, default_section=default_section).lower(), value)

    for segment in sorted(children, key=sort_key):
        node = children[segment]
        section_path = "/".join((*prefix, segment))
        child_items = _render_section_nodes(
            node["children"],
            overrides,
            prefix=(*prefix, segment),
            depth=depth + 1,
            default_section=default_section,
        )
        rendered = {
            "text": resolve_section_title(section_path, overrides, default_section=default_section),
            "items": _sorted_links(node["entries"]) + child_items,
            "collapsed": resolve_section_collapsed(
                section_path,
                overrides,
                depth=depth,
                default_section=default_section,
            ),
        }
        items.append(rendered)
    return items


def build_sidebar_data(
    entries: Iterable[IndexEntry],
    *,
    workflow_definitions: Mapping[str, Any] | None = None,
) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, dict[str, Any]] = defaultdict(_new_section_node)
    labels: dict[str, str] = {}
    section_overrides_by_root: dict[str, Mapping[str, SectionOverride]] = {}
    default_sections_by_root: dict[str, str] = {}

    for workflow in (workflow_definitions or {}).values():
        workflow_root = workflow.output_root.name
        section_overrides_by_root[workflow_root] = load_section_overrides(
            workflow.source_root,
            default_section=workflow.default_section,
        )
        default_sections_by_root[workflow_root] = workflow.default_section

    for entry in sorted(entries, key=lambda item: (item.workflow_root, item.section, item.title.lower(), item.link)):
        _insert_section_entry(grouped[entry.workflow_root], entry)
        labels[entry.workflow_root] = entry.workflow_label

    sidebar: dict[str, list[dict[str, Any]]] = {}
    for workflow_root, tree in grouped.items():
        items = _render_section_nodes(
            tree["children"],
            section_overrides_by_root.get(workflow_root, {}),
            default_section=default_sections_by_root.get(workflow_root, "general"),
        )
        sidebar[f"/{workflow_root}/"] = items
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
