<template>
  <span
    v-if="label"
    class="plan-badge-light"
    :class="badgeClass"
    :title="title"
  >
    <span v-if="showStar" class="plan-badge-light__star" aria-hidden="true">★</span>
    {{ label }}
  </span>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  plan: { type: String, default: 'free' },
  role: { type: String, default: 'user' },
  size: { type: String, default: 'sm' }, // sm | md
})

const PLAN_LABELS = {
  free: 'Gratuit',
  premium: 'Premium',
  premium_plus: 'Premium+',
}

const label = computed(() => {
  if (props.role === 'admin') return 'Admin'
  if (props.role === 'demo') return 'Démo'
  return PLAN_LABELS[props.plan] || props.plan
})

const isGold = computed(() =>
  props.role === 'admin' ||
  props.role === 'demo' ||
  props.plan === 'premium' ||
  props.plan === 'premium_plus'
)

const badgeClass = computed(() => ({
  'plan-badge-light--gold': isGold.value,
  'plan-badge-light--free': !isGold.value,
  'plan-badge-light--md': props.size === 'md',
}))

const showStar = computed(() =>
  props.plan === 'premium' || props.plan === 'premium_plus' || props.role === 'demo'
)

const title = computed(() => {
  if (props.role === 'admin') return 'Compte administrateur'
  if (props.role === 'demo') return 'Compte démonstration'
  if (props.plan === 'premium') return 'Offre Premium'
  if (props.plan === 'premium_plus') return 'Offre Premium+'
  return 'Offre gratuite'
})
</script>

<style scoped>
.plan-badge-light {
  @apply inline-flex items-center gap-0.5 px-2.5 py-0.5 rounded-full text-[11px] font-bold uppercase tracking-wide leading-none;
}

.plan-badge-light--md {
  @apply px-3 py-1 text-xs tracking-wider;
}

.plan-badge-light--free {
  @apply bg-slate-100 text-slate-600 border border-slate-200;
}

.plan-badge-light--gold {
  color: #5c4510;
  background: linear-gradient(135deg, #fffbeb 0%, #fde68a 40%, #f59e0b 100%);
  border: 1px solid #d4af37;
  box-shadow: 0 1px 2px rgba(180, 134, 11, 0.2);
}

.plan-badge-light__star {
  font-size: 0.7em;
  color: #b8860b;
}
</style>
