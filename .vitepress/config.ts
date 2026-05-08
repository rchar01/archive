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

function escapeVueProp(value: string): string {
  return value
    .replace(/&/g, '&amp;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
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
    search: { provider: 'local' },
  },
})
