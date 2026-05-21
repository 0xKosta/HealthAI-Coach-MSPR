<template>
  <div class="space-y-8 animate-fade-in">

    <!-- Header -->
    <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
      <div>
        <h1 class="text-3xl font-bold text-brand-primary">Programme d'Entraînement</h1>
        <p class="text-slate-500 mt-1">Générez un plan IA personnalisé selon votre profil et vos objectifs</p>
      </div>
      <UserSelector v-if="userStore.users.length" v-model="userStore.selectedUserId" :users="userStore.users" />
    </div>

    <!-- Formulaire de configuration -->
    <div class="card">
      <h2 class="text-xl font-bold text-brand-primary mb-6">Paramètres du programme</h2>
      <div class="grid grid-cols-1 sm:grid-cols-2 gap-6">
        <div>
          <label class="label">Équipement disponible</label>
          <div class="grid grid-cols-2 gap-2">
            <button
              v-for="eq in equipmentOptions" :key="eq.value"
              @click="form.equipment = eq.value"
              class="flex items-center gap-2.5 px-3 py-3 rounded-xl border text-sm font-medium transition-all duration-200"
              :class="form.equipment === eq.value
                ? 'bg-brand-accent text-white border-brand-accent shadow-sm'
                : 'border-slate-200 text-slate-600 bg-white hover:border-brand-accent/40 hover:text-brand-primary'"
            >
              <span class="material-symbols-outlined text-[20px] leading-none">{{ eq.icon }}</span>
              {{ eq.label }}
            </button>
          </div>
        </div>
        <div>
          <label class="label">Jours d'entraînement par semaine</label>
          <div class="flex gap-2">
            <button
              v-for="d in [1,2,3,4,5,6,7]" :key="d"
              @click="form.daysPerWeek = d"
              class="w-10 h-10 rounded-xl border text-sm font-bold transition-all duration-200"
              :class="form.daysPerWeek === d
                ? 'bg-brand-primary text-white border-brand-primary shadow-sm'
                : 'border-slate-200 text-slate-600 bg-white hover:border-brand-primary/40'"
            >{{ d }}</button>
          </div>
          <p class="text-xs text-slate-400 mt-2">{{ daysLabel }}</p>
        </div>
      </div>
      <div class="mt-6 pt-5 border-t border-slate-100 flex items-center justify-between gap-4">
        <p class="text-sm text-slate-500">
          <span class="font-medium text-brand-primary">{{ userStore.selectedUser?.name }}</span>
          · {{ goalLabels[userStore.selectedUser?.goal] }} · {{ form.daysPerWeek }}j/semaine
        </p>
        <button @click="generatePlan" :disabled="generating" class="btn-primary">
          <div v-if="generating" class="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
          <svg v-else class="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round">
            <polygon points="5 3 19 12 5 21 5 3"/>
          </svg>
          {{ generating ? 'Génération...' : 'Générer le programme' }}
        </button>
      </div>
    </div>

    <ErrorAlert v-if="planError" :message="planError" />

    <!-- Résultat programme IA -->
    <div v-if="plan" class="card animate-slide-up">
      <div class="flex items-center justify-between mb-5">
        <div>
          <h2 class="text-xl font-bold text-brand-primary">Votre programme</h2>
          <p class="text-sm text-slate-500 mt-0.5">{{ plan.user_name }} · {{ form.daysPerWeek }} jours/semaine</p>
        </div>
        <button @click="generatePlan" class="btn-secondary text-xs">
          <svg class="w-3.5 h-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round">
            <polyline points="23 4 23 10 17 10"/><polyline points="1 20 1 14 7 14"/>
            <path d="M3.51 9a9 9 0 0114.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0020.49 15"/>
          </svg>
          Régénérer
        </button>
      </div>
      <AIAdviceCard title="Programme d'entraînement IA" :content="plan.plan" />
    </div>

  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useUserStore } from '@/stores/userStore'
import { coachAPI } from '@/services/api'
import UserSelector from '@/components/ui/UserSelector.vue'
import ErrorAlert from '@/components/ui/ErrorAlert.vue'
import AIAdviceCard from '@/components/ui/AIAdviceCard.vue'

const userStore = useUserStore()

const form = ref({ equipment: 'dumbbell', daysPerWeek: 3 })
const generating = ref(false)
const planError = ref('')
const plan = ref(null)

const equipmentOptions = [
  { value: 'none',       label: 'Aucun',         icon: 'self_improvement' },
  { value: 'dumbbell',   label: 'Haltères',       icon: 'fitness_center' },
  { value: 'barbell',    label: 'Barre',           icon: 'sports_gymnastics' },
  { value: 'machine',    label: 'Machines',        icon: 'precision_manufacturing' },
  { value: 'resistance', label: 'Élastiques',      icon: 'sports_martial_arts' },
  { value: 'full',       label: 'Tout matériel',   icon: 'exercise' },
]

const goalLabels = {
  weight_loss: 'Perte de poids', muscle_gain: 'Prise de muscle',
  sleep_improvement: 'Améliorer le sommeil', maintenance: 'Maintien',
}

const daysLabel = computed(() => {
  const d = form.value.daysPerWeek
  if (d <= 2) return 'Débutant — récupération optimale'
  if (d <= 4) return 'Intermédiaire — bon équilibre'
  if (d <= 5) return 'Avancé — haute fréquence'
  return 'Expert — programme intensif'
})

async function generatePlan() {
  if (!userStore.selectedUserId) return
  generating.value = true; planError.value = ''; plan.value = null
  try {
    const res = await coachAPI.getWorkoutPlan(userStore.selectedUserId, form.value.equipment, form.value.daysPerWeek)
    plan.value = res.data
  } catch {
    planError.value = "Erreur lors de la génération du programme. Vérifiez la connexion à l'API."
  } finally {
    generating.value = false
  }
}
</script>
