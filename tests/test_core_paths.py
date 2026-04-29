from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts.core.paths import relative_link, relative_to_tool, relative_to_workspace, slugify, tool_root, trim, workspace_root


class PathsTests(unittest.TestCase):
    def test_slugify_normalizes_titles(self) -> None:
        self.assertEqual(slugify("  Hello, World!  "), "hello-world")
        self.assertEqual(slugify("***"), "note")

    def test_trim_collapses_whitespace(self) -> None:
        self.assertEqual(trim("  many\n words\t here  "), "many words here")

    def test_relative_link_uses_forward_slashes(self) -> None:
        source = Path("docs/knowledge/linux/index.md")
        target = Path("docs/operations/index.md")

        self.assertEqual(relative_link(source, target), "../../operations/index.md")

    def test_workspace_root_defaults_to_tool_root(self) -> None:
        with patch.dict("os.environ", {}, clear=True):
            self.assertEqual(workspace_root(), tool_root())

    def test_workspace_root_uses_external_workspace_when_set(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir, patch.dict("os.environ", {"WORKSPACE": tmp_dir}, clear=True):
            self.assertEqual(workspace_root(), Path(tmp_dir).resolve())

    def test_relative_to_workspace_hides_external_workspace_prefix(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir, patch.dict("os.environ", {"WORKSPACE": tmp_dir}, clear=True):
            source = Path(tmp_dir) / "sources" / "notes" / "example.md"
            self.assertEqual(relative_to_workspace(source), "sources/notes/example.md")
            self.assertEqual(relative_to_tool(source), source.resolve().as_posix())


if __name__ == "__main__":
    unittest.main()
