<template>
  <!-- Fond #F4F7FB (fond neutre) — cartes/Dashboard/surfaces UI -->
  <div class="card-sm flex items-center gap-4">
    <div class="w-12 h-12 rounded-xl flex items-center justify-center shrink-0" :class="iconBg">
      <svg class="w-6 h-6" :class="iconColor" viewBox="0 0 24 24" fill="none"
           stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"
           v-html="icon" />
    </div>
    <div>
      <p class="text-xs font-medium text-slate-600">{{ label }}</p>
      <p class="text-xl font-bold text-brand-primary">{{ value }}</p>
      <p v-if="sub" class="text-xs text-slate-600">{{ sub }}</p>
    </div>
  </div>
</template>

<script setup>
defineProps({
  label:     String,
  value:     [String, Number],
  sub:       String,
  icon:      String,
  iconBg:    { type: String, default: 'bg-brand-accent/10' },
  iconColor: { type: String, default: 'text-brand-accent' },
})
</script>
