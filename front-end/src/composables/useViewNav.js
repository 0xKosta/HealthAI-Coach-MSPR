import { computed, unref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useDashboardScope } from './useDashboardScope'

// Navigation ordonnée entre les 4 vues partagées
// (Dashboard ← Nutrition ← Entraînement ← Tendances).
// Fournit la liste d'onglets, l'index actif, des helpers de navigation
// et des handlers tactiles pour le swipe gauche/droite sur mobile.
const SWIPE_THRESHOLD = 55 // px de déplacement horizontal minimum

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

  function onTouchStart(event) {
    const touch = event.changedTouches?.[0]
    if (!touch) return
    startX = touch.clientX
    startY = touch.clientY
    lockedHorizontal = false
  }

  // Dès qu'un geste devient franchement horizontal, on bloque le comportement
  // natif du navigateur (geste "retour"/"suivant"), qui sinon recharge la page.
  function onTouchMove(event) {
    const touch = event.touches?.[0]
    if (!touch) return
    const dx = touch.clientX - startX
    const dy = touch.clientY - startY
    if (!lockedHorizontal && Math.abs(dx) > 10 && Math.abs(dx) > Math.abs(dy)) {
      lockedHorizontal = true
    }
    if (lockedHorizontal && event.cancelable) {
      event.preventDefault()
    }
  }

  function onTouchEnd(event) {
    const touch = event.changedTouches?.[0]
    if (!touch) return
    const dx = touch.clientX - startX
    const dy = touch.clientY - startY
    // On n'agit que sur un swipe franchement horizontal pour ne pas
    // gêner le scroll vertical ni les graphiques (Tendances).
    const isHorizontal = Math.abs(dx) > SWIPE_THRESHOLD && Math.abs(dx) > Math.abs(dy) * 1.2
    if (!isHorizontal) return
    if (dx < 0) goNext()
    else goPrev()
  }

  return { tabs, activeIndex, goTo, goNext, goPrev, onTouchStart, onTouchMove, onTouchEnd }
}
