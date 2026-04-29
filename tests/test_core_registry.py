from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts.core.paths import tool_root
from scripts.core.registry import discover_workflows, get_workflow


class RegistryTests(unittest.TestCase):
    def test_discovers_shipped_workflows(self) -> None:
        workflows = discover_workflows()

        self.assertIn("note", workflows)
        self.assertIn("doc", workflows)
        self.assertEqual(workflows["note"].label, "Notes")
        self.assertEqual(workflows["doc"].label, "Docs")
        self.assertEqual(workflows["note"].knowledge_panel, True)
        self.assertEqual(workflows["note"].backlinks, True)
        self.assertEqual(workflows["note"].related, True)

    def test_workflow_paths_and_templates_exist(self) -> None:
        note = get_workflow("note")
        doc = get_workflow("doc")

        self.assertTrue(note.config_path.exists())
        self.assertTrue(note.template_path.exists())
        self.assertTrue(doc.config_path.exists())
        self.assertTrue(doc.template_path.exists())

    def test_source_roots_follow_workspace_but_output_roots_stay_in_tool_repo(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir, patch.dict("os.environ", {"WORKSPACE": tmp_dir}, clear=True):
            workflows = discover_workflows()

        note = workflows["note"]
        self.assertEqual(note.source_root, Path(tmp_dir).resolve() / "sources" / "notes")
        self.assertEqual(note.output_root, tool_root() / "content" / "notes")


if __name__ == "__main__":
    unittest.main()
