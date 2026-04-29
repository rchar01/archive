from __future__ import annotations

import unittest
from pathlib import Path

from scripts.core.content_links import extract_internal_content_links, normalize_content_link


class ContentLinksTests(unittest.TestCase):
    def test_normalize_content_link_trims_markdown_suffix(self) -> None:
        self.assertEqual(normalize_content_link("notes/general/example.md"), "/notes/general/example")

    def test_extract_internal_content_links_supports_absolute_and_relative_links(self) -> None:
        body = "[Absolute](/docs/guide/example) [Relative](../peer.md) [External](https://example.com)"
        output_path = Path("/tmp/content/notes/testing/example.md")

        self.assertEqual(
            extract_internal_content_links(body, output_path=output_path, content_dir=Path("/tmp/content")),
            ["/docs/guide/example", "/notes/peer"],
        )


if __name__ == "__main__":
    unittest.main()
