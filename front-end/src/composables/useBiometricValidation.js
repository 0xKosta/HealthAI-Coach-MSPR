/** Règles biométriques alignées sur api/biometrics.py */

export const BIOMETRIC_LIMITS = {
  age: { min: 18, max: 100 },
  height_cm: { min: 90, max: 230 },
  weight_kg: { min: 20, max: 300 },
  bmi: { min: 10, max: 80 },
}

export function computeBmi(weightKg, heightCm) {
  if (weightKg == null || heightCm == null) return null
  const h = heightCm / 100
  const value = weightKg / (h * h)
  return Number.isFinite(value) ? Math.round(value * 10) / 10 : null
}

/**
 * Valide le formulaire profil.
 * @returns {{ formError: string, fieldErrors: Record<string, string> }}
 */
export function validateBiometricForm({ age, weight_kg, height_cm }) {
  const fieldErrors = {}
  const { age: aLim, height_cm: hLim, weight_kg: wLim, bmi: bLim } = BIOMETRIC_LIMITS

  if (age != null && !Number.isNaN(age)) {
    if (age < aLim.min || age > aLim.max) {
      fieldErrors.age = `L'âge doit être compris entre ${aLim.min} et ${aLim.max} ans.`
    }
  }

  if (weight_kg != null && !Number.isNaN(weight_kg)) {
    if (weight_kg < wLim.min || weight_kg > wLim.max) {
      fieldErrors.weight_kg = `Le poids doit être compris entre ${wLim.min} et ${wLim.max} kg.`
    }
  }

  if (height_cm != null && !Number.isNaN(height_cm)) {
    if (height_cm < hLim.min || height_cm > hLim.max) {
      fieldErrors.height_cm = `La taille doit être comprise entre ${hLim.min} et ${hLim.max} cm.`
    }
  }

  if (
    weight_kg != null &&
    height_cm != null &&
    !fieldErrors.weight_kg &&
    !fieldErrors.height_cm
  ) {
    const bmi = computeBmi(weight_kg, height_cm)
    if (bmi != null && (bmi < bLim.min || bmi > bLim.max)) {
      fieldErrors.bmi = `L'IMC calculé (${bmi}) doit être compris entre ${bLim.min} et ${bLim.max}.`
    }
  }

  const firstFieldError = Object.values(fieldErrors)[0] || ''
  return { formError: firstFieldError, fieldErrors }
}

export function parseApiErrorDetail(detail) {
  if (typeof detail === 'string') return detail
  if (Array.isArray(detail)) {
    return detail
      .map((e) => (typeof e === 'string' ? e : e.msg || JSON.stringify(e)))
      .join(' ')
  }
  return null
}
