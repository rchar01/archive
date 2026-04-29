from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts.core.content_writer import GeneratedPage, render_generated_markdown


class ContentWriterTests(unittest.TestCase):
    def test_generated_warning_renders_after_frontmatter(self) -> None:
        page = GeneratedPage(
            title="Example Page",
            body="# Example Page\n",
            source_path=Path("sources/notes/example.md"),
            output_path=Path("content/notes/example.md"),
            description="Example summary.",
        )

        rendered = render_generated_markdown(page)

        self.assertTrue(rendered.startswith("---\n"))
        self.assertIn("---\n\n<!--\nGENERATED FILE. DO NOT EDIT.", rendered)
        self.assertIn("source_path: sources/notes/example.md", rendered)
        self.assertIn("\n-->\n\n# Example Page\n", rendered)

    def test_generated_frontmatter_uses_workspace_relative_source_path(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir, patch.dict("os.environ", {"WORKSPACE": tmp_dir}, clear=True):
            page = GeneratedPage(
                title="Example Page",
                body="# Example Page\n",
                source_path=Path(tmp_dir) / "sources" / "notes" / "example.md",
                output_path=Path("content/notes/example.md"),
            )

            rendered = render_generated_markdown(page)

        self.assertIn("source_path: sources/notes/example.md", rendered)


if __name__ == "__main__":
    unittest.main()
