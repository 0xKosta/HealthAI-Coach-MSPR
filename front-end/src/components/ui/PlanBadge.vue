<template>
  <span
    v-if="label"
    class="plan-badge"
    :class="badgeClass"
    :title="title"
  >
    <span v-if="showStar" class="plan-badge__star" aria-hidden="true">★</span>
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
  'plan-badge--gold': isGold.value,
  'plan-badge--free': !isGold.value && props.plan === 'free',
  'plan-badge--md': props.size === 'md',
}))

const showStar = computed(() =>
  props.plan === 'premium' || props.plan === 'premium_plus' || props.role === 'demo'
)

const title = computed(() => {
  if (props.role === 'admin') return 'Compte administrateur'
  if (props.role === 'demo') return 'Compte démonstration'
  if (props.plan === 'premium') return 'Offre Premium - 9,99 €/mois'
  if (props.plan === 'premium_plus') return 'Offre Premium+ - 19,99 €/mois'
  return 'Offre gratuite - fonctionnalités de base'
})
</script>

<style scoped>
.plan-badge {
  @apply inline-flex items-center gap-0.5 px-2 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider leading-none;
}

.plan-badge--md {
  @apply px-2.5 py-1 text-xs;
}

.plan-badge--free {
  @apply bg-white/10 text-slate-300 border border-white/20;
}

.plan-badge--gold {
  color: #3d2e0a;
  background: linear-gradient(135deg, #fff8e1 0%, #f0d78c 35%, #d4af37 70%, #b8860b 100%);
  border: 1px solid rgba(212, 175, 55, 0.65);
  box-shadow:
    0 1px 2px rgba(184, 134, 11, 0.35),
    inset 0 1px 0 rgba(255, 255, 255, 0.45);
}

.plan-badge__star {
  font-size: 0.65em;
  line-height: 1;
  opacity: 0.9;
}
</style>
