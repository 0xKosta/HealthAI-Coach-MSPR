<template>
  <!-- Navbar principale — fond #08104D (bleu nuit, zones structurantes) -->
  <nav class="fixed top-0 inset-x-0 z-50 bg-brand-primary border-b border-brand-secondary/50 shadow-md">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
      <div class="relative flex items-center h-20 sm:h-16 w-full">

        <!-- Logo — centré mobile, à gauche desktop -->
        <RouterLink
          to="/admin"
          class="absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 sm:static sm:translate-x-0 sm:translate-y-0 flex items-center"
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

        <!-- Indicateur statut -->
        <div class="ml-auto flex items-center gap-2 text-xs text-slate-400 relative z-10">
          <span class="w-2 h-2 rounded-full bg-brand-success animate-pulse-slow"></span>
          <span class="hidden lg:block">API connectée</span>
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
import { useRoute } from 'vue-router'

const route = useRoute()

const navLinks = computed(() => [
  {
    to: '/admin', label: 'Utilisateurs', shortLabel: 'Users',
    icon: '<path d="M3 9l9-7 9 7v11a2 2 0 01-2 2H5a2 2 0 01-2-2z"/><polyline points="9 22 9 12 15 12 15 22"/>'
  },
  {
    to: '/exercises', label: 'Exercices', shortLabel: 'Exercices',
    icon: '<circle cx="12" cy="12" r="10"/><path d="M8 12h8M12 8v8"/>'
  },
])

function isActive(link) {
  if (link.to === '/admin') {
    return route.path === '/admin' || route.path.startsWith('/admin/dashboard/')
  }
  return route.path.startsWith(link.to)
}
</script>
