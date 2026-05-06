from __future__ import annotations

import re
from pathlib import Path

from scripts.core.frontmatter import (
    MarkdownDocument,
    dump_frontmatter,
    parse_frontmatter,
    read_markdown,
    split_frontmatter_and_body,
    write_markdown,
)


def render_frontmatter(data: dict) -> str:
    return dump_frontmatter(data)


def load_markdown(path: Path) -> tuple[dict, str]:
    document = read_markdown(path)
    return document.frontmatter, document.body


def save_markdown(path: Path, frontmatter: dict, body: str) -> None:
    write_markdown(path, MarkdownDocument(frontmatter=frontmatter, body=body))


def extract_headings(body: str) -> list[tuple[int, str]]:
    return [(len(match.group(1)), match.group(2).strip()) for match in re.finditer(r"^(#{1,6})\s+(.+?)\s*$", body, re.MULTILINE)]


def has_section(body: str, heading: str, *, level: int | None = None) -> bool:
    normalized = heading.strip().lower()
    return any((level is None or heading_level == level) and title.lower() == normalized for heading_level, title in extract_headings(body))


def ensure_h1(body: str, title: str) -> str:
    if any(level == 1 for level, _ in extract_headings(body)):
        return body
    return f"# {title}\n\n{body.lstrip()}" if body.strip() else f"# {title}\n"


def normalize_heading_spacing(body: str) -> str:
    body = re.sub(r"\n{3,}(#{1,6}\s)", r"\n\n\1", body)
    return re.sub(r"^(#{1,6}\s+.+)\n(?!\n)", r"\1\n\n", body, flags=re.MULTILINE)


def strip_thematic_breaks_before_h2(body: str) -> str:
    lines = body.splitlines()
    cleaned: list[str] = []
    index = 0

    while index < len(lines):
        line = lines[index]
        if re.fullmatch(r"\s*(?:-{3,}|\*{3,}|_{3,})\s*", line):
            next_index = index + 1
            while next_index < len(lines) and not lines[next_index].strip():
                next_index += 1
            if next_index < len(lines) and re.match(r"##\s+", lines[next_index]):
                while cleaned and not cleaned[-1].strip():
                    cleaned.pop()
                if cleaned:
                    cleaned.append("")
                index = next_index
                continue

        cleaned.append(line)
        index += 1

    return "\n".join(cleaned)


def markdown_files(base: Path) -> list[Path]:
    return sorted(path for path in base.rglob("*.md") if path.is_file())
