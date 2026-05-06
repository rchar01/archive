from __future__ import annotations

from datetime import date
import re

from scripts.core.frontmatter import MarkdownDocument
from scripts.core.identifiers import generate_entry_id
from scripts.core.markdown import ensure_h1, has_section, normalize_heading_spacing, strip_thematic_breaks_before_h2
from scripts.core.paths import trim
from scripts.core.sections import normalize_section_path
from scripts.core.summaries import summary_from_body
from scripts.core.validation import require_choice, require_field, require_list


def normalize_section(section: str, default_section: str) -> str:
    return normalize_section_path(section, default_section=default_section)


def normalize_tags(raw_tags: object) -> list[str]:
    if not isinstance(raw_tags, list):
        return []
    return [trim(str(tag)) for tag in raw_tags if trim(str(tag))]


def normalize_related_manual(raw_links: object) -> list[str]:
    if not isinstance(raw_links, list):
        return []
    return [trim(str(link)) for link in raw_links if trim(str(link))]


def optional_bool(document: MarkdownDocument, name: str) -> bool | None:
    value = document.frontmatter.get(name)
    return value if isinstance(value, bool) else None


def optional_string(document: MarkdownDocument, name: str) -> str | None:
    value = document.frontmatter.get(name)
    if not isinstance(value, str):
        return None
    cleaned = trim(value)
    return cleaned or None


def build_body(body: str, title: str) -> str:
    cleaned = strip_thematic_breaks_before_h2(body.strip())
    if has_section(cleaned, "Overview"):
        return normalize_heading_spacing(ensure_h1(cleaned, title)).rstrip() + "\n"

    later_heading = next((match for match in re.finditer(r"(?m)^##\s+", cleaned)), None)
    if later_heading:
        overview = cleaned[: later_heading.start()].strip()
        remainder = cleaned[later_heading.start() :].strip()
    else:
        overview = cleaned
        remainder = ""

    if not overview:
        overview = summary_from_body(cleaned)

    lines = [f"# {title}", "", "## Overview", ""]
    if overview:
        lines.extend([overview, ""])
    if remainder:
        lines.extend([remainder, ""])
    return "\n".join(lines).rstrip() + "\n"


def from_incoming(document: MarkdownDocument, *, default_section: str = "general") -> MarkdownDocument:
    title = trim(str(require_field(document.frontmatter, "title")))
    kind = trim(str(require_field(document.frontmatter, "kind")))
    require_choice(kind, ["doc"], "kind")
    tags = normalize_tags(require_list(document.frontmatter, "tags"))
    related_manual = normalize_related_manual(document.frontmatter.get("related_manual", []))
    today = date.today().isoformat()
    frontmatter = {
        "id": generate_entry_id(),
        "title": title,
        "kind": "doc",
        "section": normalize_section(str(document.frontmatter.get("section") or ""), default_section),
        "status": "draft",
        "tags": tags,
        "created": today,
        "updated": today,
    }
    if related_manual:
        frontmatter["related_manual"] = related_manual
    for name in ("hide_knowledge_panel", "hide_backlinks", "hide_related"):
        value = optional_bool(document, name)
        if value is not None:
            frontmatter[name] = value
    for name in ("nav_title", "priority", "slug", "summary"):
        value = optional_string(document, name)
        if value is not None:
            frontmatter[name] = value

    return MarkdownDocument(
        frontmatter=frontmatter,
        body=build_body(document.body, title),
    )
