import { computed, unref } from 'vue'
import { useAuthStore } from '@/stores/authStore'
import {
  blocksAiFeatures,
  hasInvalidProfileData,
  PROFILE_AI_REQUIRED_MSG,
  PROFILE_INVALID_MSG,
} from '@/composables/useProfileCompletion'

export const PLAN_AI_REQUIRED_MSG =
  'Les analyses et conseils IA sont réservés à l\'offre Premium (9,99 €/mois) ou Premium+.'

/** Profil incomplet/invalide ou plan free sans droit IA. */
export function useAiGate(profileUser) {
  const auth = useAuthStore()

  const profileBlocksAi = computed(() => blocksAiFeatures(unref(profileUser)))
  const planBlocksAi = computed(() => !auth.canUseAi)
  const aiBlocked = computed(() => profileBlocksAi.value || planBlocksAi.value)

  const aiGateTitle = computed(() => {
    const user = unref(profileUser)
    if (profileBlocksAi.value) {
      return hasInvalidProfileData(user)
        ? 'Analyse IA verrouillée'
        : 'Analyse IA verrouillée'
    }
    if (planBlocksAi.value) return 'Coach IA — offre Premium'
    return ''
  })

  const aiGateDescription = computed(() => {
    const user = unref(profileUser)
    if (profileBlocksAi.value) {
      return hasInvalidProfileData(user) ? PROFILE_INVALID_MSG : PROFILE_AI_REQUIRED_MSG
    }
    if (planBlocksAi.value) return PLAN_AI_REQUIRED_MSG
    return ''
  })

  return {
    profileBlocksAi,
    planBlocksAi,
    aiBlocked,
    aiGateTitle,
    aiGateDescription,
  }
}
