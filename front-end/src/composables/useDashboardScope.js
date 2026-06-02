import { computed } from 'vue'
import { useRoute } from 'vue-router'

// Détermine si les vues partagées (Dashboard/Nutrition/Workout/Trends)
// sont affichées dans le contexte admin (/admin/dashboard/:id) ou
// utilisateur (/dashboard/:id), et construit les liens correspondants.
export function useDashboardScope() {
  const route = useRoute()

  const isAdminScope = computed(() => route.path.startsWith('/admin'))

  function basePath(userId) {
    return isAdminScope.value
      ? `/admin/dashboard/${userId}`
      : `/dashboard/${userId}`
  }

  return { isAdminScope, basePath }
}
