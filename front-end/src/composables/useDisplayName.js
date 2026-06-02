import { computed } from 'vue'
import { useAuthStore } from '@/stores/authStore'
import { useDashboardScope } from '@/composables/useDashboardScope'

/** Prénom + nom user_auth si disponibles, sinon users.name (legacy). */
export function formatProfileDisplayName(user) {
  if (!user) return ''
  if (user.first_name) {
    return [user.first_name, user.last_name].filter(Boolean).join(' ')
  }
  return user.name ?? ''
}

/** Prénom auth en espace perso ; prénom/nom user_auth en vue admin. */
export function useDisplayName(profileUser) {
  const auth = useAuthStore()
  const { isAdminScope } = useDashboardScope()
  return computed(() => {
    if (!isAdminScope.value && auth.currentUser?.first_name) {
      return auth.currentUser.first_name
    }
    return formatProfileDisplayName(profileUser.value)
  })
}
