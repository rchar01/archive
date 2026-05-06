from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from scripts.core.markdown import (
    load_markdown,
    markdown_files,
    parse_frontmatter,
    render_frontmatter,
    save_markdown,
    strip_thematic_breaks_before_h2,
)


class MarkdownTests(unittest.TestCase):
    def test_parse_and_render_frontmatter(self) -> None:
        text = "---\ntitle: Example\ntags:\n- one\n- two\n---\n\nBody\n"

        frontmatter, body = parse_frontmatter(text)

        self.assertEqual(frontmatter["title"], "Example")
        self.assertEqual(frontmatter["tags"], ["one", "two"])
        self.assertEqual(body, "Body\n")
        self.assertIn("title: Example", render_frontmatter(frontmatter))

    def test_parse_frontmatter_preserves_extra_blank_lines_in_body(self) -> None:
        text = "---\ntitle: Example\n---\n\n\nBody\n"

        _, body = parse_frontmatter(text)

        self.assertEqual(body, "\nBody\n")

    def test_save_and_load_markdown_round_trip(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            path = Path(tmp_dir) / "example.md"
            save_markdown(path, {"title": "Sample"}, "Body line with hard break.  \n---\n\n")

            frontmatter, body = load_markdown(path)

        self.assertEqual(frontmatter["title"], "Sample")
        self.assertEqual(body, "Body line with hard break.  \n---\n\n")

    def test_markdown_files_finds_markdown_under_base(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            (root / "a.md").write_text("# A\n")
            (root / "nested").mkdir()
            (root / "nested" / "b.md").write_text("# B\n")
            (root / "c.txt").write_text("ignore\n")

            paths = markdown_files(root)

        self.assertEqual([path.name for path in paths], ["a.md", "b.md"])

    def test_strip_thematic_break_before_h2(self) -> None:
        body = "Lead paragraph.\n\n---\n\n## Next\n\nMore.\n"

        cleaned = strip_thematic_breaks_before_h2(body)

        self.assertEqual(cleaned, "Lead paragraph.\n\n## Next\n\nMore.")

    def test_strip_star_and_underscore_breaks_before_h2(self) -> None:
        self.assertEqual(
            strip_thematic_breaks_before_h2("Lead\n\n***\n\n## Next\n"),
            "Lead\n\n## Next",
        )
        self.assertEqual(
            strip_thematic_breaks_before_h2("Lead\n\n___\n\n## Next\n"),
            "Lead\n\n## Next",
        )

    def test_preserves_thematic_breaks_not_before_h2(self) -> None:
        self.assertEqual(
            strip_thematic_breaks_before_h2("Lead\n\n---\n\nStill prose.\n"),
            "Lead\n\n---\n\nStill prose.",
        )
        self.assertEqual(
            strip_thematic_breaks_before_h2("Lead\n\n---\n\n### Nested\n"),
            "Lead\n\n---\n\n### Nested",
        )


if __name__ == "__main__":
    unittest.main()
