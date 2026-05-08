<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { useData, useRoute } from 'vitepress'

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
type ThemeConfig = {
  knowledgePanel?: boolean
  knowledgePanelBacklinks?: boolean
  knowledgePanelRelated?: boolean
}
type PanelItem = {
  link: string
  title: string
  kind: string
  section: string
  summary: string
  sourceLabel?: string
  sourceTone?: 'brand' | 'muted'
}

const pages = pagesData as PageMap
const linkgraph = linkgraphData as LinkgraphMap
const relatedIndex = relatedData as RelatedMap

const METADATA_VISIBLE_TAG_COUNT = 5
const RELATED_VISIBLE_COUNT = 3
const BACKLINKS_VISIBLE_COUNT = 3

const route = useRoute()
const { frontmatter, theme } = useData()
const showAllRelated = ref(false)
const showAllBacklinks = ref(false)

function normalizePath(path: string): string {
  const cleaned = path.split(/[?#]/u, 1)[0]?.trim() ?? ''
  if (!cleaned || cleaned === '/') {
    return '/'
  }
  const prefixed = cleaned.startsWith('/') ? cleaned : `/${cleaned}`
  return prefixed.endsWith('/') ? prefixed.slice(0, -1) : prefixed
}

function hasBooleanOverride(value: unknown): value is boolean {
  return typeof value === 'boolean'
}

function resolveEnabled(hideValue: unknown, workflowDefault: boolean | null | undefined, globalDefault: boolean | undefined): boolean {
  if (hasBooleanOverride(hideValue)) {
    return !hideValue
  }
  if (typeof workflowDefault === 'boolean') {
    return workflowDefault
  }
  if (typeof globalDefault === 'boolean') {
    return globalDefault
  }
  return true
}

function pageTitle(link: string): string {
  return pages[link]?.title?.trim() || link
}

function pageKind(link: string): string {
  return pages[link]?.kind?.trim() || ''
}

function pageSection(link: string): string {
  return pages[link]?.section?.trim() || ''
}

function pageSummary(link: string): string {
  return pages[link]?.summary?.trim() || ''
}

function humanizeSection(section: string): string {
  if (!section) {
    return ''
  }
  return section
    .split('/')
    .map((part) => part.trim().toLowerCase())
    .filter((part) => part.length > 0)
    .join('/')
}

function buildItems(links: string[]): PanelItem[] {
  const seen = new Set<string>()
  const items: PanelItem[] = []
  for (const link of links) {
    const normalized = normalizePath(link)
    if (normalized === currentPath.value || seen.has(normalized)) {
      continue
    }
    seen.add(normalized)
    items.push({
      link: normalized,
      title: pageTitle(normalized),
      kind: pageKind(normalized),
      section: humanizeSection(pageSection(normalized)),
      summary: pageSummary(normalized),
    })
  }
  return items
}

const currentPath = computed(() => normalizePath(route.path))
const currentPage = computed(() => pages[currentPath.value] ?? null)
const currentTheme = computed(() => (theme.value ?? {}) as ThemeConfig)

watch(currentPath, () => {
  showAllRelated.value = false
  showAllBacklinks.value = false
})

const panelEnabled = computed(() =>
  resolveEnabled(
    frontmatter.value.hide_knowledge_panel,
    currentPage.value?.workflow?.knowledge_panel,
    currentTheme.value.knowledgePanel,
  ),
)

const relatedEnabled = computed(() =>
  resolveEnabled(frontmatter.value.hide_related, currentPage.value?.workflow?.related, currentTheme.value.knowledgePanelRelated),
)

const backlinksEnabled = computed(() =>
  resolveEnabled(
    frontmatter.value.hide_backlinks,
    currentPage.value?.workflow?.backlinks,
    currentTheme.value.knowledgePanelBacklinks,
  ),
)

const metadataTags = computed(() => {
  const tags = Array.isArray(frontmatter.value.tags)
    ? frontmatter.value.tags
    : Array.isArray(currentPage.value?.tags)
      ? currentPage.value?.tags
      : []
  return tags.filter((tag): tag is string => typeof tag === 'string' && tag.trim().length > 0)
})

const visibleMetadataTags = computed(() => metadataTags.value.slice(0, METADATA_VISIBLE_TAG_COUNT))
const hiddenMetadataTags = computed(() => metadataTags.value.slice(METADATA_VISIBLE_TAG_COUNT))
const hiddenMetadataTagCount = computed(() => hiddenMetadataTags.value.length)
const hiddenMetadataTagsLabel = computed(() => hiddenMetadataTags.value.join(', '))
const hiddenMetadataTagsAriaLabel = computed(() => {
  if (hiddenMetadataTagCount.value === 0) {
    return ''
  }
  return `${hiddenMetadataTagCount.value} more tags: ${hiddenMetadataTagsLabel.value}`
})

const updated = computed(() => {
  const value = frontmatter.value.updated ?? currentPage.value?.updated
  return typeof value === 'string' && value.trim().length > 0 ? value.trim() : ''
})

const manualRelatedLinks = computed(() => {
  const rawLinks = Array.isArray(frontmatter.value.related_manual)
    ? frontmatter.value.related_manual
    : Array.isArray(currentPage.value?.related_manual)
      ? currentPage.value?.related_manual
      : []
  return buildItems(rawLinks.filter((link): link is string => typeof link === 'string' && link.trim().length > 0))
})

const autoRelatedLinks = computed(() => {
  const rawLinks = relatedIndex[currentPath.value]?.related ?? []
  const hiddenLinks = new Set(manualRelatedLinks.value.map((item) => item.link))
  return buildItems(rawLinks.filter((link) => !hiddenLinks.has(normalizePath(link))))
})

const relatedLinks = computed(() => [
  ...manualRelatedLinks.value.map((item) => ({ ...item, sourceLabel: 'curated', sourceTone: 'brand' as const })),
  ...autoRelatedLinks.value.map((item) => ({ ...item, sourceLabel: 'suggested', sourceTone: 'muted' as const })),
])

const backlinks = computed(() => buildItems(linkgraph[currentPath.value]?.backlinks ?? []))

const visibleRelatedLinks = computed(() => {
  if (showAllRelated.value) {
    return relatedLinks.value
  }
  return relatedLinks.value.slice(0, RELATED_VISIBLE_COUNT)
})

const visibleBacklinks = computed(() => {
  if (showAllBacklinks.value) {
    return backlinks.value
  }
  return backlinks.value.slice(0, BACKLINKS_VISIBLE_COUNT)
})

const hasMetadata = computed(() => metadataTags.value.length > 0 || updated.value.length > 0)
const relatedCount = computed(() => relatedLinks.value.length)
const showRelated = computed(() => relatedEnabled.value && relatedCount.value > 0)
const showBacklinks = computed(() => backlinksEnabled.value && backlinks.value.length > 0)
const shouldRender = computed(() => panelEnabled.value && currentPage.value !== null && (hasMetadata.value || showRelated.value || showBacklinks.value))
const canToggleRelated = computed(() => relatedCount.value > RELATED_VISIBLE_COUNT)
const canToggleBacklinks = computed(() => backlinks.value.length > BACKLINKS_VISIBLE_COUNT)
const hiddenRelatedCount = computed(() => relatedCount.value - visibleRelatedLinks.value.length)
const hiddenBacklinksCount = computed(() => backlinks.value.length - visibleBacklinks.value.length)
</script>

<template>
  <section v-if="shouldRender" class="knowledge-panel">
    <header class="knowledge-panel__header">
      <p class="knowledge-panel__eyebrow">Context</p>

      <div v-if="hasMetadata" class="knowledge-panel__meta">
        <div v-if="metadataTags.length > 0" class="knowledge-panel__tags">
          <span v-for="tag in visibleMetadataTags" :key="tag" class="knowledge-panel__tag" :title="tag">{{ tag }}</span>
          <span
            v-if="hiddenMetadataTagCount > 0"
            class="knowledge-panel__tag knowledge-panel__tag--overflow"
            :title="hiddenMetadataTagsLabel"
            :aria-label="hiddenMetadataTagsAriaLabel"
          >
            +{{ hiddenMetadataTagCount }}
          </span>
        </div>
        <p v-if="updated" class="knowledge-panel__updated">Updated {{ updated }}</p>
      </div>
    </header>

    <div
      class="knowledge-panel__sections"
      :class="{ 'knowledge-panel__sections--split': showRelated && showBacklinks }"
    >
      <section v-if="showRelated" class="knowledge-panel__section">
        <div class="knowledge-panel__section-header">
          <div class="knowledge-panel__section-heading">
            <h3 class="knowledge-panel__section-title">Related</h3>
            <span aria-hidden="true" class="knowledge-panel__count">{{ relatedCount }}</span>
          </div>

          <button
            v-if="canToggleRelated"
            type="button"
            class="knowledge-panel__toggle"
            aria-controls="knowledge-panel-related-list"
            :aria-expanded="showAllRelated"
            @click="showAllRelated = !showAllRelated"
          >
            {{ showAllRelated ? 'Show less' : `Show ${hiddenRelatedCount} more` }}
          </button>
        </div>

        <ul id="knowledge-panel-related-list" class="knowledge-panel__list">
          <li v-for="item in visibleRelatedLinks" :key="`related-${item.link}`" class="knowledge-panel__item">
            <a :href="item.link" class="knowledge-panel__link">
              <span class="knowledge-panel__link-topline">
                <span class="knowledge-panel__link-title" :title="item.title">{{ item.title }}</span>
                <span v-if="item.kind || item.section || item.sourceLabel" class="knowledge-panel__link-meta">
                  <span v-if="item.kind" class="knowledge-panel__pill knowledge-panel__pill--neutral" :title="item.kind">{{ item.kind }}</span>
                  <span v-if="item.section" class="knowledge-panel__pill knowledge-panel__pill--neutral" :title="item.section">{{ item.section }}</span>
                  <span
                    v-if="item.sourceLabel"
                    class="knowledge-panel__pill"
                    :class="item.sourceTone === 'brand' ? 'knowledge-panel__pill--brand' : 'knowledge-panel__pill--muted'"
                    :title="item.sourceLabel"
                  >
                    {{ item.sourceLabel }}
                  </span>
                </span>
              </span>

              <span v-if="item.summary" class="knowledge-panel__link-summary" :title="item.summary">{{ item.summary }}</span>
            </a>
          </li>
        </ul>
      </section>

      <section v-if="showBacklinks" class="knowledge-panel__section">
        <div class="knowledge-panel__section-header">
          <div class="knowledge-panel__section-heading">
            <h3 class="knowledge-panel__section-title">Backlinks</h3>
            <span aria-hidden="true" class="knowledge-panel__count">{{ backlinks.length }}</span>
          </div>

          <button
            v-if="canToggleBacklinks"
            type="button"
            class="knowledge-panel__toggle"
            aria-controls="knowledge-panel-backlinks-list"
            :aria-expanded="showAllBacklinks"
            @click="showAllBacklinks = !showAllBacklinks"
          >
            {{ showAllBacklinks ? 'Show less' : `Show ${hiddenBacklinksCount} more` }}
          </button>
        </div>

        <ul id="knowledge-panel-backlinks-list" class="knowledge-panel__list">
          <li v-for="item in visibleBacklinks" :key="`backlink-${item.link}`" class="knowledge-panel__item">
            <a :href="item.link" class="knowledge-panel__link">
              <span class="knowledge-panel__link-topline">
                <span class="knowledge-panel__link-title" :title="item.title">{{ item.title }}</span>
                <span v-if="item.kind || item.section" class="knowledge-panel__link-meta">
                  <span v-if="item.kind" class="knowledge-panel__pill knowledge-panel__pill--neutral" :title="item.kind">{{ item.kind }}</span>
                  <span v-if="item.section" class="knowledge-panel__pill knowledge-panel__pill--neutral" :title="item.section">{{ item.section }}</span>
                </span>
              </span>

              <span v-if="item.summary" class="knowledge-panel__link-summary" :title="item.summary">{{ item.summary }}</span>
            </a>
          </li>
        </ul>
      </section>
    </div>
  </section>
</template>

<style scoped>
.knowledge-panel {
  margin-top: 1.75rem;
  padding: 0.9rem 1rem;
  border: 1px solid var(--vp-c-divider);
  border-radius: 14px;
  background: var(--vp-c-bg-soft);
}

.knowledge-panel__header {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  min-width: 0;
  gap: 0.45rem 0.75rem;
}

.knowledge-panel__eyebrow {
  flex: 0 0 100%;
  margin: 0;
  font-size: 0.75rem;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--vp-c-text-2);
}

.knowledge-panel__meta,
.knowledge-panel__tags {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  min-width: 0;
  gap: 0.4rem;
}

.knowledge-panel__meta {
  flex: 1 1 100%;
  justify-content: space-between;
}

.knowledge-panel__tags {
  flex: 1 1 auto;
}

.knowledge-panel__tag,
.knowledge-panel__count,
.knowledge-panel__pill {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: 999px;
  font-size: 0.73rem;
  font-weight: 600;
  line-height: 1.2;
}

.knowledge-panel__tag,
.knowledge-panel__pill--neutral,
.knowledge-panel__pill--muted,
.knowledge-panel__count {
  color: var(--vp-c-text-2);
  background: var(--vp-c-default-soft);
}

.knowledge-panel__tag,
.knowledge-panel__pill {
  max-inline-size: min(100%, 18rem);
  min-width: 0;
  padding: 0.15rem 0.5rem;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.knowledge-panel__pill {
  text-transform: none;
}

.knowledge-panel__tag--overflow {
  color: var(--vp-c-brand-1);
  background: color-mix(in srgb, var(--vp-c-brand-1) 10%, transparent);
}

.knowledge-panel__pill--brand {
  color: var(--vp-c-brand-1);
  background: color-mix(in srgb, var(--vp-c-brand-1) 12%, transparent);
}

.knowledge-panel__updated {
  margin: 0;
  margin-left: auto;
  font-size: 0.82rem;
  text-align: right;
  white-space: nowrap;
  color: var(--vp-c-text-2);
}

.knowledge-panel__sections {
  display: grid;
  gap: 0.9rem;
  margin-top: 0.8rem;
}

.knowledge-panel__section {
  min-width: 0;
  padding-top: 0.8rem;
  border-top: 1px solid var(--vp-c-divider);
}

.knowledge-panel__section-header {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: 0.45rem 0.8rem;
  margin-bottom: 0.45rem;
}

.knowledge-panel__section-heading {
  display: inline-flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 0.45rem;
}

.knowledge-panel__section-title {
  margin: 0;
  font-size: 0.82rem;
  font-weight: 700;
  letter-spacing: 0.06em;
  text-transform: uppercase;
}

.knowledge-panel__count {
  min-width: 1.5rem;
  padding: 0.1rem 0.4rem;
}

.knowledge-panel__list {
  display: grid;
  gap: 0.45rem;
  margin: 0;
  padding: 0;
  list-style: none;
}

.knowledge-panel__item {
  min-width: 0;
}

.knowledge-panel__link {
  display: grid;
  gap: 0.18rem;
  padding: 0.45rem 0.5rem;
  border: 1px solid transparent;
  border-radius: 10px;
  color: inherit;
  text-decoration: none;
  transition: border-color 0.18s ease;
}

.knowledge-panel__link:hover,
.knowledge-panel__link:focus-visible {
  border-color: color-mix(in srgb, var(--vp-c-brand-1) 70%, var(--vp-c-divider));
}

.knowledge-panel__link-topline {
  display: grid;
  gap: 0.2rem;
  min-width: 0;
}

.knowledge-panel__link-title {
  display: -webkit-box;
  overflow: hidden;
  font-weight: 600;
  line-height: 1.3;
  color: var(--vp-c-text-1);
  overflow-wrap: anywhere;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 2;
}

.knowledge-panel__link-meta {
  display: flex;
  flex-wrap: wrap;
  min-width: 0;
  gap: 0.35rem;
  align-items: center;
}

.knowledge-panel__link-summary {
  display: -webkit-box;
  overflow: hidden;
  font-size: 0.82rem;
  line-height: 1.35;
  color: var(--vp-c-text-2);
  overflow-wrap: anywhere;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 2;
}

.knowledge-panel__toggle {
  padding: 0;
  border: 0;
  font: inherit;
  font-size: 0.83rem;
  font-weight: 600;
  color: var(--vp-c-brand-1);
  background: transparent;
  cursor: pointer;
}

.knowledge-panel__toggle:hover,
.knowledge-panel__toggle:focus-visible {
  text-decoration: underline;
}

@media (min-width: 900px) {
  .knowledge-panel__sections--split {
    grid-template-columns: minmax(0, 1fr) minmax(0, 1fr);
    gap: 1rem;
  }
}

@media (max-width: 640px) {
  .knowledge-panel {
    padding: 0.85rem 0.9rem;
  }

  .knowledge-panel__meta {
    align-items: flex-start;
  }

  .knowledge-panel__updated {
    flex-basis: 100%;
  }

  .knowledge-panel__section-header {
    align-items: flex-start;
  }

  .knowledge-panel__link {
    padding-left: 0;
    padding-right: 0;
  }
}
</style>
