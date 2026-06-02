/** Jours de données distincts requis pour débloquer l'analyse IA des tendances. */
export const MIN_TREND_ANALYSIS_DAYS = 7

export function countDistinctMetricDays(metrics) {
  if (!metrics?.length) return 0
  const days = new Set(
    metrics.map((m) => {
      const d = new Date(m.record_date)
      return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
    })
  )
  return days.size
}

export function canUnlockTrendAnalysis(metrics) {
  return countDistinctMetricDays(metrics) >= MIN_TREND_ANALYSIS_DAYS
}
