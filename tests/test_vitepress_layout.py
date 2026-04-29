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

        self.assertIn("srcDir: 'content'", config)
        self.assertIn("outDir: 'site'", config)
        self.assertIn("import nav from './nav.generated'", config)
        self.assertIn("import sidebar from './sidebar.generated'", config)
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
        self.assertIn("pages.generated.json", knowledge_panel)
        self.assertIn("linkgraph.generated.json", knowledge_panel)
        self.assertIn("related.generated.json", knowledge_panel)
        self.assertIn("loadMermaid", mermaid_component)
        self.assertIn("securityLevel: 'strict'", mermaid_component)
        self.assertIn("watch([() => props.code, () => isDark.value]", mermaid_component)
        self.assertIn("import('mermaid')", mermaid_client)


if __name__ == "__main__":
    unittest.main()
