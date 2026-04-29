from __future__ import annotations

from collections import defaultdict
from typing import Any

from scripts.core.content_links import extract_internal_content_links, normalize_content_link
from scripts.core.frontmatter import read_markdown
from scripts.core.markdown import markdown_files
from scripts.core.paths import CONTENT_DIR
from scripts.core.registry import WorkflowDefinition
from scripts.core.validation import require_field, require_optional_slug


def collect_outgoing_links(
    workflows: dict[str, WorkflowDefinition],
    pages_by_link: dict[str, dict[str, Any]],
    *,
    content_dir=CONTENT_DIR,
) -> dict[str, list[str]]:
    outgoing_links_by_link: dict[str, list[str]] = {}

    for workflow in workflows.values():
        validator = workflow.load_module("validator")
        for path in markdown_files(workflow.source_root):
            document = read_markdown(path)
            validator.validate(document, required_sections=workflow.required_sections)
            title = str(require_field(document.frontmatter, "title")).strip()
            section = str(require_field(document.frontmatter, "section")).strip()
            slug = require_optional_slug(document.frontmatter, "slug")
            output_path = workflow.output_path_for(title, section, slug=slug)
            link = normalize_content_link(output_path.relative_to(content_dir).as_posix())
            outgoing_links_by_link[link] = [
                target_link
                for target_link in extract_internal_content_links(
                    document.body,
                    output_path=output_path,
                    content_dir=content_dir,
                )
                if target_link in pages_by_link and target_link != link
            ]

    return outgoing_links_by_link


def build_linkgraph(
    pages_by_link: dict[str, dict[str, Any]], outgoing_links_by_link: dict[str, list[str]]
) -> dict[str, dict[str, list[str]]]:
    backlinks_by_link: dict[str, list[str]] = defaultdict(list)
    page_titles = {link: str(page["title"]) for link, page in pages_by_link.items()}

    for source_link, targets in outgoing_links_by_link.items():
        for target_link in targets:
            if target_link in pages_by_link and source_link != target_link:
                backlinks_by_link[target_link].append(source_link)

    linkgraph: dict[str, dict[str, list[str]]] = {}
    for link in sorted(pages_by_link):
        outbound = [target for target in outgoing_links_by_link.get(link, []) if target in pages_by_link and target != link]
        seen_outbound: set[str] = set()
        deduped_outbound: list[str] = []
        for target in outbound:
            if target in seen_outbound:
                continue
            seen_outbound.add(target)
            deduped_outbound.append(target)

        backlinks = sorted(
            set(backlinks_by_link.get(link, [])),
            key=lambda value: (page_titles.get(value, "").lower(), value),
        )
        linkgraph[link] = {
            "outbound": deduped_outbound,
            "backlinks": backlinks,
        }

    return linkgraph
