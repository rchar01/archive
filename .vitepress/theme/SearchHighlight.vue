<script setup lang="ts">
import { onBeforeUnmount, onMounted } from 'vue'
import { onContentUpdated, useRouter } from 'vitepress'

const SEARCH_FILTER_KEY = 'vitepress:local-search-filter'
const LAST_QUERY_KEY = 'archive:last-local-search-query'
const PENDING_HIGHLIGHT_KEY = 'archive:pending-search-highlight'
const PENDING_HIGHLIGHT_TTL_MS = 10_000
const HIGHLIGHT_CLASS = 'archive-search-highlight'
const HIGHLIGHT_SELECTOR = `mark.${HIGHLIGHT_CLASS}`
// Keep code examples untouched; VitePress/Shiki code blocks contain nested
// token spans, copy controls, line markers, and other interactive wrappers.
const SKIP_SELECTOR = [
  'script',
  'style',
  'textarea',
  'select',
  'option',
  'input',
  'button',
  'pre',
  'code',
  'div[class*="language-"]',
  '.vp-code',
  '.vp-code-group',
  '.lang',
  '.copy',
  'svg',
  'canvas',
  'mark',
  '.VPNav',
  '.VPSidebar',
  '.VPDocAside',
  '.archive-knowledge-panel',
].join(',')

type PendingHighlight = {
  path: string
  terms: string[]
  createdAt: number
}

type RouterWithHighlightPatch = ReturnType<typeof useRouter> & {
  __archiveSearchHighlightOriginalGo?: ReturnType<typeof useRouter>['go']
}

const router = useRouter() as RouterWithHighlightPatch
let pendingHighlight: PendingHighlight | null = null
let activeHighlight: PendingHighlight | null = null
let highlightedPath: string | null = null

function normalizePath(value: string): string {
  const path = value.replace(/\.html$/u, '').replace(/\/+$/u, '')
  return path || '/'
}

function currentPath(): string {
  return normalizePath(window.location.pathname)
}

function readPendingHighlight(): PendingHighlight | null {
  if (pendingHighlight && Date.now() - pendingHighlight.createdAt <= PENDING_HIGHLIGHT_TTL_MS) {
    return pendingHighlight
  }
  pendingHighlight = null

  const rawValue = window.sessionStorage.getItem(PENDING_HIGHLIGHT_KEY)
  if (!rawValue) {
    return null
  }

  try {
    const parsed = JSON.parse(rawValue) as Partial<PendingHighlight>
    if (typeof parsed.path !== 'string' || !Array.isArray(parsed.terms) || typeof parsed.createdAt !== 'number') {
      return null
    }
    if (Date.now() - parsed.createdAt > PENDING_HIGHLIGHT_TTL_MS) {
      window.sessionStorage.removeItem(PENDING_HIGHLIGHT_KEY)
      return null
    }
    return {
      path: parsed.path,
      terms: parsed.terms.filter((term): term is string => typeof term === 'string'),
      createdAt: parsed.createdAt,
    }
  } catch {
    window.sessionStorage.removeItem(PENDING_HIGHLIGHT_KEY)
    return null
  }
}

function writePendingHighlight(value: PendingHighlight): void {
  pendingHighlight = value
  window.sessionStorage.setItem(PENDING_HIGHLIGHT_KEY, JSON.stringify(value))
}

function clearPendingHighlight(): void {
  pendingHighlight = null
  window.sessionStorage.removeItem(PENDING_HIGHLIGHT_KEY)
}

function escapeRegExp(value: string): string {
  return value.replace(/[.*+?^${}()|[\]\\]/gu, '\\$&')
}

function extractHighlightTerms(query: string): string[] {
  const seen = new Set<string>()
  const terms: string[] = []
  const tokens = query.match(/#[\p{L}\p{N}]+(?:-[\p{L}\p{N}]+)*\*?|[\p{L}\p{N}]+(?:[-_][\p{L}\p{N}]+)*/gu) ?? []

  for (const token of tokens) {
    if (token.startsWith('#')) {
      continue
    }
    const normalized = token.toLowerCase()
    if (normalized.length < 2 || seen.has(normalized)) {
      continue
    }
    seen.add(normalized)
    terms.push(token)
  }

  return terms
}

function unwrapHighlight(mark: Element): void {
  const parent = mark.parentNode
  if (!parent) {
    return
  }

  parent.replaceChild(document.createTextNode(mark.textContent ?? ''), mark)
  parent.normalize()
}

function clearHighlights(root: ParentNode = document, clearActive = true): void {
  root.querySelectorAll(HIGHLIGHT_SELECTOR).forEach(unwrapHighlight)
  if (clearActive) {
    activeHighlight = null
    highlightedPath = null
  }
}

function textNodeIsSearchable(node: Text): boolean {
  const value = node.nodeValue
  if (!value?.trim()) {
    return false
  }

  const parent = node.parentElement
  return Boolean(parent && !parent.closest(SKIP_SELECTOR))
}

function markTextNode(node: Text, regex: RegExp): number {
  const text = node.nodeValue ?? ''
  const fragment = document.createDocumentFragment()
  let lastIndex = 0
  let count = 0

  for (const match of text.matchAll(regex)) {
    const matchText = match[0]
    const index = match.index ?? 0
    if (index > lastIndex) {
      fragment.append(document.createTextNode(text.slice(lastIndex, index)))
    }

    const mark = document.createElement('mark')
    mark.className = HIGHLIGHT_CLASS
    mark.textContent = matchText
    fragment.append(mark)
    lastIndex = index + matchText.length
    count += 1
  }

  if (lastIndex < text.length) {
    fragment.append(document.createTextNode(text.slice(lastIndex)))
  }

  node.parentNode?.replaceChild(fragment, node)
  return count
}

function markTerms(root: Element, terms: string[]): number {
  const prefixes = terms.slice().sort((a, b) => b.length - a.length).map(escapeRegExp).join('|')
  const regex = new RegExp(`(?<![\\p{L}\\p{N}_-])(?:${prefixes})[\\p{L}\\p{N}]*(?:[-_][\\p{L}\\p{N}]+)*`, 'giu')
  const nodes: Text[] = []
  let count = 0
  const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT, {
    acceptNode(node) {
      return textNodeIsSearchable(node as Text) ? NodeFilter.FILTER_ACCEPT : NodeFilter.FILTER_REJECT
    },
  })

  while (walker.nextNode()) {
    const node = walker.currentNode as Text
    regex.lastIndex = 0
    if (regex.test(node.nodeValue ?? '')) {
      nodes.push(node)
    }
  }

  for (const node of nodes) {
    regex.lastIndex = 0
    count += markTextNode(node, regex)
  }

  return count
}

function pageContentRoot(): Element | null {
  return document.querySelector('.VPDoc main.main > .vp-doc') ?? document.querySelector('.VPHome .vp-doc')
}

function applyActiveHighlight(): void {
  if (!activeHighlight) {
    return
  }

  if (activeHighlight.path !== currentPath()) {
    clearHighlights()
    return
  }

  const root = pageContentRoot()
  if (!root || root.querySelector(HIGHLIGHT_SELECTOR)) {
    return
  }

  const count = markTerms(root, activeHighlight.terms)
  if (count > 0) {
    highlightedPath = currentPath()
  }
}

function applyPendingHighlight(): void {
  const pending = readPendingHighlight()
  if (!pending) {
    if (highlightedPath && highlightedPath !== currentPath()) {
      clearHighlights()
      return
    }
    applyActiveHighlight()
    return
  }

  if (pending.path !== currentPath()) {
    if (highlightedPath && highlightedPath !== currentPath()) {
      clearHighlights()
    }
    return
  }

  const terms = pending.terms
  if (terms.length === 0) {
    clearPendingHighlight()
    clearHighlights()
    return
  }

  const root = pageContentRoot()
  if (root) {
    clearHighlights(root, false)
    const count = markTerms(root, terms)
    if (count > 0) {
      clearPendingHighlight()
      activeHighlight = { ...pending, terms }
      highlightedPath = currentPath()
    }
  }
}

function scheduleUntilHighlighted(): void {
  scheduleHighlight()
  const startedAt = Date.now()
  const interval = window.setInterval(() => {
    if (!readPendingHighlight() || Date.now() - startedAt > PENDING_HIGHLIGHT_TTL_MS) {
      window.clearInterval(interval)
      return
    }

    scheduleHighlight()
    if (highlightedPath === currentPath()) {
      window.clearInterval(interval)
    }
  }, 100)
}

function scheduleHighlight(): void {
  window.requestAnimationFrame(() => {
    window.requestAnimationFrame(applyPendingHighlight)
  })
}

function scheduleHighlightRetries(): void {
  scheduleUntilHighlighted()
  for (const delay of [250, 750, 1500]) {
    window.setTimeout(scheduleUntilHighlighted, delay)
  }
}

function captureSearchTarget(target: string): void {
  const url = new URL(target, window.location.href)
  if (url.origin !== window.location.origin) {
    return
  }
  const targetPath = normalizePath(url.pathname)

  const query =
    (window as Window & { __archiveLastLocalSearchQuery?: string }).__archiveLastLocalSearchQuery ??
    window.sessionStorage.getItem(LAST_QUERY_KEY) ??
    window.sessionStorage.getItem(SEARCH_FILTER_KEY) ??
    ''
  writePendingHighlight({
    path: targetPath,
    terms: extractHighlightTerms(query),
    createdAt: Date.now(),
  })

  // For cross-page results, wait for VitePress to mount the destination body.
  // The URL can change before the new content exists, and marking too early can
  // consume the pending query against the old page.
  if (targetPath === currentPath()) {
    scheduleHighlightRetries()
  }
}

function captureSearchResult(anchor: HTMLAnchorElement): void {
  captureSearchTarget(anchor.href)
}

function closestSearchResult(value: EventTarget | null): HTMLAnchorElement | null {
  return value instanceof Element ? value.closest<HTMLAnchorElement>('.VPLocalSearchBox a.result[href]') : null
}

function onDocumentPointerDown(event: PointerEvent): void {
  const anchor = closestSearchResult(event.target)
  if (anchor) {
    captureSearchResult(anchor)
  }
}

function onDocumentKeydown(event: KeyboardEvent): void {
  if (event.key === 'Escape' && !document.querySelector('.VPLocalSearchBox')) {
    clearPendingHighlight()
    clearHighlights()
    return
  }

  if (event.key !== 'Enter' || !document.querySelector('.VPLocalSearchBox')) {
    return
  }

  const selected = document.querySelector<HTMLAnchorElement>('.VPLocalSearchBox a.result.selected[href]')
  if (selected) {
    captureSearchResult(selected)
  }
}

onMounted(() => {
  if (!router.__archiveSearchHighlightOriginalGo) {
    router.__archiveSearchHighlightOriginalGo = router.go
    router.go = ((target: string) => {
      if (document.querySelector('.VPLocalSearchBox')) {
        captureSearchTarget(target)
      }
      return router.__archiveSearchHighlightOriginalGo?.call(router, target)
    }) as typeof router.go
  }

  document.addEventListener('pointerdown', onDocumentPointerDown, true)
  document.addEventListener('keydown', onDocumentKeydown, true)
})

onBeforeUnmount(() => {
  if (router.__archiveSearchHighlightOriginalGo) {
    router.go = router.__archiveSearchHighlightOriginalGo
    delete router.__archiveSearchHighlightOriginalGo
  }

  document.removeEventListener('pointerdown', onDocumentPointerDown, true)
  document.removeEventListener('keydown', onDocumentKeydown, true)
})

onContentUpdated(scheduleHighlightRetries)
</script>

<template></template>
