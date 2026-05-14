<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, ref, shallowRef, watch } from 'vue'
import { useRouter } from 'vitepress'
import {
  forceCenter,
  forceCollide,
  forceLink,
  forceManyBody,
  forceSimulation,
  forceX,
  forceY,
  type Simulation,
  type SimulationLinkDatum,
  type SimulationNodeDatum,
} from 'd3-force'

import linkgraphData from '@archive-generated/knowledge/linkgraph.generated.json'
import pagesData from '@archive-generated/knowledge/pages.generated.json'
import relatedData from '@archive-generated/knowledge/related.generated.json'

type PageInfo = {
  title?: string
  link?: string
  kind?: string
  section?: string
  tags?: string[]
  summary?: string
  updated?: string
  source_path?: string
  related_manual?: string[]
  workflow?: {
    knowledge_panel?: boolean
    backlinks?: boolean
    related?: boolean
  }
}

type PageMap = Record<string, PageInfo>
type LinkgraphMap = Record<string, { outbound?: string[]; backlinks?: string[] }>
type RelatedMap = Record<string, { related?: string[] }>
type GraphPage = Required<Pick<PageInfo, 'title' | 'link' | 'kind' | 'section'>> & {
  tags: string[]
  summary: string
  relatedManual: string[]
}
type GraphNode = SimulationNodeDatum & GraphPage & {
  id: string
  radius: number
  degree: number
  label: string
}
type GraphEdge = SimulationLinkDatum<GraphNode> & {
  id: string
  sourceId: string
  targetId: string
  type: 'link' | 'curated' | 'suggested' | 'tag'
  label: string
}
type ViewTransform = {
  x: number
  y: number
  k: number
}

const pages = pagesData as PageMap
const linkgraph = linkgraphData as LinkgraphMap
const relatedIndex = relatedData as RelatedMap
const router = useRouter()

const WIDTH = 1080
const HEIGHT = 640
const CENTER_X = WIDTH / 2
const CENTER_Y = HEIGHT / 2
const NODE_LIMIT = 160
const MIN_ZOOM = 0.45
const MAX_ZOOM = 2.6
const FIT_MAX_ZOOM = 2.2
const INITIAL_TRANSFORM: ViewTransform = { x: 0, y: 0, k: 1 }
const GOLDEN_ANGLE = Math.PI * (3 - Math.sqrt(5))

const selectedKind = ref('')
const selectedSection = ref('')
const selectedTag = ref('')
const searchQuery = ref('')
const focusedLink = ref('')
const selectedLink = ref('')
const hoveredLink = ref('')
const neighborhoodOnly = ref(false)
const showLinks = ref(true)
const showCurated = ref(true)
const showSuggested = ref(true)
const showTagEdges = ref(false)
const showIsolated = ref(true)
const transform = ref<ViewTransform>({ ...INITIAL_TRANSFORM })
const graphNodes = shallowRef<GraphNode[]>([])
const graphEdges = shallowRef<GraphEdge[]>([])
const graphStage = ref<HTMLDivElement | null>(null)
const isClient = ref(false)
const isPanning = ref(false)
const draggingNodeId = ref('')
const pointerStart = ref({ x: 0, y: 0 })
const panStart = ref<ViewTransform>({ ...INITIAL_TRANSFORM })
const didDragNode = ref(false)
let simulation: Simulation<GraphNode, GraphEdge> | null = null
let fitGraphTimeout: number | undefined

function normalizePath(path: string): string {
  const cleaned = path.split(/[?#]/u, 1)[0]?.trim() ?? ''
  if (!cleaned || cleaned === '/') {
    return '/'
  }
  const prefixed = cleaned.startsWith('/') ? cleaned : `/${cleaned}`
  return prefixed.endsWith('/') ? prefixed.slice(0, -1) : prefixed
}

function normalizeFilterValue(value: string): string {
  return value.trim().toLowerCase()
}

function clamp(value: number, min: number, max: number): number {
  return Math.min(Math.max(value, min), max)
}

function pageLabel(title: string): string {
  const cleaned = title.trim()
  if (cleaned.length <= 30) {
    return cleaned
  }
  return `${cleaned.slice(0, 27).trimEnd()}...`
}

function searchableText(page: GraphPage): string {
  const tagText = page.tags.flatMap((tag) => [tag, `#${tag}`]).join(' ')
  return `${page.title} ${page.link} ${page.kind} ${page.section} ${page.summary} ${tagText}`.toLowerCase()
}

function queryTerms(value: string): string[] {
  return value
    .trim()
    .toLowerCase()
    .split(/\s+/u)
    .map((term) => term.replace(/^#/u, ''))
    .filter(Boolean)
}

function graphPoint(event: PointerEvent | WheelEvent): { x: number; y: number } {
  const rect = graphStage.value?.getBoundingClientRect()
  if (!rect) {
    return { x: CENTER_X, y: CENTER_Y }
  }
  const viewX = (event.clientX - rect.left) * (WIDTH / rect.width)
  const viewY = (event.clientY - rect.top) * (HEIGHT / rect.height)
  return {
    x: (viewX - transform.value.x) / transform.value.k,
    y: (viewY - transform.value.y) / transform.value.k,
  }
}

function edgeNode(value: string | number | GraphNode | undefined): GraphNode | null {
  if (!value || typeof value === 'string' || typeof value === 'number') {
    return null
  }
  return value
}

const allPages = computed<GraphPage[]>(() =>
  Object.entries(pages)
    .map(([link, page]) => {
      const normalizedLink = normalizePath(page.link || link)
      return {
        title: page.title?.trim() || normalizedLink,
        link: normalizedLink,
        kind: page.kind?.trim() || 'page',
        section: page.section?.trim() || 'general',
        tags: Array.isArray(page.tags) ? page.tags.filter((tag): tag is string => typeof tag === 'string' && tag.trim().length > 0) : [],
        summary: page.summary?.trim() || '',
        relatedManual: Array.isArray(page.related_manual)
          ? page.related_manual.filter((target): target is string => typeof target === 'string' && target.trim().length > 0).map(normalizePath)
          : [],
      }
    })
    .sort((left, right) => left.title.localeCompare(right.title) || left.link.localeCompare(right.link)),
)

const pagesByLink = computed(() => new Map(allPages.value.map((page) => [page.link, page])))
const kinds = computed(() => [...new Set(allPages.value.map((page) => page.kind))].sort())
const sections = computed(() => [...new Set(allPages.value.map((page) => page.section))].sort())
const tags = computed(() => [...new Set(allPages.value.flatMap((page) => page.tags.map((tag) => tag.trim())))].sort())

const controlFilteredPages = computed(() => {
  const kind = normalizeFilterValue(selectedKind.value)
  const section = normalizeFilterValue(selectedSection.value)
  const tag = normalizeFilterValue(selectedTag.value)
  return allPages.value.filter((page) => {
    if (kind && normalizeFilterValue(page.kind) !== kind) {
      return false
    }
    if (section && normalizeFilterValue(page.section) !== section) {
      return false
    }
    if (tag && !page.tags.some((pageTag) => normalizeFilterValue(pageTag) === tag)) {
      return false
    }
    return true
  })
})

const baseFilteredPages = computed(() => {
  const terms = queryTerms(searchQuery.value)
  if (terms.length === 0) {
    return controlFilteredPages.value
  }
  return controlFilteredPages.value.filter((page) => {
    const text = searchableText(page)
    return terms.every((term) => text.includes(term))
  })
})

const focusNeighborhood = computed(() => {
  if (!focusedLink.value) {
    return new Set<string>()
  }
  const links = new Set<string>([focusedLink.value])
  for (const link of linkgraph[focusedLink.value]?.outbound ?? []) {
    links.add(normalizePath(link))
  }
  for (const link of linkgraph[focusedLink.value]?.backlinks ?? []) {
    links.add(normalizePath(link))
  }
  return links
})

const filteredPages = computed(() => {
  if (!neighborhoodOnly.value || !focusedLink.value) {
    return baseFilteredPages.value
  }
  return baseFilteredPages.value.filter((page) => focusNeighborhood.value.has(page.link))
})

const candidatePages = computed(() => filteredPages.value.slice(0, NODE_LIMIT))
const candidateLinks = computed(() => new Set(candidatePages.value.map((page) => page.link)))

function edgePriority(type: GraphEdge['type']): number {
  return { link: 4, curated: 3, suggested: 2, tag: 1 }[type]
}

function addEdge(edges: Map<string, GraphEdge>, source: string, target: string, type: GraphEdge['type'], label: string): void {
  if (!candidateLinks.value.has(source) || !candidateLinks.value.has(target) || source === target) {
    return
  }
  const id = [source, target].sort().join(' -> ')
  const existing = edges.get(id)
  if (existing && edgePriority(existing.type) >= edgePriority(type)) {
    return
  }
  edges.set(id, { id, source, target, sourceId: source, targetId: target, type, label })
}

const candidateEdges = computed(() => {
  const edges = new Map<string, GraphEdge>()
  if (showLinks.value) {
    for (const page of candidatePages.value) {
      for (const rawTarget of linkgraph[page.link]?.outbound ?? []) {
        addEdge(edges, page.link, normalizePath(rawTarget), 'link', 'article link')
      }
    }
  }
  if (showCurated.value) {
    for (const page of candidatePages.value) {
      for (const target of page.relatedManual) {
        addEdge(edges, page.link, target, 'curated', 'curated related')
      }
    }
  }
  if (showSuggested.value) {
    for (const page of candidatePages.value) {
      for (const rawTarget of relatedIndex[page.link]?.related ?? []) {
        addEdge(edges, page.link, normalizePath(rawTarget), 'suggested', 'suggested related')
      }
    }
  }
  if (showTagEdges.value) {
    const byTag = new Map<string, GraphPage[]>()
    for (const page of candidatePages.value) {
      for (const tag of page.tags) {
        const normalized = normalizeFilterValue(tag)
        if (normalized) {
          byTag.set(normalized, [...(byTag.get(normalized) ?? []), page])
        }
      }
    }
    for (const [tag, taggedPages] of byTag.entries()) {
      const sorted = taggedPages.slice().sort((left, right) => left.title.localeCompare(right.title))
      for (let index = 0; index < sorted.length - 1; index += 1) {
        addEdge(edges, sorted[index].link, sorted[index + 1].link, 'tag', `shared tag: ${tag}`)
      }
    }
  }
  return [...edges.values()]
})

const connectedCandidateLinks = computed(() => {
  const links = new Set<string>()
  for (const edge of candidateEdges.value) {
    links.add(edge.sourceId)
    links.add(edge.targetId)
  }
  return links
})
const visiblePages = computed(() => (showIsolated.value ? candidatePages.value : candidatePages.value.filter((page) => connectedCandidateLinks.value.has(page.link))))
const hasTruncatedNodes = computed(() => filteredPages.value.length > candidatePages.value.length)
const visibleLinks = computed(() => new Set(visiblePages.value.map((page) => page.link)))
const visibleLinkEdges = computed(() => candidateEdges.value.filter((edge) => visibleLinks.value.has(edge.sourceId) && visibleLinks.value.has(edge.targetId)))
const isolatedCount = computed(() => visiblePages.value.filter((page) => !connectedCandidateLinks.value.has(page.link)).length)

const graphNodeMap = computed(() => new Map(graphNodes.value.map((node) => [node.id, node])))
const selectedNode = computed(() => graphNodeMap.value.get(selectedLink.value) ?? graphNodeMap.value.get(focusedLink.value) ?? null)

const searchMatches = computed(() => {
  const terms = queryTerms(searchQuery.value)
  if (terms.length === 0) {
    return []
  }
  return controlFilteredPages.value
    .filter((page) => {
      const text = searchableText(page)
      return terms.every((term) => text.includes(term))
    })
    .slice(0, 8)
})
const activeFilters = computed(() => [
  ...(searchQuery.value.trim() ? [`Search: ${searchQuery.value.trim()}`] : []),
  ...(selectedKind.value ? [`Workflow: ${selectedKind.value}`] : []),
  ...(selectedSection.value ? [`Section: ${selectedSection.value}`] : []),
  ...(selectedTag.value ? [`Tag: ${selectedTag.value}`] : []),
])

const activeLink = computed(() => hoveredLink.value || selectedLink.value || focusedLink.value)
const activeNeighborhood = computed(() => {
  if (!activeLink.value) {
    return new Set<string>()
  }
  const links = new Set<string>([activeLink.value])
  for (const edge of graphEdges.value) {
    if (edge.sourceId === activeLink.value) {
      links.add(edge.targetId)
    }
    if (edge.targetId === activeLink.value) {
      links.add(edge.sourceId)
    }
  }
  return links
})
const selectedEdgeCounts = computed(() => {
  const link = selectedNode.value?.id ?? ''
  const counts = { links: 0, curated: 0, suggested: 0, tags: 0 }
  if (!link) {
    return counts
  }
  for (const edge of graphEdges.value) {
    if (edge.sourceId !== link && edge.targetId !== link) {
      continue
    }
    if (edge.type === 'link') {
      counts.links += 1
    } else if (edge.type === 'curated') {
      counts.curated += 1
    } else if (edge.type === 'suggested') {
      counts.suggested += 1
    } else {
      counts.tags += 1
    }
  }
  return counts
})

const resultSummary = computed(() => {
  const pageCount = filteredPages.value.length
  const shownCount = visiblePages.value.length
  const edgeCount = graphEdges.value.length
  if (pageCount === 0) {
    return 'No pages match the current filters.'
  }
  const visibleText = hasTruncatedNodes.value ? `${shownCount} of ${pageCount}` : `${shownCount}`
  const isolatedText = isolatedCount.value > 0 ? ` ${isolatedCount.value} isolated.` : ''
  return `Showing ${visibleText} pages connected by ${edgeCount} graph edges.${isolatedText}`
})

function buildInitialGraph(): { nodes: GraphNode[]; edges: GraphEdge[] } {
  const degreeByLink = new Map<string, number>()
  for (const edge of visibleLinkEdges.value) {
    degreeByLink.set(edge.source, (degreeByLink.get(edge.source) ?? 0) + 1)
    degreeByLink.set(edge.target, (degreeByLink.get(edge.target) ?? 0) + 1)
  }

  const nodes = visiblePages.value.map((page, index): GraphNode => {
    const angle = index * GOLDEN_ANGLE
    const radius = Math.sqrt(index + 1) * 30
    const degree = degreeByLink.get(page.link) ?? 0
    return {
      ...page,
      id: page.link,
      x: CENTER_X + Math.cos(angle) * radius,
      y: CENTER_Y + Math.sin(angle) * radius,
      radius: 8 + Math.min(degree, 8),
      degree,
      label: pageLabel(page.title),
    }
  })

  const edges = visibleLinkEdges.value.map((edge): GraphEdge => ({ ...edge, source: edge.sourceId, target: edge.targetId }))

  return { nodes, edges }
}

function stopSimulation(): void {
  simulation?.stop()
  simulation = null
}

function startSimulation(): void {
  stopSimulation()
  const nodes = graphNodes.value
  const edges = graphEdges.value
  if (!isClient.value || nodes.length === 0) {
    return
  }

  simulation = forceSimulation<GraphNode>(nodes)
    .force('link', forceLink<GraphNode, GraphEdge>(edges).id((node) => node.id).distance(110).strength(0.46))
    .force('charge', forceManyBody<GraphNode>().strength((node) => -220 - node.degree * 18))
    .force('collide', forceCollide<GraphNode>().radius((node) => node.radius + 26).strength(0.85))
    .force('x', forceX<GraphNode>(CENTER_X).strength(0.035))
    .force('y', forceY<GraphNode>(CENTER_Y).strength(0.035))
    .force('center', forceCenter(CENTER_X, CENTER_Y))
    .alpha(0.95)
    .alphaDecay(0.045)
    .on('tick', () => {
      graphNodes.value = [...nodes]
      graphEdges.value = [...edges]
    })
}

function rebuildGraph(): void {
  const graph = buildInitialGraph()
  graphNodes.value = graph.nodes
  graphEdges.value = graph.edges
  if (!visibleLinks.value.has(selectedLink.value)) {
    selectedLink.value = ''
  }
  if (!visibleLinks.value.has(focusedLink.value)) {
    focusedLink.value = ''
    neighborhoodOnly.value = false
  }
  void nextTick(startSimulation)
  scheduleFitGraph()
}

function clearFitGraphTimeout(): void {
  if (fitGraphTimeout === undefined) {
    return
  }
  window.clearTimeout(fitGraphTimeout)
  fitGraphTimeout = undefined
}

function scheduleFitGraph(): void {
  if (!isClient.value) {
    return
  }
  clearFitGraphTimeout()
  fitGraphTimeout = window.setTimeout(() => {
    fitGraphTimeout = undefined
    fitGraph()
  }, 450)
}

function resetFilters(): void {
  selectedKind.value = ''
  selectedSection.value = ''
  selectedTag.value = ''
  searchQuery.value = ''
  focusedLink.value = ''
  selectedLink.value = ''
  neighborhoodOnly.value = false
  showLinks.value = true
  showCurated.value = true
  showSuggested.value = true
  showTagEdges.value = false
  showIsolated.value = true
  void nextTick(fitGraph)
}

function nodesForFit(positioned: GraphNode[]): GraphNode[] {
  if (activeNeighborhood.value.size > 0) {
    const activeNodes = positioned.filter((node) => activeNeighborhood.value.has(node.id))
    if (activeNodes.length > 0) {
      return activeNodes
    }
  }

  const connectedNodes = positioned.filter((node) => node.degree > 0)
  if (connectedNodes.length >= 2) {
    return connectedNodes
  }

  return positioned
}

function fitGraph(): void {
  const positioned = graphNodes.value.filter((node) => typeof node.x === 'number' && typeof node.y === 'number')
  if (positioned.length === 0) {
    transform.value = { ...INITIAL_TRANSFORM }
    return
  }
  const fitNodes = nodesForFit(positioned)
  const minX = Math.min(...fitNodes.map((node) => Number(node.x) - node.radius))
  const maxX = Math.max(...fitNodes.map((node) => Number(node.x) + node.radius))
  const minY = Math.min(...fitNodes.map((node) => Number(node.y) - node.radius))
  const maxY = Math.max(...fitNodes.map((node) => Number(node.y) + node.radius))
  const graphWidth = Math.max(maxX - minX, 1)
  const graphHeight = Math.max(maxY - minY, 1)
  const nextZoom = clamp(Math.min((WIDTH * 0.9) / graphWidth, (HEIGHT * 0.86) / graphHeight), MIN_ZOOM, FIT_MAX_ZOOM)
  transform.value = {
    k: nextZoom,
    x: CENTER_X - ((minX + maxX) / 2) * nextZoom,
    y: CENTER_Y - ((minY + maxY) / 2) * nextZoom,
  }
}

function resetView(): void {
  fitGraph()
}

function focusPage(link: string): void {
  const normalized = normalizePath(link)
  focusedLink.value = normalized
  selectedLink.value = normalized
  void nextTick(fitGraph)
}

function focusFirstSearchMatch(): void {
  const match = searchMatches.value[0]
  if (match) {
    focusPage(match.link)
  }
}

function openNode(node: GraphNode): void {
  router.go(node.link)
}

function selectNode(node: GraphNode): void {
  if (didDragNode.value) {
    didDragNode.value = false
    return
  }
  focusedLink.value = node.id
  selectedLink.value = node.id
}

function filterByTag(tag: string): void {
  selectedTag.value = tag
}

function nodeIsMuted(node: GraphNode): boolean {
  return activeNeighborhood.value.size > 0 && !activeNeighborhood.value.has(node.id)
}

function nodeIsActive(node: GraphNode): boolean {
  return node.id === activeLink.value || node.id === selectedLink.value || node.id === focusedLink.value
}

function edgeIsMuted(edge: GraphEdge): boolean {
  return activeNeighborhood.value.size > 0 && edge.sourceId !== activeLink.value && edge.targetId !== activeLink.value
}

function edgeIsActive(edge: GraphEdge): boolean {
  return edge.sourceId === activeLink.value || edge.targetId === activeLink.value
}

function shouldShowLabel(node: GraphNode): boolean {
  return graphNodes.value.length <= 18 || node.degree >= 3 || nodeIsActive(node)
}

function edgeX(edge: GraphEdge, side: 'source' | 'target'): number {
  return edgeNode(side === 'source' ? edge.source : edge.target)?.x ?? CENTER_X
}

function edgeY(edge: GraphEdge, side: 'source' | 'target'): number {
  return edgeNode(side === 'source' ? edge.source : edge.target)?.y ?? CENTER_Y
}

function startPan(event: PointerEvent): void {
  if (draggingNodeId.value || event.button !== 0) {
    return
  }
  isPanning.value = true
  pointerStart.value = { x: event.clientX, y: event.clientY }
  panStart.value = { ...transform.value }
  ;(event.currentTarget as Element).setPointerCapture?.(event.pointerId)
}

function movePointer(event: PointerEvent): void {
  if (draggingNodeId.value) {
    const point = graphPoint(event)
    const node = graphNodes.value.find((item) => item.id === draggingNodeId.value)
    if (node) {
      node.fx = point.x
      node.fy = point.y
      didDragNode.value = true
      simulation?.alphaTarget(0.18).restart()
    }
    return
  }

  if (!isPanning.value) {
    return
  }
  transform.value = {
    ...transform.value,
    x: panStart.value.x + event.clientX - pointerStart.value.x,
    y: panStart.value.y + event.clientY - pointerStart.value.y,
  }
}

function endPointer(event: PointerEvent): void {
  if (draggingNodeId.value) {
    const node = graphNodes.value.find((item) => item.id === draggingNodeId.value)
    if (node) {
      node.fx = null
      node.fy = null
    }
    draggingNodeId.value = ''
    simulation?.alphaTarget(0)
  }
  isPanning.value = false
  ;(event.currentTarget as Element).releasePointerCapture?.(event.pointerId)
}

function startNodeDrag(node: GraphNode, event: PointerEvent): void {
  if (event.button !== 0) {
    return
  }
  draggingNodeId.value = node.id
  selectedLink.value = node.id
  didDragNode.value = false
  node.fx = node.x
  node.fy = node.y
  ;(event.currentTarget as Element).setPointerCapture?.(event.pointerId)
  simulation?.alphaTarget(0.22).restart()
}

function zoomGraph(event: WheelEvent): void {
  event.preventDefault()
  const rect = graphStage.value?.getBoundingClientRect()
  if (!rect) {
    return
  }
  const oldZoom = transform.value.k
  const nextZoom = clamp(oldZoom * (event.deltaY > 0 ? 0.88 : 1.14), MIN_ZOOM, MAX_ZOOM)
  const px = (event.clientX - rect.left) * (WIDTH / rect.width)
  const py = (event.clientY - rect.top) * (HEIGHT / rect.height)
  const graphX = (px - transform.value.x) / oldZoom
  const graphY = (py - transform.value.y) / oldZoom
  transform.value = {
    k: nextZoom,
    x: px - graphX * nextZoom,
    y: py - graphY * nextZoom,
  }
}

watch([visiblePages, visibleLinkEdges], rebuildGraph, { immediate: true })

onMounted(() => {
  isClient.value = true
  startSimulation()
  scheduleFitGraph()
})

onBeforeUnmount(() => {
  clearFitGraphTimeout()
  stopSimulation()
})
</script>

<template>
  <section class="knowledge-graph" aria-labelledby="knowledge-graph-title">
    <div class="knowledge-graph__toolbar">
      <div class="knowledge-graph__filters">
        <div class="knowledge-graph__control knowledge-graph__control--search">
          <label for="knowledge-graph-search">Search Graph</label>
          <input
            id="knowledge-graph-search"
            v-model="searchQuery"
            type="search"
            autocomplete="off"
            placeholder="Search title, section, summary, route, or #tag"
            @keydown.enter.prevent="focusFirstSearchMatch"
          />
        </div>

        <div class="knowledge-graph__control">
          <label for="knowledge-graph-kind">Workflow</label>
          <select id="knowledge-graph-kind" v-model="selectedKind">
            <option value="">All workflows</option>
            <option v-for="kind in kinds" :key="kind" :value="kind">{{ kind }}</option>
          </select>
        </div>

        <div class="knowledge-graph__control">
          <label for="knowledge-graph-section">Section</label>
          <select id="knowledge-graph-section" v-model="selectedSection">
            <option value="">All sections</option>
            <option v-for="section in sections" :key="section" :value="section">{{ section }}</option>
          </select>
        </div>

        <div class="knowledge-graph__control">
          <label for="knowledge-graph-tag">Tag</label>
          <select id="knowledge-graph-tag" v-model="selectedTag">
            <option value="">All tags</option>
            <option v-for="tag in tags" :key="tag" :value="tag">{{ tag }}</option>
          </select>
        </div>
      </div>

      <div class="knowledge-graph__options">
        <div class="knowledge-graph__option-group" aria-label="Edge types">
          <span class="knowledge-graph__actions-label">Edges</span>
          <label class="knowledge-graph__checkbox">
            <input v-model="showLinks" type="checkbox" />
            Links
          </label>
          <label class="knowledge-graph__checkbox">
            <input v-model="showCurated" type="checkbox" />
            Curated
          </label>
          <label class="knowledge-graph__checkbox">
            <input v-model="showSuggested" type="checkbox" />
            Suggested
          </label>
          <label class="knowledge-graph__checkbox">
            <input v-model="showTagEdges" type="checkbox" />
            Tags
          </label>
        </div>

        <div class="knowledge-graph__option-group" aria-label="Graph view">
          <span class="knowledge-graph__actions-label">View</span>
          <label class="knowledge-graph__checkbox">
            <input v-model="neighborhoodOnly" type="checkbox" :disabled="!focusedLink" />
            Neighborhood
          </label>
          <label class="knowledge-graph__checkbox">
            <input v-model="showIsolated" type="checkbox" />
            Isolated
          </label>
        </div>

        <div class="knowledge-graph__option-group knowledge-graph__option-group--actions">
          <button type="button" class="knowledge-graph__button" @click="resetView">Reset View</button>
          <button type="button" class="knowledge-graph__button" @click="resetFilters">Clear Filters</button>
        </div>
      </div>

      <div v-if="activeFilters.length > 0" class="knowledge-graph__active-filters">
        <span v-for="filter in activeFilters" :key="filter" class="knowledge-graph__filter-pill">{{ filter }}</span>
      </div>
    </div>

    <p id="knowledge-graph-title" class="knowledge-graph__summary">{{ resultSummary }}</p>
    <p v-if="hasTruncatedNodes" class="knowledge-graph__notice">
      Narrow the filters or focus a neighborhood to see omitted pages. The graph caps visible nodes to keep navigation responsive.
    </p>

    <div class="knowledge-graph__layout">
      <div
        ref="graphStage"
        class="knowledge-graph__stage"
        aria-label="Interactive graph of Archive pages connected by article links"
        @pointerdown="startPan"
        @pointermove="movePointer"
        @pointerup="endPointer"
        @pointercancel="endPointer"
        @wheel="zoomGraph"
      >
        <svg :viewBox="`0 0 ${WIDTH} ${HEIGHT}`" class="knowledge-graph__svg">
          <g :transform="`translate(${transform.x} ${transform.y}) scale(${transform.k})`">
            <g class="knowledge-graph__edges">
              <line
                v-for="edge in graphEdges"
                :key="edge.id"
                :x1="edgeX(edge, 'source')"
                :y1="edgeY(edge, 'source')"
                :x2="edgeX(edge, 'target')"
                :y2="edgeY(edge, 'target')"
                class="knowledge-graph__edge"
                :class="{
                  'knowledge-graph__edge--active': edgeIsActive(edge),
                  'knowledge-graph__edge--muted': edgeIsMuted(edge),
                  [`knowledge-graph__edge--${edge.type}`]: true,
                }"
              >
                <title>{{ pagesByLink.get(edge.sourceId)?.title }} -> {{ pagesByLink.get(edge.targetId)?.title }} ({{ edge.label }})</title>
              </line>
            </g>

            <g class="knowledge-graph__nodes">
              <g
                v-for="node in graphNodes"
                :key="node.id"
                class="knowledge-graph__node-group"
                :class="{
                  'knowledge-graph__node-group--active': nodeIsActive(node),
                  'knowledge-graph__node-group--muted': nodeIsMuted(node),
                }"
                :transform="`translate(${node.x ?? CENTER_X} ${node.y ?? CENTER_Y})`"
                tabindex="0"
                role="button"
                :aria-label="`Select ${node.title}`"
                @pointerenter="hoveredLink = node.id"
                @pointerleave="hoveredLink = ''"
                @pointerdown.stop="startNodeDrag(node, $event)"
                @click.stop="selectNode(node)"
                @keydown.enter.prevent="selectNode(node)"
              >
                <circle :r="node.radius" class="knowledge-graph__node" />
                <text v-if="shouldShowLabel(node)" :y="-node.radius - 8" class="knowledge-graph__label">{{ node.label }}</text>
                <title>{{ node.title }}{{ node.summary ? ` - ${node.summary}` : '' }}</title>
              </g>
            </g>
          </g>
        </svg>
      </div>

      <aside class="knowledge-graph__details" aria-live="polite">
        <header class="knowledge-graph__details-header">
          <p class="knowledge-graph__details-eyebrow">Context</p>
        </header>
        <template v-if="selectedNode">
          <div class="knowledge-graph__sections">
            <section class="knowledge-graph__section">
              <div class="knowledge-graph__section-header">
                <div class="knowledge-graph__section-heading">
                  <h3 class="knowledge-graph__section-title">Selected</h3>
                  <span class="knowledge-graph__count" aria-label="Selected article edge count">{{ selectedNode.degree }}</span>
                </div>
                <button type="button" class="knowledge-graph__open" @click="openNode(selectedNode)">Open Page</button>
              </div>

              <div class="knowledge-graph__selected-card">
                <span class="knowledge-graph__selected-topline">
                  <span class="knowledge-graph__selected-title" :title="selectedNode.title">{{ selectedNode.title }}</span>
                  <span class="knowledge-graph__selected-meta">
                    <span class="knowledge-graph__pill knowledge-graph__pill--neutral" :title="selectedNode.kind">{{ selectedNode.kind }}</span>
                    <span class="knowledge-graph__pill knowledge-graph__pill--neutral" :title="selectedNode.section">{{ selectedNode.section }}</span>
                    <span class="knowledge-graph__pill knowledge-graph__pill--muted" :title="selectedNode.link">{{ selectedNode.link }}</span>
                    <span v-if="selectedEdgeCounts.links > 0" class="knowledge-graph__pill knowledge-graph__pill--brand">{{ selectedEdgeCounts.links }} links</span>
                    <span v-if="selectedEdgeCounts.curated > 0" class="knowledge-graph__pill knowledge-graph__pill--brand">{{ selectedEdgeCounts.curated }} curated</span>
                    <span v-if="selectedEdgeCounts.suggested > 0" class="knowledge-graph__pill knowledge-graph__pill--muted">{{ selectedEdgeCounts.suggested }} suggested</span>
                    <span v-if="selectedEdgeCounts.tags > 0" class="knowledge-graph__pill knowledge-graph__pill--muted">{{ selectedEdgeCounts.tags }} tag edges</span>
                  </span>
                </span>
                <span v-if="selectedNode.summary" class="knowledge-graph__selected-summary" :title="selectedNode.summary">{{ selectedNode.summary }}</span>
              </div>

              <div v-if="selectedNode.tags.length > 0" class="knowledge-graph__tags" aria-label="Selected article tags">
                <button v-for="tag in selectedNode.tags" :key="tag" type="button" @click="filterByTag(tag)">{{ tag }}</button>
              </div>
            </section>
          </div>
        </template>
        <div v-else class="knowledge-graph__sections">
          <section class="knowledge-graph__section">
            <div class="knowledge-graph__section-header">
              <div class="knowledge-graph__section-heading">
                <h3 class="knowledge-graph__section-title">Selected</h3>
                <span class="knowledge-graph__count" aria-hidden="true">0</span>
              </div>
            </div>
            <p class="knowledge-graph__empty">Select a node or search result to inspect it. Use Open Page when you want to navigate.</p>
          </section>
        </div>
      </aside>
    </div>
  </section>
</template>

<style scoped>
.knowledge-graph {
  width: 100%;
  max-width: 100%;
  margin-top: 1.4rem;
}

.knowledge-graph__toolbar {
  display: grid;
  width: 100%;
  gap: 0.75rem;
  margin-bottom: 0.9rem;
}

.knowledge-graph__filters {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 0.75rem;
}

.knowledge-graph__control--search {
  grid-column: 1 / -1;
}

.knowledge-graph__control {
  position: relative;
  display: grid;
  align-content: start;
  gap: 0.25rem;
  min-width: 0;
}

.knowledge-graph__control label,
.knowledge-graph__details-eyebrow,
.knowledge-graph__actions-label {
  font-size: 0.78rem;
  font-weight: 700;
  color: var(--vp-c-text-2);
}

.knowledge-graph__control input,
.knowledge-graph__control select,
.knowledge-graph__button {
  min-height: 2.35rem;
  border: 1px solid var(--vp-c-divider);
  border-radius: 10px;
  font: inherit;
  color: var(--vp-c-text-1);
  background: var(--vp-c-bg);
}

.knowledge-graph__control input,
.knowledge-graph__control select {
  width: 100%;
  padding: 0 0.65rem;
}

.knowledge-graph__options {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 0.45rem 0.85rem;
  padding: 0.5rem 0.6rem;
  border: 1px solid var(--vp-c-divider);
  border-radius: 14px;
  background: var(--vp-c-bg-soft);
}

.knowledge-graph__option-group {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 0.35rem 0.55rem;
  min-width: 0;
}

.knowledge-graph__option-group--actions {
  margin-left: auto;
}

.knowledge-graph__actions-label {
  letter-spacing: 0.06em;
  text-transform: uppercase;
}

.knowledge-graph__button {
  min-height: 2rem;
  padding: 0 0.85rem;
  font-weight: 700;
  cursor: pointer;
}

.knowledge-graph__checkbox {
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  min-height: 1.8rem;
  color: var(--vp-c-text-2);
  font-size: 0.86rem;
  font-weight: 600;
}

.knowledge-graph__button:hover,
.knowledge-graph__button:focus-visible,
.knowledge-graph__control input:focus-visible,
.knowledge-graph__control select:focus-visible {
  border-color: var(--vp-c-brand-1);
  outline: none;
}

.knowledge-graph__active-filters,
.knowledge-graph__selected-meta,
.knowledge-graph__tags {
  display: flex;
  flex-wrap: wrap;
  gap: 0.35rem;
}

.knowledge-graph__active-filters {
  align-items: center;
}

.knowledge-graph__filter-pill,
.knowledge-graph__pill,
.knowledge-graph__count,
.knowledge-graph__tags button {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  max-width: 100%;
  min-width: 0;
  padding: 0.15rem 0.5rem;
  overflow: hidden;
  border: 0;
  border-radius: 999px;
  font: inherit;
  font-size: 0.73rem;
  font-weight: 600;
  line-height: 1.2;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.knowledge-graph__filter-pill,
.knowledge-graph__pill--neutral,
.knowledge-graph__count {
  color: var(--vp-c-text-2);
  background: var(--vp-c-default-soft);
}

.knowledge-graph__count {
  min-width: 1.5rem;
  padding: 0.1rem 0.4rem;
}

.knowledge-graph__pill--muted {
  color: var(--vp-c-text-2);
  background: color-mix(in srgb, var(--vp-c-text-3) 14%, transparent);
}

.knowledge-graph__pill--brand,
.knowledge-graph__tags button {
  color: var(--vp-c-brand-1);
  background: color-mix(in srgb, var(--vp-c-brand-1) 12%, transparent);
}

.knowledge-graph__tags button {
  cursor: pointer;
}

.knowledge-graph__tags button:hover,
.knowledge-graph__tags button:focus-visible {
  background: color-mix(in srgb, var(--vp-c-brand-1) 18%, transparent);
  outline: none;
}

.knowledge-graph__summary,
.knowledge-graph__notice {
  margin: 0 0 0.75rem;
  color: var(--vp-c-text-2);
}

.knowledge-graph__notice {
  font-size: 0.9rem;
}

.knowledge-graph__layout {
  display: grid;
  width: 100%;
  grid-template-columns: minmax(0, 1fr);
  gap: 0.9rem;
}

.knowledge-graph__stage {
  display: block;
  width: 100%;
  max-width: 100%;
  overflow: hidden;
  border: 1px solid var(--vp-c-divider);
  border-radius: 14px;
  background:
    radial-gradient(circle at 52% 48%, color-mix(in srgb, var(--vp-c-brand-1) 7%, transparent), transparent 34%),
    var(--vp-c-bg-soft);
  cursor: grab;
  touch-action: none;
}

.knowledge-graph__stage:active {
  cursor: grabbing;
}

.knowledge-graph__svg {
  display: block;
  width: 100%;
  height: clamp(520px, 60vw, 680px);
}

.knowledge-graph__edge {
  stroke: color-mix(in srgb, var(--vp-c-text-3) 58%, transparent);
  stroke-width: 1.25;
  transition:
    opacity 0.16s ease,
    stroke 0.16s ease,
    stroke-width 0.16s ease;
}

.knowledge-graph__edge--active {
  stroke: var(--vp-c-brand-1);
  stroke-width: 2.2;
}

.knowledge-graph__edge--curated {
  stroke: color-mix(in srgb, var(--vp-c-brand-1) 72%, var(--vp-c-text-2));
  stroke-dasharray: 7 5;
}

.knowledge-graph__edge--suggested {
  stroke: color-mix(in srgb, var(--vp-c-text-2) 76%, transparent);
  stroke-dasharray: 4 6;
}

.knowledge-graph__edge--tag {
  stroke: color-mix(in srgb, var(--vp-c-text-3) 48%, transparent);
  stroke-dasharray: 2 7;
}

.knowledge-graph__edge--muted {
  opacity: 0.13;
}

.knowledge-graph__node-group {
  cursor: pointer;
  outline: none;
  transition: opacity 0.16s ease;
}

.knowledge-graph__node-group--muted {
  opacity: 0.2;
}

.knowledge-graph__node {
  fill: var(--vp-c-brand-1);
  stroke: var(--vp-c-bg);
  stroke-width: 2.5;
  filter: drop-shadow(0 2px 5px color-mix(in srgb, var(--vp-c-brand-1) 18%, transparent));
  transition:
    fill 0.18s ease,
    stroke 0.18s ease,
    stroke-width 0.18s ease;
}

.knowledge-graph__node-group:hover .knowledge-graph__node,
.knowledge-graph__node-group:focus-visible .knowledge-graph__node,
.knowledge-graph__node-group--active .knowledge-graph__node {
  fill: var(--vp-c-brand-2);
  stroke: var(--vp-c-text-1);
  stroke-width: 4;
}

.knowledge-graph__label {
  fill: var(--vp-c-text-1);
  paint-order: stroke;
  stroke: var(--vp-c-bg-soft);
  stroke-width: 5px;
  stroke-linejoin: round;
  font-size: 12px;
  font-weight: 700;
  text-anchor: middle;
  pointer-events: none;
}

.knowledge-graph__details {
  min-width: 0;
  padding: 0.9rem 1rem;
  border: 1px solid var(--vp-c-divider);
  border-radius: 14px;
  background: var(--vp-c-bg-soft);
}

.knowledge-graph__details-header {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  min-width: 0;
  gap: 0.45rem 0.75rem;
}

.knowledge-graph__details-eyebrow {
  flex: 0 0 100%;
  margin: 0;
  font-size: 0.75rem;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.knowledge-graph__sections {
  display: grid;
  gap: 0.9rem;
  margin-top: 0.8rem;
}

.knowledge-graph__section {
  min-width: 0;
  padding-top: 0.8rem;
  border-top: 1px solid var(--vp-c-divider);
}

.knowledge-graph__section-header {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: 0.45rem 0.8rem;
  margin-bottom: 0.45rem;
}

.knowledge-graph__section-heading {
  display: inline-flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 0.45rem;
}

.knowledge-graph__section-title {
  margin: 0;
  font-size: 0.82rem;
  font-weight: 700;
  letter-spacing: 0.06em;
  text-transform: uppercase;
}

.knowledge-graph__selected-card {
  display: grid;
  gap: 0.18rem;
  padding: 0.45rem 0.5rem;
  border: 1px solid transparent;
  border-radius: 10px;
}

.knowledge-graph__selected-topline {
  display: grid;
  gap: 0.2rem;
  min-width: 0;
}

.knowledge-graph__selected-title {
  display: -webkit-box;
  overflow: hidden;
  font-weight: 600;
  line-height: 1.3;
  color: var(--vp-c-text-1);
  overflow-wrap: anywhere;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 2;
}

.knowledge-graph__selected-summary {
  display: -webkit-box;
  overflow: hidden;
  font-size: 0.82rem;
  line-height: 1.35;
  color: var(--vp-c-text-2);
  overflow-wrap: anywhere;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 2;
}

.knowledge-graph__open {
  padding: 0;
  border: 0;
  font: inherit;
  font-size: 0.83rem;
  font-weight: 600;
  color: var(--vp-c-brand-1);
  background: transparent;
  cursor: pointer;
}

.knowledge-graph__open:hover,
.knowledge-graph__open:focus-visible {
  text-decoration: underline;
  outline: none;
}

.knowledge-graph__tags {
  margin-top: 0.45rem;
}

.knowledge-graph__empty {
  margin: 0;
  color: var(--vp-c-text-2);
  font-size: 0.82rem;
  line-height: 1.35;
}

@media (max-width: 960px) {
  .knowledge-graph__filters {
    grid-template-columns: 1fr;
  }

  .knowledge-graph__control--search {
    grid-column: auto;
  }

  .knowledge-graph__option-group--actions {
    margin-left: 0;
  }

  .knowledge-graph__svg {
    height: clamp(420px, 86vw, 560px);
  }
}
</style>
