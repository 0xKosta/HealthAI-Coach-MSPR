<template>
  <div class="flex items-center gap-3">
    <label class="label mb-0 whitespace-nowrap text-slate-600">Utilisateur :</label>
    <div class="relative">
      <select
        :value="modelValue"
        @change="$emit('update:modelValue', Number($event.target.value))"
        class="select pr-10 min-w-[200px] appearance-none"
      >
        <option v-for="user in users" :key="user.id" :value="user.id">
          {{ user.name }} — {{ goalLabel(user.goal) }}
        </option>
      </select>
      <svg class="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400 pointer-events-none"
           viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round">
        <polyline points="6 9 12 15 18 9"/>
      </svg>
    </div>
  </div>
</template>

<script setup>
defineProps({ modelValue: Number, users: { type: Array, default: () => [] } })
defineEmits(['update:modelValue'])

const goalLabels = {
  weight_loss:        'Perte de poids',
  muscle_gain:        'Prise de muscle',
  sleep_improvement:  'Améliorer le sommeil',
  maintenance:        'Maintien',
}
function goalLabel(goal) { return goalLabels[goal] || goal }
</script>
