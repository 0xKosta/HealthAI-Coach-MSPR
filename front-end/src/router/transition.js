import { ref } from 'vue'

// Nom de transition appliqué au <RouterView> (voir App.vue).
// 'slide-left'  : navigation « en avant »  (Dashboard → … → Tendances)
// 'slide-right' : navigation « en arrière »
// 'page'        : transition par défaut (fondu vertical) hors vues partagées
export const transitionName = ref('page')

// Position d'une vue partagée dans l'ordre Dashboard → Nutrition → Entraînement → Tendances.
// Renvoie null si la route n'est pas une de ces 4 vues.
function viewIndex(path) {
  if (!path) return null
  if (path.includes('/nutrition')) return 1
  if (path.includes('/workout')) return 2
  if (path.includes('/trends')) return 3
  if (/\/dashboard\/\d+$/.test(path)) return 0
  return null
}

export function updateTransition(to, from) {
  const ti = viewIndex(to?.path)
  const fi = viewIndex(from?.path)

  if (ti !== null && fi !== null && ti !== fi) {
    transitionName.value = ti > fi ? 'slide-left' : 'slide-right'
  } else {
    transitionName.value = 'page'
  }
}
