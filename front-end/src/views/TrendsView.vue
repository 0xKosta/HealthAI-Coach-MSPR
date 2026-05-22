<template>
  <div class="space-y-8 animate-fade-in">

    <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
      <div>
        <h1 class="text-3xl font-bold text-brand-primary">Tendances Biométriques</h1>
        <p class="text-slate-600 mt-1">Évolution de vos données de santé sur 30 jours</p>
      </div>
      <UserSelector v-if="userStore.users.length" v-model="userStore.selectedUserId" :users="userStore.users" />
    </div>

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
          :value="`${avgSleep} h`" sub="Durée quotidienne"
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
      <div class="card">
        <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6">
          <div>
            <h2 class="text-xl font-bold text-brand-primary">Analyse des tendances</h2>
            <p class="text-sm text-slate-600 mt-0.5">Interprétation IA de l'évolution sur 30 jours</p>
          </div>
          <button @click="fetchTrendAnalysis" :disabled="trendLoading" class="btn-primary">
            <div v-if="trendLoading" class="w-4 h-4 border-2 border-brand-primary border-t-transparent rounded-full animate-spin"></div>
            <svg v-else class="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round">
              <path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z"/><path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z"/>
            </svg>
            {{ trendLoading ? 'Analyse...' : 'Analyser les tendances' }}
          </button>
        </div>

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
      </div>
    </template>

    <!-- État vide -->
    <div v-if="!metricsLoading && !metricsError && !userMetrics.length"
         class="flex flex-col items-center justify-center py-16 text-center">
      <div class="w-20 h-20 rounded-2xl bg-brand-neutral border border-slate-200 flex items-center justify-center mb-5">
        <svg class="w-10 h-10 text-slate-300" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
          <polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/>
        </svg>
      </div>
      <p class="text-brand-secondary font-medium">Aucune donnée biométrique disponible</p>
      <p class="text-slate-600 text-sm mt-1">Sélectionnez un autre utilisateur ou importez des métriques</p>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { useUserStore } from '@/stores/userStore'
import { metricsAPI, coachAPI } from '@/services/api'
import UserSelector from '@/components/ui/UserSelector.vue'
import LoadingSpinner from '@/components/ui/LoadingSpinner.vue'
import ErrorAlert from '@/components/ui/ErrorAlert.vue'
import AIAdviceCard from '@/components/ui/AIAdviceCard.vue'
import StatCard from '@/components/ui/StatCard.vue'

const userStore = useUserStore()
const allMetrics = ref([])
const metricsLoading = ref(false)
const metricsError = ref('')
const trendAnalysis = ref('')
const trendLoading = ref(false)
const trendError = ref('')

const userMetrics = computed(() =>
  allMetrics.value
    .slice()
    .sort((a, b) => new Date(a.record_date) - new Date(b.record_date))
    .slice(-30)
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
  return v.length ? (v.reduce((s, m) => s + m.sleep_hours, 0) / v.length).toFixed(1) : '—'
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

async function loadMetrics() {
  if (!userStore.selectedUserId) return
  metricsLoading.value = true; metricsError.value = ''
  try { const res = await metricsAPI.getByUser(userStore.selectedUserId); allMetrics.value = res.data }
  catch { metricsError.value = 'Impossible de charger les métriques biométriques.' }
  finally { metricsLoading.value = false }
}

async function fetchTrendAnalysis() {
  if (!userStore.selectedUserId) return
  trendLoading.value = true; trendError.value = ''; trendAnalysis.value = ''
  try {
    const res = await coachAPI.getBiometricTrend(userStore.selectedUserId)
    trendAnalysis.value = res.data.analysis
  } catch {
    trendError.value = "Erreur lors de l'analyse. Vérifiez la connexion à l'API."
  } finally {
    trendLoading.value = false
  }
}

watch(() => userStore.selectedUserId, () => { trendAnalysis.value = ''; trendError.value = ''; loadMetrics() })
onMounted(() => loadMetrics())
</script>
