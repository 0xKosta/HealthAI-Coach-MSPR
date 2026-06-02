import { validateBiometricForm } from './useBiometricValidation'

/** Profil santé minimum requis pour les fonctionnalités IA personnalisées. */
export function isProfileIncomplete(user) {
  if (!user) return false
  return user.age == null || user.weight_kg == null || user.height_cm == null || !user.goal
}

export function getProfileEditPath(userId, { admin = false } = {}) {
  if (!userId) return admin ? '/admin' : '/'
  return admin
    ? `/admin/dashboard/${userId}/profile`
    : `/dashboard/${userId}/profile`
}

export const PROFILE_AI_REQUIRED_MSG =
  'Renseignez âge, poids, taille et objectif pour activer les fonctionnalités IA.'

export const PROFILE_INVALID_MSG =
  'Certaines données de votre profil sont incorrectes. Corrigez-les pour réactiver les analyses et conseils IA.'

/** Détecte les anomalies biométriques (API profile_issues ou validation locale). */
function collectClientProfileIssues(user) {
  if (!user) return []
  const { fieldErrors } = validateBiometricForm({
    age: user.age,
    weight_kg: user.weight_kg,
    height_cm: user.height_cm,
  })
  return Object.values(fieldErrors)
}

export function getProfileIssues(user) {
  if (!user) return []
  if (Array.isArray(user.profile_issues) && user.profile_issues.length > 0) {
    return [...user.profile_issues]
  }
  return collectClientProfileIssues(user)
}

/** Données biométriques présentes mais hors limites (legacy ou saisie directe en BDD). */
export function hasInvalidProfileData(user) {
  return getProfileIssues(user).length > 0
}

/** Profil incomplet ou données biométriques invalides — bloque coach / analyses IA. */
export function blocksAiFeatures(user) {
  if (!user) return true
  return isProfileIncomplete(user) || hasInvalidProfileData(user)
}

/** Affiche le tableau de bord d'accueil (complétion ou correction). */
export function showProfileWelcomeBoard(user) {
  if (!user) return false
  return isProfileIncomplete(user) || hasInvalidProfileData(user)
}

export function getProfileEditPathForUser(userId, isAdminScope = false) {
  if (isAdminScope && userId) return `/dashboard/${userId}/profile`
  return '/profile/edit'
}
