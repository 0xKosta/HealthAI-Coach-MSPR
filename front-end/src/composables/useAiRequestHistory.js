import { ref, watch } from 'vue'
import { aiRequestsAPI } from '@/services/api'

/** Quotas affichés si les en-têtes HTTP ne sont pas lisibles (ex. CORS). */
export const PLAN_HISTORY_QUOTA = {
  premium: { windowDays: 7, limitMax: 20 },
  premium_plus: { windowDays: 30, limitMax: 50 },
}

export const REQUEST_TYPE_LABELS = {
  advice: 'Conseil',
  analyze_photo: 'Photo repas',
  workout_plan: 'Programme',
  biometric_trend: 'Tendances',
  meal_plan: 'Plan repas',
}

export function formatAiRequestDate(iso) {
  if (!iso) return '—'
  try {
    return new Intl.DateTimeFormat('fr-FR', {
      dateStyle: 'short',
      timeStyle: 'short',
    }).format(new Date(iso))
  } catch {
    return iso
  }
}

export function resolveResponseText(row) {
  const out = row?.output_json
  if (!out) return row?.output_summary || ''
  if (row.request_type === 'advice') return out.advice || ''
  if (row.request_type === 'analyze_photo') return out.advice || ''
  if (row.request_type === 'workout_plan' || row.request_type === 'meal_plan') return out.plan || ''
  if (row.request_type === 'biometric_trend') return out.analysis || ''
  return row.output_summary || ''
}

export function formatHistoryWindowLabel(sinceIso, windowDays) {
  if (!sinceIso || !windowDays) return ''
  try {
    const since = new Date(sinceIso)
    const sinceLabel = new Intl.DateTimeFormat('fr-FR', { dateStyle: 'medium' }).format(since)
    return `Fenêtre glissante : ${windowDays} jour${windowDays > 1 ? 's' : ''} (depuis le ${sinceLabel})`
  } catch {
    return `Derniers ${windowDays} jours`
  }
}

function readHeader(headers, name) {
  const v = headers?.[name]
  if (v === undefined || v === null || v === '') return null
  const n = Number(v)
  return Number.isFinite(n) ? n : null
}

export function useAiRequestHistory(userIdRef, requestTypeRef, options = {}) {
  const { enabledRef = null, planRef = null, variantRef = null } = options
  const items = ref([])
  const loading = ref(false)
  const error = ref('')
  const total = ref(0)
  const countInWindow = ref(0)
  const limitMax = ref(0)
  const windowDays = ref(0)
  const windowSince = ref(null)
  const unlimited = ref(false)

  async function load() {
    if (enabledRef?.value === false) {
      items.value = []
      return
    }
    const userId = userIdRef.value
    const requestType = requestTypeRef.value
    if (!userId) {
      items.value = []
      total.value = 0
      countInWindow.value = 0
      return
    }
    loading.value = true
    error.value = ''
    try {
      const params = { skip: 0, limit: 100 }
      if (requestType) params.request_type = requestType
      const res = await aiRequestsAPI.listByUser(userId, params)
      items.value = res.data || []
      total.value = items.value.length
      let days = readHeader(res.headers, 'x-history-days')
      let limit = readHeader(res.headers, 'x-history-limit')
      let count = readHeader(res.headers, 'x-history-count')

      const plan = planRef?.value
      const isUser = variantRef?.value === 'user'
      if (isUser && plan && PLAN_HISTORY_QUOTA[plan]) {
        if (days == null || days === 0) days = PLAN_HISTORY_QUOTA[plan].windowDays
        if (limit == null || limit === 0) limit = PLAN_HISTORY_QUOTA[plan].limitMax
      }

      windowDays.value = days ?? 0
      limitMax.value = limit ?? 0
      countInWindow.value = count ?? items.value.length
      windowSince.value = res.headers?.['x-history-since'] || null
      unlimited.value =
        variantRef?.value === 'admin' ||
        (windowDays.value === 0 && limitMax.value === 0 && !isUser)
    } catch (e) {
      if (e.response?.status === 403) {
        error.value = ''
        items.value = []
      } else {
        error.value = "Impossible de charger l'historique IA."
        items.value = []
      }
      total.value = 0
      countInWindow.value = 0
    } finally {
      loading.value = false
    }
  }

  watch(
    [userIdRef, requestTypeRef, enabledRef, planRef, variantRef].filter(Boolean),
    load,
    { immediate: true }
  )

  return {
    items,
    loading,
    error,
    total,
    countInWindow,
    limitMax,
    windowDays,
    windowSince,
    unlimited,
    reload: load,
  }
}
