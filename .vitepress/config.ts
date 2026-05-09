import { existsSync, readFileSync } from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

import { defineConfig } from 'vitepress'

const CONFIG_DIR = path.dirname(fileURLToPath(import.meta.url))
const TOOL_ROOT = path.resolve(CONFIG_DIR, '..')

function normalizeInstanceName(value: string): string {
  const cleaned = value
    .trim()
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-+|-+$/g, '')
  return cleaned || 'default'
}

function resolveWorkspaceRoot(): string {
  const rawValue = process.env.WORKSPACE?.trim() ?? ''
  if (!rawValue) {
    return TOOL_ROOT
  }
  return path.resolve(rawValue)
}

function resolveArchiveInstance(workspaceRoot: string): string {
  const rawValue = process.env.ARCHIVE_INSTANCE?.trim() ?? ''
  if (rawValue) {
    return normalizeInstanceName(rawValue)
  }
  if (workspaceRoot === TOOL_ROOT) {
    return 'default'
  }
  return normalizeInstanceName(path.basename(workspaceRoot))
}

function readGeneratedJson<T>(filePath: string, fallback: T): T {
  if (!existsSync(filePath)) {
    return fallback
  }
  return JSON.parse(readFileSync(filePath, 'utf8')) as T
}

function toConfigPath(targetPath: string): string {
  const relativePath = path.relative(TOOL_ROOT, targetPath)
  return relativePath || '.'
}

const workspaceRoot = resolveWorkspaceRoot()
const archiveInstance = resolveArchiveInstance(workspaceRoot)
const useLegacyGeneratedLayout = archiveInstance === 'default' && workspaceRoot === TOOL_ROOT
const instanceRoot = path.join(TOOL_ROOT, '.instances', archiveInstance)
const generatedDir = useLegacyGeneratedLayout ? CONFIG_DIR : path.join(instanceRoot, 'generated')
const contentDir = useLegacyGeneratedLayout ? path.join(TOOL_ROOT, 'content') : path.join(instanceRoot, 'content')
const siteDir = useLegacyGeneratedLayout ? path.join(TOOL_ROOT, 'site') : path.join(instanceRoot, 'site')
const nav = readGeneratedJson(path.join(generatedDir, 'nav.generated.json'), [{ text: 'Home', link: '/' }])
const sidebar = readGeneratedJson(path.join(generatedDir, 'sidebar.generated.json'), {})
const TAG_SEARCH_PREFIX = 'archivetag-'
const TAG_SEARCH_WILDCARD_PREFIX = 'archivetagprefix-'

function escapeVueProp(value: string): string {
  return value
    .replace(/&/g, '&amp;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
}

function normalizeTagSearchValue(value: unknown): string {
  if (typeof value !== 'string') {
    return ''
  }
  const cleaned = value
    .trim()
    .toLowerCase()
    .replace(/[^\p{L}\p{N}]+/gu, '-')
    .replace(/^-+|-+$/g, '')
  return cleaned
}

function normalizeTagSearchToken(value: unknown): string {
  const cleaned = normalizeTagSearchValue(value)
  return cleaned ? `${TAG_SEARCH_PREFIX}${cleaned}` : ''
}

function prefixTagSearchTokens(value: string): string[] {
  const tokens: string[] = []
  for (let length = 1; length <= value.length; length += 1) {
    tokens.push(`${TAG_SEARCH_WILDCARD_PREFIX}${value.slice(0, length)}`)
  }
  return tokens
}

function collectTagSearchTokens(frontmatter: Record<string, unknown> | undefined): string[] {
  if (!frontmatter) {
    return []
  }
  const seen = new Set<string>()
  const tokens: string[] = []
  for (const field of ['tags', 'search_tags']) {
    const rawValue = frontmatter[field]
    if (!Array.isArray(rawValue)) {
      continue
    }
    for (const item of rawValue) {
      const normalized = normalizeTagSearchValue(item)
      if (!normalized) {
        continue
      }
      const tagTokens = [
        `${TAG_SEARCH_PREFIX}${normalized}`,
        ...prefixTagSearchTokens(normalized),
      ]
      for (const token of tagTokens) {
        if (seen.has(token)) {
          continue
        }
        seen.add(token)
        tokens.push(token)
      }
    }
  }
  return tokens
}

function tokenizeSearchText(text: string): string[] {
  return (text.match(/#[\p{L}\p{N}]+(?:-[\p{L}\p{N}]+)*\*?|[\p{L}\p{N}]+(?:[-_][\p{L}\p{N}]+)*/gu) ?? [])
    .map((term) => {
      if (!term.startsWith('#')) {
        return term
      }
      const isWildcardQuery = term.endsWith('*')
      const cleaned = normalizeTagSearchValue(isWildcardQuery ? term.slice(1, -1) : term.slice(1))
      if (!cleaned) {
        return ''
      }
      return `${isWildcardQuery ? TAG_SEARCH_WILDCARD_PREFIX : TAG_SEARCH_PREFIX}${cleaned}`
    })
    .filter((term) => term.length > 0)
}

const searchTokenizer = (text: string) =>
  (text.match(/#[\p{L}\p{N}]+(?:-[\p{L}\p{N}]+)*\*?|[\p{L}\p{N}]+(?:[-_][\p{L}\p{N}]+)*/gu) ?? [])
    .map((term) => {
      if (!term.startsWith('#')) {
        return term
      }
      const isWildcardQuery = term.endsWith('*')
      const cleaned = term
        .slice(1, isWildcardQuery ? -1 : undefined)
        .trim()
        .toLowerCase()
        .replace(/[^\p{L}\p{N}]+/gu, '-')
        .replace(/^-+|-+$/g, '')
      return cleaned ? `${isWildcardQuery ? 'archivetagprefix-' : 'archivetag-'}${cleaned}` : ''
    })
    .filter((term) => term.length > 0)

const searchPrefixOption = (term: string) => !term.startsWith('archivetag-') && !term.startsWith('archivetagprefix-')
const searchFuzzyOption = (term: string) => (term.startsWith('archivetag-') || term.startsWith('archivetagprefix-') ? false : 0.2)

async function renderSearchHtml(src: string, env: object, md: { renderAsync?: (src: string, env: object) => Promise<string>; render: (src: string, env: object) => string }): Promise<string> {
  if (typeof md.renderAsync === 'function') {
    return md.renderAsync(src, env)
  }
  return md.render(src, env)
}

export default defineConfig({
  lang: 'en-US',
  title: 'Archive',
  description: 'Source-first documentation system',
  srcDir: toConfigPath(contentDir),
  outDir: toConfigPath(siteDir),
  head: [
    ['link', { rel: 'icon', type: 'image/svg+xml', href: '/vitepress-logo-mini.svg' }],
  ],
  vite: {
    publicDir: path.join(TOOL_ROOT, 'content', 'public'),
    resolve: {
      alias: {
        '@archive-generated': generatedDir,
      },
    },
  },
  markdown: {
    config(md) {
      const defaultFence = md.renderer.rules.fence

      md.renderer.rules.fence = (tokens, idx, options, env, self) => {
        const token = tokens[idx]
        if (token.info.trim() === 'mermaid') {
          const code = escapeVueProp(JSON.stringify(token.content))
          return `<MermaidDiagram :code='${code}' />`
        }

        return defaultFence ? defaultFence(tokens, idx, options, env, self) : self.renderToken(tokens, idx, options)
      }
    },
  },
  cleanUrls: true,
  themeConfig: {
    nav,
    sidebar,
    outline: { level: [2, 3] },
    knowledgePanel: true,
    knowledgePanelBacklinks: true,
    knowledgePanelRelated: true,
    search: {
      provider: 'local',
      options: {
        miniSearch: {
          options: {
            tokenize: searchTokenizer,
          },
          searchOptions: {
            prefix: searchPrefixOption,
            fuzzy: searchFuzzyOption,
            tokenize: searchTokenizer,
          },
        },
        async _render(src, env, md) {
          const html = await renderSearchHtml(src, env, md)
          if (env.frontmatter?.search === false) {
            return ''
          }
          const tagTokens = collectTagSearchTokens(env.frontmatter)
          if (tagTokens.length === 0) {
            return html
          }
          return `${html}\n<div hidden>${tagTokens.join(' ')}</div>`
        },
      },
    },
  },
})
