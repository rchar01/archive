from __future__ import annotations

import unittest

from scripts.core.generated_sections import (
    render_generated_footer,
    replace_generated_section,
    split_body_and_generated_sections,
    strip_all_generated_sections,
    strip_generated_section,
)


class GeneratedSectionsTests(unittest.TestCase):
    def test_replace_and_split_generated_sections(self) -> None:
        body = "Hello world\n"
        updated = replace_generated_section(body, "backlinks", "## Backlinks\n\n- [One](one.md)")

        cleaned, sections = split_body_and_generated_sections(updated)

        self.assertEqual(cleaned, "Hello world")
        self.assertEqual(sections["backlinks"], "## Backlinks\n\n- [One](one.md)")

    def test_strip_generated_section_removes_only_target_section(self) -> None:
        body = replace_generated_section("Body\n", "backlinks", "Backlink content")
        body = replace_generated_section(body, "related", "Related content")

        stripped = strip_generated_section(body, "backlinks")

        self.assertEqual(strip_all_generated_sections(stripped), "Body")
        self.assertIn("Related content", stripped)
        self.assertNotIn("Backlink content", stripped)

    def test_generated_section_round_trip_preserves_trailing_spaces(self) -> None:
        body = "Body line with hard break.  \n"

        updated = replace_generated_section(body, "backlinks", "## Backlinks\n\n- [One](one.md)")

        self.assertEqual(strip_all_generated_sections(updated), body.rstrip("\n"))

    def test_render_generated_footer_has_no_markdown_rule(self) -> None:
        footer = render_generated_footer({"backlinks": "### Backlinks\n\n- [One](one.md)"})

        self.assertNotIn("\n---\n", footer)
        self.assertIn("### Backlinks", footer)


if __name__ == "__main__":
    unittest.main()
