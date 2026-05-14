from __future__ import annotations

import unittest
from unittest.mock import patch

from scripts.core.features import knowledge_graph_enabled
from scripts.core.index_builder import build_index_pages
from scripts.core.index_builder import IndexEntry
from scripts.core.index_builder import WorkflowOverview
from scripts.core.index_builder import render_home_page
from scripts.core.index_builder import render_graph_page
from scripts.core.index_builder import render_workflow_index
from scripts.core.index_builder import shorten_navigation_title
from scripts.core.sidebar_builder import build_nav_data


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

    def test_render_home_page_adds_graph_as_last_browse_card(self) -> None:
        page = render_home_page(
            [WorkflowOverview(root="notes", label="Notes", entry_count=3, section_count=2)],
            [],
            entry_count=3,
        )

        self.assertIn('href="/graph/"', page)
        self.assertIn("Knowledge Graph", page)
        self.assertIn("Explore pages by links, curated relationships, suggestions, and tags.", page)
        self.assertLess(page.index('href="/notes/"'), page.index('href="/graph/"'))

    def test_render_home_page_omits_graph_card_when_disabled(self) -> None:
        page = render_home_page(
            [WorkflowOverview(root="notes", label="Notes", entry_count=3, section_count=2)],
            [],
            entry_count=3,
            knowledge_graph_enabled=False,
        )

        self.assertNotIn('href="/graph/"', page)
        self.assertNotIn("Knowledge Graph", page)

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
        self.assertIn("search_tags:", tag_page)
        self.assertIn("- DNS Server", tag_page)
        self.assertIn("2 pages tagged `DNS Server` across 2 workflows.", tag_page)
        self.assertIn('href="/notes/general/docker-dns-issue"', tag_page)
        self.assertIn('href="/docs/reference/resolver-guide"', tag_page)

    def test_build_index_pages_generates_graph_page_when_content_exists(self) -> None:
        pages = build_index_pages(
            [
                IndexEntry(
                    workflow_root="notes",
                    workflow_label="Notes",
                    section="general",
                    title="Docker DNS Issue",
                    link="/notes/general/docker-dns-issue",
                    created="2026-04-27",
                )
            ]
        )

        graph_page = pages["graph/index.md"]
        self.assertIn("title: Knowledge Graph", graph_page)
        self.assertIn("pageClass: archive-graph-page", graph_page)
        self.assertIn("search: false", graph_page)
        self.assertIn("aside: false", graph_page)
        self.assertIn("<KnowledgeGraph />", graph_page)

    def test_build_index_pages_skips_graph_page_without_content(self) -> None:
        pages = build_index_pages([])

        self.assertNotIn("graph/index.md", pages)

    def test_build_index_pages_skips_graph_page_when_disabled(self) -> None:
        pages = build_index_pages(
            [
                IndexEntry(
                    workflow_root="notes",
                    workflow_label="Notes",
                    section="general",
                    title="Docker DNS Issue",
                    link="/notes/general/docker-dns-issue",
                    created="2026-04-27",
                )
            ],
            knowledge_graph_enabled=False,
        )

        self.assertNotIn("graph/index.md", pages)
        self.assertNotIn('href="/graph/"', pages["index.md"])

    def test_render_graph_page_describes_clickable_article_links(self) -> None:
        page = render_graph_page(2)

        self.assertIn("# Knowledge Graph", page)
        self.assertIn("Explore 2 pages connected by links, related entries, and tags.", page)

    def test_build_nav_data_adds_graph_link_when_content_exists(self) -> None:
        nav = build_nav_data(
            [
                IndexEntry(
                    workflow_root="notes",
                    workflow_label="Notes",
                    section="general",
                    title="Docker DNS Issue",
                    link="/notes/general/docker-dns-issue",
                    created="2026-04-27",
                )
            ]
        )

        self.assertEqual(nav[0], {"text": "Home", "link": "/"})
        self.assertEqual(nav[1], {"text": "Notes", "link": "/notes/"})
        self.assertEqual(nav[2], {"text": "Graph", "link": "/graph/"})

    def test_build_nav_data_skips_graph_link_without_content(self) -> None:
        nav = build_nav_data([])

        self.assertEqual(nav, [{"text": "Home", "link": "/"}])

    def test_build_nav_data_skips_graph_link_when_disabled(self) -> None:
        nav = build_nav_data(
            [
                IndexEntry(
                    workflow_root="notes",
                    workflow_label="Notes",
                    section="general",
                    title="Docker DNS Issue",
                    link="/notes/general/docker-dns-issue",
                    created="2026-04-27",
                )
            ],
            knowledge_graph_enabled=False,
        )

        self.assertEqual(nav, [{"text": "Home", "link": "/"}, {"text": "Notes", "link": "/notes/"}])

    def test_knowledge_graph_feature_flag_defaults_on_and_accepts_off_values(self) -> None:
        with patch.dict("os.environ", {}, clear=True):
            self.assertTrue(knowledge_graph_enabled())

        for value in ("0", "false", "no", "off", " OFF "):
            with self.subTest(value=value), patch.dict("os.environ", {"ARCHIVE_KNOWLEDGE_GRAPH": value}, clear=True):
                self.assertFalse(knowledge_graph_enabled())

        with patch.dict("os.environ", {"ARCHIVE_KNOWLEDGE_GRAPH": "1"}, clear=True):
            self.assertTrue(knowledge_graph_enabled())


if __name__ == "__main__":
    unittest.main()
