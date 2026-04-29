from __future__ import annotations

import unittest

from scripts.core.summaries import first_sentence, plain_text_summary_line, summary_from_body, truncate_summary


class SummariesTests(unittest.TestCase):
    def test_plain_text_summary_line_strips_markdown(self) -> None:
        line = "- [Example](example.md) with `code` and **bold** text"
        self.assertEqual(plain_text_summary_line(line), "Example with code and bold text")

    def test_truncate_summary_preserves_word_boundary(self) -> None:
        text = "one two three four five"
        self.assertEqual(truncate_summary(text, limit=12), "one two...")

    def test_first_sentence_extracts_sentence(self) -> None:
        self.assertEqual(first_sentence("Alpha beta. Gamma delta."), "Alpha beta.")

    def test_summary_from_body_skips_headings_and_code(self) -> None:
        body = "# Title\n\n```bash\necho hi\n```\n\nFirst useful sentence. Second one.\n"
        self.assertEqual(summary_from_body(body), "First useful sentence.")


if __name__ == "__main__":
    unittest.main()
