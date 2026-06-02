import { createRouter, createWebHistory } from 'vue-router'
import DashboardView from '@/views/DashboardView.vue'
import NutritionView from '@/views/NutritionView.vue'
import WorkoutView from '@/views/WorkoutView.vue'
import ExercisesView from '@/views/ExercisesView.vue'
import TrendsView from '@/views/TrendsView.vue'
import TrendsUsersView from '@/views/TrendsUsersView.vue'
import LoginView from '@/views/LoginView.vue'
import RegisterView from '@/views/RegisterView.vue'
import NoProfileView from '@/views/NoProfileView.vue'
import ProfileEditView from '@/views/ProfileEditView.vue'
import { useAuthStore } from '@/stores/authStore'
import { resolvePostAuthRoute } from '@/router/redirect'
import { updateTransition } from '@/router/transition'

const routes = [
  // — Auth (accessible uniquement aux visiteurs non connectés) —
  { path: '/login',    name: 'Login',    component: LoginView,    meta: { guestOnly: true, public: true } },
  { path: '/register', name: 'Register', component: RegisterView, meta: { guestOnly: true, public: true } },

  // — Espace utilisateur (connecté) —
  { path: '/dashboard/:userId',           name: 'Dashboard',     component: DashboardView, meta: { requiresAuth: true } },
  { path: '/dashboard/:userId/nutrition', name: 'Nutrition',     component: NutritionView, meta: { requiresAuth: true } },
  { path: '/dashboard/:userId/workout',   name: 'Workout',       component: WorkoutView,   meta: { requiresAuth: true } },
  { path: '/dashboard/:userId/trends',    name: 'Trends',        component: TrendsView,    meta: { requiresAuth: true } },
  { path: '/dashboard/:userId/profile',   name: 'Profile',       component: ProfileEditView, meta: { requiresAuth: true } },
  { path: '/exercises',                   name: 'Exercises',     component: ExercisesView, meta: { requiresAuth: true } },
  { path: '/no-profile',                  name: 'NoProfile',     component: NoProfileView, meta: { requiresAuth: true } },

  // — Back-office admin (connecté + rôle admin) —
  { path: '/admin',                             name: 'AdminUsers',      component: TrendsUsersView, meta: { requiresAuth: true, requiresAdmin: true } },
  { path: '/admin/dashboard/:userId',           name: 'AdminDashboard',  component: DashboardView,   meta: { requiresAuth: true, requiresAdmin: true } },
  { path: '/admin/dashboard/:userId/trends',    name: 'AdminTrends',     component: TrendsView,      meta: { requiresAuth: true, requiresAdmin: true } },
  { path: '/admin/dashboard/:userId/nutrition', name: 'AdminNutrition',  component: NutritionView,   meta: { requiresAuth: true, requiresAdmin: true } },
  { path: '/admin/dashboard/:userId/workout',   name: 'AdminWorkout',    component: WorkoutView,     meta: { requiresAuth: true, requiresAdmin: true } },
  { path: '/admin/dashboard/:userId/profile',  name: 'AdminProfile',    component: ProfileEditView, meta: { requiresAuth: true, requiresAdmin: true } },

  // — Racine : redirige selon l'état d'authentification (géré dans le guard) —
  { path: '/', name: 'Root', redirect: () => '/login' },

  // — Fallback —
  { path: '/:pathMatch(.*)*', redirect: '/' },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
  scrollBehavior: () => ({ top: 0 }),
})

router.beforeEach(async (to) => {
  const auth = useAuthStore()

  // Réhydratation au rechargement : token présent mais profil non chargé
  if (auth.isAuthenticated && !auth.currentUser) {
    await auth.fetchMe()
  }

  // Racine → redirection contextuelle
  if (to.name === 'Root') {
    return auth.isAuthenticated ? resolvePostAuthRoute(auth) : '/login'
  }

  // Pages visiteurs (login/register) : rediriger si déjà connecté
  if (to.meta.guestOnly && auth.isAuthenticated) {
    return resolvePostAuthRoute(auth)
  }

  // Routes protégées
  if (to.meta.requiresAuth && !auth.isAuthenticated) {
    return { path: '/login', query: { redirect: to.fullPath } }
  }

  // Routes admin
  if (to.meta.requiresAdmin && !auth.isAdmin) {
    return resolvePostAuthRoute(auth)
  }

  // Espace utilisateur : on ne peut consulter que SON propre profil
  // (l'admin garde l'accès à tous les profils via /admin/...)
  if (
    to.path.startsWith('/dashboard/') &&
    !auth.isAdmin &&
    to.params.userId !== undefined
  ) {
    if (!auth.profileId) return '/no-profile'
    if (Number(to.params.userId) !== auth.profileId) {
      return `/dashboard/${auth.profileId}`
    }
  }

  return true
})

// Détermine le sens de l'animation (horizontal) selon l'ordre des vues partagées.
router.afterEach((to, from) => {
  updateTransition(to, from)
})

export default router
