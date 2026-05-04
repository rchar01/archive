from __future__ import annotations

import os
import subprocess
import tempfile
import unittest
from pathlib import Path

from scripts.core.frontmatter import read_markdown


class ArchiveCliSurfaceTests(unittest.TestCase):
    def repo_root(self) -> Path:
        return Path(__file__).resolve().parents[1]

    def cli_path(self) -> Path:
        return self.repo_root() / "scripts" / "cli" / "archive.py"

    def install_script(self) -> Path:
        return self.repo_root() / "scripts" / "install-cli"

    def make_workspace(self, root: Path) -> Path:
        for rel_path in (
            Path("incoming") / "new",
            Path("incoming") / "review",
            Path("sources") / "notes",
            Path("sources") / "docs",
        ):
            (root / rel_path).mkdir(parents=True, exist_ok=True)
        return root

    def run_cli(self, *args: str, cwd: Path, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["python3", str(self.cli_path()), *args],
            cwd=cwd,
            env={**os.environ, **(env or {})},
            capture_output=True,
            text=True,
        )

    def test_import_infers_workspace_from_current_directory(self) -> None:
        with tempfile.TemporaryDirectory() as workspace_dir, tempfile.TemporaryDirectory() as raw_dir:
            workspace = self.make_workspace(Path(workspace_dir))
            raw_path = Path(raw_dir) / "dns-notes.md"
            raw_path.write_text("Containers can reach IPs but fail to resolve names.\n")

            result = self.run_cli(
                "import",
                str(raw_path),
                "--kind",
                "doc",
                "--section",
                "networking",
                cwd=workspace,
            )

            self.assertEqual(result.returncode, 0, msg=result.stderr)
            target = workspace / "incoming" / "new" / "dns-notes.md"
            self.assertEqual(result.stdout.strip(), "incoming/new/dns-notes.md")
            self.assertTrue(target.exists())
            document = read_markdown(target)
            self.assertEqual(document.frontmatter["title"], "Dns Notes")
            self.assertEqual(document.frontmatter["kind"], "doc")
            self.assertEqual(document.frontmatter["section"], "networking")
            self.assertEqual(document.frontmatter["processing"], "review")
            self.assertEqual(document.frontmatter["tags"], [])
            self.assertIn("Containers can reach IPs", document.body)

    def test_import_requires_workspace_when_not_in_workspace(self) -> None:
        with tempfile.TemporaryDirectory() as cwd_dir, tempfile.TemporaryDirectory() as raw_dir:
            raw_path = Path(raw_dir) / "raw.md"
            raw_path.write_text("hello\n")

            result = self.run_cli("import", str(raw_path), "--kind", "note", cwd=Path(cwd_dir))

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("Could not infer workspace", result.stderr)

    def test_install_script_writes_archive_launcher(self) -> None:
        with tempfile.TemporaryDirectory(dir=self.repo_root()) as bin_dir:
            target = Path(bin_dir) / "archive"
            result = subprocess.run(
                ["bash", str(self.install_script())],
                cwd=self.repo_root(),
                env={**os.environ, "BIN_DIR": bin_dir},
                capture_output=True,
                text=True,
            )

            self.assertEqual(result.returncode, 0, msg=result.stderr)
            self.assertEqual(result.stdout.strip(), str(target))
            self.assertTrue(target.exists())
            help_result = subprocess.run([str(target), "--help"], capture_output=True, text=True)
            self.assertEqual(help_result.returncode, 0, msg=help_result.stderr)
            self.assertIn("Archive authoring CLI", help_result.stdout)


if __name__ == "__main__":
    unittest.main()
