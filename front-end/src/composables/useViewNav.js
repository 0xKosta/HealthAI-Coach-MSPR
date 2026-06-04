import { computed, unref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useDashboardScope } from './useDashboardScope'

// Navigation ordonnée entre les 4 vues partagées
// (Dashboard ← Nutrition ← Entraînement ← Tendances).
// Swipe horizontal : ne pas bloquer les taps (PWA / tactile surtout sur Nutrition).
const SWIPE_THRESHOLD = 55
const SWIPE_LOCK_PX = 12
const PREVENT_DEFAULT_PX = 28

const INTERACTIVE_SELECTOR = [
  'a',
  'button',
  'input',
  'select',
  'textarea',
  'label',
  '[role="button"]',
  '[role="tab"]',
  '[data-no-swipe]',
  '.nutrition-tabs',
  '.nutrition-tabs__btn',
  '.nutrition-module-nav',
  '.btn-primary',
  '.btn-secondary',
  '.btn-danger',
  '.cursor-pointer',
].join(', ')

function isInteractiveTarget(target) {
  if (!target || !(target instanceof Element)) return false
  return !!target.closest(INTERACTIVE_SELECTOR)
}

export function useViewNav(userIdRef) {
  const route = useRoute()
  const router = useRouter()
  const { basePath } = useDashboardScope()

  const userId = computed(() => unref(userIdRef))
  const base = computed(() => basePath(userId.value))

  const tabs = computed(() => [
    { label: 'Dashboard', to: base.value },
    { label: 'Nutrition', to: `${base.value}/nutrition` },
    { label: 'Entraînement', to: `${base.value}/workout` },
    { label: 'Tendances', to: `${base.value}/trends` },
  ])

  const activeIndex = computed(() => {
    if (route.path.includes('/nutrition')) return 1
    if (route.path.includes('/workout')) return 2
    if (route.path.includes('/trends')) return 3
    return 0
  })

  function goTo(index) {
    if (!userId.value) return
    if (index < 0 || index >= tabs.value.length) return
    if (index === activeIndex.value) return
    router.push(tabs.value[index].to)
  }

  const goNext = () => goTo(activeIndex.value + 1)
  const goPrev = () => goTo(activeIndex.value - 1)

  let startX = 0
  let startY = 0
  let lockedHorizontal = false
  let tracking = false
  let skipSwipe = false

  function onPointerDown(event) {
    if (isInteractiveTarget(event.target)) {
      skipSwipe = true
      return
    }
    skipSwipe = false
    if (event.pointerType === 'mouse' && event.button !== 0) return
    startX = event.clientX
    startY = event.clientY
    lockedHorizontal = false
    tracking = true
  }

  function onPointerMove(event) {
    if (!tracking || skipSwipe) return
    if (event.pointerType === 'mouse' && !(event.buttons & 1)) return

    const dx = event.clientX - startX
    const dy = event.clientY - startY
    if (!lockedHorizontal && Math.abs(dx) > SWIPE_LOCK_PX && Math.abs(dx) > Math.abs(dy)) {
      lockedHorizontal = true
      if (event.pointerType === 'mouse') {
        try {
          event.currentTarget?.setPointerCapture(event.pointerId)
        } catch {
          /* ignore */
        }
      }
    }
    if (lockedHorizontal && Math.abs(dx) > PREVENT_DEFAULT_PX && event.cancelable) {
      event.preventDefault()
    }
  }

  function onPointerUp(event) {
    if (!tracking) return
    tracking = false

    try {
      event.currentTarget?.releasePointerCapture(event.pointerId)
    } catch {
      /* ignore */
    }

    if (skipSwipe) {
      skipSwipe = false
      return
    }

    const dx = event.clientX - startX
    const dy = event.clientY - startY
    if (!lockedHorizontal) return

    const isHorizontal =
      Math.abs(dx) > SWIPE_THRESHOLD && Math.abs(dx) > Math.abs(dy) * 1.2
    if (!isHorizontal) return
    if (dx < 0) goNext()
    else goPrev()
  }

  return {
    tabs,
    activeIndex,
    goTo,
    goNext,
    goPrev,
    onPointerDown,
    onPointerMove,
    onPointerUp,
  }
}
