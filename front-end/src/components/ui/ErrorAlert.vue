<template>
  <div class="flex items-start gap-3 p-4 bg-red-50 border border-brand-error/30 rounded-xl animate-fade-in">
    <svg class="w-5 h-5 text-brand-error mt-0.5 shrink-0" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round">
      <circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/>
    </svg>
    <div>
      <p class="text-sm font-semibold text-brand-error">Erreur</p>
      <p class="text-sm text-red-700 mt-0.5">{{ message }}</p>
    </div>
  </div>
</template>

<script setup>
defineProps({ message: { type: String, required: true } })
</script>
