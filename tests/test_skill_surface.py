from __future__ import annotations

import os
import subprocess
import tempfile
import unittest
from pathlib import Path


class ArchiveSkillSurfaceTests(unittest.TestCase):
    def repo_root(self) -> Path:
        return Path(__file__).resolve().parents[1]

    def test_install_and_uninstall_skill_scripts_manage_archive_authoring(self) -> None:
        install_script = self.repo_root() / "scripts" / "install-skill"
        uninstall_script = self.repo_root() / "scripts" / "uninstall-skill"

        with tempfile.TemporaryDirectory(dir=self.repo_root()) as skills_dir:
            env = {**os.environ, "SKILLS_DIR": skills_dir}
            target = Path(skills_dir) / "archive-authoring"

            install = subprocess.run(["bash", str(install_script)], cwd=self.repo_root(), env=env, capture_output=True, text=True)
            self.assertEqual(install.returncode, 0, msg=install.stderr)
            self.assertEqual(install.stdout.strip(), str(target))
            self.assertTrue((target / "SKILL.md").exists())
            self.assertIn("name: archive-authoring", (target / "SKILL.md").read_text())

            uninstall = subprocess.run(["bash", str(uninstall_script)], cwd=self.repo_root(), env=env, capture_output=True, text=True)
            self.assertEqual(uninstall.returncode, 0, msg=uninstall.stderr)
            self.assertEqual(uninstall.stdout.strip(), str(target))
            self.assertFalse(target.exists())


if __name__ == "__main__":
    unittest.main()
