from __future__ import annotations

import argparse
import sys
from datetime import date
from pathlib import Path
from typing import Any

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.core.frontmatter import MarkdownDocument, parse_frontmatter, render_markdown
from scripts.core.identifiers import generate_entry_id
from scripts.core.io import write_text
from scripts.core.paths import relative_to_workspace
from scripts.core.registry import get_workflow
from scripts.core.validation import require_optional_slug


def optional_string(value: str | None) -> str | None:
    cleaned = str(value or "").strip()
    return cleaned or None


def parse_csv(value: str | None) -> list[str]:
    cleaned = optional_string(value)
    if cleaned is None:
        return []
    values: list[str] = []
    for item in cleaned.split(","):
        candidate = item.strip()
        if candidate and candidate not in values:
            values.append(candidate)
    return values


def build_frontmatter_extra(args: argparse.Namespace) -> dict[str, Any]:
    frontmatter: dict[str, Any] = {}

    slug = optional_string(args.slug)
    if slug is not None:
        frontmatter["slug"] = require_optional_slug({"slug": slug}, "slug")

    for name in ("nav_title", "summary", "priority"):
        value = optional_string(getattr(args, name))
        if value is not None:
            frontmatter[name] = value

    tags = parse_csv(args.tags)
    if tags:
        frontmatter["tags"] = tags

    related_manual: list[str] = []
    for value in args.related_manual:
        related_manual.extend(parse_csv(value))
    if related_manual:
        frontmatter["related_manual"] = related_manual

    for field in ("hide_knowledge_panel", "hide_backlinks", "hide_related"):
        if getattr(args, field):
            frontmatter[field] = True

    return frontmatter


def render_template(template: str, *, title: str, section: str, frontmatter_extra: dict[str, Any]) -> str:
    today = date.today().isoformat()
    rendered = (
        template.replace("{{ id }}", generate_entry_id())
        .replace("{{ title }}", title)
        .replace("{{ section }}", section)
        .replace("{{ date }}", today)
    )
    frontmatter, body = parse_frontmatter(rendered)
    frontmatter.update(frontmatter_extra)
    return render_markdown(MarkdownDocument(frontmatter=frontmatter, body=body))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--kind", required=True)
    parser.add_argument("--title", required=True)
    parser.add_argument("--section")
    parser.add_argument("--slug")
    parser.add_argument("--nav-title")
    parser.add_argument("--summary")
    parser.add_argument("--priority")
    parser.add_argument("--tags")
    parser.add_argument("--related-manual", action="append", default=[])
    parser.add_argument("--hide-knowledge-panel", action="store_true")
    parser.add_argument("--hide-backlinks", action="store_true")
    parser.add_argument("--hide-related", action="store_true")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args(argv)

    workflow = get_workflow(args.kind)
    section = workflow.normalize_section(args.section)
    target = workflow.source_path_for(args.title, section)
    if target.exists() and not args.force:
        raise SystemExit(f"Refusing to overwrite existing file: {relative_to_workspace(target)}")

    template = workflow.template_path.read_text()
    write_text(target, render_template(template, title=args.title, section=section, frontmatter_extra=build_frontmatter_extra(args)))
    print(relative_to_workspace(target))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
