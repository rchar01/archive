from __future__ import annotations

from collections.abc import Sequence

from scripts.core.frontmatter import MarkdownDocument
from scripts.core.validation import (
    require_choice,
    require_field,
    require_iso_date,
    require_list,
    require_optional_bool,
    require_optional_slug,
    require_optional_string,
    require_sections,
)


def validate(document: MarkdownDocument, *, required_sections: Sequence[str]) -> None:
    require_field(document.frontmatter, "id")
    require_field(document.frontmatter, "title")
    require_field(document.frontmatter, "section")
    require_field(document.frontmatter, "status")
    require_iso_date(document.frontmatter, "created")
    require_iso_date(document.frontmatter, "updated")
    require_choice(str(require_field(document.frontmatter, "kind")).strip(), ["note"], "kind")
    require_list(document.frontmatter, "tags")
    require_list(document.frontmatter, "related_manual")
    require_optional_bool(document.frontmatter, "hide_knowledge_panel")
    require_optional_bool(document.frontmatter, "hide_backlinks")
    require_optional_bool(document.frontmatter, "hide_related")
    require_optional_string(document.frontmatter, "nav_title")
    require_optional_string(document.frontmatter, "priority")
    require_optional_slug(document.frontmatter, "slug")
    require_optional_string(document.frontmatter, "summary")
    require_sections(document.body, required_sections)
