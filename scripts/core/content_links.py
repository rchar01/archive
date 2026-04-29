from __future__ import annotations

import os
import re
from pathlib import Path

from scripts.core.paths import CONTENT_DIR


MARKDOWN_LINK_PATTERN = re.compile(r"(?<!!)\[[^\]]+\]\(([^)]+)\)")


def normalize_content_link(path: str) -> str:
    normalized = path.replace("\\", "/").strip()
    normalized = normalized.lstrip("./")
    if not normalized.startswith("/"):
        normalized = "/" + normalized
    if normalized.endswith("/index.md"):
        return normalized[: -len("index.md")]
    if normalized == "/index.md":
        return "/"
    if normalized.endswith(".md"):
        return normalized[: -len(".md")]
    return normalized


def parse_markdown_link_target(raw_target: str) -> str:
    target = raw_target.strip()
    if target.startswith("<") and ">" in target:
        return target[1 : target.index(">")].strip()
    return target.split()[0] if target else ""


def is_external_link(target: str) -> bool:
    lowered = target.lower()
    return lowered.startswith(("http://", "https://", "mailto:", "tel:", "data:")) or target.startswith("#")


def resolve_content_link(target: str, *, output_path: Path, content_dir: Path = CONTENT_DIR) -> str:
    if is_external_link(target):
        return ""
    if target.startswith("/"):
        return normalize_content_link(target)

    relative_base = output_path.relative_to(content_dir).parent.as_posix()
    resolved = os.path.normpath(os.path.join(relative_base, target)).replace("\\", "/")
    return normalize_content_link(resolved)


def extract_internal_content_links(body: str, *, output_path: Path, content_dir: Path = CONTENT_DIR) -> list[str]:
    links: list[str] = []
    seen: set[str] = set()

    for raw_target in MARKDOWN_LINK_PATTERN.findall(body):
        target = parse_markdown_link_target(raw_target)
        if not target:
            continue
        normalized = resolve_content_link(target, output_path=output_path, content_dir=content_dir)
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        links.append(normalized)

    return links
