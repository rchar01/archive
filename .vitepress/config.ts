import { defineConfig } from 'vitepress'
import nav from './nav.generated'
import sidebar from './sidebar.generated'

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
  srcDir: 'content',
  outDir: 'site',
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
    knowledgePanel: true,
    knowledgePanelBacklinks: true,
    knowledgePanelRelated: true,
    search: { provider: 'local' },
  },
})
