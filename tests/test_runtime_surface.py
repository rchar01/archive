from __future__ import annotations

import os
import subprocess
import tempfile
import unittest
from pathlib import Path


class RuntimeSurfaceTests(unittest.TestCase):
    def repo_root(self) -> Path:
        return Path(__file__).resolve().parents[1]

    def source_container_runtime(self, workspace: str) -> list[str]:
        script = self.repo_root() / "scripts" / "runtime" / "_container.sh"
        result = subprocess.run(
            [
                "bash",
                "-lc",
                f'source "{script}"; printf "%s\\n" "$HOST_WORKSPACE" "$CONTAINER_WORKSPACE"; printf "%s\\n" "${{WORKSPACE_VOLUME_ARGS[@]}}"',
            ],
            cwd=self.repo_root(),
            env={**os.environ, "WORKSPACE": workspace},
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout.splitlines()

    def prepare_runtime_context(self, *, site_dir: Path, build_dir: Path) -> tuple[subprocess.CompletedProcess[str], Path]:
        script = self.repo_root() / "scripts" / "runtime" / "_container.sh"
        result = subprocess.run(
            ["bash", "-lc", f'source "{script}"; prepare_runtime_build_context'],
            cwd=self.repo_root(),
            env={
                **os.environ,
                "SITE_DIR": str(site_dir),
                "BUILD_DIR": str(build_dir),
                "RUNTIME_BUILD_CONTEXT_ROOT": str(build_dir / "runtime-image"),
            },
            capture_output=True,
            text=True,
        )
        return result, build_dir / "runtime-image"

    def test_makefile_exposes_dev_and_runtime_lifecycle_targets(self) -> None:
        makefile = (self.repo_root() / "Makefile").read_text()

        for target in (
            "build-linkgraph:",
            "build-related:",
            "dev-bg:",
            "dev-logs:",
            "dev-status:",
            "dev-stop:",
            "init-workspace:",
            "runtime-build:",
            "runtime-run:",
            "runtime-logs:",
            "runtime-status:",
            "runtime-stop:",
        ):
            self.assertIn(target, makefile)

    def test_makefile_defaults_and_exports_workspace(self) -> None:
        makefile = (self.repo_root() / "Makefile").read_text()

        self.assertIn("WORKSPACE ?= .", makefile)
        self.assertIn("export WORKSPACE", makefile)

    def test_container_runtime_uses_repo_workspace_path_in_standalone_mode(self) -> None:
        lines = self.source_container_runtime(".")

        self.assertEqual(lines[0], str(self.repo_root().resolve()))
        self.assertEqual(lines[1], "/workspace")
        self.assertEqual(lines[2:], ["-v", f"{self.repo_root().resolve()}:/workspace:z"])

    def test_container_runtime_mounts_external_workspace_separately(self) -> None:
        with tempfile.TemporaryDirectory() as workspace_dir:
            lines = self.source_container_runtime(workspace_dir)

        self.assertEqual(lines[0], str(Path(workspace_dir).resolve()))
        self.assertEqual(lines[1], "/workspace-workspace")
        self.assertEqual(
            lines[2:],
            [
                "-v",
                f"{self.repo_root().resolve()}:/workspace:z",
                "-v",
                f"{Path(workspace_dir).resolve()}:/workspace-workspace:z",
            ],
        )

    def test_container_runtime_resolves_missing_relative_workspace_inside_repo(self) -> None:
        lines = self.source_container_runtime(".runtime-test-workspace")

        self.assertEqual(lines[0], str((self.repo_root() / ".runtime-test-workspace").resolve()))
        self.assertEqual(lines[1], "/workspace/.runtime-test-workspace")
        self.assertEqual(lines[2:], ["-v", f"{self.repo_root().resolve()}:/workspace:z"])

    def test_runtime_build_context_packages_prebuilt_site_only(self) -> None:
        with tempfile.TemporaryDirectory() as site_dir, tempfile.TemporaryDirectory() as build_dir:
            site_root = Path(site_dir)
            (site_root / "index.html").write_text("<html><body>Archive</body></html>\n")
            (site_root / "assets").mkdir()
            (site_root / "assets" / "app.js").write_text("console.log('archive');\n")

            result, context_root = self.prepare_runtime_context(site_dir=site_root, build_dir=Path(build_dir))

            self.assertEqual(result.returncode, 0, msg=result.stderr)
            self.assertEqual(result.stdout.strip(), str(context_root))
            self.assertTrue((context_root / "Containerfile.runtime").exists())
            self.assertTrue((context_root / "Caddyfile.runtime").exists())
            self.assertTrue((context_root / "site" / "index.html").exists())
            self.assertTrue((context_root / "site" / "assets" / "app.js").exists())

    def test_runtime_build_context_requires_prebuilt_site(self) -> None:
        with tempfile.TemporaryDirectory() as site_dir, tempfile.TemporaryDirectory() as build_dir:
            result, _ = self.prepare_runtime_context(site_dir=Path(site_dir), build_dir=Path(build_dir))

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("run make build first", result.stderr)

    def test_runtime_containerfile_packages_prebuilt_site_with_caddy(self) -> None:
        containerfile = (self.repo_root() / "Containerfile.runtime").read_text()
        caddyfile = (self.repo_root() / "Caddyfile.runtime").read_text()
        containerignore = (self.repo_root() / ".containerignore").read_text()
        package_json = (self.repo_root() / "package.json").read_text()

        self.assertIn("FROM docker.io/library/caddy:2-alpine", containerfile)
        self.assertIn("COPY Caddyfile.runtime /etc/caddy/Caddyfile", containerfile)
        self.assertIn("COPY site/ /usr/share/caddy/", containerfile)
        self.assertNotIn("npm run docs:build", containerfile)
        self.assertNotIn("python3 scripts/tasks/build_content.py", containerfile)
        self.assertIn("try_files {path} {path}.html {path}/index.html =404", caddyfile)
        self.assertIn("incoming/", containerignore)
        self.assertIn('"mermaid":', package_json)


if __name__ == "__main__":
    unittest.main()
