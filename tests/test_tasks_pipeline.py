from __future__ import annotations

import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

from scripts.core.io import read_json
from scripts.core.frontmatter import MarkdownDocument, read_markdown, write_markdown
from scripts.core.registry import WorkflowDefinition, get_workflow
from scripts.core.validation import ValidationError
from scripts.tasks import (
    accept_review,
    build_content,
    build_indexes,
    build_linkgraph,
    build_related,
    build_sidebar,
    init_workspace,
    new_entry,
    process_incoming,
    validate_sources,
)


class TaskPipelineTests(unittest.TestCase):
    def make_workflow(self, root: Path, kind: str) -> WorkflowDefinition:
        actual = get_workflow(kind)
        return WorkflowDefinition(
            kind=actual.kind,
            label=actual.label,
            source_root=root / actual.source_root.relative_to(actual.source_root.parents[1]),
            output_root=root / actual.output_root.relative_to(actual.output_root.parents[1]),
            default_section=actual.default_section,
            required_sections=actual.required_sections,
            knowledge_panel=actual.knowledge_panel,
            backlinks=actual.backlinks,
            related=actual.related,
            workflow_dir=actual.workflow_dir,
        )

    def test_new_entry_creates_canonical_source_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            workflow = self.make_workflow(root, "note")

            with patch("scripts.tasks.new_entry.get_workflow", return_value=workflow):
                new_entry.main(["--kind", "note", "--title", "Docker DNS Issue", "--section", "containers"])

            target = workflow.source_path_for("Docker DNS Issue", "containers")
            self.assertTrue(target.exists())
            frontmatter, body = read_markdown(target).frontmatter, read_markdown(target).body
            self.assertEqual(frontmatter["kind"], "note")
            self.assertIn("## Summary", body)
            self.assertNotIn("## Details", body)

    def test_new_entry_prints_workspace_relative_path(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            workflow = self.make_workflow(root, "note")
            output = io.StringIO()

            with patch.dict("os.environ", {"WORKSPACE": tmp_dir}, clear=True), patch(
                "scripts.tasks.new_entry.get_workflow", return_value=workflow
            ), redirect_stdout(output):
                new_entry.main(["--kind", "note", "--title", "Docker DNS Issue", "--section", "containers"])

            self.assertEqual(output.getvalue().strip(), "sources/notes/containers/docker-dns-issue.md")

    def test_new_entry_accepts_optional_metadata_flags(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            workflow = self.make_workflow(root, "doc")

            with patch("scripts.tasks.new_entry.get_workflow", return_value=workflow):
                new_entry.main(
                    [
                        "--kind",
                        "doc",
                        "--title",
                        "Homelab Firewall",
                        "--section",
                        "homelab/networking",
                        "--slug",
                        "edge-firewall",
                        "--nav-title",
                        "Edge Firewall",
                        "--summary",
                        "Firewall overview and operating notes.",
                        "--priority",
                        "high",
                        "--tags",
                        "firewall, homelab, networking",
                        "--related-manual",
                        "/docs/networking/dns-basics, /notes/homelab/router-checklist",
                        "--hide-knowledge-panel",
                        "--hide-backlinks",
                        "--hide-related",
                    ]
                )

            target = workflow.source_path_for("Homelab Firewall", "homelab/networking")
            saved = read_markdown(target)
            self.assertEqual(saved.frontmatter["slug"], "edge-firewall")
            self.assertEqual(saved.frontmatter["nav_title"], "Edge Firewall")
            self.assertEqual(saved.frontmatter["summary"], "Firewall overview and operating notes.")
            self.assertEqual(saved.frontmatter["priority"], "high")
            self.assertEqual(saved.frontmatter["tags"], ["firewall", "homelab", "networking"])
            self.assertEqual(
                saved.frontmatter["related_manual"],
                ["/docs/networking/dns-basics", "/notes/homelab/router-checklist"],
            )
            self.assertEqual(saved.frontmatter["hide_knowledge_panel"], True)
            self.assertEqual(saved.frontmatter["hide_backlinks"], True)
            self.assertEqual(saved.frontmatter["hide_related"], True)
            self.assertIn("## Overview", saved.body)
            self.assertNotIn("## Details", saved.body)

    def test_new_entry_rejects_invalid_slug(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            workflow = self.make_workflow(root, "note")

            with patch("scripts.tasks.new_entry.get_workflow", return_value=workflow):
                with self.assertRaises(ValidationError):
                    new_entry.main(["--kind", "note", "--title", "Docker DNS Issue", "--slug", "Bad Slug"])

    def test_new_entry_deduplicates_comma_separated_list_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            workflow = self.make_workflow(root, "note")

            with patch("scripts.tasks.new_entry.get_workflow", return_value=workflow):
                new_entry.main(
                    [
                        "--kind",
                        "note",
                        "--title",
                        "Docker DNS Issue",
                        "--tags",
                        "docker, dns, docker, dns",
                        "--related-manual",
                        "/docs/networking/dns-basics, /docs/networking/dns-basics",
                        "--related-manual",
                        "/notes/testing/docker-dns-issue",
                    ]
                )

            target = workflow.source_path_for("Docker DNS Issue", workflow.default_section)
            saved = read_markdown(target)
            self.assertEqual(saved.frontmatter["tags"], ["docker", "dns"])
            self.assertEqual(
                saved.frontmatter["related_manual"],
                ["/docs/networking/dns-basics", "/notes/testing/docker-dns-issue"],
            )

    def test_init_workspace_creates_workspace_skeleton_and_templates(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            workspace_root = Path(tmp_dir) / "workspace"
            output = io.StringIO()

            with redirect_stdout(output):
                init_workspace.main([str(workspace_root)])

            self.assertEqual(output.getvalue().strip(), str(workspace_root.resolve()))
            self.assertTrue((workspace_root / "incoming" / "new").is_dir())
            self.assertTrue((workspace_root / "incoming" / "review").is_dir())
            self.assertTrue((workspace_root / "sources" / "notes").is_dir())
            self.assertTrue((workspace_root / "sources" / "docs").is_dir())
            self.assertIn("ARCHIVE_DIR ?= ../archive", (workspace_root / "Makefile").read_text())
            self.assertIn('WORKSPACE := $(CURDIR)', (workspace_root / "Makefile").read_text())
            self.assertIn('ARCHIVE_INSTANCE ?= $(notdir $(CURDIR))', (workspace_root / "Makefile").read_text())
            self.assertIn("help:", (workspace_root / "Makefile").read_text())
            self.assertIn(
                '$(MAKE) -C $(ARCHIVE_DIR) WORKSPACE="$(WORKSPACE)" ARCHIVE_INSTANCE="$(ARCHIVE_INSTANCE)" help',
                (workspace_root / "Makefile").read_text(),
            )
            self.assertIn("canonical Archive content", (workspace_root / "README.md").read_text())
            self.assertIn("Archive workspace repo", (workspace_root / "AGENTS.md").read_text())
            self.assertIn("Use Available Specialist Tools", (workspace_root / "AGENTS.md").read_text())
            self.assertIn(".DS_Store", (workspace_root / ".gitignore").read_text())

    def test_init_workspace_preserves_existing_templates_and_canonical_docs_without_force(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            workspace_root = Path(tmp_dir) / "workspace"
            canonical_doc = workspace_root / "sources" / "docs" / "homelab" / "dns.md"
            canonical_doc.parent.mkdir(parents=True, exist_ok=True)
            canonical_doc.write_text("# DNS\n")
            (workspace_root / "README.md").write_text("existing\n")
            (workspace_root / "AGENTS.md").write_text("custom-agents\n")
            (workspace_root / "Makefile").write_text("custom-makefile\n")
            (workspace_root / ".gitignore").write_text("custom-ignore\n")

            init_workspace.main([str(workspace_root)])

            self.assertEqual((workspace_root / "README.md").read_text(), "existing\n")
            self.assertEqual((workspace_root / "AGENTS.md").read_text(), "custom-agents\n")
            self.assertEqual((workspace_root / "Makefile").read_text(), "custom-makefile\n")
            self.assertEqual((workspace_root / ".gitignore").read_text(), "custom-ignore\n")
            self.assertEqual(canonical_doc.read_text(), "# DNS\n")
            self.assertTrue((workspace_root / "incoming" / "new").is_dir())
            self.assertTrue((workspace_root / "incoming" / "review").is_dir())
            self.assertTrue((workspace_root / "sources" / "notes").is_dir())

    def test_init_workspace_force_overwrites_root_templates_only(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            workspace_root = Path(tmp_dir) / "workspace"
            canonical_doc = workspace_root / "sources" / "docs" / "homelab" / "dns.md"
            canonical_doc.parent.mkdir(parents=True, exist_ok=True)
            canonical_doc.write_text("# DNS\n")
            (workspace_root / "README.md").write_text("existing\n")
            (workspace_root / "AGENTS.md").write_text("custom-agents\n")
            (workspace_root / "Makefile").write_text("custom-makefile\n")
            (workspace_root / ".gitignore").write_text("custom-ignore\n")

            init_workspace.main(["--force", str(workspace_root)])

            self.assertIn("canonical Archive content", (workspace_root / "README.md").read_text())
            self.assertIn("Archive workspace repo", (workspace_root / "AGENTS.md").read_text())
            self.assertIn("ARCHIVE_DIR ?= ../archive", (workspace_root / "Makefile").read_text())
            self.assertIn(".DS_Store", (workspace_root / ".gitignore").read_text())
            self.assertEqual(canonical_doc.read_text(), "# DNS\n")

    def test_process_incoming_auto_writes_to_sources(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            incoming_dir = root / "incoming" / "new"
            incoming_dir.mkdir(parents=True)
            workflow = self.make_workflow(root, "note")

            write_markdown(
                incoming_dir / "docker-dns.md",
                MarkdownDocument(
                    frontmatter={
                        "title": "Docker DNS Issue",
                        "kind": "note",
                        "section": "containers",
                        "processing": "auto",
                        "tags": ["docker", "dns"],
                        "related_manual": ["/docs/networking/dns-basics"],
                        "hide_backlinks": True,
                        "summary": "Incoming summary.",
                    },
                    body="Containers can reach IPs but fail to resolve names.\n",
                ),
            )

            with patch("scripts.tasks.process_incoming.get_workflow", return_value=workflow), patch(
                "scripts.tasks.process_incoming.write_json_report"
            ):
                process_incoming.main([str(incoming_dir)])

            target = workflow.source_path_for("Docker DNS Issue", "containers")
            self.assertTrue(target.exists())
            self.assertFalse((incoming_dir / "docker-dns.md").exists())
            saved = read_markdown(target)
            self.assertEqual(saved.frontmatter["related_manual"], ["/docs/networking/dns-basics"])
            self.assertEqual(saved.frontmatter["hide_backlinks"], True)
            self.assertEqual(saved.frontmatter["summary"], "Incoming summary.")

    def test_process_incoming_review_then_accept_review(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            incoming_dir = root / "incoming" / "new"
            review_dir = root / "incoming" / "review"
            incoming_dir.mkdir(parents=True)
            workflow = self.make_workflow(root, "doc")

            write_markdown(
                incoming_dir / "homelab-firewall.md",
                MarkdownDocument(
                    frontmatter={
                        "title": "Homelab Firewall",
                        "kind": "doc",
                        "section": "homelab/networking",
                        "processing": "review",
                        "tags": ["firewall"],
                    },
                    body="The firewall protects the homelab network.\n",
                ),
            )

            with patch("scripts.tasks.process_incoming.get_workflow", return_value=workflow), patch(
                "scripts.tasks.process_incoming.write_json_report"
            ), patch("scripts.tasks.accept_review.get_workflow", return_value=workflow):
                process_incoming.main([str(incoming_dir)])
                review_path = review_dir / "homelab-firewall.md"
                self.assertTrue(review_path.exists())
                accept_review.main([str(review_path)])

            target = workflow.source_path_for("Homelab Firewall", "homelab/networking")
            self.assertTrue(target.exists())
            self.assertFalse((review_dir / "homelab-firewall.md").exists())

    def test_process_incoming_uses_workspace_default_path(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            incoming_dir = root / "incoming" / "new"
            incoming_dir.mkdir(parents=True)
            workflow = self.make_workflow(root, "note")

            write_markdown(
                incoming_dir / "docker-dns.md",
                MarkdownDocument(
                    frontmatter={
                        "title": "Docker DNS Issue",
                        "kind": "note",
                        "section": "containers",
                        "processing": "auto",
                        "tags": ["docker"],
                    },
                    body="Containers can reach IPs but fail to resolve names.\n",
                ),
            )

            with patch.dict("os.environ", {"WORKSPACE": tmp_dir}, clear=True), patch(
                "scripts.tasks.process_incoming.get_workflow", return_value=workflow
            ), patch("scripts.tasks.process_incoming.write_json_report"):
                process_incoming.main([])

            self.assertTrue(workflow.source_path_for("Docker DNS Issue", "containers").exists())

    def test_accept_review_resolves_workspace_relative_file_argument(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            review_dir = root / "incoming" / "review"
            review_dir.mkdir(parents=True)
            workflow = self.make_workflow(root, "doc")

            write_markdown(
                review_dir / "homelab-firewall.md",
                MarkdownDocument(
                    frontmatter={
                        "title": "Homelab Firewall",
                        "kind": "doc",
                        "section": "homelab/networking",
                        "tags": ["firewall"],
                    },
                    body="The firewall protects the homelab network.\n",
                ),
            )

            with patch.dict("os.environ", {"WORKSPACE": tmp_dir}, clear=True), patch(
                "scripts.tasks.accept_review.get_workflow", return_value=workflow
            ):
                accept_review.main(["incoming/review/homelab-firewall.md"])

            self.assertTrue(workflow.source_path_for("Homelab Firewall", "homelab/networking").exists())
            self.assertFalse((review_dir / "homelab-firewall.md").exists())

    def test_private_workspace_flow_keeps_sources_in_workspace_and_generated_output_in_tool_root(self) -> None:
        with tempfile.TemporaryDirectory() as workspace_dir, tempfile.TemporaryDirectory() as tool_dir:
            workspace_root = Path(workspace_dir)
            tool_root = Path(tool_dir)
            note_actual = get_workflow("note")
            note_workflow = WorkflowDefinition(
                kind=note_actual.kind,
                label=note_actual.label,
                source_root=workspace_root / "sources" / "notes",
                output_root=tool_root / "content" / "notes",
                default_section=note_actual.default_section,
                required_sections=note_actual.required_sections,
                knowledge_panel=note_actual.knowledge_panel,
                backlinks=note_actual.backlinks,
                related=note_actual.related,
                workflow_dir=note_actual.workflow_dir,
            )
            workflows = {"note": note_workflow}
            knowledge_dir = tool_root / ".vitepress" / "knowledge"
            generated_vitepress_dir = tool_root / ".vitepress"

            init_workspace.main([workspace_dir])

            with patch.dict("os.environ", {"WORKSPACE": workspace_dir}, clear=True), patch(
                "scripts.tasks.new_entry.get_workflow", return_value=note_workflow
            ):
                new_entry.main(["--kind", "note", "--title", "Docker DNS Issue", "--section", "containers"])

            write_markdown(
                workspace_root / "incoming" / "new" / "vlan-tagging.md",
                MarkdownDocument(
                    frontmatter={
                        "title": "VLAN Tagging",
                        "kind": "note",
                        "section": "networking",
                        "processing": "auto",
                        "tags": ["networking"],
                    },
                    body="Tagged interfaces need matching switch configuration.\n",
                ),
            )

            with patch.dict("os.environ", {"WORKSPACE": workspace_dir}, clear=True), patch(
                "scripts.tasks.process_incoming.get_workflow", return_value=note_workflow
            ), patch("scripts.tasks.process_incoming.write_json_report"), patch(
                "scripts.tasks.validate_sources.discover_workflows", return_value=workflows
            ), patch("scripts.tasks.validate_sources.write_json_report"), patch(
                "scripts.tasks.build_content.discover_workflows", return_value=workflows
            ), patch("scripts.tasks.build_content.write_json_report"), patch(
                "scripts.tasks.build_linkgraph.discover_workflows", return_value=workflows
            ), patch("scripts.tasks.build_linkgraph.KNOWLEDGE_DIR", knowledge_dir), patch(
                "scripts.tasks.build_related.KNOWLEDGE_DIR", knowledge_dir
            ), patch("scripts.tasks.build_indexes.CONTENT_DIR", tool_root / "content"), patch(
                "scripts.tasks.build_indexes.discover_workflows", return_value=workflows
            ), patch("scripts.tasks.build_sidebar.CONTENT_DIR", tool_root / "content"), patch(
                "scripts.tasks.build_sidebar.discover_workflows", return_value=workflows
            ), patch("scripts.tasks.build_sidebar.GENERATED_VITEPRESS_DIR", generated_vitepress_dir):
                process_incoming.main([])
                validate_sources.main([])
                build_content.main([])
                build_linkgraph.main([])
                build_related.main([])
                build_indexes.main([])
                build_sidebar.main([])

            self.assertTrue((workspace_root / "sources" / "notes" / "containers" / "docker-dns-issue.md").exists())
            self.assertTrue((workspace_root / "sources" / "notes" / "networking" / "vlan-tagging.md").exists())
            self.assertFalse((workspace_root / "incoming" / "new" / "vlan-tagging.md").exists())
            self.assertFalse((workspace_root / "content").exists())
            self.assertFalse((workspace_root / ".vitepress").exists())

            generated_note = tool_root / "content" / "notes" / "containers" / "docker-dns-issue.md"
            generated_vlan = tool_root / "content" / "notes" / "networking" / "vlan-tagging.md"
            self.assertTrue(generated_note.exists())
            self.assertTrue(generated_vlan.exists())
            self.assertTrue((tool_root / "content" / "index.md").exists())
            self.assertTrue((tool_root / "content" / "notes" / "index.md").exists())
            self.assertTrue((generated_vitepress_dir / "nav.generated.ts").exists())
            self.assertTrue((generated_vitepress_dir / "sidebar.generated.ts").exists())
            self.assertTrue((knowledge_dir / "pages.generated.json").exists())
            self.assertTrue((knowledge_dir / "linkgraph.generated.json").exists())
            self.assertTrue((knowledge_dir / "related.generated.json").exists())
            self.assertIn("source_path: sources/notes/containers/docker-dns-issue.md", generated_note.read_text())
            self.assertIn("source_path: sources/notes/networking/vlan-tagging.md", generated_vlan.read_text())

    def test_validate_sources_rejects_duplicate_output_paths(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            workflow = self.make_workflow(root, "note")
            workflow.source_root.mkdir(parents=True)

            duplicate_one = workflow.source_root / "containers" / "first.md"
            duplicate_two = workflow.source_root / "containers" / "second.md"
            write_markdown(
                duplicate_one,
                MarkdownDocument(
                    frontmatter={
                        "id": "id-1",
                        "title": "Docker DNS Issue",
                        "kind": "note",
                        "section": "containers",
                        "status": "draft",
                        "tags": [],
                        "created": "2026-04-24",
                        "updated": "2026-04-24",
                    },
                    body="# Docker DNS Issue\n\n## Summary\n\nOne.\n\n## Details\n\nTwo.\n\n## Related\n",
                ),
            )
            write_markdown(
                duplicate_two,
                MarkdownDocument(
                    frontmatter={
                        "id": "id-2",
                        "title": "Docker DNS Issue",
                        "kind": "note",
                        "section": "containers",
                        "status": "draft",
                        "tags": [],
                        "created": "2026-04-24",
                        "updated": "2026-04-24",
                    },
                    body="# Docker DNS Issue\n\n## Summary\n\nOne.\n\n## Details\n\nTwo.\n\n## Related\n",
                ),
            )

            with patch("scripts.tasks.validate_sources.discover_workflows", return_value={"note": workflow}), patch(
                "scripts.tasks.validate_sources.write_json_report"
            ):
                with self.assertRaises(Exception):
                    validate_sources.main([])

    def test_validate_sources_rejects_thematic_break_immediately_before_h2(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            workflow = self.make_workflow(root, "note")
            workflow.source_root.mkdir(parents=True)

            target = workflow.source_root / "containers" / "docker-dns-issue.md"
            write_markdown(
                target,
                MarkdownDocument(
                    frontmatter={
                        "id": "20260424T103000",
                        "title": "Docker DNS Issue",
                        "kind": "note",
                        "section": "containers",
                        "status": "draft",
                        "tags": [],
                        "created": "2026-04-24",
                        "updated": "2026-04-24",
                    },
                    body="# Docker DNS Issue\n\n## Summary\n\nOne.\n\n---\n\n## Fix\n\nTwo.\n",
                ),
            )

            with patch("scripts.tasks.validate_sources.discover_workflows", return_value={"note": workflow}), patch(
                "scripts.tasks.validate_sources.write_json_report"
            ):
                with self.assertRaises(ValidationError) as exc:
                    validate_sources.main([])

            self.assertIn("sources/notes/containers/docker-dns-issue.md", str(exc.exception))
            self.assertIn("line ", str(exc.exception))
            self.assertIn("thematic break immediately before ## heading", str(exc.exception))

    def test_validate_sources_allows_thematic_break_before_prose(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            workflow = self.make_workflow(root, "note")
            workflow.source_root.mkdir(parents=True)

            target = workflow.source_root / "containers" / "docker-dns-issue.md"
            write_markdown(
                target,
                MarkdownDocument(
                    frontmatter={
                        "id": "20260424T103000",
                        "title": "Docker DNS Issue",
                        "kind": "note",
                        "section": "containers",
                        "status": "draft",
                        "tags": [],
                        "created": "2026-04-24",
                        "updated": "2026-04-24",
                    },
                    body="# Docker DNS Issue\n\n## Summary\n\nOne.\n\n---\n\nStill prose.\n",
                ),
            )

            with patch("scripts.tasks.validate_sources.discover_workflows", return_value={"note": workflow}), patch(
                "scripts.tasks.validate_sources.write_json_report"
            ):
                validate_sources.main([])

    def test_validate_sources_rejects_duplicate_ids(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            workflow = self.make_workflow(root, "note")
            workflow.source_root.mkdir(parents=True)

            first = workflow.source_root / "containers" / "first.md"
            second = workflow.source_root / "networking" / "second.md"
            write_markdown(
                first,
                MarkdownDocument(
                    frontmatter={
                        "id": "same-id",
                        "title": "Docker DNS Issue",
                        "kind": "note",
                        "section": "containers",
                        "status": "draft",
                        "tags": [],
                        "created": "2026-04-24",
                        "updated": "2026-04-24",
                    },
                    body="# Docker DNS Issue\n\n## Summary\n\nOne.\n\n## Details\n\nTwo.\n\n## Related\n",
                ),
            )
            write_markdown(
                second,
                MarkdownDocument(
                    frontmatter={
                        "id": "same-id",
                        "title": "VLAN Tagging",
                        "kind": "note",
                        "section": "networking",
                        "status": "draft",
                        "tags": [],
                        "created": "2026-04-24",
                        "updated": "2026-04-24",
                    },
                    body="# VLAN Tagging\n\n## Summary\n\nOne.\n\n## Details\n\nTwo.\n\n## Related\n",
                ),
            )

            with patch("scripts.tasks.validate_sources.discover_workflows", return_value={"note": workflow}), patch(
                "scripts.tasks.validate_sources.write_json_report"
            ):
                with self.assertRaises(Exception):
                    validate_sources.main([])

    def test_build_tasks_generate_content_indexes_and_sidebar(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            note_workflow = self.make_workflow(root, "note")
            doc_workflow = self.make_workflow(root, "doc")
            note_workflow.source_root.mkdir(parents=True)
            doc_workflow.source_root.mkdir(parents=True)
            source_path = note_workflow.source_path_for("Docker DNS Issue", "containers")
            write_markdown(
                source_path,
                MarkdownDocument(
                    frontmatter={
                        "id": "20260424T103000",
                        "title": "Docker DNS Issue",
                        "kind": "note",
                        "section": "containers",
                        "status": "draft",
                        "tags": ["docker", "dns"],
                        "created": "2026-04-24",
                        "updated": "2026-04-24",
                    },
                    body="# Docker DNS Issue\n\n## Summary\n\nDNS fails.\n\n## Details\n\nMore detail.\n\n## Related\n",
                ),
            )
            write_markdown(
                doc_workflow.source_root / "testing" / "guardrail.md",
                MarkdownDocument(
                    frontmatter={
                        "id": "20260424T103001",
                        "title": "Knowledge Panel Guardrail Stress Test for Extremely Long Titles, Verbose Metadata, and Summary Copy That Would Otherwise Expand the Compact Context Rail Beyond Its Intended Reading Rhythm",
                        "nav_title": "Knowledge Panel Guardrail Stress Test",
                        "kind": "doc",
                        "section": "testing",
                        "slug": "knowledge-panel-guardrail-stress-test",
                        "status": "draft",
                        "tags": ["knowledge", "testing"],
                        "created": "2026-04-24",
                        "updated": "2026-04-24",
                        "summary": "Stress-test article for compact knowledge panel guardrails.",
                    },
                    body="# Knowledge Panel Guardrail Stress Test for Extremely Long Titles, Verbose Metadata, and Summary Copy That Would Otherwise Expand the Compact Context Rail Beyond Its Intended Reading Rhythm\n\n## Overview\n\nLong.\n\n## Details\n\nMore detail.\n\n## References\n",
                ),
            )
            write_markdown(
                doc_workflow.source_root / "testing" / "auto-fallback.md",
                MarkdownDocument(
                    frontmatter={
                        "id": "20260424T103002",
                        "title": "Knowledge Panel Automatic Navigation Title Fallback Evaluation for Pages That Intentionally Omit nav_title While Still Carrying a Longer Editorial Title",
                        "kind": "doc",
                        "section": "testing",
                        "slug": "knowledge-panel-automatic-navigation-title-fallback-evaluation",
                        "status": "draft",
                        "tags": ["knowledge", "testing"],
                        "created": "2026-04-24",
                        "updated": "2026-04-24",
                        "summary": "Verification doc for automatic navigation-title fallback.",
                    },
                    body="# Knowledge Panel Automatic Navigation Title Fallback Evaluation for Pages That Intentionally Omit nav_title While Still Carrying a Longer Editorial Title\n\n## Overview\n\nLong.\n\n## Details\n\nMore detail.\n\n## References\n",
                ),
            )

            workflows = {"note": note_workflow, "doc": doc_workflow}
            knowledge_dir = root / ".vitepress" / "knowledge"
            generated_vitepress_dir = root / ".vitepress"
            with patch("scripts.tasks.validate_sources.discover_workflows", return_value=workflows), patch(
                "scripts.tasks.validate_sources.write_json_report"
            ), patch("scripts.tasks.build_content.discover_workflows", return_value=workflows), patch(
                "scripts.tasks.build_content.write_json_report"
            ), patch("scripts.tasks.build_linkgraph.discover_workflows", return_value=workflows), patch(
                "scripts.tasks.build_linkgraph.KNOWLEDGE_DIR", knowledge_dir
            ), patch("scripts.tasks.build_related.KNOWLEDGE_DIR", knowledge_dir), patch(
                "scripts.tasks.build_indexes.CONTENT_DIR", root / "content"
            ), patch("scripts.tasks.build_indexes.discover_workflows", return_value=workflows), patch(
                "scripts.tasks.build_sidebar.CONTENT_DIR", root / "content"
            ), patch("scripts.tasks.build_sidebar.discover_workflows", return_value=workflows), patch(
                "scripts.tasks.build_sidebar.GENERATED_VITEPRESS_DIR", generated_vitepress_dir
            ):
                validate_sources.main([])
                build_content.main([])
                build_linkgraph.main([])
                build_related.main([])
                build_indexes.main([])
                build_sidebar.main([])

            self.assertTrue((root / "content" / "notes" / "containers" / "docker-dns-issue.md").exists())
            self.assertTrue((root / "content" / "docs" / "testing" / "knowledge-panel-guardrail-stress-test.md").exists())
            self.assertTrue((root / "content" / "docs" / "testing" / "knowledge-panel-automatic-navigation-title-fallback-evaluation.md").exists())
            self.assertTrue((root / "content" / "index.md").exists())
            self.assertTrue((root / "content" / "notes" / "index.md").exists())
            self.assertTrue((root / "content" / "docs" / "index.md").exists())
            self.assertTrue((root / "content" / "tags" / "dns" / "index.md").exists())
            self.assertTrue((root / "content" / "tags" / "knowledge" / "index.md").exists())
            self.assertTrue((generated_vitepress_dir / "sidebar.generated.ts").exists())
            self.assertTrue((generated_vitepress_dir / "nav.generated.ts").exists())
            self.assertTrue((knowledge_dir / "pages.generated.json").exists())
            self.assertTrue((knowledge_dir / "linkgraph.generated.json").exists())
            self.assertTrue((knowledge_dir / "related.generated.json").exists())

            home_page = (root / "content" / "index.md").read_text()
            docs_index = (root / "content" / "docs" / "index.md").read_text()
            dns_tag_page = (root / "content" / "tags" / "dns" / "index.md").read_text()
            knowledge_tag_page = (root / "content" / "tags" / "knowledge" / "index.md").read_text()
            generated_doc = (root / "content" / "docs" / "testing" / "knowledge-panel-guardrail-stress-test.md").read_text()
            nav = (generated_vitepress_dir / "nav.generated.ts").read_text()
            sidebar = (generated_vitepress_dir / "sidebar.generated.ts").read_text()
            page_catalog = read_json(knowledge_dir / "pages.generated.json")

            self.assertIn("layout: home", home_page)
            self.assertIn("pageClass: archive-home", home_page)
            self.assertIn("hero:", home_page)
            self.assertIn("## Recently Added", home_page)
            self.assertIn('class="archive-home__workflows"', home_page)
            self.assertIn('href="/notes/"', home_page)
            self.assertIn('href="/docs/"', home_page)
            self.assertIn(
                '<a class="archive-entry" href="/notes/containers/docker-dns-issue">',
                home_page,
            )
            self.assertIn("Docker DNS Issue", home_page)
            self.assertIn("Notes · 2026-04-24", home_page)
            self.assertIn(
                '<a class="archive-entry" href="/docs/testing/knowledge-panel-guardrail-stress-test">',
                home_page,
            )
            self.assertIn("Knowledge Panel Guardrail Stress Test", home_page)
            self.assertIn(
                '<a class="archive-entry" href="/docs/testing/knowledge-panel-automatic-navigation-title-fallback-evaluation">',
                home_page,
            )
            notes_index = (root / "content" / "notes" / "index.md").read_text()
            self.assertIn("pageClass: archive-index", docs_index)
            self.assertIn("pageClass: archive-index", notes_index)
            self.assertIn(
                '<a class="archive-entry" href="/notes/containers/docker-dns-issue">',
                notes_index,
            )
            self.assertIn("Docker DNS Issue", notes_index)
            self.assertIn(
                '<a class="archive-entry" href="/docs/testing/knowledge-panel-guardrail-stress-test">',
                docs_index,
            )
            self.assertIn(
                '<a class="archive-entry" href="/docs/testing/knowledge-panel-automatic-navigation-title-fallback-evaluation">',
                docs_index,
            )
            self.assertIn("# Tag: dns", dns_tag_page)
            self.assertIn('href="/notes/containers/docker-dns-issue"', dns_tag_page)
            self.assertIn("# Tag: knowledge", knowledge_tag_page)
            self.assertIn('href="/docs/testing/knowledge-panel-guardrail-stress-test"', knowledge_tag_page)
            self.assertIn('href="/docs/testing/knowledge-panel-automatic-navigation-title-fallback-evaluation"', knowledge_tag_page)
            self.assertNotIn("Extremely Long Titles", docs_index)
            self.assertIn('"text": "Notes"', nav)
            self.assertIn('"text": "Docs"', nav)
            self.assertIn('"/notes/"', sidebar)
            self.assertIn('"/docs/"', sidebar)
            self.assertIn('"text": "Knowledge Panel Guardrail Stress Test"', sidebar)
            self.assertIn('"text": "Knowledge Panel Automatic Navigation Title Fallback..."', sidebar)
            self.assertNotIn("Extremely Long Titles", sidebar)
            self.assertEqual(page_catalog["/notes/containers/docker-dns-issue"]["workflow"]["knowledge_panel"], True)
            self.assertEqual(
                page_catalog["/docs/testing/knowledge-panel-guardrail-stress-test"]["title"],
                "Knowledge Panel Guardrail Stress Test for Extremely Long Titles, Verbose Metadata, and Summary Copy That Would Otherwise Expand the Compact Context Rail Beyond Its Intended Reading Rhythm",
            )
            self.assertEqual(
                page_catalog["/docs/testing/knowledge-panel-guardrail-stress-test"]["nav_title"],
                "Knowledge Panel Guardrail Stress Test",
            )
            self.assertEqual(page_catalog["/docs/testing/knowledge-panel-guardrail-stress-test"]["slug"], "knowledge-panel-guardrail-stress-test")
            self.assertIn("nav_title: Knowledge Panel Guardrail Stress Test", generated_doc)
            self.assertIn("slug: knowledge-panel-guardrail-stress-test", generated_doc)

    def test_build_sidebar_nests_section_paths_dynamically(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            workflow = self.make_workflow(root, "doc")
            workflow.source_root.mkdir(parents=True)
            (workflow.source_root / "_sections.yaml").write_text(
                "sections:\n"
                "  homelab:\n"
                "    title: Homelab\n"
                "    collapsed: false\n"
                "  homelab/security:\n"
                "    title: Security\n"
                "    collapsed: true\n"
                "  homelab/omv:\n"
                "    title: OMV\n"
                "    collapsed: true\n"
            )

            for title, section, slug in (
                ("Homelab HTTPS Setup", "homelab/security", "homelab-https-setup"),
                (
                    "Homelab HTTPS Certificates with Local ECDSA CA",
                    "homelab/security",
                    "homelab-https-certificates-with-local-ecdsa-ca",
                ),
                (
                    "Internal HTTPS Setup with Local DNS for OMV",
                    "homelab/networking",
                    "internal-https-setup-with-local-dns-for-omv",
                ),
                ("OMV Backup and Restore Strategy", "homelab/omv", "omv-backup-and-restore-strategy"),
                ("Linux Review", "linux", "linux-review"),
            ):
                write_markdown(
                    workflow.source_path_for(title, section),
                    MarkdownDocument(
                        frontmatter={
                            "id": f"20260506T{slug[:6]}",
                            "title": title,
                            "kind": "doc",
                            "section": section,
                            "slug": slug,
                            "status": "draft",
                            "tags": [],
                            "created": "2026-05-06",
                            "updated": "2026-05-06",
                        },
                        body="# Placeholder\n\n## Overview\n\nOne.\n\n## Details\n\nTwo.\n",
                    ),
                )

            workflows = {"doc": workflow}
            generated_vitepress_dir = root / ".vitepress"
            with patch("scripts.tasks.build_indexes.discover_workflows", return_value=workflows), patch(
                "scripts.tasks.build_indexes.CONTENT_DIR", root / "content"
            ), patch("scripts.tasks.build_sidebar.discover_workflows", return_value=workflows), patch(
                "scripts.tasks.build_sidebar.CONTENT_DIR", root / "content"
            ), patch("scripts.tasks.build_sidebar.GENERATED_VITEPRESS_DIR", generated_vitepress_dir):
                build_indexes.main([])
                build_sidebar.main([])

            sidebar_text = (generated_vitepress_dir / "sidebar.generated.ts").read_text()
            sidebar = json.loads(sidebar_text.removeprefix("export default "))
            docs_index = (root / "content" / "docs" / "index.md").read_text()

            docs_items = sidebar["/docs/"]
            self.assertEqual(docs_items[0]["text"], "Homelab")
            self.assertEqual(docs_items[0]["collapsed"], False)
            self.assertEqual(docs_items[0]["items"][0]["text"], "Networking")
            self.assertEqual(docs_items[0]["items"][0]["collapsed"], True)
            self.assertEqual(docs_items[0]["items"][1]["text"], "OMV")
            self.assertEqual(docs_items[0]["items"][1]["collapsed"], True)
            self.assertEqual(docs_items[0]["items"][2]["text"], "Security")
            self.assertEqual(docs_items[0]["items"][2]["collapsed"], True)
            self.assertEqual(
                docs_items[0]["items"][2]["items"],
                [
                    {
                        "text": "Homelab HTTPS Certificates with Local ECDSA CA",
                        "link": "/docs/homelab/security/homelab-https-certificates-with-local-ecdsa-ca",
                    },
                    {
                        "text": "Homelab HTTPS Setup",
                        "link": "/docs/homelab/security/homelab-https-setup",
                    },
                ],
            )
            self.assertEqual(docs_items[1]["text"], "Linux")
            self.assertEqual(docs_items[1]["collapsed"], False)
            self.assertEqual(docs_items[1]["items"], [{"text": "Linux Review", "link": "/docs/linux/linux-review"}])
            self.assertIn("## Homelab / OMV", docs_index)
            self.assertIn("## Homelab / Security", docs_index)

    def test_build_content_copies_adjacent_assets_when_output_uses_slug(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            workflow = self.make_workflow(root, "doc")
            workflow.source_root.mkdir(parents=True)

            source_path = workflow.source_root / "testing" / "assets" / "local-image-assets-example.md"
            write_markdown(
                source_path,
                MarkdownDocument(
                    frontmatter={
                        "id": "20260427T103000",
                        "title": "Source-Adjacent Asset Folder Example",
                        "kind": "doc",
                        "section": "testing/assets",
                        "slug": "source-adjacent-asset-folder-example",
                        "status": "draft",
                        "tags": ["assets", "images"],
                        "created": "2026-04-27",
                        "updated": "2026-04-27",
                    },
                    body=(
                        "# Source-Adjacent Asset Folder Example\n\n"
                        "## Overview\n\n"
                        "This page verifies local image assets beside a canonical source file.\n\n"
                        "## Details\n\n"
                        "![Topology](./local-image-assets-example.assets/topology.svg)\n\n"
                        "## References\n\n"
                        "- `scripts/tasks/build_content.py`\n"
                    ),
                ),
            )
            source_asset = source_path.with_name("local-image-assets-example.assets")
            source_asset.mkdir(parents=True)
            (source_asset / "topology.svg").write_text(
                '<svg xmlns="http://www.w3.org/2000/svg" width="120" height="40"><text x="8" y="24">topology</text></svg>\n'
            )

            plain_source_path = workflow.source_root / "testing" / "assets" / "plain-image-assets-example.md"
            write_markdown(
                plain_source_path,
                MarkdownDocument(
                    frontmatter={
                        "id": "20260427T103001",
                        "title": "Plain Source-Adjacent Asset Example",
                        "kind": "doc",
                        "section": "testing/assets",
                        "status": "draft",
                        "tags": ["assets"],
                        "created": "2026-04-27",
                        "updated": "2026-04-27",
                    },
                    body=(
                        "# Plain Source-Adjacent Asset Example\n\n"
                        "## Overview\n\n"
                        "This page keeps a local diagram without an explicit slug.\n\n"
                        "## Details\n\n"
                        "![Diagram](./plain-image-assets-example.assets/diagram.svg)\n\n"
                        "## References\n\n"
                        "- `docs/doc.md`\n"
                    ),
                ),
            )
            plain_source_asset = plain_source_path.with_name("plain-image-assets-example.assets")
            plain_source_asset.mkdir(parents=True)
            (plain_source_asset / "diagram.svg").write_text(
                '<svg xmlns="http://www.w3.org/2000/svg" width="120" height="40"><text x="8" y="24">diagram</text></svg>\n'
            )

            with patch("scripts.tasks.build_content.discover_workflows", return_value={"doc": workflow}), patch(
                "scripts.tasks.build_content.write_json_report"
            ):
                build_content.main([])
                build_content.main([])

            output_page = workflow.output_root / "testing" / "assets" / "source-adjacent-asset-folder-example.md"
            output_asset = workflow.output_root / "testing" / "assets" / "local-image-assets-example.assets" / "topology.svg"
            plain_output_page = workflow.output_root / "testing" / "assets" / "plain-source-adjacent-asset-example.md"
            plain_output_asset = workflow.output_root / "testing" / "assets" / "plain-image-assets-example.assets" / "diagram.svg"

            self.assertTrue(output_page.exists())
            self.assertTrue(output_asset.exists())
            self.assertTrue(plain_output_page.exists())
            self.assertTrue(plain_output_asset.exists())
            self.assertIn("./local-image-assets-example.assets/topology.svg", output_page.read_text())
            self.assertIn("./plain-image-assets-example.assets/diagram.svg", plain_output_page.read_text())
            self.assertIn("topology", output_asset.read_text())
            self.assertIn("diagram", plain_output_asset.read_text())

    def test_build_content_copies_adjacent_assets_from_external_workspace_sources(self) -> None:
        with tempfile.TemporaryDirectory() as workspace_dir, tempfile.TemporaryDirectory() as tool_dir:
            workspace_root = Path(workspace_dir)
            tool_root = Path(tool_dir)
            actual = get_workflow("doc")
            workflow = WorkflowDefinition(
                kind=actual.kind,
                label=actual.label,
                source_root=workspace_root / "sources" / "docs",
                output_root=tool_root / "content" / "docs",
                default_section=actual.default_section,
                required_sections=actual.required_sections,
                knowledge_panel=actual.knowledge_panel,
                backlinks=actual.backlinks,
                related=actual.related,
                workflow_dir=actual.workflow_dir,
            )
            workflow.source_root.mkdir(parents=True)

            source_path = workflow.source_root / "testing" / "assets" / "local-image-assets-example.md"
            write_markdown(
                source_path,
                MarkdownDocument(
                    frontmatter={
                        "id": "20260427T103000",
                        "title": "Source-Adjacent Asset Folder Example",
                        "kind": "doc",
                        "section": "testing/assets",
                        "slug": "source-adjacent-asset-folder-example",
                        "status": "draft",
                        "tags": ["assets", "images"],
                        "created": "2026-04-27",
                        "updated": "2026-04-27",
                    },
                    body=(
                        "# Source-Adjacent Asset Folder Example\n\n"
                        "## Overview\n\n"
                        "This page verifies local image assets beside a canonical source file.\n\n"
                        "## Details\n\n"
                        "![Topology](./local-image-assets-example.assets/topology.svg)\n\n"
                        "## References\n\n"
                        "- `scripts/tasks/build_content.py`\n"
                    ),
                ),
            )
            source_asset = source_path.with_name("local-image-assets-example.assets")
            source_asset.mkdir(parents=True)
            (source_asset / "topology.svg").write_text(
                '<svg xmlns="http://www.w3.org/2000/svg" width="120" height="40"><text x="8" y="24">topology</text></svg>\n'
            )

            with patch.dict("os.environ", {"WORKSPACE": workspace_dir}, clear=True), patch(
                "scripts.tasks.build_content.discover_workflows", return_value={"doc": workflow}
            ), patch("scripts.tasks.build_content.write_json_report"):
                build_content.main([])

            output_page = workflow.output_root / "testing" / "assets" / "source-adjacent-asset-folder-example.md"
            output_asset = workflow.output_root / "testing" / "assets" / "local-image-assets-example.assets" / "topology.svg"

            self.assertTrue(output_page.exists())
            self.assertTrue(output_asset.exists())
            self.assertIn("source_path: sources/docs/testing/assets/local-image-assets-example.md", output_page.read_text())
            self.assertIn("./local-image-assets-example.assets/topology.svg", output_page.read_text())
            self.assertIn("topology", output_asset.read_text())

    def test_long_titles_without_nav_title_use_shortened_navigation_label(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            doc_workflow = self.make_workflow(root, "doc")
            doc_workflow.source_root.mkdir(parents=True)

            write_markdown(
                doc_workflow.source_root / "testing" / "auto-fallback.md",
                MarkdownDocument(
                    frontmatter={
                        "id": "20260424T103000",
                        "title": "Knowledge Panel Automatic Navigation Title Fallback Evaluation for Pages That Intentionally Omit nav_title While Still Carrying a Longer Editorial Title",
                        "kind": "doc",
                        "section": "testing",
                        "slug": "knowledge-panel-automatic-navigation-title-fallback-evaluation",
                        "status": "draft",
                        "tags": ["knowledge"],
                        "created": "2026-04-24",
                        "updated": "2026-04-24",
                    },
                    body="# Knowledge Panel Automatic Navigation Title Fallback Evaluation for Pages That Intentionally Omit nav_title While Still Carrying a Longer Editorial Title\n\n## Overview\n\nOne.\n\n## Details\n\nTwo.\n\n## References\n",
                ),
            )

            workflows = {"doc": doc_workflow}
            generated_vitepress_dir = root / ".vitepress"
            with patch("scripts.tasks.build_indexes.discover_workflows", return_value=workflows), patch(
                "scripts.tasks.build_indexes.CONTENT_DIR", root / "content"
            ), patch("scripts.tasks.build_sidebar.discover_workflows", return_value=workflows), patch(
                "scripts.tasks.build_sidebar.CONTENT_DIR", root / "content"
            ), patch("scripts.tasks.build_sidebar.GENERATED_VITEPRESS_DIR", generated_vitepress_dir):
                build_indexes.main([])
                build_sidebar.main([])

            docs_index = (root / "content" / "docs" / "index.md").read_text()
            sidebar = (generated_vitepress_dir / "sidebar.generated.ts").read_text()

            self.assertIn(
                'href="/docs/testing/knowledge-panel-automatic-navigation-title-fallback-evaluation"',
                docs_index,
            )
            self.assertIn("Knowledge Panel Automatic Navigation Title Fallback...", docs_index)
            self.assertIn('"text": "Knowledge Panel Automatic Navigation Title Fallback..."', sidebar)
            self.assertNotIn("While Still Carrying a Longer Editorial Title", docs_index)

    def test_build_knowledge_metadata_generates_linkgraph_and_related_index(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            note_workflow = self.make_workflow(root, "note")
            doc_workflow = self.make_workflow(root, "doc")
            note_workflow.source_root.mkdir(parents=True)
            doc_workflow.source_root.mkdir(parents=True)

            write_markdown(
                note_workflow.source_path_for("Alpha Note", "testing"),
                MarkdownDocument(
                    frontmatter={
                        "id": "20260424T103000",
                        "title": "Alpha Note",
                        "kind": "note",
                        "section": "testing",
                        "status": "draft",
                        "tags": ["alpha", "dns"],
                        "related_manual": ["/docs/testing/gamma-doc"],
                        "created": "2026-04-24",
                        "updated": "2026-04-24",
                        "summary": "Manual summary.",
                    },
                    body="# Alpha Note\n\n## Summary\n\nLinks out.\n\n## Details\n\nSee [Beta Note](/notes/testing/beta-note) and [Gamma Doc](/docs/testing/gamma-doc).\n\n## Related\n",
                ),
            )
            write_markdown(
                note_workflow.source_path_for("Beta Note", "testing"),
                MarkdownDocument(
                    frontmatter={
                        "id": "20260424T103001",
                        "title": "Beta Note",
                        "kind": "note",
                        "section": "testing",
                        "status": "draft",
                        "tags": ["dns"],
                        "created": "2026-04-24",
                        "updated": "2026-04-24",
                    },
                    body="# Beta Note\n\n## Summary\n\nPoints back.\n\n## Details\n\nSee [Alpha Note](/notes/testing/alpha-note).\n\n## Related\n",
                ),
            )
            write_markdown(
                doc_workflow.source_path_for("Gamma Doc", "testing"),
                MarkdownDocument(
                    frontmatter={
                        "id": "20260424T103002",
                        "title": "Gamma Doc",
                        "kind": "doc",
                        "section": "testing",
                        "status": "draft",
                        "tags": ["dns"],
                        "created": "2026-04-24",
                        "updated": "2026-04-24",
                    },
                    body="# Gamma Doc\n\n## Overview\n\nReferences Alpha.\n\n## Details\n\nSee [Alpha Note](/notes/testing/alpha-note).\n\n## References\n",
                ),
            )

            workflows = {"note": note_workflow, "doc": doc_workflow}
            knowledge_dir = root / ".vitepress" / "knowledge"
            with patch("scripts.tasks.build_content.discover_workflows", return_value=workflows), patch(
                "scripts.tasks.build_content.write_json_report"
            ), patch("scripts.tasks.build_linkgraph.discover_workflows", return_value=workflows), patch(
                "scripts.tasks.build_linkgraph.KNOWLEDGE_DIR", knowledge_dir
            ), patch("scripts.tasks.build_related.KNOWLEDGE_DIR", knowledge_dir):
                build_content.main([])
                build_linkgraph.main([])
                build_related.main([])

            alpha_page = (root / "content" / "notes" / "testing" / "alpha-note.md").read_text()
            page_catalog = read_json(knowledge_dir / "pages.generated.json")
            linkgraph = read_json(knowledge_dir / "linkgraph.generated.json")
            related_index = read_json(knowledge_dir / "related.generated.json")

            self.assertNotIn("### Related Links", alpha_page)
            self.assertNotIn("### Backlinks", alpha_page)
            self.assertIn("related_manual:", alpha_page)
            self.assertIn("summary: Manual summary.", alpha_page)
            self.assertEqual(page_catalog["/notes/testing/alpha-note"]["summary"], "Manual summary.")
            self.assertEqual(page_catalog["/notes/testing/alpha-note"]["related_manual"], ["/docs/testing/gamma-doc"])
            self.assertEqual(
                linkgraph["/notes/testing/alpha-note"]["outbound"],
                ["/notes/testing/beta-note", "/docs/testing/gamma-doc"],
            )
            self.assertEqual(
                linkgraph["/notes/testing/alpha-note"]["backlinks"],
                ["/notes/testing/beta-note", "/docs/testing/gamma-doc"],
            )
            self.assertIn("/notes/testing/beta-note", related_index["/notes/testing/alpha-note"]["related"])
            self.assertNotIn("/docs/testing/gamma-doc", related_index["/notes/testing/alpha-note"]["related"])

    def test_home_page_limits_recent_items_to_ten(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            workflow = self.make_workflow(root, "note")
            workflow.source_root.mkdir(parents=True)

            for day in range(1, 13):
                title = f"Entry {day:02d}"
                source_path = workflow.source_path_for(title, "general")
                write_markdown(
                    source_path,
                    MarkdownDocument(
                        frontmatter={
                            "id": f"202604{day:02d}T103000",
                            "title": title,
                            "kind": "note",
                            "section": "general",
                            "status": "draft",
                            "tags": [],
                            "created": f"2026-04-{day:02d}",
                            "updated": f"2026-04-{day:02d}",
                        },
                        body=f"# {title}\n\n## Summary\n\nSummary {day}.\n\n## Details\n\nDetails {day}.\n\n## Related\n",
                    ),
                )

            workflows = {"note": workflow}
            with patch("scripts.tasks.build_indexes.discover_workflows", return_value=workflows), patch(
                "scripts.tasks.build_indexes.CONTENT_DIR", root / "content"
            ):
                build_indexes.main([])

            home_page = (root / "content" / "index.md").read_text()
            self.assertEqual(home_page.count('href="/notes/general/entry-'), 10)
            self.assertIn('href="/notes/general/entry-12"', home_page)
            self.assertIn('href="/notes/general/entry-03"', home_page)
            self.assertNotIn('href="/notes/general/entry-02"', home_page)
            self.assertNotIn('href="/notes/general/entry-01"', home_page)

    def test_dynamic_workflow_navigation_follows_non_empty_workflows(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            base_workflow = get_workflow("note")
            playbook_workflow = WorkflowDefinition(
                kind="playbook",
                label="Playbooks",
                source_root=root / "sources" / "playbooks",
                output_root=root / "content" / "playbooks",
                default_section="general",
                required_sections=("Overview",),
                knowledge_panel=None,
                backlinks=None,
                related=None,
                workflow_dir=base_workflow.workflow_dir,
            )
            playbook_workflow.source_root.mkdir(parents=True)

            write_markdown(
                playbook_workflow.source_path_for("Cluster Rollout", "operations"),
                MarkdownDocument(
                    frontmatter={
                        "id": "20260424T103000",
                        "title": "Cluster Rollout",
                        "kind": "playbook",
                        "section": "operations",
                        "status": "draft",
                        "tags": [],
                        "created": "2026-04-24",
                        "updated": "2026-04-24",
                    },
                    body="# Cluster Rollout\n\n## Overview\n\nRoll out the cluster update.\n",
                ),
            )

            workflows = {"playbook": playbook_workflow}
            generated_vitepress_dir = root / ".vitepress"
            with patch("scripts.tasks.build_indexes.discover_workflows", return_value=workflows), patch(
                "scripts.tasks.build_indexes.CONTENT_DIR", root / "content"
            ), patch("scripts.tasks.build_sidebar.discover_workflows", return_value=workflows), patch(
                "scripts.tasks.build_sidebar.CONTENT_DIR", root / "content"
            ), patch("scripts.tasks.build_sidebar.GENERATED_VITEPRESS_DIR", generated_vitepress_dir):
                build_indexes.main([])
                build_sidebar.main([])

            home_page = (root / "content" / "index.md").read_text()
            nav = (generated_vitepress_dir / "nav.generated.ts").read_text()
            sidebar = (generated_vitepress_dir / "sidebar.generated.ts").read_text()

            self.assertIn('href="/playbooks/"', home_page)
            self.assertIn("Playbooks", home_page)
            self.assertIn('"text": "Playbooks"', nav)
            self.assertIn('"/playbooks/"', sidebar)


if __name__ == "__main__":
    unittest.main()
