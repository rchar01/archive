from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

import yaml


def humanize_section_segment(value: str) -> str:
    return value.replace("-", " ").replace("_", " ").strip().title()


def normalize_section_path(section: str | None = None, *, default_section: str = "general") -> str:
    raw = str(section or "").strip().strip("/").replace("\\", "/")
    parts = [part.strip().lower() for part in raw.split("/") if part.strip()]
    if parts:
        return "/".join(parts)
    fallback = str(default_section or "general").strip()
    if fallback == "":
        fallback = "general"
    return "/".join(part.strip().lower() for part in fallback.strip("/").replace("\\", "/").split("/") if part.strip()) or "general"


def section_parts(section: str | None = None, *, default_section: str = "general") -> list[str]:
    return normalize_section_path(section, default_section=default_section).split("/")


@dataclass(frozen=True)
class SectionOverride:
    title: str | None = None
    collapsed: bool | None = None


def section_config_path(source_root: Path) -> Path:
    return source_root / "_sections.yaml"


def load_section_overrides(source_root: Path, *, default_section: str = "general") -> dict[str, SectionOverride]:
    path = section_config_path(source_root)
    if not path.exists():
        return {}

    data = yaml.safe_load(path.read_text()) or {}
    if not isinstance(data, dict):
        raise ValueError(f"Section config must be a mapping: {path}")

    raw_sections = data.get("sections") or {}
    if not isinstance(raw_sections, dict):
        raise ValueError(f"Section config field 'sections' must be a mapping: {path}")

    overrides: dict[str, SectionOverride] = {}
    for raw_key, raw_value in raw_sections.items():
        key = normalize_section_path(str(raw_key), default_section=default_section)
        if not isinstance(raw_value, dict):
            raise ValueError(f"Section override must be a mapping for '{raw_key}': {path}")

        title = raw_value.get("title")
        if title is not None:
            if not isinstance(title, str) or not title.strip():
                raise ValueError(f"Section override field 'title' must be a non-empty string for '{raw_key}': {path}")
            title = title.strip()

        collapsed = raw_value.get("collapsed")
        if collapsed is not None and not isinstance(collapsed, bool):
            raise ValueError(f"Section override field 'collapsed' must be a boolean for '{raw_key}': {path}")

        overrides[key] = SectionOverride(title=title, collapsed=collapsed)

    return overrides


def resolve_section_title(
    section: str,
    overrides: Mapping[str, SectionOverride],
    *,
    default_section: str = "general",
) -> str:
    normalized = normalize_section_path(section, default_section=default_section)
    override = overrides.get(normalized)
    if override is not None and override.title is not None:
        return override.title
    return humanize_section_segment(normalized.rsplit("/", 1)[-1])


def section_display_title(
    section: str,
    overrides: Mapping[str, SectionOverride],
    *,
    default_section: str = "general",
) -> str:
    parts = section_parts(section, default_section=default_section)
    titles: list[str] = []
    prefix: list[str] = []
    for part in parts:
        prefix.append(part)
        titles.append(resolve_section_title("/".join(prefix), overrides, default_section=default_section))
    return " / ".join(titles)


def resolve_section_collapsed(
    section: str,
    overrides: Mapping[str, SectionOverride],
    *,
    depth: int,
    default_section: str = "general",
) -> bool:
    normalized = normalize_section_path(section, default_section=default_section)
    override = overrides.get(normalized)
    if override is not None and override.collapsed is not None:
        return override.collapsed
    return depth > 0
