from __future__ import annotations

from collections import Counter
from collections.abc import Iterable, Mapping, Sequence
from datetime import date
import re
from typing import Any

from scripts.core.frontmatter import split_frontmatter_and_body
from scripts.core.markdown import has_section


class ValidationError(ValueError):
    pass


THEMATIC_BREAK_RE = re.compile(r"\s*(?:-{3,}|\*{3,}|_{3,})\s*")
H2_HEADING_RE = re.compile(r"##\s+")


def require_field(frontmatter: Mapping[str, Any], name: str) -> Any:
    value = frontmatter.get(name)
    if value is None:
        raise ValidationError(f"Missing required field: {name}")
    if isinstance(value, str) and not value.strip():
        raise ValidationError(f"Field must not be blank: {name}")
    return value


def require_choice(value: str, allowed: Sequence[str], field_name: str) -> str:
    if value not in allowed:
        raise ValidationError(f"Invalid {field_name}: {value}; expected one of {', '.join(allowed)}")
    return value


def require_list(frontmatter: Mapping[str, Any], name: str) -> list[Any]:
    value = frontmatter.get(name, [])
    if not isinstance(value, list):
        raise ValidationError(f"Field must be a list: {name}")
    return value


def require_optional_bool(frontmatter: Mapping[str, Any], name: str) -> bool | None:
    value = frontmatter.get(name)
    if value is None:
        return None
    if not isinstance(value, bool):
        raise ValidationError(f"Field must be a boolean: {name}")
    return value


def require_optional_string(frontmatter: Mapping[str, Any], name: str) -> str | None:
    value = frontmatter.get(name)
    if value is None:
        return None
    if not isinstance(value, str):
        raise ValidationError(f"Field must be a string: {name}")
    cleaned = value.strip()
    if not cleaned:
        raise ValidationError(f"Field must not be blank: {name}")
    return cleaned


def require_optional_slug(frontmatter: Mapping[str, Any], name: str) -> str | None:
    value = require_optional_string(frontmatter, name)
    if value is None:
        return None
    if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", value):
        raise ValidationError(f"Field must be a lowercase slug with hyphens only: {name}")
    return value


def require_iso_date(frontmatter: Mapping[str, Any], name: str) -> str:
    value = str(require_field(frontmatter, name)).strip()
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
        raise ValidationError(f"Field must be an ISO date (YYYY-MM-DD): {name}")
    try:
        date.fromisoformat(value)
    except ValueError as exc:
        raise ValidationError(f"Field must be an ISO date (YYYY-MM-DD): {name}") from exc
    return value


def require_sections(body: str, required_sections: Sequence[str]) -> None:
    missing = [section for section in required_sections if not has_section(body, section)]
    if missing:
        raise ValidationError(f"Missing required sections: {', '.join(missing)}")


def body_start_line(text: str) -> int:
    _, body = split_frontmatter_and_body(text)
    return text[: len(text) - len(body)].count("\n") + 1


def lint_body(body: str, *, start_line: int = 1) -> list[str]:
    errors: list[str] = []
    lines = body.splitlines()

    for index, line in enumerate(lines):
        if not THEMATIC_BREAK_RE.fullmatch(line):
            continue

        next_index = index + 1
        while next_index < len(lines) and not lines[next_index].strip():
            next_index += 1

        if next_index < len(lines) and H2_HEADING_RE.match(lines[next_index]):
            errors.append(
                f"line {start_line + index}: thematic break immediately before ## heading; remove the break and use the heading as the section boundary"
            )

    return errors


def check_body_lints(body: str, *, start_line: int = 1) -> None:
    errors = lint_body(body, start_line=start_line)
    if errors:
        raise ValidationError("; ".join(errors))


def find_duplicates(values: Iterable[str]) -> list[str]:
    counts = Counter(value for value in values if value)
    return sorted(value for value, count in counts.items() if count > 1)


def check_duplicate_ids(ids: Iterable[str]) -> None:
    duplicates = find_duplicates(ids)
    if duplicates:
        raise ValidationError(f"Duplicate ids: {', '.join(duplicates)}")


def check_duplicate_output_paths(paths: Iterable[str]) -> None:
    duplicates = find_duplicates(paths)
    if duplicates:
        raise ValidationError(f"Duplicate output paths: {', '.join(duplicates)}")
