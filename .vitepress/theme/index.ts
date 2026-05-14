import DefaultTheme from 'vitepress/theme'
import type { Theme } from 'vitepress'
import { defineAsyncComponent, h } from 'vue'

import './archive.css'
import './mermaid.css'
import BackToTop from './BackToTop.vue'
import KnowledgePanel from './KnowledgePanel.vue'
import MermaidDiagram from './MermaidDiagram.vue'
import OutlineAutoScroll from './OutlineAutoScroll'
import SearchHighlight from './SearchHighlight.vue'
import { patchLocalSearch } from './localSearch'

const KnowledgeGraph = defineAsyncComponent(() => import('./KnowledgeGraph.vue'))

const theme: Theme = {
  extends: DefaultTheme,
  enhanceApp({ app }) {
    patchLocalSearch()
    app.component('KnowledgeGraph', KnowledgeGraph)
    app.component('MermaidDiagram', MermaidDiagram)
  },
  Layout() {
    return h(DefaultTheme.Layout, null, {
      'aside-outline-after': () => h(OutlineAutoScroll),
      'doc-after': () => h(KnowledgePanel),
      'layout-bottom': () => [h(BackToTop), h(SearchHighlight)],
    })
  },
}

export default theme
