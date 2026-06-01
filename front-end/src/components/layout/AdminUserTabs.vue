<template>
  <div class="bg-white border border-slate-200 rounded-xl p-1 inline-flex flex-wrap gap-1">
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
</template>

<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'

const props = defineProps({
  userId: { type: Number, required: true },
})

const route = useRoute()

const tabs = computed(() => [
  { label: 'Dashboard', to: `/admin/dashboard/${props.userId}` },
  { label: 'Nutrition', to: `/admin/dashboard/${props.userId}/nutrition` },
  { label: 'Entraînement', to: `/admin/dashboard/${props.userId}/workout` },
  { label: 'Tendances', to: `/admin/dashboard/${props.userId}/trends` },
])

function isActive(tab) {
  if (tab.to.includes('/workout')) return route.path.includes('/workout')
  if (tab.to.includes('/nutrition')) return route.path.includes('/nutrition')
  if (tab.to.includes('/trends')) return route.path.includes('/trends')
  return /^\/admin\/dashboard\/\d+$/.test(route.path)
}
</script>
