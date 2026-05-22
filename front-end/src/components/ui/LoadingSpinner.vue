<template>
  <div class="flex flex-col items-center justify-center gap-3 py-12">
    <div class="relative w-12 h-12">
      <div class="absolute inset-0 rounded-full border-2 border-slate-200"></div>
      <div class="absolute inset-0 rounded-full border-2 border-t-brand-accent animate-spin"></div>
    </div>
    <p v-if="message" class="text-sm text-slate-600">{{ message }}</p>
  </div>
</template>

<script setup>
defineProps({ message: { type: String, default: '' } })
</script>
