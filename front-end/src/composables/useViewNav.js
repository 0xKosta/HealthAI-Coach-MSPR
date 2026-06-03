import { computed, unref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useDashboardScope } from './useDashboardScope'

// Navigation ordonnée entre les 4 vues partagées
// (Dashboard ← Nutrition ← Entraînement ← Tendances).
// Swipe horizontal : ne pas intercepter les clics sur liens / boutons.
const SWIPE_THRESHOLD = 55

function isInteractiveTarget(target) {
  if (!target || !(target instanceof Element)) return false
  return !!target.closest(
    'a, button, input, select, textarea, label, [role="button"], [role="tab"], .nutrition-tabs, .nutrition-module-nav'
  )
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

  function onPointerDown(event) {
    if (isInteractiveTarget(event.target)) return
    if (event.pointerType === 'mouse' && event.button !== 0) return
    startX = event.clientX
    startY = event.clientY
    lockedHorizontal = false
    tracking = true
  }

  function onPointerMove(event) {
    if (!tracking) return
    if (event.pointerType === 'mouse' && !(event.buttons & 1)) return

    const dx = event.clientX - startX
    const dy = event.clientY - startY
    if (!lockedHorizontal && Math.abs(dx) > 10 && Math.abs(dx) > Math.abs(dy)) {
      lockedHorizontal = true
      try {
        event.currentTarget?.setPointerCapture(event.pointerId)
      } catch {
        /* ignore */
      }
    }
    if (lockedHorizontal && event.cancelable) {
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

    if (!lockedHorizontal) return

    const dx = event.clientX - startX
    const dy = event.clientY - startY
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
