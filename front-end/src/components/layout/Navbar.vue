<template>
  <!-- Navbar principale — fond #08104D (bleu nuit, zones structurantes) -->
  <nav class="fixed top-0 inset-x-0 z-50 bg-brand-primary border-b border-brand-secondary/50 shadow-md">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
      <div class="flex items-center justify-between h-16">

        <!-- Logo -->
        <RouterLink to="/" class="flex items-center gap-2.5 group">
          <!-- Icône bouclier -->
          <svg viewBox="0 0 48 48" class="h-9 w-9 shrink-0" fill="none" xmlns="http://www.w3.org/2000/svg">
            <!-- Bouclier -->
            <path d="M24 4L6 11V24C6 34 14 42 24 45C34 42 42 34 42 24V11L24 4Z"
                  fill="#123C69" stroke="#00B4D8" stroke-width="1.5"/>
            <!-- Croix médicale -->
            <rect x="20" y="14" width="8" height="20" rx="2" fill="white"/>
            <rect x="14" y="20" width="20" height="8" rx="2" fill="white"/>
            <!-- Circuits IA (cyan) -->
            <circle cx="36" cy="20" r="2" fill="#00B4D8"/>
            <circle cx="36" cy="28" r="2" fill="#00B4D8"/>
            <circle cx="41" cy="24" r="1.5" fill="#00B4D8"/>
            <line x1="36" y1="20" x2="36" y2="28" stroke="#00B4D8" stroke-width="1.2"/>
            <line x1="36" y1="24" x2="41" y2="24" stroke="#00B4D8" stroke-width="1.2"/>
            <line x1="36" y1="20" x2="39" y2="17" stroke="#00B4D8" stroke-width="1.2"/>
            <circle cx="39" cy="17" r="1.5" fill="#00B4D8"/>
          </svg>
          <!-- Texte logo — masqué sur mobile -->
          <span class="hidden sm:flex flex-col leading-tight">
            <span class="text-white font-bold text-lg tracking-tight">HealthAI <span class="text-brand-accent">Coach</span></span>
            <span class="text-slate-400 text-[10px] font-normal tracking-wide">Santé connectée · IA</span>
          </span>
        </RouterLink>

        <!-- Liens desktop -->
        <div class="hidden sm:flex items-center gap-1">
          <RouterLink
            v-for="link in navLinks"
            :key="link.to"
            :to="link.to"
            class="flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-medium transition-all duration-200"
            :class="isActive(link.to)
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
        <div class="flex items-center gap-2 text-xs text-slate-400">
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
        :class="isActive(link.to) ? 'text-brand-accent' : 'text-slate-400'"
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
import { useRoute } from 'vue-router'

const route = useRoute()

const navLinks = [
  {
    to: '/', label: 'Dashboard', shortLabel: 'Home',
    icon: '<path d="M3 9l9-7 9 7v11a2 2 0 01-2 2H5a2 2 0 01-2-2z"/><polyline points="9 22 9 12 15 12 15 22"/>'
  },
  {
    to: '/nutrition', label: 'Nutrition', shortLabel: 'Nutrition',
    icon: '<path d="M18 8h1a4 4 0 010 8h-1"/><path d="M2 8h16v9a4 4 0 01-4 4H6a4 4 0 01-4-4V8z"/><line x1="6" y1="1" x2="6" y2="4"/><line x1="10" y1="1" x2="10" y2="4"/><line x1="14" y1="1" x2="14" y2="4"/>'
  },
  {
    to: '/workout', label: 'Entraînement', shortLabel: 'Workout',
    icon: '<path d="M6 4v16M18 4v16M10 8H6M10 16H6M18 8h-4M18 16h-4"/>'
  },
  {
    to: '/trends', label: 'Tendances', shortLabel: 'Trends',
    icon: '<polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/>'
  },
]

function isActive(to) {
  return to === '/' ? route.path === '/' : route.path.startsWith(to)
}
</script>
