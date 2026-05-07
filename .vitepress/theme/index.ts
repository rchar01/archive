import DefaultTheme from 'vitepress/theme'
import type { Theme } from 'vitepress'
import { h } from 'vue'

import './archive.css'
import './mermaid.css'
import KnowledgePanel from './KnowledgePanel.vue'
import MermaidDiagram from './MermaidDiagram.vue'
import OutlineAutoScroll from './OutlineAutoScroll'

const theme: Theme = {
  extends: DefaultTheme,
  enhanceApp({ app }) {
    app.component('MermaidDiagram', MermaidDiagram)
  },
  Layout() {
    return h(DefaultTheme.Layout, null, {
      'aside-outline-after': () => h(OutlineAutoScroll),
      'doc-after': () => h(KnowledgePanel),
    })
  },
}

export default theme
