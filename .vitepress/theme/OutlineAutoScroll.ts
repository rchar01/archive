import { onContentUpdated } from 'vitepress'
import { defineComponent, h, nextTick, onMounted, onUnmounted } from 'vue'

const ASIDE_CONTAINER_SELECTOR = '.VPDoc .aside-container'
const OUTLINE_SELECTOR = '.VPDocAsideOutline'
const ACTIVE_LINK_SELECTOR = '.VPDocAsideOutline .outline-link.active'
const EDGE_PADDING = 72
const ANIMATION_DURATION_MS = 340
const MIN_SCROLL_DELTA = 6

function clamp(value: number, min: number, max: number): number {
  return Math.min(Math.max(value, min), max)
}

function easeOutCubic(progress: number): number {
  return 1 - Math.pow(1 - progress, 3)
}

function targetScrollTopForActiveLink(container: HTMLElement, activeLink: HTMLElement): number | null {
  const containerRect = container.getBoundingClientRect()
  const activeRect = activeLink.getBoundingClientRect()
  const safeTop = containerRect.top + EDGE_PADDING
  const safeBottom = containerRect.bottom - EDGE_PADDING

  if (activeRect.top >= safeTop && activeRect.bottom <= safeBottom) {
    return null
  }

  const offsetWithinContainer = activeRect.top - containerRect.top + container.scrollTop
  const maxScrollTop = Math.max(container.scrollHeight - container.clientHeight, 0)
  const targetScrollTop = offsetWithinContainer - container.clientHeight / 2 + activeRect.height / 2
  return clamp(targetScrollTop, 0, maxScrollTop)
}

export default defineComponent({
  name: 'OutlineAutoScroll',
  setup() {
    let syncFrame = 0
    let animationFrame = 0
    let animationTarget: number | null = null
    let observer: MutationObserver | null = null

    const cancelAnimation = () => {
      if (animationFrame) {
        cancelAnimationFrame(animationFrame)
        animationFrame = 0
      }
      animationTarget = null
    }

    const animateScroll = (container: HTMLElement, targetScrollTop: number) => {
      if (Math.abs(container.scrollTop - targetScrollTop) < MIN_SCROLL_DELTA) {
        container.scrollTop = targetScrollTop
        cancelAnimation()
        return
      }

      if (animationTarget !== null && Math.abs(animationTarget - targetScrollTop) < MIN_SCROLL_DELTA) {
        return
      }

      cancelAnimation()

      const startScrollTop = container.scrollTop
      const startedAt = performance.now()
      animationTarget = targetScrollTop

      const step = (now: number) => {
        const progress = clamp((now - startedAt) / ANIMATION_DURATION_MS, 0, 1)
        const eased = easeOutCubic(progress)
        container.scrollTop = startScrollTop + (targetScrollTop - startScrollTop) * eased

        if (progress < 1) {
          animationFrame = requestAnimationFrame(step)
          return
        }

        container.scrollTop = targetScrollTop
        animationFrame = 0
        animationTarget = null
      }

      animationFrame = requestAnimationFrame(step)
    }

    const scrollActiveOutlineIntoView = () => {
      const container = document.querySelector<HTMLElement>(ASIDE_CONTAINER_SELECTOR)
      const activeLink = document.querySelector<HTMLElement>(ACTIVE_LINK_SELECTOR)
      if (!container || !activeLink) {
        cancelAnimation()
        return
      }

      const targetScrollTop = targetScrollTopForActiveLink(container, activeLink)
      if (targetScrollTop === null) {
        return
      }

      animateScroll(container, targetScrollTop)
    }

    const scheduleScrollSync = () => {
      if (syncFrame) {
        cancelAnimationFrame(syncFrame)
      }
      syncFrame = requestAnimationFrame(() => {
        syncFrame = 0
        scrollActiveOutlineIntoView()
      })
    }

    const bindObserver = () => {
      observer?.disconnect()
      observer = null

      const outline = document.querySelector<HTMLElement>(OUTLINE_SELECTOR)
      if (!outline) {
        return
      }

      observer = new MutationObserver(scheduleScrollSync)
      observer.observe(outline, {
        subtree: true,
        childList: true,
        attributes: true,
        attributeFilter: ['class'],
      })
    }

    const handleResize = () => {
      scheduleScrollSync()
    }

    onMounted(() => {
      bindObserver()
      scheduleScrollSync()
      window.addEventListener('resize', handleResize)
    })

    onContentUpdated(async () => {
      await nextTick()
      bindObserver()
      scheduleScrollSync()
    })

    onUnmounted(() => {
      if (syncFrame) {
        cancelAnimationFrame(syncFrame)
      }
      cancelAnimation()
      observer?.disconnect()
      window.removeEventListener('resize', handleResize)
    })

    return () => h('span', { 'aria-hidden': 'true', style: 'display:none' })
  },
})
