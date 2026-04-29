from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from scripts.core.frontmatter import dump_frontmatter
from scripts.core.io import write_text
from scripts.core.paths import relative_to_workspace


GENERATED_FRONTMATTER_FIELDS = (
    "related_manual",
    "hide_knowledge_panel",
    "hide_backlinks",
    "hide_related",
    "nav_title",
    "priority",
    "slug",
    "summary",
    "updated",
)


@dataclass(frozen=True)
class GeneratedPage:
    title: str
    body: str
    source_path: Path
    output_path: Path
    description: str = ""
    tags: list[str] = field(default_factory=list)
    frontmatter_extra: dict[str, Any] = field(default_factory=dict)
    regenerate_command: str = "make build-content"


def build_generated_frontmatter_extra(source_frontmatter: dict[str, Any]) -> dict[str, Any]:
    extra: dict[str, Any] = {}
    for field in GENERATED_FRONTMATTER_FIELDS:
        value = source_frontmatter.get(field)
        if value is None:
            continue
        if isinstance(value, str):
            value = value.strip()
            if not value:
                continue
        extra[field] = value
    return extra


def generated_warning(source_path: str, regenerate_command: str = "make build-content") -> str:
    return (
        "<!--\n"
        "GENERATED FILE. DO NOT EDIT.\n\n"
        f"Source:\n{source_path}\n\n"
        f"Regenerate with:\n{regenerate_command}\n"
        "-->\n\n"
    )


def build_frontmatter(page: GeneratedPage) -> dict[str, Any]:
    frontmatter: dict[str, Any] = {
        "title": page.title,
        "source_path": relative_to_workspace(page.source_path),
        "editLink": False,
    }
    if page.description:
        frontmatter["description"] = page.description
    if page.tags:
        frontmatter["tags"] = page.tags
    frontmatter.update(page.frontmatter_extra)
    return frontmatter


def render_generated_markdown(page: GeneratedPage) -> str:
    source_path = relative_to_workspace(page.source_path)
    return dump_frontmatter(build_frontmatter(page)) + generated_warning(source_path, page.regenerate_command) + page.body


def write_generated_markdown(page: GeneratedPage) -> None:
    write_text(page.output_path, render_generated_markdown(page))
