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
        local_search = (vitepress_dir / "theme" / "localSearch.ts").read_text()
        knowledge_panel = (vitepress_dir / "theme" / "KnowledgePanel.vue").read_text()
        mermaid_component = (vitepress_dir / "theme" / "MermaidDiagram.vue").read_text()
        mermaid_client = (vitepress_dir / "theme" / "mermaidClient.ts").read_text()
        search_highlight = (vitepress_dir / "theme" / "SearchHighlight.vue").read_text()
        archive_css = (vitepress_dir / "theme" / "archive.css").read_text()

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
        self.assertIn("function splitSearchHtmlIntoSections(html: string): SearchSection[]", config)
        self.assertIn("async function splitIntoSearchSections(file: string, html: string): Promise<SearchSection[]>", config)
        self.assertIn("path.basename(file, path.extname(file))", config)
        self.assertIn("const searchTokenizer = (text: string) =>", config)
        self.assertIn("const searchPrefixOption = (term: string) => !term.startsWith('archivetag-') && !term.startsWith('archivetagprefix-')", config)
        self.assertIn("const searchFuzzyOption = (term: string) => (term.startsWith('archivetag-') || term.startsWith('archivetagprefix-') ? false : 0.2)", config)
        self.assertIn("async function renderSearchHtml(", config)
        self.assertIn("tokenize: searchTokenizer", config)
        self.assertIn("_splitIntoSections: splitIntoSearchSections", config)
        self.assertIn("searchOptions: {", config)
        self.assertIn("prefix: searchPrefixOption", config)
        self.assertIn("fuzzy: searchFuzzyOption", config)
        self.assertIn("return cleaned ? `${isWildcardQuery ? 'archivetagprefix-' : 'archivetag-'}${cleaned}` : ''", config)
        self.assertIn("const html = await renderSearchHtml(src, env, md)", config)
        self.assertIn("const tagTokens = collectTagSearchTokens(env.frontmatter)", config)
        self.assertIn("return appendTagSearchMarker(html, tagTokens)", config)
        self.assertIn("import { patchLocalSearch } from './localSearch'", theme_index)
        self.assertIn("import SearchHighlight from './SearchHighlight.vue'", theme_index)
        self.assertIn("patchLocalSearch()", theme_index)
        self.assertIn("const TAG_QUERY_RE =", local_search)
        self.assertIn("const LAST_QUERY_KEY = 'archive:last-local-search-query'", local_search)
        self.assertIn("__archiveLastLocalSearchQuery = query", local_search)
        self.assertIn("combineWith: 'AND'", local_search)
        self.assertIn("isPageLevelResult", local_search)
        self.assertIn("doc-after", theme_index)
        self.assertIn("KnowledgePanel", theme_index)
        self.assertIn("MermaidDiagram", theme_index)
        self.assertIn("SearchHighlight", theme_index)
        self.assertIn("app.component('MermaidDiagram'", theme_index)
        self.assertIn("const SEARCH_FILTER_KEY = 'vitepress:local-search-filter'", search_highlight)
        self.assertIn("const LAST_QUERY_KEY = 'archive:last-local-search-query'", search_highlight)
        self.assertIn("const PENDING_HIGHLIGHT_KEY = 'archive:pending-search-highlight'", search_highlight)
        self.assertIn("Keep code examples untouched", search_highlight)
        self.assertIn("'pre',", search_highlight)
        self.assertIn("'code',", search_highlight)
        self.assertIn('div[class*="language-"]', search_highlight)
        self.assertIn("'.vp-code-group',", search_highlight)
        self.assertIn("'.lang',", search_highlight)
        self.assertIn("'.copy',", search_highlight)
        self.assertIn("let activeHighlight: PendingHighlight | null = null", search_highlight)
        self.assertIn("let highlightedPath: string | null = null", search_highlight)
        self.assertIn("onContentUpdated(scheduleHighlightRetries)", search_highlight)
        self.assertIn("if (targetPath === currentPath())", search_highlight)
        self.assertIn("wait for VitePress to mount the destination body", search_highlight)
        self.assertIn("import { onContentUpdated, useRouter } from 'vitepress'", search_highlight)
        self.assertIn("function scheduleHighlightRetries(): void", search_highlight)
        self.assertIn("function scheduleUntilHighlighted(): void", search_highlight)
        self.assertIn("function pageContentRoot(): Element | null", search_highlight)
        self.assertIn("function markTerms(root: Element, terms: string[]): number", search_highlight)
        self.assertIn("(?<![\\\\p{L}\\\\p{N}_-])", search_highlight)
        self.assertIn("function applyActiveHighlight(): void", search_highlight)
        self.assertIn("activeHighlight = { ...pending, terms }", search_highlight)
        self.assertIn("if (count > 0)", search_highlight)
        self.assertIn("router.go = ((target: string) =>", search_highlight)
        self.assertIn("captureSearchTarget(target)", search_highlight)
        self.assertIn("function extractHighlightTerms(query: string): string[]", search_highlight)
        self.assertIn("if (token.startsWith('#'))", search_highlight)
        self.assertIn("function clearHighlights(root: ParentNode = document, clearActive = true): void", search_highlight)
        self.assertIn("if (highlightedPath && highlightedPath !== currentPath())", search_highlight)
        self.assertIn("function closestSearchResult(value: EventTarget | null): HTMLAnchorElement | null", search_highlight)
        self.assertIn("document.addEventListener('pointerdown', onDocumentPointerDown, true)", search_highlight)
        self.assertIn("document.addEventListener('keydown', onDocumentKeydown, true)", search_highlight)
        self.assertIn("event.key === 'Escape'", search_highlight)
        self.assertIn(".VPLocalSearchBox a.result[href]", search_highlight)
        self.assertIn("mark.archive-search-highlight", archive_css)
        self.assertIn("var(--vp-local-search-highlight-bg", archive_css)
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
        script = r"""
const MiniSearch = require('minisearch')
const TAG_SEARCH_PREFIX = 'archivetag-'
const TAG_SEARCH_WILDCARD_PREFIX = 'archivetagprefix-'
const normalizeTagSearchValue = (value) => {
  if (typeof value !== 'string') return ''
  return value.trim().toLowerCase().replace(/[^\p{L}\p{N}]+/gu, '-').replace(/^-+|-+$/g, '')
}
const prefixTokens = (value) => Array.from({ length: value.length }, (_, index) => `${TAG_SEARCH_WILDCARD_PREFIX}${value.slice(0, index + 1)}`)
const tokenizeSearchText = (text) => (text.match(/#[\p{L}\p{N}]+(?:-[\p{L}\p{N}]+)*\*?|[\p{L}\p{N}]+(?:[-_][\p{L}\p{N}]+)*/gu) ?? []).map((term) => {
  if (!term.startsWith('#')) return term
  const isWildcardQuery = term.endsWith('*')
  const cleaned = normalizeTagSearchValue(isWildcardQuery ? term.slice(1, -1) : term.slice(1))
  if (!cleaned) return ''
  return `${isWildcardQuery ? TAG_SEARCH_WILDCARD_PREFIX : TAG_SEARCH_PREFIX}${cleaned}`
}).filter(Boolean)
const isTagSearchToken = (term) => term.startsWith(TAG_SEARCH_PREFIX) || term.startsWith(TAG_SEARCH_WILDCARD_PREFIX)
const TAG_QUERY_RE = /#[\p{L}\p{N}]+(?:-[\p{L}\p{N}]+)*\*?/u
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
const isPageLevelResult = (result) => !result.id.includes('#')
const search = (query) => {
  if (TAG_QUERY_RE.test(query)) {
    return index.search(query, { combineWith: 'AND', filter: isPageLevelResult })
  }
  return index.search(query, { filter: (result) => !isPageLevelResult(result) })
}
index.add({ id: 'plain#troubleshooting', text: 'dns troubleshooting' })
index.add({ id: 'tagged-dns', text: ['dns troubleshooting', 'archivetag-dns', ...prefixTokens('dns')].join(' ') })
index.add({ id: 'tagged-images', text: ['image storage', 'archivetag-images', ...prefixTokens('images')].join(' ') })
index.add({ id: 'tagged-images#storage', text: 'image storage' })
index.add({ id: 'tagged-image-tools', text: ['image conversion', 'archivetag-image-tools', ...prefixTokens('image-tools')].join(' ') })
index.add({ id: 'tagged-image-tools#conversion', text: 'image conversion' })
index.add({ id: 'tagged-image-tools-dns', text: ['dns image routing', 'archivetag-dns', ...prefixTokens('dns'), 'archivetag-image-tools', ...prefixTokens('image-tools')].join(' ') })
const exactResults = search('#dns').map((result) => result.id)
if (JSON.stringify(exactResults) !== JSON.stringify(['tagged-dns', 'tagged-image-tools-dns'])) {
  console.error(JSON.stringify(exactResults))
  process.exit(1)
}
const wildcardResults = search('#image*').map((result) => result.id)
if (JSON.stringify(wildcardResults.slice().sort()) !== JSON.stringify(['tagged-image-tools', 'tagged-image-tools-dns', 'tagged-images'])) {
  console.error(JSON.stringify(wildcardResults))
  process.exit(1)
}
const qualifiedResults = search('#image* storage').map((result) => result.id)
if (JSON.stringify(qualifiedResults) !== JSON.stringify(['tagged-images'])) {
  console.error(JSON.stringify(qualifiedResults))
  process.exit(1)
}
const multiTagResults = search('#dns #image-tools routing').map((result) => result.id)
if (JSON.stringify(multiTagResults) !== JSON.stringify(['tagged-image-tools-dns'])) {
  console.error(JSON.stringify(multiTagResults))
  process.exit(1)
}
const plainResults = search('image').map((result) => result.id)
if (plainResults.includes('tagged-images') || plainResults.includes('tagged-image-tools')) {
  console.error(JSON.stringify(plainResults))
  process.exit(1)
}
"""

        subprocess.run(["node", "-e", script], check=True, cwd=Path(__file__).resolve().parents[1])


if __name__ == "__main__":
    unittest.main()
