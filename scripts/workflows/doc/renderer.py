from __future__ import annotations

from pathlib import Path

from scripts.core.content_writer import GeneratedPage, build_generated_frontmatter_extra
from scripts.core.frontmatter import MarkdownDocument
from scripts.core.markdown import ensure_h1, normalize_heading_spacing, strip_thematic_breaks_before_h2
from scripts.core.summaries import summary_from_body
from scripts.core.validation import require_field, require_list


def render(document: MarkdownDocument, *, source_path: Path, output_path: Path) -> GeneratedPage:
    title = str(require_field(document.frontmatter, "title")).strip()
    tags = [str(tag).strip() for tag in require_list(document.frontmatter, "tags") if str(tag).strip()]
    body = normalize_heading_spacing(strip_thematic_breaks_before_h2(ensure_h1(document.body, title))).rstrip() + "\n"
    frontmatter_extra = build_generated_frontmatter_extra(document.frontmatter)
    summary = str(frontmatter_extra.get("summary") or summary_from_body(body)).strip()
    return GeneratedPage(
        title=title,
        description=summary,
        tags=tags,
        source_path=source_path,
        output_path=output_path,
        body=body,
        frontmatter_extra=frontmatter_extra,
    )
