from __future__ import annotations

import os
import re
import subprocess
import tempfile
import unittest
from pathlib import Path


class RuntimeSurfaceTests(unittest.TestCase):
    def repo_root(self) -> Path:
        return Path(__file__).resolve().parents[1]

    def source_container_runtime(self, workspace: str, *, archive_instance: str | None = None) -> list[str]:
        script = self.repo_root() / "scripts" / "runtime" / "_container.sh"
        env = {**os.environ, "WORKSPACE": workspace}
        if archive_instance is not None:
            env["ARCHIVE_INSTANCE"] = archive_instance
        result = subprocess.run(
            [
                "bash",
                "-lc",
                (
                    f'source "{script}"; '
                    'printf "%s\\n" '
                    '"$HOST_WORKSPACE" "$CONTAINER_WORKSPACE" "$ARCHIVE_INSTANCE" '
                    '"$DEV_CONTAINER_NAME" "$RUNTIME_CONTAINER_NAME" "$SITE_DIR" "$BUILD_DIR" "$RUNTIME_BUILD_CONTEXT_ROOT"; '
                    'printf "%s\\n" "${WORKSPACE_VOLUME_ARGS[@]}"'
                ),
            ],
            cwd=self.repo_root(),
            env=env,
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
            "install-cli:",
            "install-skill:",
            "init-workspace:",
            "runtime-build:",
            "runtime-run:",
            "runtime-logs:",
            "runtime-status:",
            "runtime-stop:",
            "uninstall-skill:",
        ):
            self.assertIn(target, makefile)

    def test_makefile_defaults_and_exports_workspace(self) -> None:
        makefile = (self.repo_root() / "Makefile").read_text()

        self.assertIn("WORKSPACE ?= .", makefile)
        self.assertIn("ARCHIVE_INSTANCE ?=", makefile)
        self.assertIn("export WORKSPACE ARCHIVE_INSTANCE", makefile)

    def test_container_runtime_uses_repo_workspace_path_in_standalone_mode(self) -> None:
        lines = self.source_container_runtime(".")

        self.assertEqual(lines[0], str(self.repo_root().resolve()))
        self.assertEqual(lines[1], "/workspace")
        self.assertEqual(lines[2], "default")
        self.assertEqual(lines[3], "archive-dev-server")
        self.assertEqual(lines[4], "archive-runtime")
        self.assertEqual(lines[5], str((self.repo_root() / "site").resolve()))
        self.assertEqual(lines[6], str((self.repo_root() / "build").resolve()))
        self.assertEqual(lines[7], str((self.repo_root() / "build" / "runtime-image").resolve()))
        self.assertEqual(lines[8:], ["-v", f"{self.repo_root().resolve()}:/workspace:z"])

    def test_container_runtime_mounts_external_workspace_separately(self) -> None:
        with tempfile.TemporaryDirectory() as workspace_dir:
            lines = self.source_container_runtime(workspace_dir)

        instance_name = re.sub(r"[^A-Za-z0-9]+", "-", Path(workspace_dir).resolve().name.lower()).strip("-")
        self.assertEqual(lines[0], str(Path(workspace_dir).resolve()))
        self.assertEqual(lines[1], "/workspace-workspace")
        self.assertEqual(lines[2], instance_name)
        self.assertEqual(lines[3], f"archive-dev-server-{instance_name}")
        self.assertEqual(lines[4], f"archive-runtime-{instance_name}")
        self.assertEqual(lines[5], str((self.repo_root() / ".instances" / instance_name / "site").resolve()))
        self.assertEqual(lines[6], str((self.repo_root() / ".instances" / instance_name / "build").resolve()))
        self.assertEqual(
            lines[7],
            str((self.repo_root() / ".instances" / instance_name / "build" / "runtime-image").resolve()),
        )
        self.assertEqual(
            lines[8:],
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
        self.assertEqual(lines[2], "runtime-test-workspace")
        self.assertEqual(lines[8:], ["-v", f"{self.repo_root().resolve()}:/workspace:z"])

    def test_container_runtime_allows_explicit_archive_instance_override(self) -> None:
        with tempfile.TemporaryDirectory() as workspace_dir:
            lines = self.source_container_runtime(workspace_dir, archive_instance="Lab A")

        self.assertEqual(lines[2], "lab-a")
        self.assertEqual(lines[3], "archive-dev-server-lab-a")
        self.assertEqual(lines[4], "archive-runtime-lab-a")

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

    def test_gitignore_excludes_generated_runtime_build_context(self) -> None:
        gitignore = (self.repo_root() / ".gitignore").read_text()

        self.assertIn("build/runtime-image/", gitignore)
        self.assertIn(".instances/", gitignore)
        self.assertIn(".vitepress/nav.generated.json", gitignore)

    def test_theme_mounts_outline_auto_scroll_helper(self) -> None:
        theme_index = (self.repo_root() / ".vitepress" / "theme" / "index.ts").read_text()
        helper = (self.repo_root() / ".vitepress" / "theme" / "OutlineAutoScroll.ts").read_text()

        self.assertIn("import OutlineAutoScroll from './OutlineAutoScroll'", theme_index)
        self.assertIn("'aside-outline-after': () => h(OutlineAutoScroll)", theme_index)
        self.assertIn("scrollActiveOutlineIntoView", helper)
        self.assertIn(".VPDocAsideOutline .outline-link.active", helper)
        self.assertIn("easeOutCubic", helper)
        self.assertIn("requestAnimationFrame(step)", helper)
        self.assertIn("ANIMATION_DURATION_MS = 340", helper)


if __name__ == "__main__":
    unittest.main()
