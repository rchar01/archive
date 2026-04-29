from __future__ import annotations

from typing import Any

from scripts.core.content_links import normalize_content_link
from scripts.core.frontmatter import read_markdown
from scripts.core.markdown import markdown_files
from scripts.core.paths import CONTENT_DIR, relative_to_workspace
from scripts.core.registry import WorkflowDefinition
from scripts.core.validation import require_optional_string, require_optional_slug
from scripts.core.summaries import summary_from_body
from scripts.core.validation import require_field, require_list


def resolve_summary(frontmatter: dict[str, Any], body: str) -> str:
    value = frontmatter.get("summary")
    if isinstance(value, str) and value.strip():
        return value.strip()
    return summary_from_body(body)


def workflow_panel_defaults(workflow: WorkflowDefinition) -> dict[str, bool | None]:
    return {
        "knowledge_panel": workflow.knowledge_panel,
        "backlinks": workflow.backlinks,
        "related": workflow.related,
    }


def collect_page_catalog(
    workflows: dict[str, WorkflowDefinition], *, content_dir=CONTENT_DIR
) -> dict[str, dict[str, Any]]:
    pages: dict[str, dict[str, Any]] = {}

    for workflow in workflows.values():
        validator = workflow.load_module("validator")
        for path in markdown_files(workflow.source_root):
            document = read_markdown(path)
            validator.validate(document, required_sections=workflow.required_sections)
            title = str(require_field(document.frontmatter, "title")).strip()
            nav_title = require_optional_string(document.frontmatter, "nav_title") or ""
            slug = require_optional_slug(document.frontmatter, "slug") or ""
            section = str(require_field(document.frontmatter, "section")).strip()
            output_path = workflow.output_path_for(title, section, slug=slug)
            link = normalize_content_link(output_path.relative_to(content_dir).as_posix())
            pages[link] = {
                "title": title,
                "nav_title": nav_title,
                "link": link,
                "kind": workflow.kind,
                "section": section,
                "slug": slug,
                "tags": [str(tag).strip() for tag in require_list(document.frontmatter, "tags") if str(tag).strip()],
                "summary": resolve_summary(document.frontmatter, document.body),
                "updated": str(document.frontmatter.get("updated") or "").strip(),
                "source_path": relative_to_workspace(path),
                "related_manual": [
                    str(target).strip()
                    for target in require_list(document.frontmatter, "related_manual")
                    if str(target).strip()
                ],
                "workflow": workflow_panel_defaults(workflow),
            }

    return pages
