from __future__ import annotations

import re
from collections.abc import Iterable


DEFAULT_GENERATED_SECTIONS = ("backlinks", "related")
FOOTER_START = "<!-- GENERATED:FOOTER START -->"
FOOTER_END = "<!-- GENERATED:FOOTER END -->"


def generated_marker_start(name: str) -> str:
    return f"<!-- GENERATED:{name.upper()} START -->"


def generated_marker_end(name: str) -> str:
    return f"<!-- GENERATED:{name.upper()} END -->"


def section_pattern(name: str) -> re.Pattern[str]:
    return re.compile(
        rf"\n*{re.escape(generated_marker_start(name))}\n(.*?)\n{re.escape(generated_marker_end(name))}\n*",
        re.DOTALL,
    )


def footer_pattern() -> re.Pattern[str]:
    return re.compile(
        rf"\n*{re.escape(FOOTER_START)}\n(.*?)\n{re.escape(FOOTER_END)}\n*",
        re.DOTALL,
    )


def split_body_and_generated_sections(
    body: str, section_names: Iterable[str] = DEFAULT_GENERATED_SECTIONS
) -> tuple[str, dict[str, str]]:
    names = tuple(section_names)
    sections: dict[str, str] = {}
    working = body
    footer_match = footer_pattern().search(working)
    if footer_match:
        footer_content = footer_match.group(1)
        working = footer_pattern().sub("", working)
        for name in names:
            match = section_pattern(name).search(footer_content)
            if match:
                sections[name] = match.group(1).strip()

    for name in names:
        match = section_pattern(name).search(working)
        if match:
            sections[name] = match.group(1).strip()
            working = section_pattern(name).sub("", working)

    return working, sections


def render_generated_footer(
    sections: dict[str, str], section_names: Iterable[str] = DEFAULT_GENERATED_SECTIONS
) -> str:
    blocks = []
    for name in tuple(section_names):
        section = sections.get(name, "").strip()
        if not section:
            continue
        blocks.append(f"{generated_marker_start(name)}\n{section}\n{generated_marker_end(name)}")
    if not blocks:
        return ""
    return f"{FOOTER_START}\n" + "\n\n".join(blocks) + f"\n{FOOTER_END}"


def strip_generated_section(
    body: str, name: str, section_names: Iterable[str] = DEFAULT_GENERATED_SECTIONS
) -> str:
    cleaned_body, sections = split_body_and_generated_sections(body, section_names)
    sections.pop(name, None)
    footer = render_generated_footer(sections, section_names)
    base = cleaned_body.rstrip("\n")
    if footer and base:
        return base + "\n\n" + footer + "\n"
    if footer:
        return footer + "\n"
    return cleaned_body


def strip_all_generated_sections(body: str, section_names: Iterable[str] = DEFAULT_GENERATED_SECTIONS) -> str:
    cleaned_body, _ = split_body_and_generated_sections(body, section_names)
    return cleaned_body


def replace_generated_section(
    body: str,
    name: str,
    section: str,
    section_names: Iterable[str] = DEFAULT_GENERATED_SECTIONS,
) -> str:
    cleaned_body, sections = split_body_and_generated_sections(body, section_names)
    sections[name] = section.strip()
    footer = render_generated_footer(sections, section_names)
    base = cleaned_body.rstrip("\n")
    if footer and base:
        return base + "\n\n" + footer + "\n"
    if footer:
        return footer + "\n"
    return cleaned_body
