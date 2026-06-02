/** Profil santé minimum requis pour les fonctionnalités IA personnalisées. */
export function isProfileIncomplete(user) {
  if (!user) return false
  return user.age == null || user.weight_kg == null || user.height_cm == null || !user.goal
}

export function getProfileEditPath(userId) {
  return userId ? `/dashboard/${userId}/profile` : '/'
}

export const PROFILE_AI_REQUIRED_MSG =
  'Renseignez âge, poids, taille et objectif pour activer les fonctionnalités IA.'
