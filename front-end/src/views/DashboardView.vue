<template>
  <div class="space-y-8 animate-fade-in" @touchstart.passive="onTouchStart" @touchmove="onTouchMove" @touchend.passive="onTouchEnd">

    <!-- Header -->
    <div class="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
      <div>
        <h1 class="text-3xl font-bold text-brand-primary">Dashboard</h1>
        <p class="text-slate-600 mt-1">
          {{ isProfileIncomplete && !isAdminScope
            ? 'Finalisez votre profil pour débloquer votre suivi santé'
            : "Vue d'ensemble santé de l'utilisateur sélectionné" }}
        </p>
      </div>
      <div v-if="isAdminScope" class="flex flex-wrap items-center gap-3">
        <button class="btn-secondary" @click="goToUsersList">Changer d'utilisateur</button>
      </div>
    </div>

    <AdminUserTabs v-if="activeUserId" :user-id="activeUserId" />

    <LoadingSpinner v-if="userLoading" message="Chargement du profil utilisateur..." />
    <ErrorAlert v-else-if="userError" :message="userError" />

    <template v-else-if="user">

      <!-- Hero onboarding (utilisateur) -->
      <div
        v-if="isProfileIncomplete && !isAdminScope && activeUserId"
        class="card border-2 border-brand-accent/25 bg-gradient-to-br from-white to-brand-accent/5"
      >
        <div class="flex flex-col lg:flex-row lg:items-start gap-6">
          <div class="flex-1">
            <p class="text-sm font-semibold text-brand-accent uppercase tracking-wide mb-1">Bienvenue</p>
            <h2 class="text-2xl font-bold text-brand-primary">
              Bonjour {{ displayName }} 👋
            </h2>
            <p class="text-slate-600 mt-2 max-w-xl">
              Votre coach IA a besoin de quelques informations pour calculer vos indicateurs
              et vous proposer des conseils personnalisés.
            </p>

            <div class="mt-5">
              <div class="flex justify-between text-sm mb-2">
                <span class="font-medium text-brand-primary">Profil complété</span>
                <span class="text-slate-600">{{ profileCompletedCount }}/{{ profileSteps.length }}</span>
              </div>
              <div class="h-2.5 bg-slate-100 rounded-full overflow-hidden">
                <div
                  class="h-full rounded-full bg-gradient-to-r from-brand-accent to-teal-500 transition-all duration-500"
                  :style="{ width: `${profileCompletionPercent}%` }"
                ></div>
              </div>
            </div>

            <ul class="mt-5 space-y-2.5">
              <li
                v-for="step in profileSteps"
                :key="step.key"
                class="flex items-center gap-3 text-sm"
              >
                <span
                  class="w-6 h-6 rounded-full flex items-center justify-center shrink-0 border"
                  :class="step.completed
                    ? 'bg-brand-success/15 border-brand-success/40 text-teal-700'
                    : 'bg-white border-slate-200 text-slate-400'"
                >
                  <svg v-if="step.completed" class="w-3.5 h-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round">
                    <path d="M20 6L9 17l-5-5" />
                  </svg>
                  <span v-else class="w-1.5 h-1.5 rounded-full bg-slate-300"></span>
                </span>
                <span :class="step.completed ? 'text-slate-600 line-through' : 'text-brand-primary font-medium'">
                  {{ step.label }}
                </span>
              </li>
            </ul>
          </div>

          <div class="flex flex-col items-stretch lg:items-end gap-3 lg:min-w-[220px]">
            <RouterLink :to="profileEditPath" class="btn-primary justify-center">
              Compléter mon profil
              <span class="material-symbols-outlined text-[18px] leading-none">arrow_forward</span>
            </RouterLink>
            <p class="text-xs text-slate-500 text-center lg:text-right">
              Environ 30 s · Âge, poids, taille, objectif
            </p>
          </div>
        </div>
      </div>

      <!-- Alerte admin : profil incomplet -->
      <RouterLink
        v-else-if="isProfileIncomplete && isAdminScope && activeUserId"
        :to="profileEditPath"
        class="flex items-center gap-3 p-4 rounded-xl bg-brand-warning/10 border border-brand-warning/30 text-amber-800 hover:bg-brand-warning/15 transition-colors"
      >
        <span class="material-symbols-outlined text-[22px] leading-none text-brand-warning">info</span>
        <span class="text-sm font-medium">Profil utilisateur incomplet — métriques et conseil IA indisponibles.</span>
        <span class="material-symbols-outlined text-[18px] leading-none ml-auto">chevron_right</span>
      </RouterLink>

      <!-- Profil + Stats -->
      <div class="grid grid-cols-1 lg:grid-cols-3 gap-4">

        <!-- Carte profil -->
        <div class="card lg:col-span-1">
          <div class="flex items-center gap-4 mb-5">
            <div class="w-14 h-14 rounded-2xl border flex items-center justify-center" :class="avatarBgClass">
              <svg v-if="user.gender === 'female'" class="w-7 h-7 text-pink-600" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round">
                <circle cx="12" cy="8" r="4" /><path d="M12 12v9M9 18h6" />
              </svg>
              <svg v-else-if="user.gender === 'male'" class="w-7 h-7 text-sky-700" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round">
                <circle cx="10" cy="14" r="5" /><path d="M14 10l6-6M16 4h4v4" />
              </svg>
              <svg v-else class="w-7 h-7 text-slate-400" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round">
                <circle cx="12" cy="8" r="4" /><path d="M5 21a7 7 0 0 1 14 0" />
              </svg>
            </div>
            <div>
              <h2 class="text-xl font-bold text-brand-primary">{{ displayName }}</h2>
              <span v-if="user.goal" :class="goalBadgeClass">{{ goalLabel }}</span>
              <span v-else class="badge-warning text-xs">Objectif à définir</span>
            </div>
          </div>

          <div class="grid grid-cols-2 gap-3">
            <div class="bg-white rounded-xl p-3 text-center border border-slate-100">
              <p class="text-2xl font-bold text-brand-primary">{{ user.age ?? '—' }}</p>
              <p class="text-xs text-slate-600">ans</p>
            </div>
            <div class="bg-white rounded-xl p-3 text-center border border-slate-100">
              <p class="text-2xl font-bold" :class="bmiColor">{{ user.bmi != null ? user.bmi.toFixed(1) : '—' }}</p>
              <p class="text-xs text-slate-600">IMC</p>
            </div>
            <div class="bg-white rounded-xl p-3 text-center border border-slate-100">
              <p class="text-2xl font-bold text-brand-primary">{{ user.weight_kg != null ? `${user.weight_kg} kg` : '—' }}</p>
              <p class="text-xs text-slate-600">Poids</p>
            </div>
            <div class="bg-white rounded-xl p-3 text-center border border-slate-100">
              <p class="text-2xl font-bold text-brand-primary">{{ user.height_cm != null ? `${(user.height_cm / 100).toFixed(2)} m` : '—' }}</p>
              <p class="text-xs text-slate-600">Taille</p>
            </div>
          </div>

          <div v-if="user.body_fat_pct" class="mt-3 bg-white rounded-xl p-3 border border-slate-100">
            <div class="flex justify-between mb-1.5">
              <span class="text-xs text-slate-600">Masse grasse</span>
              <span class="text-xs font-semibold text-brand-secondary">{{ user.body_fat_pct?.toFixed(1) }}%</span>
            </div>
            <div class="h-2 bg-slate-100 rounded-full overflow-hidden">
              <div class="h-full rounded-full bg-gradient-to-r from-brand-accent to-brand-success transition-all duration-700"
                   :style="{ width: `${Math.min(user.body_fat_pct, 50) * 2}%` }"></div>
            </div>
          </div>
        </div>

        <!-- Stats rapides (profil complet) -->
        <div v-if="!isProfileIncomplete" class="lg:col-span-2 grid grid-cols-2 gap-4">
          <StatCard
            label="Score santé estimé"
            :value="healthScore"
            sub="Basé sur l'IMC et objectif"
            icon='<path d="M22 12h-4l-3 9L9 3l-3 9H2"/>'
            iconBg="bg-brand-success/15"
            iconColor="text-teal-600"
          />
          <StatCard
            label="Objectif"
            :value="goalLabel"
            :sub="genderLabel"
            icon='<circle cx="12" cy="12" r="10"/><path d="M8 14s1.5 2 4 2 4-2 4-2"/><line x1="9" y1="9" x2="9.01" y2="9"/><line x1="15" y1="9" x2="15.01" y2="9"/>'
            iconBg="bg-brand-accent/10"
            iconColor="text-brand-accent"
          />
          <StatCard
            label="IMC"
            :value="bmiCategory"
            :sub="bmiSubLabel"
            :icon='`<rect x="2" y="3" width="20" height="14" rx="2"/><line x1="8" y1="21" x2="16" y2="21"/><line x1="12" y1="17" x2="12" y2="21"/>`'
            :iconBg="bmiIconBg"
            :iconColor="bmiIconColor"
          />
          <StatCard
            label="Statut"
            value="Suivi actif"
            sub="Données synchronisées"
            icon='<path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>'
            iconBg="bg-brand-success/15"
            iconColor="text-teal-600"
          />
        </div>

        <!-- Placeholder stats (profil incomplet) -->
        <div
          v-else
          class="card lg:col-span-2 flex flex-col items-center justify-center text-center py-10 px-6 border border-dashed border-slate-200 bg-slate-50/50"
        >
          <div class="w-14 h-14 rounded-2xl bg-white border border-slate-200 flex items-center justify-center mb-4">
            <span class="material-symbols-outlined text-[28px] text-slate-400">monitoring</span>
          </div>
          <h3 class="text-lg font-bold text-brand-primary">Vos indicateurs apparaîtront ici</h3>
          <p class="text-sm text-slate-600 mt-2 max-w-sm">
            Score santé, IMC et suivi personnalisé — disponibles dès que le profil est complété.
          </p>
          <RouterLink v-if="activeUserId" :to="profileEditPath" class="btn-secondary mt-5">
            Compléter le profil
          </RouterLink>
        </div>
      </div>

      <!-- Conseil IA -->
      <div class="card" :class="{ 'opacity-75': isProfileIncomplete }">
        <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6">
          <div class="flex items-start gap-3">
            <div
              v-if="isProfileIncomplete"
              class="w-10 h-10 rounded-xl bg-slate-100 border border-slate-200 flex items-center justify-center shrink-0"
            >
              <span class="material-symbols-outlined text-[22px] text-slate-500">lock</span>
            </div>
            <div>
              <h2 class="text-xl font-bold text-brand-primary">Conseil personnalisé</h2>
              <p class="text-sm text-slate-600 mt-0.5">
                {{ isProfileIncomplete
                  ? 'Renseignez âge, poids, taille et objectif pour activer l\'analyse IA.'
                  : 'Analyse IA basée sur votre profil complet' }}
              </p>
            </div>
          </div>
          <RouterLink
            v-if="isProfileIncomplete && activeUserId"
            :to="profileEditPath"
            class="btn-primary justify-center shrink-0"
          >
            Débloquer le conseil IA
          </RouterLink>
          <button
            v-else
            @click="fetchAdvice"
            :disabled="adviceLoading"
            class="btn-primary shrink-0"
          >
            <div v-if="adviceLoading" class="w-4 h-4 border-2 border-brand-primary border-t-transparent rounded-full animate-spin"></div>
            <svg v-else class="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round">
              <circle cx="12" cy="12" r="10"/><path d="M12 8v4l3 3"/>
            </svg>
            {{ adviceLoading ? 'Analyse en cours...' : 'Obtenir un conseil IA' }}
          </button>
        </div>

        <template v-if="!isProfileIncomplete">
          <ErrorAlert v-if="adviceError" :message="adviceError" />

          <div v-if="!advice && !adviceLoading && !adviceError"
               class="flex flex-col items-center justify-center py-10 text-center">
            <div class="w-16 h-16 rounded-2xl bg-brand-accent/10 border border-brand-accent/20 flex items-center justify-center mb-4">
              <svg class="w-8 h-8 text-brand-accent/50" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round">
                <path d="M12 2a10 10 0 1 0 10 10"/><circle cx="18" cy="6" r="3" fill="currentColor"/>
              </svg>
            </div>
            <p class="text-slate-600 text-sm">Cliquez sur le bouton pour recevoir un conseil personnalisé</p>
          </div>

          <AIAdviceCard v-if="advice" :title="`Conseil pour ${displayName}`" :content="advice" />
        </template>

        <div
          v-else
          class="flex flex-col items-center justify-center py-8 text-center rounded-xl bg-slate-50 border border-slate-100"
        >
          <p class="text-sm text-slate-600 max-w-md">
            Le coach IA analyse votre profil complet pour des recommandations adaptées à votre objectif.
          </p>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useUserStore } from '@/stores/userStore'
import { useAuthStore } from '@/stores/authStore'
import { useDashboardScope } from '@/composables/useDashboardScope'
import { isProfileIncomplete as checkProfileIncomplete, getProfileEditPath } from '@/composables/useProfileCompletion'
import { useViewNav } from '@/composables/useViewNav'
import { coachAPI, usersAPI } from '@/services/api'
import AdminUserTabs from '@/components/layout/AdminUserTabs.vue'
import LoadingSpinner from '@/components/ui/LoadingSpinner.vue'
import ErrorAlert from '@/components/ui/ErrorAlert.vue'
import AIAdviceCard from '@/components/ui/AIAdviceCard.vue'
import StatCard from '@/components/ui/StatCard.vue'

const userStore = useUserStore()
const auth = useAuthStore()
const { isAdminScope } = useDashboardScope()
const route = useRoute()
const router = useRouter()
const activeUserId = ref(null)
const { onTouchStart, onTouchMove, onTouchEnd } = useViewNav(activeUserId)
const activeUser = ref(null)
const userLoading = ref(false)
const userError = ref('')
const user = computed(() => activeUser.value)

const displayName = computed(() => {
  if (!isAdminScope.value && auth.currentUser?.first_name) {
    return auth.currentUser.first_name
  }
  return activeUser.value?.name
})

const profileEditPath = computed(() => getProfileEditPath(activeUserId.value))

const avatarBgClass = computed(() => {
  const g = activeUser.value?.gender
  if (g === 'female') return 'bg-pink-100 border-pink-200'
  if (g === 'male') return 'bg-sky-100 border-sky-200'
  return 'bg-slate-100 border-slate-200'
})

const isProfileIncomplete = computed(() => checkProfileIncomplete(activeUser.value))

const profileSteps = computed(() => {
  const u = activeUser.value
  if (!u) return []
  return [
    { key: 'age', label: 'Âge', completed: u.age != null },
    { key: 'weight', label: 'Poids', completed: u.weight_kg != null },
    { key: 'height', label: 'Taille', completed: u.height_cm != null },
    { key: 'goal', label: 'Objectif santé', completed: !!u.goal },
  ]
})

const profileCompletedCount = computed(() =>
  profileSteps.value.filter((s) => s.completed).length
)

const profileCompletionPercent = computed(() => {
  const total = profileSteps.value.length
  if (!total) return 0
  return Math.round((profileCompletedCount.value / total) * 100)
})

const advice = ref('')
const adviceLoading = ref(false)
const adviceError = ref('')

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
    activeUser.value = res.data
    userStore.selectUser(activeUserId.value)
  } catch {
    userError.value = "Impossible de charger ce profil utilisateur."
    activeUser.value = null
  } finally {
    userLoading.value = false
  }
}

function goToUsersList() {
  router.push(isAdminScope.value ? '/admin' : '/')
}

watch(() => route.params.userId, async () => {
  advice.value = ''
  adviceError.value = ''
  activeUserId.value = parseUserIdFromRoute()
  if (!activeUserId.value) {
    goToUsersList()
    return
  }
  await loadUserProfile()
}, { immediate: true })

// Recharger le profil au retour depuis l'édition (ex. après complétion)
watch(() => route.fullPath, async (path, prev) => {
  if (!activeUserId.value || !prev) return
  if (prev.includes('/profile') && !path.includes('/profile')) {
    await loadUserProfile()
  }
})

const goalLabels = {
  weight_loss: 'Perte de poids', muscle_gain: 'Prise de muscle',
  sleep_improvement: 'Améliorer le sommeil', maintenance: 'Maintien',
}
const genderLabels = { male: 'Homme', female: 'Femme', other: 'Autre' }

const goalLabel   = computed(() => goalLabels[user.value?.goal] || user.value?.goal || '—')
const genderLabel = computed(() => genderLabels[user.value?.gender] || user.value?.gender || '—')

const goalBadgeClass = computed(() => ({
  weight_loss: 'badge-accent', muscle_gain: 'badge-success',
  sleep_improvement: 'badge-warning', maintenance: 'badge-primary',
}[user.value?.goal] || 'badge-primary'))

const bmiColor = computed(() => {
  const b = user.value?.bmi
  if (!b) return 'text-brand-primary'
  if (b < 18.5) return 'text-brand-warning'
  if (b < 25)   return 'text-teal-600'
  if (b < 30)   return 'text-brand-warning'
  return 'text-brand-error'
})
const bmiIconBg = computed(() => {
  const b = user.value?.bmi
  if (!b) return 'bg-slate-100'
  if (b >= 18.5 && b < 25) return 'bg-brand-success/15'
  if (b < 30) return 'bg-brand-warning/15'
  return 'bg-brand-error/10'
})
const bmiIconColor = computed(() => {
  const b = user.value?.bmi
  if (!b) return 'text-slate-400'
  if (b >= 18.5 && b < 25) return 'text-teal-600'
  if (b < 30) return 'text-amber-600'
  return 'text-brand-error'
})
const bmiCategory = computed(() => {
  const b = user.value?.bmi
  if (!b) return '—'
  if (b < 18.5) return 'Insuffisant'
  if (b < 25)   return 'Normal'
  if (b < 30)   return 'Surpoids'
  return 'Obésité'
})
const bmiSubLabel = computed(() => {
  const b = user.value?.bmi
  return b != null ? `${b.toFixed(1)} kg/m²` : '—'
})
const healthScore = computed(() => {
  const u = user.value
  if (!u?.bmi) return '—'
  let s = 50
  const b = u.bmi
  if (b >= 18.5 && b < 25) s += 30
  else if (b >= 25 && b < 30) s += 10
  if (u.goal === 'maintenance') s += 10
  if (u.goal === 'muscle_gain') s += 5
  return `${Math.min(s, 100)}/100`
})

async function fetchAdvice() {
  if (!user.value || isProfileIncomplete.value) return
  adviceLoading.value = true; adviceError.value = ''; advice.value = ''
  try {
    const res = await coachAPI.getAdvice(user.value.id)
    advice.value = res.data.advice
  } catch {
    adviceError.value = "Impossible d'obtenir un conseil. Vérifiez la connexion à l'API."
  } finally {
    adviceLoading.value = false
  }
}
</script>
