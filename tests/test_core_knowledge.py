from __future__ import annotations

import unittest

from scripts.core.related import build_related_index


class KnowledgeCoreTests(unittest.TestCase):
    def test_build_related_index_dedupes_manual_links_from_auto_results(self) -> None:
        pages_by_link = {
            "/notes/testing/alpha-note": {
                "title": "Alpha Note",
                "kind": "note",
                "section": "testing",
                "tags": ["dns"],
                "related_manual": ["/docs/testing/gamma-doc"],
            },
            "/notes/testing/beta-note": {
                "title": "Beta Note",
                "kind": "note",
                "section": "testing",
                "tags": ["dns"],
                "related_manual": [],
            },
            "/docs/testing/gamma-doc": {
                "title": "Gamma Doc",
                "kind": "doc",
                "section": "testing",
                "tags": ["dns"],
                "related_manual": [],
            },
        }
        linkgraph = {
            "/notes/testing/alpha-note": {
                "outbound": ["/notes/testing/beta-note", "/docs/testing/gamma-doc"],
                "backlinks": ["/notes/testing/beta-note", "/docs/testing/gamma-doc"],
            },
            "/notes/testing/beta-note": {
                "outbound": ["/notes/testing/alpha-note"],
                "backlinks": ["/notes/testing/alpha-note"],
            },
            "/docs/testing/gamma-doc": {
                "outbound": ["/notes/testing/alpha-note"],
                "backlinks": ["/notes/testing/alpha-note"],
            },
        }

        related_index = build_related_index(pages_by_link, linkgraph)

        self.assertIn("/notes/testing/beta-note", related_index["/notes/testing/alpha-note"]["related"])
        self.assertNotIn("/docs/testing/gamma-doc", related_index["/notes/testing/alpha-note"]["related"])


if __name__ == "__main__":
    unittest.main()
