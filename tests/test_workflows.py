from __future__ import annotations

import unittest
from datetime import datetime, timezone
from pathlib import Path

from scripts.core.frontmatter import MarkdownDocument
from scripts.core.identifiers import generate_entry_id
from scripts.core.registry import get_workflow
from scripts.core.validation import ValidationError
from scripts.workflows.doc import adapter as doc_adapter, renderer as doc_renderer, validator as doc_validator
from scripts.workflows.note import adapter as note_adapter, renderer as note_renderer, validator as note_validator


class WorkflowTests(unittest.TestCase):
    def test_generate_entry_id_includes_subsecond_precision(self) -> None:
        self.assertEqual(
            generate_entry_id(datetime(2026, 4, 24, 12, 19, 27, 123456, tzinfo=timezone.utc)),
            "20260424T121927123456",
        )

    def test_note_workflow_normalizes_and_renders(self) -> None:
        workflow = get_workflow("note")
        incoming = MarkdownDocument(
            frontmatter={
                "title": "Docker DNS Issue",
                "nav_title": "DNS Issue",
                "kind": "note",
                "section": "containers",
                "slug": "dns-issue",
                "tags": ["docker", "dns"],
                "related_manual": ["/docs/networking/dns-basics"],
                "hide_backlinks": True,
                "summary": "Author summary.",
            },
            body="Containers can reach IPs but fail to resolve names.\n",
        )

        normalized = note_adapter.from_incoming(incoming, default_section=workflow.default_section)
        note_validator.validate(normalized, required_sections=workflow.required_sections)
        page = note_renderer.render(
            normalized,
            source_path=Path("sources/notes/containers/docker-dns-issue.md"),
            output_path=Path("content/notes/containers/docker-dns-issue.md"),
        )

        self.assertEqual(normalized.frontmatter["kind"], "note")
        self.assertEqual(normalized.frontmatter["section"], "containers")
        self.assertIn("## Summary", normalized.body)
        self.assertNotIn("## Details", normalized.body)
        self.assertNotIn("## Related", normalized.body)
        self.assertEqual(page.title, "Docker DNS Issue")
        self.assertEqual(page.tags, ["docker", "dns"])
        self.assertEqual(page.description, "Author summary.")
        self.assertEqual(normalized.frontmatter["nav_title"], "DNS Issue")
        self.assertEqual(normalized.frontmatter["slug"], "dns-issue")
        self.assertEqual(page.frontmatter_extra["related_manual"], ["/docs/networking/dns-basics"])
        self.assertEqual(page.frontmatter_extra["hide_backlinks"], True)
        self.assertEqual(page.frontmatter_extra["nav_title"], "DNS Issue")
        self.assertEqual(page.frontmatter_extra["slug"], "dns-issue")

    def test_note_workflow_accepts_summary_without_details(self) -> None:
        workflow = get_workflow("note")
        minimal = MarkdownDocument(
            frontmatter={
                "id": "20260424T103000",
                "title": "Docker DNS Issue",
                "kind": "note",
                "section": "containers",
                "status": "draft",
                "tags": ["docker"],
                "created": "2026-04-24",
                "updated": "2026-04-24",
            },
            body="# Docker DNS Issue\n\n## Summary\n\nDNS fails.\n",
        )

        note_validator.validate(minimal, required_sections=workflow.required_sections)

    def test_doc_workflow_normalizes_and_renders(self) -> None:
        workflow = get_workflow("doc")
        incoming = MarkdownDocument(
            frontmatter={
                "title": "Homelab Firewall",
                "kind": "doc",
                "section": "homelab/networking",
                "tags": ["firewall"],
            },
            body="This page describes the firewall role.\n",
        )

        normalized = doc_adapter.from_incoming(incoming, default_section=workflow.default_section)
        doc_validator.validate(normalized, required_sections=workflow.required_sections)
        page = doc_renderer.render(
            normalized,
            source_path=Path("sources/docs/homelab/networking/homelab-firewall.md"),
            output_path=Path("content/docs/homelab/networking/homelab-firewall.md"),
        )

        self.assertEqual(normalized.frontmatter["kind"], "doc")
        self.assertEqual(normalized.frontmatter["section"], "homelab/networking")
        self.assertIn("## Overview", normalized.body)
        self.assertNotIn("## Details", normalized.body)
        self.assertNotIn("## References", normalized.body)
        self.assertEqual(page.title, "Homelab Firewall")
        self.assertEqual(page.tags, ["firewall"])

    def test_note_workflow_strips_thematic_break_before_later_h2(self) -> None:
        workflow = get_workflow("note")
        incoming = MarkdownDocument(
            frontmatter={
                "title": "Docker DNS Issue",
                "kind": "note",
                "section": "containers",
                "tags": ["docker"],
            },
            body="Lead summary.\n\n---\n\n## Fix\n\nDo this.\n",
        )

        normalized = note_adapter.from_incoming(incoming, default_section=workflow.default_section)

        self.assertEqual(
            normalized.body,
            "# Docker DNS Issue\n\n## Summary\n\nLead summary.\n\n## Fix\n\nDo this.\n",
        )

    def test_doc_renderer_strips_thematic_break_before_later_h2(self) -> None:
        document = MarkdownDocument(
            frontmatter={
                "id": "20260424T103000",
                "title": "Homelab Firewall",
                "kind": "doc",
                "section": "homelab/networking",
                "status": "draft",
                "tags": ["firewall"],
                "created": "2026-04-24",
                "updated": "2026-04-24",
            },
            body="# Homelab Firewall\n\n## Overview\n\nOne.\n\n---\n\n## Rules\n\nTwo.\n",
        )

        page = doc_renderer.render(
            document,
            source_path=Path("sources/docs/homelab/networking/homelab-firewall.md"),
            output_path=Path("content/docs/homelab/networking/homelab-firewall.md"),
        )

        self.assertNotIn("\n---\n\n## Rules", page.body)
        self.assertIn("## Rules\n\nTwo.", page.body)

    def test_doc_workflow_accepts_overview_without_details(self) -> None:
        workflow = get_workflow("doc")
        minimal = MarkdownDocument(
            frontmatter={
                "id": "20260424T103000",
                "title": "Homelab Firewall",
                "kind": "doc",
                "section": "homelab/networking",
                "status": "draft",
                "tags": ["firewall"],
                "created": "2026-04-24",
                "updated": "2026-04-24",
            },
            body="# Homelab Firewall\n\n## Overview\n\nOne.\n",
        )

        doc_validator.validate(minimal, required_sections=workflow.required_sections)

    def test_note_workflow_rejects_invalid_created_date(self) -> None:
        workflow = get_workflow("note")
        invalid = MarkdownDocument(
            frontmatter={
                "id": "20260424T103000",
                "title": "Docker DNS Issue",
                "kind": "note",
                "section": "containers",
                "status": "draft",
                "tags": ["docker"],
                "created": "20260424",
                "updated": "2026-04-24",
            },
            body="# Docker DNS Issue\n\n## Summary\n\nDNS fails.\n\n## Details\n\nMore detail.\n\n## Related\n",
        )

        with self.assertRaises(ValidationError):
            note_validator.validate(invalid, required_sections=workflow.required_sections)

    def test_doc_workflow_rejects_invalid_slug(self) -> None:
        workflow = get_workflow("doc")
        invalid = MarkdownDocument(
            frontmatter={
                "id": "20260424T103000",
                "title": "Homelab Firewall",
                "kind": "doc",
                "section": "homelab/networking",
                "slug": "Bad Slug",
                "status": "draft",
                "tags": ["firewall"],
                "created": "2026-04-24",
                "updated": "2026-04-24",
            },
            body="# Homelab Firewall\n\n## Overview\n\nOne.\n\n## Details\n\nTwo.\n\n## References\n",
        )

        with self.assertRaises(ValidationError):
            doc_validator.validate(invalid, required_sections=workflow.required_sections)


if __name__ == "__main__":
    unittest.main()
