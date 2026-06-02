<template>
  <div class="space-y-8 animate-fade-in" @touchstart.passive="onTouchStart" @touchmove="onTouchMove" @touchend.passive="onTouchEnd">

    <div class="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
      <div>
        <h1 class="text-3xl font-bold text-brand-primary">Tendances Biométriques</h1>
        <p class="text-slate-600 mt-1">Évolution de vos données de santé sur 30 jours</p>
      </div>
      <div v-if="isAdminScope" class="flex items-center gap-3">
        <button class="btn-secondary" @click="goToUsersList">Changer d'utilisateur</button>
      </div>
    </div>

    <AdminUserTabs v-if="activeUserId" :user-id="activeUserId" />

    <ProfileAiGate
      v-if="currentUser && aiBlocked && !userMetrics.length"
      :title="aiGateTitle"
      :description="aiGateDescription"
      :issues="profileBlocksAi ? profileIssues : []"
      :profile-edit-path="profileBlocksAi ? profileEditPath : ''"
      :cta-label="profileBlocksAi
        ? (hasInvalidProfile ? 'Corriger le profil' : 'Compléter mon profil')
        : ''"
    />

    <LoadingSpinner v-if="metricsLoading" message="Chargement des métriques..." />
    <ErrorAlert v-if="metricsError" :message="metricsError" />

    <template v-if="!metricsLoading && userMetrics.length">
      <!-- KPIs -->
      <div class="grid grid-cols-2 sm:grid-cols-4 gap-4">
        <StatCard
          label="Poids actuel"
          :value="`${latestMetric?.weight_kg?.toFixed(1) ?? '—'} kg`"
          :sub="weightDelta"
          icon='<path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"/>'
          iconBg="bg-brand-accent/10" iconColor="text-brand-accent"
        />
        <StatCard
          label="Sommeil moyen"
          :value="`${avgSleep}`" sub="Durée quotidienne"
          icon='<path d="M17 18a5 5 0 0 0-10 0"/><line x1="12" y1="2" x2="12" y2="9"/><line x1="4.22" y1="10.22" x2="5.64" y2="11.64"/><line x1="1" y1="18" x2="3" y2="18"/><line x1="21" y1="18" x2="23" y2="18"/><line x1="18.36" y1="11.64" x2="19.78" y2="10.22"/>'
          iconBg="bg-violet-100" iconColor="text-violet-600"
        />
        <StatCard
          label="BPM repos moy."
          :value="`${avgBpm} bpm`" sub="Fréquence cardiaque"
          icon='<polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/>'
          iconBg="bg-brand-error/10" iconColor="text-brand-error"
        />
        <StatCard
          label="Entrées métriques"
          :value="userMetrics.length" sub="30 derniers jours"
          icon='<rect x="3" y="4" width="18" height="18" rx="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/>'
          iconBg="bg-brand-success/15" iconColor="text-teal-600"
        />
      </div>

      <!-- Graphiques — fond #F4F7FB -->
      <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div class="card">
          <h3 class="text-lg font-semibold text-brand-primary mb-1">Évolution du poids</h3>
          <p class="text-xs text-slate-600 mb-4">Poids en kg sur les 30 derniers jours</p>
          <apexchart type="area" height="220" :options="weightChartOptions" :series="weightSeries" />
        </div>
        <div class="card">
          <h3 class="text-lg font-semibold text-brand-primary mb-1">Sommeil & BPM repos</h3>
          <p class="text-xs text-slate-600 mb-4">Heures de sommeil et fréquence cardiaque au repos</p>
          <apexchart type="line" height="220" :options="sleepBpmChartOptions" :series="sleepBpmSeries" />
        </div>
      </div>

      <!-- Analyse IA -->
      <div class="card" :class="{ 'opacity-90': !canRunTrendAi }">
        <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6">
          <div class="flex items-start gap-3">
            <div
              v-if="!canRunTrendAi"
              class="w-10 h-10 rounded-xl bg-slate-100 border border-slate-200 flex items-center justify-center shrink-0"
            >
              <span class="material-symbols-outlined text-[22px] text-slate-500">lock</span>
            </div>
            <div>
              <h2 class="text-xl font-bold text-brand-primary">Analyse des tendances</h2>
              <p class="text-sm text-slate-600 mt-0.5">
                {{ trendAiLockHint }}
              </p>
              <ul
                v-if="profileBlocksAi && profileIssues.length"
                class="mt-2 text-sm text-amber-900/90 list-disc list-inside"
              >
                <li v-for="(issue, index) in profileIssues" :key="index">{{ issue }}</li>
              </ul>
            </div>
          </div>
          <RouterLink
            v-if="profileBlocksAi && profileEditPath"
            :to="profileEditPath"
            class="btn-primary shrink-0 justify-center"
          >
            {{ hasInvalidProfile ? 'Corriger le profil' : 'Compléter mon profil' }}
          </RouterLink>
          <button
            v-else-if="canRunTrendAi"
            @click="fetchTrendAnalysis"
            :disabled="trendLoading"
            class="btn-primary shrink-0"
          >
            <div v-if="trendLoading" class="w-4 h-4 border-2 border-brand-primary border-t-transparent rounded-full animate-spin"></div>
            <svg v-else class="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round">
              <path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z"/><path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z"/>
            </svg>
            {{ trendLoading ? 'Analyse...' : 'Analyser les tendances' }}
          </button>
        </div>

        <div v-if="!profileBlocksAi && !canAnalyzeTrends" class="mb-6">
          <div class="flex justify-between text-sm mb-2">
            <span class="font-medium text-brand-primary">Jours de données collectés</span>
            <span class="text-slate-600">{{ distinctMetricDays }}/{{ MIN_TREND_ANALYSIS_DAYS }}</span>
          </div>
          <div class="h-2.5 bg-slate-100 rounded-full overflow-hidden">
            <div
              class="h-full rounded-full bg-gradient-to-r from-brand-accent to-teal-500 transition-all duration-500"
              :style="{ width: `${trendAnalysisProgress}%` }"
            ></div>
          </div>
          <p class="text-xs text-slate-600 mt-2">
            {{ trendDaysRemaining > 0
              ? `Encore ${trendDaysRemaining} jour${trendDaysRemaining > 1 ? 's' : ''} pour débloquer l'analyse IA.`
              : 'Presque prêt — continuez la synchronisation.' }}
          </p>
        </div>

        <template v-if="canRunTrendAi">
          <ErrorAlert v-if="trendError" :message="trendError" />

          <div v-if="!trendAnalysis && !trendLoading && !trendError"
               class="flex flex-col items-center justify-center py-10 text-center">
            <div class="w-16 h-16 rounded-2xl bg-brand-accent/10 border border-brand-accent/20 flex items-center justify-center mb-4">
              <svg class="w-8 h-8 text-brand-accent/50" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round">
                <polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/>
              </svg>
            </div>
            <p class="text-slate-600 text-sm">Cliquez pour obtenir une analyse détaillée de vos tendances</p>
          </div>

          <AIAdviceCard v-if="trendAnalysis" title="Analyse des tendances" :content="trendAnalysis" />
        </template>

        <div
          v-else
          class="flex flex-col items-center justify-center py-8 text-center rounded-xl bg-slate-50 border border-slate-100"
        >
          <p class="text-sm text-slate-600 max-w-md">
            Portez votre montre ou bracelet connecté quelques jours de plus : l'IA pourra alors
            interpréter vos tendances de poids, sommeil et fréquence cardiaque de façon fiable.
          </p>
        </div>
      </div>
    </template>

    <!-- État vide -->
    <div v-if="!metricsLoading && !metricsError && !userMetrics.length"
         class="card flex flex-col items-center justify-center py-14 px-6 text-center max-w-xl mx-auto">
      <div class="w-20 h-20 rounded-2xl bg-brand-accent/10 border border-brand-accent/20 flex items-center justify-center mb-5">
        <span class="material-symbols-outlined text-[40px] text-brand-accent/70">watch</span>
      </div>
      <p class="text-lg font-bold text-brand-primary">Aucune donnée biométrique disponible</p>
      <p class="text-slate-600 text-sm mt-2 max-w-md">
        Connectez votre montre, bracelet ou application santé pour synchroniser poids,
        sommeil et fréquence cardiaque. Vos graphiques apparaîtront dès les premières
        mesures reçues.
      </p>
      <div class="mt-5 flex items-start gap-2.5 p-3.5 rounded-xl bg-brand-warning/10 border border-brand-warning/30 text-left max-w-md">
        <span class="material-symbols-outlined text-[20px] leading-none text-brand-warning shrink-0 mt-0.5">info</span>
        <p class="text-xs text-amber-900 leading-relaxed">
          <span class="font-semibold">À noter :</span>
          pour bénéficier de l'analyse IA de HealthAI Coach sur vos tendances, un minimum de
          <span class="font-semibold">{{ MIN_TREND_ANALYSIS_DAYS }} jours</span>
          de données synchronisées est nécessaire.
        </p>
      </div>
      <p v-if="isAdminScope" class="text-slate-500 text-xs mt-3">
        Vous pouvez aussi sélectionner un autre utilisateur dans la liste admin.
      </p>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useUserStore } from '@/stores/userStore'
import { useDashboardScope } from '@/composables/useDashboardScope'
import { useViewNav } from '@/composables/useViewNav'
import {
  MIN_TREND_ANALYSIS_DAYS,
  countDistinctMetricDays,
  canUnlockTrendAnalysis,
} from '@/composables/useBiometricTrends'
import {
  getProfileEditPath,
  getProfileIssues,
  hasInvalidProfileData,
} from '@/composables/useProfileCompletion'
import { useAiGate, PLAN_AI_REQUIRED_MSG } from '@/composables/useAiAccess'
import { metricsAPI, coachAPI, usersAPI } from '@/services/api'
import AdminUserTabs from '@/components/layout/AdminUserTabs.vue'
import LoadingSpinner from '@/components/ui/LoadingSpinner.vue'
import ErrorAlert from '@/components/ui/ErrorAlert.vue'
import AIAdviceCard from '@/components/ui/AIAdviceCard.vue'
import StatCard from '@/components/ui/StatCard.vue'
import ProfileAiGate from '@/components/ui/ProfileAiGate.vue'

const userStore = useUserStore()
const { isAdminScope } = useDashboardScope()
const route = useRoute()
const router = useRouter()
const allMetrics = ref([])
const metricsLoading = ref(false)
const metricsError = ref('')
const trendAnalysis = ref('')
const trendLoading = ref(false)
const trendError = ref('')
const activeUserId = ref(null)
const currentUser = ref(null)
const { onTouchStart, onTouchMove, onTouchEnd } = useViewNav(activeUserId)

const profileEditPath = computed(() => getProfileEditPath(activeUserId.value))
const hasInvalidProfile = computed(() => hasInvalidProfileData(currentUser.value))
const profileIssues = computed(() => getProfileIssues(currentUser.value))
const { profileBlocksAi, planBlocksAi, aiBlocked, aiGateTitle, aiGateDescription } =
  useAiGate(currentUser)
const userMetrics = computed(() =>
  allMetrics.value
    .slice()
    .sort((a, b) => new Date(a.record_date) - new Date(b.record_date))
    .slice(-30)
)

const distinctMetricDays = computed(() => countDistinctMetricDays(userMetrics.value))
const canAnalyzeTrends = computed(() => canUnlockTrendAnalysis(userMetrics.value))
const canRunTrendAi = computed(() => canAnalyzeTrends.value && !aiBlocked.value)
const trendAiLockHint = computed(() => {
  if (profileBlocksAi.value) return aiGateDescription.value
  if (planBlocksAi.value) return PLAN_AI_REQUIRED_MSG
  if (!canAnalyzeTrends.value) {
    return `Disponible après ${MIN_TREND_ANALYSIS_DAYS} jours de données synchronisées`
  }
  return "Interprétation IA de l'évolution sur 30 jours"
})
const trendDaysRemaining = computed(() =>
  Math.max(0, MIN_TREND_ANALYSIS_DAYS - distinctMetricDays.value)
)
const trendAnalysisProgress = computed(() =>
  Math.min(100, Math.round((distinctMetricDays.value / MIN_TREND_ANALYSIS_DAYS) * 100))
)

const latestMetric  = computed(() => userMetrics.value.at(-1))
const oldestMetric  = computed(() => userMetrics.value.at(0))

const weightDelta = computed(() => {
  if (!latestMetric.value || !oldestMetric.value) return ''
  const d = (latestMetric.value.weight_kg - oldestMetric.value.weight_kg).toFixed(1)
  return d > 0 ? `+${d} kg ce mois` : d < 0 ? `${d} kg ce mois` : 'Stable ce mois'
})
const avgSleep = computed(() => {
  const v = userMetrics.value.filter(m => m.sleep_hours)

  if (!v.length) return '—'

  const avg = v.reduce((s, m) => s + m.sleep_hours, 0) / v.length
  const totalMinutes = Math.round(avg * 60)

  const hours = Math.floor(totalMinutes / 60)
  const minutes = totalMinutes % 60

  return `${hours}h${minutes.toString().padStart(2, '0')}`
})
const avgBpm = computed(() => {
  const v = userMetrics.value.filter(m => m.resting_bpm)
  return v.length ? Math.round(v.reduce((s, m) => s + m.resting_bpm, 0) / v.length) : '—'
})

const xCategories = computed(() =>
  userMetrics.value.map(m => { const d = new Date(m.record_date); return `${d.getDate()}/${d.getMonth() + 1}` })
)

const chartBase = {
  chart: { background: 'transparent', toolbar: { show: false }, fontFamily: 'Inter, sans-serif' },
  grid:  { borderColor: '#e2e8f0', strokeDashArray: 4 },
  tooltip: { theme: 'light' },
  xaxis: { labels: { style: { colors: '#94a3b8', fontSize: '11px' } }, axisBorder: { show: false }, axisTicks: { show: false } },
  yaxis: { labels: { style: { colors: '#94a3b8', fontSize: '11px' } } },
}

const weightChartOptions = computed(() => ({
  ...chartBase,
  colors: ['#00B4D8'],
  fill:   { type: 'gradient', gradient: { shadeIntensity: 1, opacityFrom: 0.25, opacityTo: 0, stops: [0, 100] } },
  stroke: { curve: 'smooth', width: 2.5 },
  xaxis:  { ...chartBase.xaxis, categories: xCategories.value },
  dataLabels: { enabled: false },
  markers: { size: 0 },
}))
const weightSeries = computed(() => [{ name: 'Poids (kg)', data: userMetrics.value.map(m => m.weight_kg ?? null) }])

const sleepBpmChartOptions = computed(() => ({
  ...chartBase,
  colors: ['#7C3AED', '#DC2626'],
  stroke: { curve: 'smooth', width: 2.5 },
  xaxis:  { ...chartBase.xaxis, categories: xCategories.value },
  dataLabels: { enabled: false },
  legend: { labels: { colors: '#64748b' } },
  markers: { size: 0 },
  yaxis: [
    { labels: { style: { colors: '#94a3b8', fontSize: '11px' } }, title: { text: 'Sommeil (h)', style: { color: '#7C3AED' } } },
    { opposite: true, labels: { style: { colors: '#94a3b8', fontSize: '11px' } }, title: { text: 'BPM', style: { color: '#DC2626' } } },
  ],
}))
const sleepBpmSeries = computed(() => [
  { name: 'Sommeil (h)', data: userMetrics.value.map(m => m.sleep_hours ?? null) },
  { name: 'BPM repos',   data: userMetrics.value.map(m => m.resting_bpm ?? null) },
])

async function loadUserProfile() {
  if (!activeUserId.value) return
  try {
    const res = await usersAPI.getById(activeUserId.value)
    currentUser.value = res.data
    userStore.selectUser(activeUserId.value)
  } catch {
    currentUser.value = null
  }
}

async function loadMetrics() {
  if (!activeUserId.value) return
  metricsLoading.value = true; metricsError.value = ''
  try {
    await loadUserProfile()
    const res = await metricsAPI.getByUser(activeUserId.value)
    allMetrics.value = res.data
  } catch { metricsError.value = 'Impossible de charger les métriques biométriques.' }
  finally { metricsLoading.value = false }
}

async function fetchTrendAnalysis() {
  if (!activeUserId.value || !canRunTrendAi.value) return
  trendLoading.value = true; trendError.value = ''; trendAnalysis.value = ''
  try {
    const res = await coachAPI.getBiometricTrend(activeUserId.value)
    trendAnalysis.value = res.data.analysis
  } catch {
    trendError.value = "Erreur lors de l'analyse. Vérifiez la connexion à l'API."
  } finally {
    trendLoading.value = false
  }
}

function resetTrendState() {
  trendAnalysis.value = ''
  trendError.value = ''
}

function parseUserIdFromRoute() {
  const parsed = Number(route.params.userId)
  return Number.isInteger(parsed) && parsed > 0 ? parsed : null
}

function goToUsersList() {
  router.push(isAdminScope.value ? '/admin' : '/')
}

watch(canRunTrendAi, (ok) => {
  if (!ok) resetTrendState()
})

watch(
  () => route.params.userId,
  () => {
    activeUserId.value = parseUserIdFromRoute()
    if (!activeUserId.value) {
      goToUsersList()
      return
    }
    userStore.selectUser(activeUserId.value)
    resetTrendState()
    loadMetrics()
  },
  { immediate: true }
)
</script>
