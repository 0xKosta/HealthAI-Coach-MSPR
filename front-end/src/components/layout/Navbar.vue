<template>
  <!-- Navbar principale - fond #08104D (bleu nuit, zones structurantes) -->
  <nav class="fixed top-0 inset-x-0 z-50 bg-brand-primary border-b border-brand-secondary/50 shadow-md">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
      <div class="relative flex items-center h-20 sm:h-16 w-full">

        <!-- Logo - aligné à gauche -->
        <RouterLink
          :to="homeLink"
          class="flex items-center"
        >
          <img
            src="/healthai-coach-logo-light-navbar-text-subtitle-big.svg"
            alt="HealthAI Coach"
            class="h-[4.75rem] sm:h-16 max-w-[calc(100vw-4rem)] sm:max-w-none object-contain"
          />
        </RouterLink>

        <!-- Liens desktop -->
        <div class="hidden sm:flex flex-1 items-center justify-center gap-2">
          <RouterLink
            v-for="link in navLinks"
            :key="link.to"
            :to="link.to"
            class="flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all duration-200"
            :class="isActive(link)
              ? 'bg-brand-accent text-white'
              : 'text-slate-300 hover:text-white hover:bg-white/10'"
          >
            <svg class="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor"
                 stroke-width="2" stroke-linecap="round" stroke-linejoin="round"
                 v-html="link.icon" />
            {{ link.label }}
          </RouterLink>
        </div>

        <!-- Compte + déconnexion -->
        <div class="ml-auto flex items-center gap-3 relative z-10">
          <span
            v-if="auth.currentUser"
            class="hidden md:flex items-center gap-2 text-xs text-slate-300"
          >
            <span>{{ auth.currentUser.first_name }}</span>
            <PlanBadge
              :plan="auth.plan"
              :role="auth.currentUser.role"
            />
          </span>
          <RouterLink
            v-if="!auth.isAdmin && auth.profileId"
            :to="`/dashboard/${auth.profileId}/profile`"
            class="flex items-center justify-center w-9 h-9 rounded-lg text-slate-300 hover:text-white hover:bg-white/10 transition-colors"
            title="Mon profil"
            aria-label="Modifier mon profil"
          >
            <span class="material-symbols-outlined text-[20px] leading-none">settings</span>
          </RouterLink>
          <button
            class="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium text-slate-300 hover:text-white hover:bg-white/10 transition-colors"
            @click="logout"
          >
            <svg class="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4" /><polyline points="16 17 21 12 16 7" /><line x1="21" y1="12" x2="9" y2="12" />
            </svg>
            <span class="hidden sm:inline">Déconnexion</span>
          </button>
        </div>
      </div>
    </div>
  </nav>

  <!-- Bottom nav mobile -->
  <nav class="sm:hidden fixed bottom-0 inset-x-0 z-50 bg-brand-primary border-t border-brand-secondary/50 px-2 py-1">
    <div class="flex justify-around">
      <RouterLink
        v-for="link in navLinks"
        :key="link.to"
        :to="link.to"
        class="flex flex-col items-center gap-0.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-all"
        :class="isActive(link) ? 'text-brand-accent' : 'text-slate-400'"
      >
        <svg class="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor"
             stroke-width="2" stroke-linecap="round" stroke-linejoin="round"
             v-html="link.icon" />
        {{ link.shortLabel }}
      </RouterLink>
    </div>
  </nav>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/authStore'
import PlanBadge from '@/components/ui/PlanBadge.vue'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()

const dashboardIcon = '<path d="M3 9l9-7 9 7v11a2 2 0 01-2 2H5a2 2 0 01-2-2z"/><polyline points="9 22 9 12 15 12 15 22"/>'
const exercisesIcon = '<circle cx="12" cy="12" r="10"/><path d="M8 12h8M12 8v8"/>'

const homeLink = computed(() => {
  if (auth.isAdmin) return '/admin'
  if (auth.profileId) return `/dashboard/${auth.profileId}`
  return '/'
})

const navLinks = computed(() => {
  if (auth.isAdmin) {
    return [
      { to: '/admin', label: 'Utilisateurs', shortLabel: 'Users', icon: dashboardIcon },
      { to: '/exercises', label: 'Exercices', shortLabel: 'Exercices', icon: exercisesIcon },
    ]
  }
  const links = []
  if (auth.profileId) {
    links.push({ to: `/dashboard/${auth.profileId}`, label: 'Mon espace', shortLabel: 'Accueil', icon: dashboardIcon })
  }
  links.push({ to: '/exercises', label: 'Exercices', shortLabel: 'Exercices', icon: exercisesIcon })
  return links
})

function isActive(link) {
  if (link.to === '/admin') {
    return (
      route.path === '/admin' ||
      route.path.startsWith('/admin/dashboard/') ||
      route.path.startsWith('/admin/users/')
    )
  }
  if (link.to.startsWith('/dashboard/')) {
    return route.path.startsWith('/dashboard/')
  }
  return route.path.startsWith(link.to)
}

function logout() {
  auth.logout()
  router.push('/login')
}
</script>
