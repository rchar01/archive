<script setup lang="ts">
import { onContentUpdated, useData, useRoute } from 'vitepress'
import { computed, nextTick, onMounted, onUnmounted, ref, watch } from 'vue'

const DESKTOP_MEDIA_QUERY = '(min-width: 1280px)'
const VISIBILITY_SCROLL_Y = 360
const BUTTON_WIDTH_PX = 44
const CONTENT_OFFSET_PX = 16
const VIEWPORT_EDGE_PX = 24

const route = useRoute()
const { frontmatter, theme } = useData()
const visible = ref(false)
const leftPx = ref<number | null>(null)

let desktopMediaQuery: MediaQueryList | null = null

const label = computed(() => theme.value.returnToTopLabel || 'Return to top')
const enabled = computed(() => frontmatter.value.layout !== false && frontmatter.value.layout !== 'home')

function prefersReducedMotion(): boolean {
  return window.matchMedia('(prefers-reduced-motion: reduce)').matches
}

function isDesktopWide(): boolean {
  return desktopMediaQuery?.matches ?? false
}

function syncVisibility(): void {
  visible.value = enabled.value && isDesktopWide() && window.scrollY > VISIBILITY_SCROLL_Y
}

function syncPosition(): void {
  if (!enabled.value || !isDesktopWide()) {
    leftPx.value = null
    return
  }

  const content = document.querySelector<HTMLElement>('.VPDoc .content-container')
  if (!content) {
    leftPx.value = null
    return
  }

  const contentRect = content.getBoundingClientRect()
  const minLeft = VIEWPORT_EDGE_PX
  const maxLeft = Math.max(window.innerWidth - BUTTON_WIDTH_PX - VIEWPORT_EDGE_PX, minLeft)
  const preferredLeft = contentRect.right + CONTENT_OFFSET_PX

  leftPx.value = Math.round(Math.min(Math.max(preferredLeft, minLeft), maxLeft))
}

function scrollToTop(): void {
  window.scrollTo({
    top: 0,
    left: 0,
    behavior: prefersReducedMotion() ? 'auto' : 'smooth',
  })
}

function handleViewportChange(): void {
  syncVisibility()
  syncPosition()
}

onMounted(() => {
  desktopMediaQuery = window.matchMedia(DESKTOP_MEDIA_QUERY)

  syncVisibility()
  syncPosition()
  window.addEventListener('scroll', syncVisibility, { passive: true })
  window.addEventListener('resize', handleViewportChange)
  desktopMediaQuery.addEventListener('change', handleViewportChange)
})

watch(
  () => route.path,
  async () => {
    visible.value = false
    await nextTick()
    syncVisibility()
    syncPosition()
  },
)

onContentUpdated(() => {
  syncVisibility()
  syncPosition()
})

watch(enabled, async () => {
  await nextTick()
  syncVisibility()
  syncPosition()
})

onUnmounted(() => {
  window.removeEventListener('scroll', syncVisibility)
  window.removeEventListener('resize', handleViewportChange)
  desktopMediaQuery?.removeEventListener('change', handleViewportChange)
})
</script>

<template>
  <Transition name="back-to-top-fade">
    <button
      v-if="visible"
      class="back-to-top"
      type="button"
      :style="leftPx !== null ? { left: `${leftPx}px` } : undefined"
      :aria-label="label"
      :title="label"
      @click="scrollToTop"
    >
      <span class="vpi-chevron-right back-to-top__icon" aria-hidden="true" />
    </button>
  </Transition>
</template>

<style scoped>
.back-to-top {
  position: fixed;
  left: 24px;
  bottom: 24px;
  z-index: var(--vp-z-index-local-nav);
  display: flex;
  align-items: center;
  justify-content: center;
  border: 1px solid var(--vp-c-border);
  border-radius: 999px;
  width: 44px;
  height: 44px;
  background-color: var(--vp-c-bg-soft);
  color: var(--vp-c-text-2);
  box-shadow: var(--vp-shadow-3);
  transition: color 0.25s, border-color 0.25s, background-color 0.25s, opacity 0.25s, transform 0.25s;
}

.back-to-top:hover,
.back-to-top:focus-visible {
  border-color: var(--vp-c-brand-1);
  color: var(--vp-c-brand-1);
}

.back-to-top:focus-visible {
  outline: 2px solid transparent;
  outline-offset: 2px;
}

.back-to-top__icon {
  font-size: 18px;
  transform: rotate(-90deg);
}

.back-to-top-fade-enter-active,
.back-to-top-fade-leave-active {
  transition: opacity 0.25s, transform 0.25s;
}

.back-to-top-fade-enter-from,
.back-to-top-fade-leave-to {
  opacity: 0;
  transform: translateY(8px);
}

@media (prefers-reduced-motion: reduce) {
  .back-to-top,
  .back-to-top-fade-enter-active,
  .back-to-top-fade-leave-active {
    transition: none;
  }
}

@media (max-width: 1279px) {
  .back-to-top {
    display: none;
  }
}
</style>
