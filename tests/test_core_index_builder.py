from __future__ import annotations

import unittest

from scripts.core.index_builder import build_index_pages
from scripts.core.index_builder import IndexEntry
from scripts.core.index_builder import WorkflowOverview
from scripts.core.index_builder import render_home_page
from scripts.core.index_builder import render_workflow_index
from scripts.core.index_builder import shorten_navigation_title


class IndexBuilderTests(unittest.TestCase):
    def test_shorten_navigation_title_respects_limit_with_ellipsis(self) -> None:
        result = shorten_navigation_title("A" * 61, limit=60)

        self.assertEqual(len(result), 60)
        self.assertTrue(result.endswith("..."))

    def test_render_home_page_uses_editorial_blocks(self) -> None:
        page = render_home_page(
            [WorkflowOverview(root="notes", label="Notes", entry_count=3, section_count=2)],
            [
                IndexEntry(
                    workflow_root="notes",
                    workflow_label="Notes",
                    section="general",
                    title="Long Entry Title",
                    nav_title="Short Entry",
                    link="/notes/general/short-entry",
                    created="2026-04-27",
                    summary="Concise summary.",
                )
            ],
        )

        self.assertIn("layout: home", page)
        self.assertIn("pageClass: archive-home", page)
        self.assertIn('class="archive-home__workflows"', page)
        self.assertIn('href="/notes/"', page)
        self.assertIn('class="archive-home__recent"', page)
        self.assertIn("Short Entry", page)

    def test_render_workflow_index_uses_structured_rows(self) -> None:
        page = render_workflow_index(
            "Docs",
            {
                "testing/panel": [
                    IndexEntry(
                        workflow_root="docs",
                        workflow_label="Docs",
                        section="testing/panel",
                        title="Knowledge Panel Guide",
                        link="/docs/testing/knowledge-panel-guide",
                        created="2026-04-27",
                        summary="Compact summary.",
                    )
                ]
            },
        )

        self.assertIn("pageClass: archive-index", page)
        self.assertIn('<p class="archive-index__intro">1 page across 1 section.</p>', page)
        self.assertIn('class="archive-index__entries"', page)
        self.assertIn('href="/docs/testing/knowledge-panel-guide"', page)
        self.assertNotIn("Docs · 2026-04-27", page)
        self.assertIn("2026-04-27", page)

    def test_build_index_pages_generates_case_insensitive_tag_pages(self) -> None:
        pages = build_index_pages(
            [
                IndexEntry(
                    workflow_root="notes",
                    workflow_label="Notes",
                    section="general",
                    title="Docker DNS Issue",
                    link="/notes/general/docker-dns-issue",
                    created="2026-04-27",
                    summary="First entry.",
                    tags=["DNS Server"],
                ),
                IndexEntry(
                    workflow_root="docs",
                    workflow_label="Docs",
                    section="reference",
                    title="Resolver Guide",
                    link="/docs/reference/resolver-guide",
                    created="2026-04-28",
                    summary="Second entry.",
                    tags=["dns server"],
                ),
            ]
        )

        tag_page = pages["tags/dns%20server/index.md"]
        self.assertIn("title: 'Tag: DNS Server'", tag_page)
        self.assertIn("2 pages tagged `DNS Server` across 2 workflows.", tag_page)
        self.assertIn('href="/notes/general/docker-dns-issue"', tag_page)
        self.assertIn('href="/docs/reference/resolver-guide"', tag_page)


if __name__ == "__main__":
    unittest.main()
