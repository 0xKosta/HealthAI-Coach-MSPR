<template>
  <div class="card border border-dashed border-slate-200 bg-slate-50/50">
    <div class="flex flex-col sm:flex-row sm:items-center gap-5">
      <div class="w-12 h-12 rounded-xl bg-white border border-slate-200 flex items-center justify-center shrink-0">
        <span class="material-symbols-outlined text-[24px] text-slate-500">lock</span>
      </div>
      <div class="flex-1 min-w-0">
        <h2 class="text-lg font-bold text-brand-primary">{{ title }}</h2>
        <p class="text-sm text-slate-600 mt-1">{{ description }}</p>
        <ul
          v-if="issues.length"
          class="mt-3 text-sm text-amber-900/95 space-y-1 list-disc list-inside"
        >
          <li v-for="(issue, index) in issues" :key="index">{{ issue }}</li>
        </ul>
      </div>
      <RouterLink
        v-if="profileEditPath"
        :to="profileEditPath"
        class="btn-primary shrink-0 justify-center"
      >
        {{ ctaLabel }}
      </RouterLink>
    </div>
  </div>
</template>

<script setup>
defineProps({
  title: { type: String, required: true },
  description: { type: String, required: true },
  profileEditPath: { type: String, default: '' },
  ctaLabel: { type: String, default: 'Compléter mon profil' },
  issues: { type: Array, default: () => [] },
})
</script>
