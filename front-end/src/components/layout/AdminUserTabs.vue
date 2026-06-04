<template>
  <!-- Desktop : onglets cliquables -->
  <div class="hidden sm:inline-flex bg-white border border-slate-200 rounded-xl p-1 flex-wrap gap-1">
    <RouterLink
      v-for="tab in tabs"
      :key="tab.to"
      :to="tab.to"
      class="px-3 py-1.5 rounded-lg text-sm font-medium transition-colors"
      :class="isActive(tab) ? 'bg-brand-accent text-white' : 'text-slate-600 hover:bg-slate-100'"
    >
      {{ tab.label }}
    </RouterLink>
  </div>

  <!-- Mobile : points indicateurs centrés (glisser gauche/droite pour changer) -->
  <div class="sm:hidden flex items-center justify-center gap-2 py-1">
    <button
      v-for="(tab, i) in tabs"
      :key="tab.to"
      type="button"
      class="h-2 rounded-full transition-all"
      :class="i === activeIndex ? 'w-6 bg-brand-accent' : 'w-2 bg-slate-300'"
      :aria-label="`Aller à ${tab.label}`"
      @click="goTo(i)"
      @pointerdown.stop
    ></button>
  </div>
</template>

<script setup>
import { toRef } from 'vue'
import { useRoute } from 'vue-router'
import { useViewNav } from '@/composables/useViewNav'

const props = defineProps({
  userId: { type: Number, required: true },
})

const route = useRoute()
const { tabs, activeIndex, goTo } = useViewNav(toRef(props, 'userId'))

function isActive(tab) {
  if (tab.to.includes('/workout')) return route.path.includes('/workout')
  if (tab.to.includes('/nutrition')) return route.path.includes('/nutrition')
  if (tab.to.includes('/trends')) return route.path.includes('/trends')
  return /\/dashboard\/\d+(\/profile)?$/.test(route.path)
}
</script>
