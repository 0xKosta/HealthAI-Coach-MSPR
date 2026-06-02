<template>
  <div class="card">
    <div class="flex flex-col sm:flex-row sm:items-start justify-between gap-3 mb-4">
      <div>
        <p
          v-if="variant === 'admin'"
          class="text-xs font-semibold uppercase tracking-wide text-brand-accent"
        >
          Supervision admin
        </p>
        <h2 class="text-xl font-bold text-brand-primary" :class="variant === 'admin' ? 'mt-0.5' : ''">
          {{ title }}
        </h2>
        <p v-if="description && variant === 'admin'" class="text-sm text-slate-600 mt-1">
          {{ description }}
        </p>
      </div>
      <div v-if="!loading && !error" class="flex flex-col items-end gap-1 shrink-0 text-right">
        <div
          v-if="showQuota"
          class="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full border text-sm font-semibold tabular-nums"
          :class="quotaAtCap
            ? 'bg-amber-50 border-amber-200 text-amber-900'
            : 'bg-brand-accent/10 border-brand-accent/25 text-brand-primary'"
          :title="variant === 'user' ? quotaTitle : ''"
        >
          {{ countInWindow }}/{{ effectiveLimitMax }}
        </div>
        <p v-else-if="unlimited" class="text-sm text-slate-500">
          {{ countInWindow }} entrée{{ countInWindow > 1 ? 's' : '' }}
        </p>
      </div>
    </div>

    <p
      v-if="variant === 'admin' && windowLabel"
      class="text-xs text-slate-500 mb-4 -mt-2"
    >
      {{ windowLabel }}
    </p>

    <p
      v-else-if="variant === 'user' && quotaAtCap"
      class="text-xs text-amber-800 mb-4 -mt-2"
    >
      {{ quotaCapMessage }}
    </p>

    <LoadingSpinner v-if="loading" message="Chargement de l'historique..." />
    <ErrorAlert v-else-if="error" :message="error" />

    <div
      v-else-if="!items.length"
      class="flex flex-col items-center justify-center py-12 text-center rounded-xl bg-slate-50 border border-slate-100"
    >
      <span class="material-symbols-outlined text-[40px] text-slate-300 mb-3">history</span>
      <p class="text-sm font-medium text-brand-primary">
        {{ variant === 'admin' ? 'Aucune requête enregistrée' : 'Aucune analyse enregistrée' }}
      </p>
      <p class="text-xs text-slate-500 mt-1 max-w-sm">
        {{ variant === 'admin'
          ? 'Les appels IA de cet utilisateur apparaîtront ici après utilisation de la vue utilisateur.'
          : 'Rien pour le moment.' }}
      </p>
    </div>

    <ul v-else class="space-y-3">
      <li
        v-for="row in items"
        :key="row.id"
        class="rounded-xl border border-slate-200 bg-white overflow-hidden"
      >
        <button
          type="button"
          class="w-full flex items-start gap-3 p-4 text-left hover:bg-slate-50/80 transition-colors"
          :aria-expanded="expandedId === row.id"
          @click="toggle(row.id)"
        >
          <div class="w-10 h-10 rounded-lg bg-brand-accent/10 flex items-center justify-center shrink-0">
            <span class="material-symbols-outlined text-[22px] text-brand-accent leading-none">
              {{ iconForType(row.request_type) }}
            </span>
          </div>
          <div class="min-w-0 flex-1">
            <div class="flex flex-wrap items-center gap-2 mb-1">
              <span class="text-xs font-semibold text-brand-primary">
                {{ formatAiRequestDate(row.created_at) }}
              </span>
              <span
                v-if="variant === 'admin' && row.from_cache"
                class="text-[10px] uppercase tracking-wide px-2 py-0.5 rounded-full bg-slate-100 text-slate-600"
              >
                Cache
              </span>
              <span
                class="text-[10px] uppercase tracking-wide px-2 py-0.5 rounded-full"
                :class="row.status === 'success' ? 'bg-teal-50 text-teal-700' : 'bg-red-50 text-red-700'"
              >
                {{ row.status === 'success' ? 'OK' : row.status }}
              </span>
            </div>
            <p class="text-sm font-medium text-brand-primary truncate">
              {{ row.input_summary || '—' }}
            </p>
            <p class="text-xs text-slate-500 mt-0.5 line-clamp-2">
              {{ row.output_summary || '—' }}
            </p>
          </div>
          <svg
            class="w-5 h-5 text-slate-400 shrink-0 transition-transform"
            :class="expandedId === row.id ? 'rotate-180' : ''"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="2"
            stroke-linecap="round"
          >
            <polyline points="6 9 12 15 18 9" />
          </svg>
        </button>

        <div
          v-if="expandedId === row.id"
          class="px-4 pb-4 pt-0 border-t border-slate-100 space-y-4"
        >
          <div v-if="row.input_json && Object.keys(row.input_json).length" class="rounded-lg bg-slate-50 p-3">
            <p class="text-xs font-semibold text-slate-500 uppercase mb-2">Entrée</p>
            <dl class="grid grid-cols-1 sm:grid-cols-2 gap-x-4 gap-y-1 text-sm">
              <template v-for="(val, key) in row.input_json" :key="key">
                <dt class="text-slate-500">{{ inputLabel(key) }}</dt>
                <dd class="text-brand-primary font-medium">{{ formatInputValue(key, val) }}</dd>
              </template>
            </dl>
          </div>

          <div v-if="row.request_type === 'analyze_photo' && row.photo_url" class="rounded-lg overflow-hidden border border-slate-200">
            <p class="text-xs font-semibold text-slate-500 uppercase px-3 pt-3">Photo analysée</p>
            <img
              :src="photoSrc(row.photo_url)"
              alt="Photo repas analysée"
              class="w-full max-h-80 object-contain bg-slate-100 mt-2"
              loading="lazy"
            />
          </div>

          <div
            v-if="row.request_type === 'analyze_photo' && row.output_json?.foods_detected?.length"
            class="flex flex-wrap gap-2"
          >
            <span
              v-for="food in row.output_json.foods_detected"
              :key="food"
              class="inline-flex px-2.5 py-1 rounded-full text-xs font-medium bg-brand-accent/10 text-cyan-800 border border-brand-accent/20"
            >
              {{ food }}
            </span>
          </div>

          <div
            v-if="row.request_type === 'analyze_photo' && row.output_json?.macros"
            class="grid grid-cols-2 sm:grid-cols-4 gap-2"
          >
            <div class="rounded-lg bg-amber-50 p-2 text-center">
              <p class="text-lg font-bold text-amber-700">{{ row.output_json.macros.calories }}</p>
              <p class="text-[10px] text-slate-600">kcal</p>
            </div>
            <div class="rounded-lg bg-brand-accent/10 p-2 text-center">
              <p class="text-lg font-bold text-brand-primary">{{ row.output_json.macros.protein_g }}g</p>
              <p class="text-[10px] text-slate-600">Prot.</p>
            </div>
            <div class="rounded-lg bg-teal-50 p-2 text-center">
              <p class="text-lg font-bold text-teal-700">{{ row.output_json.macros.carbs_g }}g</p>
              <p class="text-[10px] text-slate-600">Gluc.</p>
            </div>
            <div class="rounded-lg bg-violet-50 p-2 text-center">
              <p class="text-lg font-bold text-violet-700">{{ row.output_json.macros.fat_g }}g</p>
              <p class="text-[10px] text-slate-600">Lip.</p>
            </div>
          </div>

          <div v-if="responseText(row)" class="rounded-lg border border-slate-200 p-4 bg-slate-50/50">
            <p class="text-xs font-semibold text-slate-500 uppercase mb-2">Réponse IA</p>
            <div class="text-sm text-slate-700 leading-relaxed whitespace-pre-wrap">{{ responseText(row) }}</div>
          </div>
        </div>
      </li>
    </ul>
  </div>
</template>

<script setup>
import { ref, toRef, computed } from 'vue'
import { API_BASE_URL } from '@/services/api'
import {
  formatAiRequestDate,
  formatHistoryWindowLabel,
  PLAN_HISTORY_QUOTA,
  resolveResponseText,
  useAiRequestHistory,
} from '@/composables/useAiRequestHistory'
import LoadingSpinner from '@/components/ui/LoadingSpinner.vue'
import ErrorAlert from '@/components/ui/ErrorAlert.vue'

const props = defineProps({
  userId: { type: Number, required: true },
  requestType: { type: String, default: '' },
  title: { type: String, required: true },
  description: { type: String, default: '' },
  variant: { type: String, default: 'admin' },
  plan: { type: String, default: 'free' },
  enabled: { type: Boolean, default: true },
})

const expandedId = ref(null)
const userIdRef = toRef(props, 'userId')
const requestTypeRef = toRef(props, 'requestType')
const enabledRef = toRef(props, 'enabled')
const planRef = toRef(props, 'plan')
const variantRef = toRef(props, 'variant')
const {
  items,
  loading,
  error,
  countInWindow,
  limitMax,
  windowDays,
  windowSince,
  unlimited,
  reload,
} = useAiRequestHistory(userIdRef, requestTypeRef, {
  enabledRef,
  planRef,
  variantRef,
})

defineExpose({ reload })

const planQuotaFallback = computed(() => PLAN_HISTORY_QUOTA[props.plan] || null)

const showQuota = computed(() => {
  if (props.variant !== 'user') return false
  if (limitMax.value > 0 && windowDays.value > 0) return true
  return !!planQuotaFallback.value
})
const effectiveLimitMax = computed(() =>
  limitMax.value > 0 ? limitMax.value : planQuotaFallback.value?.limitMax ?? 0
)
const effectiveWindowDays = computed(() =>
  windowDays.value > 0 ? windowDays.value : planQuotaFallback.value?.windowDays ?? 0
)
const quotaAtCap = computed(
  () => showQuota.value && effectiveLimitMax.value > 0
    && countInWindow.value >= effectiveLimitMax.value
)
const windowLabel = computed(() => {
  if (windowSince.value && effectiveWindowDays.value) {
    return formatHistoryWindowLabel(windowSince.value, effectiveWindowDays.value)
  }
  if (effectiveWindowDays.value) {
    return `Fenêtre glissante : ${effectiveWindowDays.value} jour${effectiveWindowDays.value > 1 ? 's' : ''}`
  }
  return ''
})

const quotaTitle = computed(() => {
  const max = effectiveLimitMax.value
  const days = effectiveWindowDays.value
  if (!max) return ''
  return `Jusqu'à ${max} analyses enregistrées sur les ${days} derniers jours`
})

const quotaCapMessage = computed(() => {
  if (props.plan === 'premium') {
    return 'Limite atteinte. Passez à Premium+ pour conserver plus d’historique (50 analyses / 30 jours).'
  }
  return 'Limite atteinte sur la période incluse dans votre offre.'
})

function toggle(id) {
  expandedId.value = expandedId.value === id ? null : id
}

function photoSrc(photoUrl) {
  if (!photoUrl) return ''
  if (photoUrl.startsWith('http')) return photoUrl
  return `${API_BASE_URL}${photoUrl.startsWith('/') ? '' : '/'}${photoUrl}`
}

function responseText(row) {
  return resolveResponseText(row)
}

function iconForType(type) {
  return {
    advice: 'tips_and_updates',
    analyze_photo: 'restaurant',
    workout_plan: 'fitness_center',
    biometric_trend: 'monitoring',
    meal_plan: 'restaurant_menu',
  }[type] || 'smart_toy'
}

const INPUT_LABELS = {
  source: 'Source',
  mime: 'Format',
  size_bytes: 'Taille',
  equipment: 'Équipement',
  days_per_week: 'Jours / semaine',
  period_days: 'Période (jours)',
  metrics_count: 'Points de mesure',
  budget_euros: 'Budget',
  allergies: 'Allergies',
}

const EQUIPMENT_FR = {
  none: 'Poids du corps',
  dumbbell: 'Haltères',
  barbell: 'Barre',
  machine: 'Machines',
  resistance: 'Élastiques',
  full: 'Salle complète',
}

function inputLabel(key) {
  return INPUT_LABELS[key] || key
}

function formatInputValue(key, val) {
  if (key === 'equipment') return EQUIPMENT_FR[val] || val
  if (key === 'size_bytes') return `${Math.round(val / 1024)} Ko`
  if (key === 'allergies' && Array.isArray(val)) return val.length ? val.join(', ') : 'Aucune'
  if (Array.isArray(val)) return val.join(', ')
  return String(val)
}
</script>
