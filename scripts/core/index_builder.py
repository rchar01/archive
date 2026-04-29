from __future__ import annotations

from collections import defaultdict
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import date
from html import escape
from pathlib import Path
from typing import Iterable

from scripts.core.content_links import normalize_content_link
from scripts.core.frontmatter import dump_frontmatter
from scripts.core.frontmatter import read_markdown
from scripts.core.markdown import markdown_files
from scripts.core.paths import CONTENT_DIR
from scripts.core.page_catalog import resolve_summary
from scripts.core.validation import require_field, require_iso_date, require_optional_string, require_optional_slug

MAX_NAV_TITLE_LENGTH = 60


def shorten_navigation_title(title: str, *, limit: int = MAX_NAV_TITLE_LENGTH) -> str:
    cleaned = " ".join(title.split()).strip()
    if len(cleaned) <= limit:
        return cleaned
    content_limit = max(limit - 3, 1)
    prefix = cleaned[: content_limit + 1]
    if " " in prefix:
        truncated = prefix.rsplit(" ", 1)[0].rstrip(" ,;:-")
    else:
        truncated = cleaned[:content_limit].rstrip(" ,;:-")
    if not truncated:
        truncated = cleaned[:content_limit].rstrip(" ,;:-")
    return f"{truncated}..."


@dataclass(frozen=True)
class IndexEntry:
    workflow_root: str
    workflow_label: str
    section: str
    title: str
    link: str
    nav_title: str = ""
    created: str = ""
    summary: str = ""

    @property
    def display_title(self) -> str:
        return self.nav_title or shorten_navigation_title(self.title)


@dataclass(frozen=True)
class WorkflowOverview:
    root: str
    label: str
    entry_count: int
    section_count: int


def collect_index_entries(workflows: Mapping[str, object], *, content_dir: Path = CONTENT_DIR) -> list[IndexEntry]:
    entries: list[IndexEntry] = []
    for workflow in workflows.values():
        workflow_root = workflow.output_root.relative_to(content_dir).as_posix()
        for path in markdown_files(workflow.source_root):
            document = read_markdown(path)
            title = str(require_field(document.frontmatter, "title")).strip()
            nav_title = require_optional_string(document.frontmatter, "nav_title") or ""
            section = str(require_field(document.frontmatter, "section")).strip()
            created = require_iso_date(document.frontmatter, "created")
            slug = require_optional_slug(document.frontmatter, "slug")
            output_path = workflow.output_path_for(title, section, slug=slug)
            entries.append(
                IndexEntry(
                    workflow_root=workflow_root,
                    workflow_label=workflow.label,
                    section=section,
                    title=title,
                    nav_title=nav_title,
                    link=normalize_content_link(output_path.relative_to(content_dir).as_posix()),
                    created=created,
                    summary=resolve_summary(document.frontmatter, document.body),
                )
            )
    return entries


def humanize_segment(value: str) -> str:
    return value.replace("-", " ").replace("_", " ").strip().title()


def section_title(section: str) -> str:
    return " / ".join(humanize_segment(part) for part in section.split("/") if part.strip()) or "General"


def group_entries(entries: Iterable[IndexEntry]) -> dict[str, dict[str, list[IndexEntry]]]:
    grouped: dict[str, dict[str, list[IndexEntry]]] = defaultdict(lambda: defaultdict(list))
    for entry in sorted(entries, key=lambda item: (item.workflow_root, item.section, item.title.lower(), item.link)):
        grouped[entry.workflow_root][entry.section].append(entry)
    return {workflow_root: dict(sections) for workflow_root, sections in grouped.items()}


def parse_created(value: str) -> date:
    return date.fromisoformat(value)


def recent_entries(entries: Iterable[IndexEntry], *, limit: int = 10) -> list[IndexEntry]:
    return sorted(
        entries,
        key=lambda entry: (parse_created(entry.created), entry.title.lower(), entry.link),
        reverse=True,
    )[:limit]


def pluralize(count: int, singular: str, plural: str | None = None) -> str:
    if count == 1:
        return singular
    return plural or f"{singular}s"


def build_workflow_overviews(entries: Iterable[IndexEntry], workflows: Iterable[tuple[str, str]]) -> list[WorkflowOverview]:
    counts: dict[str, int] = defaultdict(int)
    sections: dict[str, set[str]] = defaultdict(set)

    for entry in entries:
        counts[entry.workflow_root] += 1
        sections[entry.workflow_root].add(entry.section)

    overviews: list[WorkflowOverview] = []
    for workflow_root, workflow_label in workflows:
        if counts[workflow_root] == 0:
            continue
        overviews.append(
            WorkflowOverview(
                root=workflow_root,
                label=workflow_label,
                entry_count=counts[workflow_root],
                section_count=len(sections[workflow_root]),
            )
        )
    return overviews


def render_entry_row(entry: IndexEntry, *, show_workflow_label: bool) -> str:
    metadata: list[str] = []
    if show_workflow_label:
        metadata.append(entry.workflow_label)
    if entry.created:
        metadata.append(entry.created)

    lines = [f'<a class="archive-entry" href="{escape(entry.link, quote=True)}">']
    lines.append('  <span class="archive-entry__header">')
    lines.append(f'    <span class="archive-entry__title">{escape(entry.display_title)}</span>')
    if metadata:
        lines.append(f'    <span class="archive-entry__meta">{escape(" · ".join(metadata))}</span>')
    lines.append("  </span>")
    if entry.summary:
        lines.append(f'  <span class="archive-entry__summary">{escape(entry.summary)}</span>')
    lines.append("</a>")
    return "\n".join(lines)


def render_workflow_card(workflow: WorkflowOverview) -> str:
    summary = f"Browse published {workflow.label.lower()} organized by section."
    meta = (
        f"{workflow.entry_count} {pluralize(workflow.entry_count, 'page')}"
        f" · {workflow.section_count} {pluralize(workflow.section_count, 'section')}"
    )
    link = f"/{workflow.root}/"
    return "\n".join(
        [
            f'<a class="archive-home__workflow" href="{escape(link, quote=True)}">',
            f'  <span class="archive-home__workflow-title">{escape(workflow.label)}</span>',
            f'  <span class="archive-home__workflow-meta">{escape(meta)}</span>',
            f'  <span class="archive-home__workflow-summary">{escape(summary)}</span>',
            "</a>",
        ]
    )


def render_home_page(workflows: list[WorkflowOverview], recent: list[IndexEntry]) -> str:
    frontmatter: dict[str, object] = {
        "title": "Home",
        "layout": "home",
        "pageClass": "archive-home",
        "hero": {
            "name": "Archive",
            "text": "Source-first publishing",
            "tagline": "Clear generated indexes for durable notes, docs, and other workflows.",
        },
    }

    hero_actions = [
        {
            "theme": "brand" if index == 0 else "alt",
            "text": f"Browse {workflow.label}",
            "link": f"/{workflow.root}/",
        }
        for index, workflow in enumerate(workflows[:2])
    ]
    if hero_actions:
        hero = dict(frontmatter["hero"])
        hero["actions"] = hero_actions
        frontmatter["hero"] = hero

    lines = [
        dump_frontmatter(frontmatter).rstrip(),
    ]

    if workflows:
        lines.extend(
            [
                "",
                "## Browse",
                "",
                '<p class="archive-home__section-copy">Published workflows appear automatically as canonical sources are added.</p>',
                "",
                '<div class="archive-home__workflows">',
            ]
        )
        for workflow in workflows:
            lines.append(render_workflow_card(workflow))
        lines.append("</div>")

    lines.extend(
        [
            "",
            "## Recently Added",
            "",
            '<p class="archive-home__section-copy">Newest published pages across every workflow.</p>',
            "",
        ]
    )
    if not recent:
        lines.append('<p class="archive-home__empty">No content yet.</p>')
        return "\n".join(lines).rstrip() + "\n"

    lines.append('<div class="archive-home__recent">')
    for entry in recent:
        lines.append(render_entry_row(entry, show_workflow_label=True))
    lines.append("</div>")
    return "\n".join(lines).rstrip() + "\n"


def render_workflow_index(title: str, sections: dict[str, list[IndexEntry]]) -> str:
    entry_count = sum(len(section_entries) for section_entries in sections.values())
    section_count = len(sections)
    intro = f"{entry_count} {pluralize(entry_count, 'page')} across {section_count} {pluralize(section_count, 'section')}."

    lines = [
        dump_frontmatter({"title": title, "pageClass": "archive-index"}).rstrip(),
        f"# {title}",
        "",
        f'<p class="archive-index__intro">{escape(intro)}</p>',
    ]
    for section, entries in sections.items():
        lines.extend(["", f"## {section_title(section)}", "", '<div class="archive-index__entries">'])
        for entry in entries:
            lines.append(render_entry_row(entry, show_workflow_label=False))
        lines.append("</div>")
    return "\n".join(lines).rstrip() + "\n"


def build_index_pages(entries: Iterable[IndexEntry], workflows: Iterable[tuple[str, str]] | None = None) -> dict[str, str]:
    entry_list = list(entries)
    grouped = group_entries(entry_list)
    pages: dict[str, str] = {}

    workflow_pairs = list(workflows or [])
    if not workflow_pairs:
        workflow_pairs = []
        seen_workflows: set[str] = set()
        for entry in entry_list:
            if entry.workflow_root in seen_workflows:
                continue
            seen_workflows.add(entry.workflow_root)
            workflow_pairs.append((entry.workflow_root, entry.workflow_label))

    active_workflows = [(workflow_root, workflow_label) for workflow_root, workflow_label in workflow_pairs if workflow_root in grouped]

    pages["index.md"] = render_home_page(build_workflow_overviews(entry_list, active_workflows), recent_entries(entry_list))

    for workflow_root, workflow_label in active_workflows:
        pages[f"{workflow_root}/index.md"] = render_workflow_index(workflow_label, grouped.get(workflow_root, {}))
    return pages
