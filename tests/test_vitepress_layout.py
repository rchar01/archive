from __future__ import annotations

import unittest
from pathlib import Path


class VitePressLayoutTests(unittest.TestCase):
    def test_repo_root_vitepress_config_targets_content_and_site(self) -> None:
        vitepress_dir = Path(__file__).resolve().parents[1] / ".vitepress"
        config_path = vitepress_dir / "config.ts"
        config = config_path.read_text()
        theme_index = (vitepress_dir / "theme" / "index.ts").read_text()
        knowledge_panel = (vitepress_dir / "theme" / "KnowledgePanel.vue").read_text()
        mermaid_component = (vitepress_dir / "theme" / "MermaidDiagram.vue").read_text()
        mermaid_client = (vitepress_dir / "theme" / "mermaidClient.ts").read_text()

        self.assertIn("const useLegacyGeneratedLayout = archiveInstance === 'default' && workspaceRoot === TOOL_ROOT", config)
        self.assertIn("const contentDir = useLegacyGeneratedLayout ? path.join(TOOL_ROOT, 'content')", config)
        self.assertIn("const siteDir = useLegacyGeneratedLayout ? path.join(TOOL_ROOT, 'site')", config)
        self.assertIn("srcDir: toConfigPath(contentDir)", config)
        self.assertIn("outDir: toConfigPath(siteDir)", config)
        self.assertIn("const nav = readGeneratedJson", config)
        self.assertIn("const sidebar = readGeneratedJson", config)
        self.assertIn("'@archive-generated': generatedDir", config)
        self.assertIn("markdown:", config)
        self.assertIn("MermaidDiagram", config)
        self.assertIn("token.info.trim() === 'mermaid'", config)
        self.assertIn("nav,", config)
        self.assertIn("knowledgePanel: true", config)
        self.assertIn("knowledgePanelBacklinks: true", config)
        self.assertIn("knowledgePanelRelated: true", config)
        self.assertIn("doc-after", theme_index)
        self.assertIn("KnowledgePanel", theme_index)
        self.assertIn("MermaidDiagram", theme_index)
        self.assertIn("app.component('MermaidDiagram'", theme_index)
        self.assertIn("@archive-generated/knowledge/pages.generated.json", knowledge_panel)
        self.assertIn("@archive-generated/knowledge/linkgraph.generated.json", knowledge_panel)
        self.assertIn("@archive-generated/knowledge/related.generated.json", knowledge_panel)
        self.assertIn("function tagLink(tag: string)", knowledge_panel)
        self.assertIn(':href="tagLink(tag)"', knowledge_panel)
        self.assertIn("loadMermaid", mermaid_component)
        self.assertIn("securityLevel: 'strict'", mermaid_component)
        self.assertIn("watch([() => props.code, () => isDark.value]", mermaid_component)
        self.assertIn("import('mermaid')", mermaid_client)


if __name__ == "__main__":
    unittest.main()
