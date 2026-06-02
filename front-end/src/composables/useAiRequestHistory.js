import { ref, watch } from 'vue'
import { aiRequestsAPI } from '@/services/api'

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

export function useAiRequestHistory(userIdRef, requestTypeRef) {
  const items = ref([])
  const loading = ref(false)
  const error = ref('')
  const total = ref(0)

  async function load() {
    const userId = userIdRef.value
    const requestType = requestTypeRef.value
    if (!userId) {
      items.value = []
      total.value = 0
      return
    }
    loading.value = true
    error.value = ''
    try {
      const params = { skip: 0, limit: 100 }
      if (requestType) params.request_type = requestType
      const res = await aiRequestsAPI.listByUser(userId, params)
      items.value = res.data || []
      total.value = Number(res.headers['x-total-count'] ?? items.value.length)
    } catch {
      error.value = "Impossible de charger l'historique IA."
      items.value = []
      total.value = 0
    } finally {
      loading.value = false
    }
  }

  watch([userIdRef, requestTypeRef], load, { immediate: true })

  return { items, loading, error, total, reload: load }
}
