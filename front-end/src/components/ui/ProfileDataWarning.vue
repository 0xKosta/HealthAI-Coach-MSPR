<template>
  <div
    class="rounded-xl border border-amber-300 bg-amber-50 px-4 py-3 flex flex-col sm:flex-row sm:items-center gap-3"
    role="alert"
  >
    <div class="flex items-start gap-3 flex-1 min-w-0">
      <span class="material-symbols-outlined text-amber-600 shrink-0">warning</span>
      <div class="min-w-0">
        <p class="font-semibold text-amber-900">Données de profil à corriger</p>
        <ul v-if="issues.length" class="mt-1 text-sm text-amber-900/90 list-disc list-inside space-y-0.5">
          <li v-for="(issue, i) in issues" :key="i">{{ issue }}</li>
        </ul>
        <p v-else class="text-sm text-amber-900/90 mt-1">{{ message }}</p>
      </div>
    </div>
    <RouterLink
      v-if="editPath"
      :to="editPath"
      class="btn-primary shrink-0 text-sm py-2 px-4 self-start sm:self-center"
    >
      Corriger mon profil
    </RouterLink>
  </div>
</template>

<script setup>
defineProps({
  issues: { type: Array, default: () => [] },
  message: { type: String, default: '' },
  editPath: { type: String, default: '' },
})
</script>
