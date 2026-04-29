<script setup lang="ts">
import { nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useData } from 'vitepress'

import { loadMermaid, nextMermaidDiagramId } from './mermaidClient'

const props = defineProps<{
  code: string
}>()

const { isDark } = useData()
const container = ref<HTMLElement | null>(null)
const svg = ref('')
const error = ref('')

let renderSequence = 0

function mermaidTheme(dark: boolean): 'dark' | 'default' {
  return dark ? 'dark' : 'default'
}

async function renderDiagram() {
  if (import.meta.env.SSR) {
    return
  }

  const source = props.code.trim()
  const currentRender = ++renderSequence

  svg.value = ''
  error.value = ''

  if (!source) {
    return
  }

  try {
    const mermaid = await loadMermaid()

    mermaid.initialize({
      startOnLoad: false,
      securityLevel: 'strict',
      theme: mermaidTheme(isDark.value),
    })

    const { svg: renderedSvg, bindFunctions } = await mermaid.render(nextMermaidDiagramId(), source)
    if (currentRender !== renderSequence) {
      return
    }

    svg.value = renderedSvg
    await nextTick()

    if (currentRender !== renderSequence || !container.value) {
      return
    }

    bindFunctions?.(container.value)
  } catch (cause) {
    if (currentRender !== renderSequence) {
      return
    }

    error.value = cause instanceof Error ? cause.message : 'Unknown Mermaid render error.'
    console.error('Failed to render Mermaid diagram.', cause)
  }
}

onMounted(() => {
  void renderDiagram()
})

watch([() => props.code, () => isDark.value], () => {
  void renderDiagram()
})

onBeforeUnmount(() => {
  renderSequence += 1
})
</script>

<template>
  <div class="mermaid-diagram">
    <div
      v-if="svg"
      ref="container"
      class="mermaid-diagram__graphic"
      v-html="svg"
    />
    <pre
      v-else
      class="mermaid-diagram__source"
    ><code>{{ code }}</code></pre>
    <p
      v-if="error"
      class="mermaid-diagram__error"
    >
      Mermaid render failed. Showing source.
    </p>
  </div>
</template>
