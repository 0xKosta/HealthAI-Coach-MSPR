import { computed } from 'vue'
import { useAuthStore } from '@/stores/authStore'
import { useDashboardScope } from '@/composables/useDashboardScope'

/** Prénom auth en espace perso ; nom du profil users en vue admin. */
export function useDisplayName(profileUser) {
  const auth = useAuthStore()
  const { isAdminScope } = useDashboardScope()
  return computed(() => {
    if (!isAdminScope.value && auth.currentUser?.first_name) {
      return auth.currentUser.first_name
    }
    return profileUser.value?.name ?? ''
  })
}
