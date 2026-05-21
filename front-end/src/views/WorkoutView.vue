<template>
  <div class="space-y-8 animate-fade-in">

    <!-- Header -->
    <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
      <div>
        <h1 class="text-3xl font-bold text-brand-primary">Programme d'Entraînement</h1>
        <p class="text-slate-500 mt-1">Générez un plan IA personnalisé et explorez le catalogue d'exercices</p>
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

    <!-- ═══════════════════════════════════════════
         CATALOGUE D'EXERCICES
    ════════════════════════════════════════════ -->
    <div class="card">
      <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-6">
        <div>
          <h2 class="text-xl font-bold text-brand-primary">Catalogue d'exercices</h2>
          <p class="text-sm text-slate-500 mt-0.5">{{ filteredExercises.length }} exercices disponibles</p>
        </div>
        <LoadingSpinner v-if="exLoading" message="" />
      </div>

      <!-- Filtres -->
      <div class="grid grid-cols-1 sm:grid-cols-3 gap-3 mb-6">
        <!-- Recherche -->
        <div class="relative">
          <svg class="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round">
            <circle cx="11" cy="11" r="8"/><path d="M21 21l-4.35-4.35"/>
          </svg>
          <input v-model="search" type="text" placeholder="Rechercher un exercice..." class="input pl-9" />
        </div>
        <!-- Muscle -->
        <div class="relative">
          <select v-model="filterMuscle" class="select appearance-none pr-9">
            <option value="">Tous les muscles</option>
            <option v-for="m in muscleGroups" :key="m" :value="m">{{ translateMuscle(m) }}</option>
          </select>
          <svg class="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400 pointer-events-none" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><polyline points="6 9 12 15 18 9"/></svg>
        </div>
        <!-- Équipement -->
        <div class="relative">
          <select v-model="filterEquipment" class="select appearance-none pr-9">
            <option value="">Tout équipement</option>
            <option v-for="e in equipmentList" :key="e" :value="e">{{ translateEquipment(e) }}</option>
          </select>
          <svg class="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400 pointer-events-none" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><polyline points="6 9 12 15 18 9"/></svg>
        </div>
      </div>

      <!-- Grille d'exercices -->
      <div v-if="!exLoading && paginatedExercises.length" class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        <div
          v-for="ex in paginatedExercises" :key="ex.id"
          class="bg-white border border-slate-100 rounded-xl overflow-hidden hover:shadow-md hover:border-brand-accent/30 transition-all duration-200 cursor-pointer group"
          @click="openModal(ex)"
        >
          <!-- GIF / Image -->
          <div class="relative h-44 bg-brand-light flex items-center justify-center overflow-hidden">
            <img
              v-if="ex.gif_url || ex.image_url"
              :src="ex.gif_url || ex.image_url"
              :alt="ex.name"
              class="h-full w-full object-cover group-hover:scale-105 transition-transform duration-300"
              loading="lazy"
              @error="(e) => e.target.style.display='none'"
            />
            <div v-else class="flex flex-col items-center gap-2 text-slate-300">
              <svg class="w-10 h-10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round">
                <path d="M6 4v16M18 4v16M10 8H6M10 16H6M18 8h-4M18 16h-4"/>
              </svg>
              <span class="text-xs">Pas d'image</span>
            </div>
            <!-- Niveau badge -->
            <span
              v-if="ex.level"
              class="absolute top-2 right-2 text-xs font-semibold px-2 py-0.5 rounded-full"
              :class="{
                'bg-brand-success/20 text-teal-700': ex.level === 'beginner',
                'bg-brand-warning/20 text-amber-700': ex.level === 'intermediate',
                'bg-brand-error/10 text-red-700':    ex.level === 'expert',
              }"
            >{{ levelLabel(ex.level) }}</span>
            <!-- Overlay "voir détails" -->
            <div class="absolute inset-0 bg-brand-primary/0 group-hover:bg-brand-primary/10 transition-colors duration-200 flex items-center justify-center">
              <span class="opacity-0 group-hover:opacity-100 transition-opacity duration-200 bg-white/90 text-brand-primary text-xs font-semibold px-3 py-1.5 rounded-full shadow">
                Voir les détails
              </span>
            </div>
          </div>

          <!-- Infos -->
          <div class="p-4">
            <h3 class="font-semibold text-brand-primary text-sm leading-snug mb-2">{{ ex.name }}</h3>
            <div class="flex flex-wrap gap-1.5">
              <span v-if="ex.muscle_group" class="badge-primary text-[11px]">
                <svg class="w-3 h-3" viewBox="0 0 24 24" fill="currentColor"><circle cx="12" cy="12" r="4"/></svg>
                {{ translateMuscle(ex.muscle_group) }}
              </span>
              <span v-if="ex.equipment" class="badge-accent text-[11px]">{{ translateEquipment(ex.equipment) }}</span>
              <span v-if="ex.type" class="bg-slate-100 text-slate-500 text-[11px] font-medium px-2 py-0.5 rounded-full">{{ translateType(ex.type) }}</span>
            </div>
          </div>
        </div>
      </div>

    <!-- ── Modale détail exercice ─────────────────────── -->
    <Teleport to="body">
      <Transition name="modal">
        <div
          v-if="selectedExercise"
          class="fixed inset-0 z-50 flex items-center justify-center p-4"
          @click.self="closeModal"
        >
          <!-- Backdrop -->
          <div class="absolute inset-0 bg-slate-900/50 backdrop-blur-sm" @click="closeModal" />

          <!-- Panneau -->
          <div class="relative bg-white rounded-2xl shadow-2xl w-full max-w-lg max-h-[90vh] overflow-y-auto z-10">

            <!-- Image / GIF -->
            <div class="relative h-56 bg-brand-light flex items-center justify-center overflow-hidden rounded-t-2xl">
              <img
                v-if="selectedExercise.gif_url || selectedExercise.image_url"
                :src="selectedExercise.gif_url || selectedExercise.image_url"
                :alt="selectedExercise.name"
                class="h-full w-full object-cover"
                @error="(e) => e.target.style.display='none'"
              />
              <div v-else class="flex flex-col items-center gap-2 text-slate-300">
                <svg class="w-12 h-12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round">
                  <path d="M6 4v16M18 4v16M10 8H6M10 16H6M18 8h-4M18 16h-4"/>
                </svg>
                <span class="text-sm">Pas d'image</span>
              </div>
              <!-- Niveau badge -->
              <span
                v-if="selectedExercise.level"
                class="absolute top-3 left-3 text-xs font-semibold px-2.5 py-1 rounded-full"
                :class="{
                  'bg-brand-success/20 text-teal-700': selectedExercise.level === 'beginner',
                  'bg-brand-warning/20 text-amber-700': selectedExercise.level === 'intermediate',
                  'bg-brand-error/10 text-red-700':    selectedExercise.level === 'expert',
                }"
              >{{ levelLabel(selectedExercise.level) }}</span>
              <!-- Bouton fermer -->
              <button
                @click="closeModal"
                class="absolute top-3 right-3 w-8 h-8 rounded-full bg-white/80 hover:bg-white shadow flex items-center justify-center text-slate-500 hover:text-brand-primary transition-colors"
              >
                <svg class="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round">
                  <path d="M18 6L6 18M6 6l12 12"/>
                </svg>
              </button>
            </div>

            <!-- Contenu -->
            <div class="p-6 space-y-5">

              <!-- Nom -->
              <h2 class="text-xl font-bold text-brand-primary leading-tight">{{ selectedExercise.name }}</h2>

              <!-- Tags -->
              <div class="flex flex-wrap gap-2">
                <span v-if="selectedExercise.muscle_group" class="badge-primary">
                  <svg class="w-3 h-3" viewBox="0 0 24 24" fill="currentColor"><circle cx="12" cy="12" r="4"/></svg>
                  {{ translateMuscle(selectedExercise.muscle_group) }}
                </span>
                <span v-if="selectedExercise.type" class="bg-slate-100 text-slate-600 text-xs font-medium px-2.5 py-1 rounded-full">
                  {{ translateType(selectedExercise.type) }}
                </span>
                <span v-if="selectedExercise.equipment" class="badge-accent">
                  {{ translateEquipment(selectedExercise.equipment) }}
                </span>
              </div>

              <!-- Séparateur -->
              <div class="border-t border-slate-100" />

              <!-- Instructions -->
              <div v-if="selectedExercise.instructions_fr || selectedExercise.instructions">
                <h3 class="text-sm font-semibold text-brand-primary mb-2 flex items-center gap-1.5">
                  <svg class="w-4 h-4 text-brand-accent" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round">
                    <circle cx="12" cy="12" r="10"/><path d="M12 16v-4M12 8h.01"/>
                  </svg>
                  Instructions
                </h3>
                <p class="text-sm text-slate-600 leading-relaxed">
                  {{ selectedExercise.instructions_fr || selectedExercise.instructions }}
                </p>
              </div>

              <!-- Lien vidéo -->
              <div v-if="selectedExercise.video_url">
                <div class="border-t border-slate-100 mb-4" />
                <a
                  :href="selectedExercise.video_url"
                  target="_blank"
                  rel="noopener noreferrer"
                  class="flex items-center gap-3 w-full px-4 py-3 bg-red-50 hover:bg-red-100 border border-red-200 hover:border-red-300 rounded-xl transition-colors group/video"
                >
                  <div class="w-9 h-9 rounded-lg bg-red-500 flex items-center justify-center flex-shrink-0 shadow-sm">
                    <svg class="w-4 h-4 text-white" viewBox="0 0 24 24" fill="currentColor">
                      <polygon points="5 3 19 12 5 21 5 3"/>
                    </svg>
                  </div>
                  <div class="flex-1 min-w-0">
                    <p class="text-sm font-semibold text-red-700">Voir la vidéo de démonstration</p>
                    <p class="text-xs text-red-500 truncate">{{ selectedExercise.video_url }}</p>
                  </div>
                  <svg class="w-4 h-4 text-red-400 group-hover/video:translate-x-0.5 transition-transform" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round">
                    <path d="M18 13v6a2 2 0 01-2 2H5a2 2 0 01-2-2V8a2 2 0 012-2h6M15 3h6v6M10 14L21 3"/>
                  </svg>
                </a>
              </div>

            </div>
          </div>
        </div>
      </Transition>
    </Teleport>

      <!-- Empty state filtres -->
      <div v-if="!exLoading && !paginatedExercises.length" class="flex flex-col items-center py-12 text-center">
        <svg class="w-10 h-10 text-slate-300 mb-3" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round">
          <circle cx="11" cy="11" r="8"/><path d="M21 21l-4.35-4.35"/>
        </svg>
        <p class="text-slate-400">Aucun exercice ne correspond aux filtres</p>
      </div>

      <!-- Pagination -->
      <div v-if="totalPages > 1" class="flex items-center justify-center gap-2 mt-6">
        <button @click="currentPage--" :disabled="currentPage === 1" class="btn-secondary px-3 py-1.5 text-sm disabled:opacity-40">
          ← Précédent
        </button>
        <span class="text-sm text-slate-500">Page {{ currentPage }} / {{ totalPages }}</span>
        <button @click="currentPage++" :disabled="currentPage === totalPages" class="btn-secondary px-3 py-1.5 text-sm disabled:opacity-40">
          Suivant →
        </button>
      </div>
    </div>

  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useUserStore } from '@/stores/userStore'
import { coachAPI, exercisesAPI } from '@/services/api'
import UserSelector from '@/components/ui/UserSelector.vue'
import ErrorAlert from '@/components/ui/ErrorAlert.vue'
import AIAdviceCard from '@/components/ui/AIAdviceCard.vue'
import LoadingSpinner from '@/components/ui/LoadingSpinner.vue'

const userStore = useUserStore()

// ── Programme IA ──────────────────────────────────
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

// ── Catalogue d'exercices ─────────────────────────
const allExercises = ref([])
const exLoading = ref(false)
const search = ref('')
const filterMuscle = ref('')
const filterEquipment = ref('')
const selectedExercise = ref(null)
const currentPage = ref(1)
const PAGE_SIZE = 12

const muscleGroups = computed(() => {
  const s = new Set(allExercises.value.map(e => e.muscle_group).filter(Boolean))
  return [...s].sort()
})

const equipmentList = computed(() => {
  const s = new Set(allExercises.value.map(e => e.equipment).filter(Boolean))
  return [...s].sort()
})

const filteredExercises = computed(() => {
  const q = search.value.toLowerCase()
  return allExercises.value.filter(e => {
    const matchSearch = !q || e.name?.toLowerCase().includes(q)
    const matchMuscle = !filterMuscle.value || e.muscle_group === filterMuscle.value
    const matchEquip  = !filterEquipment.value || e.equipment === filterEquipment.value
    return matchSearch && matchMuscle && matchEquip
  })
})

const totalPages = computed(() => Math.ceil(filteredExercises.value.length / PAGE_SIZE))

const paginatedExercises = computed(() => {
  const start = (currentPage.value - 1) * PAGE_SIZE
  return filteredExercises.value.slice(start, start + PAGE_SIZE)
})

watch([search, filterMuscle, filterEquipment], () => { currentPage.value = 1 })

function openModal(ex) {
  selectedExercise.value = ex
  document.body.style.overflow = 'hidden'
}
function closeModal() {
  selectedExercise.value = null
  document.body.style.overflow = ''
}

// ── Dictionnaires de traduction ───────────────────
const muscleGroupFr = {
  'abdominals':   'Abdominaux',
  'abductors':    'Abducteurs',
  'adductors':    'Adducteurs',
  'biceps':       'Biceps',
  'calves':       'Mollets',
  'chest':        'Pectoraux',
  'forearms':     'Avant-bras',
  'glutes':       'Fessiers',
  'hamstrings':   'Ischio-jambiers',
  'lats':         'Grand dorsal',
  'lower back':   'Bas du dos',
  'middle back':  'Dos moyen',
  'neck':         'Cou',
  'quadriceps':   'Quadriceps',
  'shoulders':    'Épaules',
  'traps':        'Trapèzes',
  'triceps':      'Triceps',
}

const equipmentFr = {
  'barbell':          'Barre',
  'body only':        'Poids du corps',
  'cable':            'Câble',
  'dumbbell':         'Haltères',
  'e-z curl bar':     'Barre EZ',
  'exercise ball':    'Ballon fitness',
  'foam roll':        'Rouleau mousse',
  'kettlebells':      'Kettlebell',
  'machine':          'Machine',
  'medicine ball':    'Médecine-ball',
  'none':             'Sans matériel',
  'other':            'Autre',
  'resistance bands': 'Élastiques',
}

const typeFr = {
  'strength':               'Renforcement',
  'stretching':             'Étirements',
  'cardio':                 'Cardio',
  'powerlifting':           'Force athlétique',
  'olympic weightlifting':  'Haltérophilie olympique',
  'plyometrics':            'Pliométrie',
  'strongman':              'Homme fort',
}

function translateMuscle(val)    { return muscleGroupFr[val?.toLowerCase()] ?? val }
function translateEquipment(val) { return equipmentFr[val?.toLowerCase()]   ?? val }
function translateType(val)      { return typeFr[val?.toLowerCase()]         ?? val }
function levelLabel(l) {
  return { beginner: 'Débutant', intermediate: 'Intermédiaire', expert: 'Expert' }[l] || l
}

async function loadExercises() {
  exLoading.value = true
  try {
    const res = await exercisesAPI.getAll()
    allExercises.value = res.data
  } catch {
    // silencieux — le catalogue est secondaire
  } finally {
    exLoading.value = false
  }
}

onMounted(() => loadExercises())
</script>

<style scoped>
.modal-enter-active { transition: opacity 0.2s ease; }
.modal-leave-active { transition: opacity 0.15s ease; }
.modal-enter-from,
.modal-leave-to     { opacity: 0; }
</style>
