// Détermine la route cible après une authentification réussie.
// - admin            → back-office /admin
// - profil santé lié → dashboard utilisateur /dashboard/:userId
// - sinon            → page expliquant l'absence de profil santé
export function resolvePostAuthRoute(auth) {
  if (auth.isAdmin) return '/admin'
  if (auth.profileId) return `/dashboard/${auth.profileId}`
  return '/no-profile'
}
