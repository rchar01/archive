from __future__ import annotations

import subprocess
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
        self.assertIn("const TAG_SEARCH_PREFIX = 'archivetag-'", config)
        self.assertIn("const TAG_SEARCH_WILDCARD_PREFIX = 'archivetagprefix-'", config)
        self.assertIn("function normalizeTagSearchValue(value: unknown)", config)
        self.assertIn("function normalizeTagSearchToken(value: unknown)", config)
        self.assertIn("function prefixTagSearchTokens(value: string): string[]", config)
        self.assertIn("function collectTagSearchTokens(frontmatter: Record<string, unknown> | undefined)", config)
        self.assertIn("function tokenizeSearchText(text: string): string[]", config)
        self.assertIn("const searchTokenizer = (text: string) =>", config)
        self.assertIn("const searchPrefixOption = (term: string) => !term.startsWith('archivetag-') && !term.startsWith('archivetagprefix-')", config)
        self.assertIn("const searchFuzzyOption = (term: string) => (term.startsWith('archivetag-') || term.startsWith('archivetagprefix-') ? false : 0.2)", config)
        self.assertIn("async function renderSearchHtml(", config)
        self.assertIn("tokenize: searchTokenizer", config)
        self.assertIn("searchOptions: {", config)
        self.assertIn("prefix: searchPrefixOption", config)
        self.assertIn("fuzzy: searchFuzzyOption", config)
        self.assertIn("return cleaned ? `${isWildcardQuery ? 'archivetagprefix-' : 'archivetag-'}${cleaned}` : ''", config)
        self.assertIn("const html = await renderSearchHtml(src, env, md)", config)
        self.assertIn("const tagTokens = collectTagSearchTokens(env.frontmatter)", config)
        self.assertIn("return `${html}\\n<div hidden>${tagTokens.join(' ')}</div>`", config)
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

    def test_hashtag_tag_search_stays_separate_from_plain_text_search(self) -> None:
        script = """
const MiniSearch = require('minisearch')
const TAG_SEARCH_PREFIX = 'archivetag-'
const TAG_SEARCH_WILDCARD_PREFIX = 'archivetagprefix-'
const normalizeTagSearchValue = (value) => {
  if (typeof value !== 'string') return ''
  return value.trim().toLowerCase().replace(/[^\\p{L}\\p{N}]+/gu, '-').replace(/^-+|-+$/g, '')
}
const prefixTokens = (value) => Array.from({ length: value.length }, (_, index) => `${TAG_SEARCH_WILDCARD_PREFIX}${value.slice(0, index + 1)}`)
const tokenizeSearchText = (text) => (text.match(/#[\\p{L}\\p{N}]+(?:-[\\p{L}\\p{N}]+)*\\*?|[\\p{L}\\p{N}]+(?:[-_][\\p{L}\\p{N}]+)*/gu) ?? []).map((term) => {
  if (!term.startsWith('#')) return term
  const isWildcardQuery = term.endsWith('*')
  const cleaned = normalizeTagSearchValue(isWildcardQuery ? term.slice(1, -1) : term.slice(1))
  if (!cleaned) return ''
  return `${isWildcardQuery ? TAG_SEARCH_WILDCARD_PREFIX : TAG_SEARCH_PREFIX}${cleaned}`
}).filter(Boolean)
const isTagSearchToken = (term) => term.startsWith(TAG_SEARCH_PREFIX) || term.startsWith(TAG_SEARCH_WILDCARD_PREFIX)
const index = new MiniSearch({
  fields: ['text'],
  storeFields: ['text'],
  tokenize: tokenizeSearchText,
  searchOptions: {
    tokenize: tokenizeSearchText,
    prefix: (term) => !isTagSearchToken(term),
    fuzzy: (term) => (isTagSearchToken(term) ? false : 0.2),
  },
})
index.add({ id: 'plain', text: 'dns troubleshooting' })
index.add({ id: 'tagged-dns', text: ['archivetag-dns', ...prefixTokens('dns')].join(' ') })
index.add({ id: 'tagged-images', text: ['archivetag-images', ...prefixTokens('images')].join(' ') })
index.add({ id: 'tagged-image-tools', text: ['archivetag-image-tools', ...prefixTokens('image-tools')].join(' ') })
const exactResults = index.search('#dns').map((result) => result.id)
if (JSON.stringify(exactResults) !== JSON.stringify(['tagged-dns'])) {
  console.error(JSON.stringify(exactResults))
  process.exit(1)
}
const wildcardResults = index.search('#image*').map((result) => result.id)
if (JSON.stringify(wildcardResults.slice().sort()) !== JSON.stringify(['tagged-image-tools', 'tagged-images'])) {
  console.error(JSON.stringify(wildcardResults))
  process.exit(1)
}
"""

        subprocess.run(["node", "-e", script], check=True, cwd=Path(__file__).resolve().parents[1])


if __name__ == "__main__":
    unittest.main()
