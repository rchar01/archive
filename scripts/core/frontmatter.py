from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from scripts.core.io import write_text


@dataclass(frozen=True)
class MarkdownDocument:
    frontmatter: dict[str, Any]
    body: str


def split_frontmatter_and_body(text: str) -> tuple[str | None, str]:
    if not text.startswith("---\n"):
        return None, text
    match = re.match(r"^---\n(.*?)\n---\n?", text, re.DOTALL)
    if not match:
        return None, text
    body = text[match.end() :]
    if body.startswith("\n"):
        body = body[1:]
    return match.group(1), body


def parse_frontmatter(text: str) -> tuple[dict[str, Any], str]:
    frontmatter_text, body = split_frontmatter_and_body(text)
    if frontmatter_text is None:
        return {}, body
    data = yaml.safe_load(frontmatter_text) or {}
    if not isinstance(data, dict):
        raise ValueError("Markdown frontmatter must parse to a mapping")
    return data, body


def dump_frontmatter(data: dict[str, Any]) -> str:
    dumped = yaml.safe_dump(data, sort_keys=False, allow_unicode=False).strip()
    return f"---\n{dumped}\n---\n\n"


def render_markdown(document: MarkdownDocument) -> str:
    if document.frontmatter:
        return dump_frontmatter(document.frontmatter) + document.body
    return document.body


def read_markdown(path: Path) -> MarkdownDocument:
    frontmatter, body = parse_frontmatter(path.read_text())
    return MarkdownDocument(frontmatter=frontmatter, body=body)


def write_markdown(path: Path, document: MarkdownDocument) -> None:
    write_text(path, render_markdown(document))
