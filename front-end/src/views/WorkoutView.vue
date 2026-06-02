<template>
  <div class="space-y-8 animate-fade-in" @touchstart.passive="onTouchStart" @touchmove="onTouchMove" @touchend.passive="onTouchEnd">

    <!-- Header -->
    <div class="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
      <div>
        <h1 class="text-3xl font-bold text-brand-primary">Programme d'Entraînement</h1>
        <p class="text-slate-600 mt-1">
          {{ profileBlocksAi
            ? (hasInvalidProfile
              ? 'Corrigez votre profil pour générer un programme IA'
              : 'Complétez votre profil pour générer un programme personnalisé')
            : 'Générez un plan IA personnalisé selon votre profil et vos objectifs' }}
        </p>
      </div>
      <div class="flex flex-wrap items-center gap-3">
        <button v-if="isAdminScope" class="btn-secondary" @click="goToUsersList">Changer d'utilisateur</button>
      </div>
    </div>

    <AdminUserTabs v-if="activeUserId" :user-id="activeUserId" />

    <LoadingSpinner v-if="userLoading" message="Chargement du profil utilisateur..." />
    <ErrorAlert v-else-if="userError" :message="userError" />

    <ProfileAiGate
      v-if="currentUser && profileBlocksAi"
      title="Génération de programme verrouillée"
      :description="profileGateDescription"
      :issues="profileIssues"
      :profile-edit-path="profileEditPath"
      :cta-label="hasInvalidProfile ? 'Corriger le profil' : (isAdminScope ? 'Modifier le profil' : 'Compléter mon profil')"
    />

    <!-- Formulaire de configuration -->
    <div v-else-if="currentUser" class="card">
      <h2 class="text-xl font-bold text-brand-primary mb-6">Paramètres du programme</h2>
      <div class="grid grid-cols-1 sm:grid-cols-2 gap-6">
        <div>
          <label class="label">Équipement disponible</label>
          <div class="grid grid-cols-2 gap-2">
            <button
              v-for="eq in equipmentOptions" :key="eq.value"
              @click="form.equipment = eq.value"
              class="flex items-center gap-2.5 px-3 py-3 rounded-xl border text-sm font-medium transition-all duration-200"
              :class="form.equipment === eq.value
                ? 'bg-brand-accent text-brand-primary border-brand-accent shadow-sm'
                : 'border-slate-200 text-slate-600 bg-white hover:border-brand-accent/40 hover:text-brand-primary'"
            >
              <span class="material-symbols-outlined text-[20px] leading-none">{{ eq.icon }}</span>
              {{ eq.label }}
            </button>
          </div>
        </div>
        <div>
          <label class="label">Jours d'entraînement par semaine</label>
          <div class="flex gap-2">
            <button
              v-for="d in [1,2,3,4,5,6,7]" :key="d"
              @click="form.daysPerWeek = d"
              class="w-10 h-10 rounded-xl border text-sm font-bold transition-all duration-200"
              :class="form.daysPerWeek === d
                ? 'bg-brand-primary text-white border-brand-primary shadow-sm'
                : 'border-slate-200 text-slate-600 bg-white hover:border-brand-primary/40'"
            >{{ d }}</button>
          </div>
          <p class="text-xs text-slate-600 mt-2">{{ daysLabel }}</p>
        </div>
      </div>
      <div class="mt-6 pt-5 border-t border-slate-100 flex items-center justify-between gap-4">
        <p class="text-sm text-slate-600">
          <span class="font-medium text-brand-primary">{{ displayName }}</span>
          · {{ goalLabels[currentUser?.goal] }} · {{ form.daysPerWeek }}j/semaine
        </p>
        <button @click="generatePlan" :disabled="generating" class="btn-primary">
          <div v-if="generating" class="w-4 h-4 border-2 border-brand-primary border-t-transparent rounded-full animate-spin"></div>
          <svg v-else class="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round">
            <polygon points="5 3 19 12 5 21 5 3"/>
          </svg>
          {{ generating ? 'Génération...' : 'Générer le programme' }}
        </button>
      </div>
    </div>

    <ErrorAlert v-if="planError" :message="planError" />

    <!-- Résultat programme IA -->
    <div v-if="plan && !profileBlocksAi" class="card animate-slide-up">
      <div class="flex items-center justify-between mb-5">
        <div>
          <h2 class="text-xl font-bold text-brand-primary">Votre programme</h2>
          <p class="text-sm text-slate-600 mt-0.5">{{ plan.user_name }} · {{ form.daysPerWeek }} jours/semaine</p>
        </div>
        <button @click="generatePlan" class="btn-secondary text-xs">
          <svg class="w-3.5 h-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round">
            <polyline points="23 4 23 10 17 10"/><polyline points="1 20 1 14 7 14"/>
            <path d="M3.51 9a9 9 0 0114.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0020.49 15"/>
          </svg>
          Régénérer
        </button>
      </div>
      <AIAdviceCard title="Programme d'entraînement IA" :content="plan.plan" />
    </div>

  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useUserStore } from '@/stores/userStore'
import { useDashboardScope } from '@/composables/useDashboardScope'
import { useViewNav } from '@/composables/useViewNav'
import { useDisplayName } from '@/composables/useDisplayName'
import {
  isProfileIncomplete,
  getProfileEditPath,
  blocksAiFeatures,
  hasInvalidProfileData,
  getProfileIssues,
  PROFILE_AI_REQUIRED_MSG,
  PROFILE_INVALID_MSG,
} from '@/composables/useProfileCompletion'
import { parseApiErrorDetail } from '@/composables/useBiometricValidation'
import { coachAPI, usersAPI } from '@/services/api'
import AdminUserTabs from '@/components/layout/AdminUserTabs.vue'
import LoadingSpinner from '@/components/ui/LoadingSpinner.vue'
import ErrorAlert from '@/components/ui/ErrorAlert.vue'
import AIAdviceCard from '@/components/ui/AIAdviceCard.vue'
import ProfileAiGate from '@/components/ui/ProfileAiGate.vue'

const userStore = useUserStore()
const { isAdminScope } = useDashboardScope()
const route = useRoute()
const router = useRouter()
const activeUserId = ref(null)
const { onTouchStart, onTouchMove, onTouchEnd } = useViewNav(activeUserId)
const currentUser = ref(null)
const userLoading = ref(false)
const userError = ref('')

const form = ref({ equipment: 'dumbbell', daysPerWeek: 3 })
const generating = ref(false)
const planError = ref('')
const plan = ref(null)

const profileIncomplete = computed(() => isProfileIncomplete(currentUser.value))
const profileBlocksAi = computed(() => blocksAiFeatures(currentUser.value))
const hasInvalidProfile = computed(() => hasInvalidProfileData(currentUser.value))
const profileEditPath = computed(() => getProfileEditPath(activeUserId.value))
const profileIssues = computed(() => getProfileIssues(currentUser.value))
const profileGateDescription = computed(() =>
  hasInvalidProfile.value ? PROFILE_INVALID_MSG : PROFILE_AI_REQUIRED_MSG
)
const displayName = useDisplayName(currentUser)

const equipmentOptions = [
  { value: 'none',       label: 'Aucun',         icon: 'self_improvement' },
  { value: 'dumbbell',   label: 'Haltères',       icon: 'fitness_center' },
  { value: 'barbell',    label: 'Barre',           icon: 'sports_gymnastics' },
  { value: 'machine',    label: 'Machines',        icon: 'precision_manufacturing' },
  { value: 'resistance', label: 'Élastiques',      icon: 'sports_martial_arts' },
  { value: 'full',       label: 'Tout matériel',   icon: 'exercise' },
]

const goalLabels = {
  weight_loss: 'Perte de poids', muscle_gain: 'Prise de muscle',
  sleep_improvement: 'Améliorer le sommeil', maintenance: 'Maintien',
}

const daysLabel = computed(() => {
  const d = form.value.daysPerWeek
  if (d <= 2) return 'Débutant — récupération optimale'
  if (d <= 4) return 'Intermédiaire — bon équilibre'
  if (d <= 5) return 'Avancé — haute fréquence'
  return 'Expert — programme intensif'
})

async function generatePlan() {
  if (!activeUserId.value || profileBlocksAi.value) return
  generating.value = true; planError.value = ''; plan.value = null
  try {
    const res = await coachAPI.getWorkoutPlan(activeUserId.value, form.value.equipment, form.value.daysPerWeek)
    plan.value = res.data
  } catch {
    planError.value = "Erreur lors de la génération du programme. Vérifiez la connexion à l'API."
  } finally {
    generating.value = false
  }
}

function parseUserIdFromRoute() {
  const parsed = Number(route.params.userId)
  return Number.isInteger(parsed) && parsed > 0 ? parsed : null
}

async function loadUserProfile() {
  if (!activeUserId.value) return
  userLoading.value = true
  userError.value = ''
  try {
    const res = await usersAPI.getById(activeUserId.value)
    currentUser.value = res.data
    userStore.selectUser(activeUserId.value)
    if (profileBlocksAi.value) {
      plan.value = null
    }
  } catch (e) {
    const detail = parseApiErrorDetail(e.response?.data?.detail)
    userError.value =
      detail ||
      (e.response?.status === 404
        ? 'Profil utilisateur introuvable.'
        : "Impossible de charger ce profil utilisateur.")
    currentUser.value = null
  } finally {
    userLoading.value = false
  }
}

function goToUsersList() {
  router.push(isAdminScope.value ? '/admin' : '/')
}

watch(() => route.params.userId, async () => {
  activeUserId.value = parseUserIdFromRoute()
  if (!activeUserId.value) {
    goToUsersList()
    return
  }
  await loadUserProfile()
}, { immediate: true })

watch(() => route.fullPath, async (path, prev) => {
  if (!activeUserId.value || !prev) return
  if (prev.includes('/profile') && !path.includes('/profile')) {
    await loadUserProfile()
  }
})
</script>
