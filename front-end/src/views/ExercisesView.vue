<template>
  <div class="space-y-8 animate-fade-in">

    <!-- Header -->
    <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
      <div>
        <h1 class="text-3xl font-bold text-brand-primary">Catalogue d'exercices</h1>
        <p class="text-slate-500 mt-1">Explorez et filtrez la bibliothèque complète d'exercices</p>
      </div>
    </div>

    <!-- Carte principale -->
    <div class="card">
      <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-6">
        <div>
          <p class="text-sm text-slate-500">{{ filteredExercises.length }} exercices disponibles</p>
        </div>
        <div class="flex items-center gap-3">
          <LoadingSpinner v-if="exLoading" message="" />
          <!-- Toggle langue FR / EN -->
          <div class="lang-toggle shrink-0" role="group" aria-label="Langue des exercices">
            <button @click="lang = 'fr'" class="lang-btn" :class="lang === 'fr' ? 'lang-btn--active' : ''">FR</button>
            <button @click="lang = 'en'" class="lang-btn" :class="lang === 'en' ? 'lang-btn--active' : ''">EN</button>
          </div>
        </div>
      </div>

      <!-- Filtres -->
      <div class="grid grid-cols-1 sm:grid-cols-3 gap-3 mb-6">
        <!-- Recherche -->
        <div class="relative">
          <svg class="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round">
            <circle cx="11" cy="11" r="8"/><path d="M21 21l-4.35-4.35"/>
          </svg>
          <input v-model="search" type="text" :placeholder="lang === 'fr' ? 'Rechercher un exercice...' : 'Search an exercise...'" class="input pl-9" />
        </div>
        <!-- Muscle -->
        <div class="relative">
          <select v-model="filterMuscle" class="select appearance-none pr-9">
            <option value="">{{ lang === 'fr' ? 'Tous les muscles' : 'All muscles' }}</option>
            <option v-for="m in muscleGroups" :key="m" :value="m">{{ filterMuscleLabel(m) }}</option>
          </select>
          <svg class="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400 pointer-events-none" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><polyline points="6 9 12 15 18 9"/></svg>
        </div>
        <!-- Équipement -->
        <div class="relative">
          <select v-model="filterEquipment" class="select appearance-none pr-9">
            <option value="">{{ lang === 'fr' ? 'Tout équipement' : 'All equipment' }}</option>
            <option v-for="e in equipmentList" :key="e" :value="e">{{ filterEquipLabel(e) }}</option>
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
              <span class="text-xs">{{ lang === 'fr' ? 'Pas d\'image' : 'No image' }}</span>
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
            <!-- Overlay -->
            <div class="absolute inset-0 bg-brand-primary/0 group-hover:bg-brand-primary/10 transition-colors duration-200 flex items-center justify-center">
              <span class="opacity-0 group-hover:opacity-100 transition-opacity duration-200 bg-white/90 text-brand-primary text-xs font-semibold px-3 py-1.5 rounded-full shadow">
                {{ lang === 'fr' ? 'Voir les détails' : 'View details' }}
              </span>
            </div>
          </div>

          <!-- Infos -->
          <div class="p-4">
            <h3 class="font-semibold text-brand-primary text-sm leading-snug mb-2">{{ exName(ex) }}</h3>
            <div class="flex flex-wrap gap-1.5">
              <span v-if="ex.muscle_group" class="badge-primary text-[11px]">
                <svg class="w-3 h-3" viewBox="0 0 24 24" fill="currentColor"><circle cx="12" cy="12" r="4"/></svg>
                {{ exMuscleLabel(ex) }}
              </span>
              <span v-if="ex.equipment" class="badge-accent text-[11px]">{{ exEquipLabel(ex) }}</span>
              <span v-if="ex.type" class="bg-slate-100 text-slate-500 text-[11px] font-medium px-2 py-0.5 rounded-full">{{ exTypeLabel(ex) }}</span>
            </div>
          </div>
        </div>
      </div>

      <!-- Modale détail exercice -->
      <Teleport to="body">
        <Transition name="modal">
          <div
            v-if="selectedExercise"
            class="fixed inset-0 z-50 flex items-center justify-center p-4"
            @click.self="closeModal"
          >
            <div class="absolute inset-0 bg-slate-900/50 backdrop-blur-sm" @click="closeModal" />
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
                  <span class="text-sm">{{ lang === 'fr' ? 'Pas d\'image' : 'No image' }}</span>
                </div>
                <span
                  v-if="selectedExercise.level"
                  class="absolute top-3 left-3 text-xs font-semibold px-2.5 py-1 rounded-full"
                  :class="{
                    'bg-brand-success/20 text-teal-700': selectedExercise.level === 'beginner',
                    'bg-brand-warning/20 text-amber-700': selectedExercise.level === 'intermediate',
                    'bg-brand-error/10 text-red-700':    selectedExercise.level === 'expert',
                  }"
                >{{ levelLabel(selectedExercise.level) }}</span>
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
                <h2 class="text-xl font-bold text-brand-primary leading-tight">{{ exName(selectedExercise) }}</h2>

                <div class="flex flex-wrap gap-2">
                  <span v-if="selectedExercise.muscle_group" class="badge-primary">
                    <svg class="w-3 h-3" viewBox="0 0 24 24" fill="currentColor"><circle cx="12" cy="12" r="4"/></svg>
                    {{ exMuscleLabel(selectedExercise) }}
                  </span>
                  <span v-if="selectedExercise.type" class="bg-slate-100 text-slate-600 text-xs font-medium px-2.5 py-1 rounded-full">
                    {{ exTypeLabel(selectedExercise) }}
                  </span>
                  <span v-if="selectedExercise.equipment" class="badge-accent">
                    {{ exEquipLabel(selectedExercise) }}
                  </span>
                </div>

                <div class="border-t border-slate-100" />

                <!-- Instructions -->
                <div v-if="exInstructions(selectedExercise)">
                  <h3 class="text-sm font-semibold text-brand-primary mb-2 flex items-center gap-1.5">
                    <svg class="w-4 h-4 text-brand-accent" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round">
                      <circle cx="12" cy="12" r="10"/><path d="M12 16v-4M12 8h.01"/>
                    </svg>
                    Instructions
                  </h3>
                  <p class="text-sm text-slate-600 leading-relaxed">{{ exInstructions(selectedExercise) }}</p>
                </div>

                <!-- Lien vidéo -->
                <div v-if="selectedExercise.video_url">
                  <div class="border-t border-slate-100 mb-4" />
                  <a
                    :href="selectedExercise.video_url"
                    target="_blank"
                    rel="noopener noreferrer"
                    class="flex items-center justify-center gap-2.5 w-full px-4 py-3 bg-red-50 hover:bg-red-100 border border-red-200 hover:border-red-300 rounded-xl transition-colors"
                  >
                    <div class="w-8 h-8 rounded-lg bg-red-500 flex items-center justify-center flex-shrink-0 shadow-sm">
                      <svg class="w-4 h-4 text-white" viewBox="0 0 24 24" fill="currentColor">
                        <polygon points="5 3 19 12 5 21 5 3"/>
                      </svg>
                    </div>
                    <p class="text-sm font-semibold text-red-700">
                      {{ lang === 'fr' ? 'Voir la vidéo de démonstration' : 'Watch demonstration video' }}
                    </p>
                  </a>
                </div>
              </div>
            </div>
          </div>
        </Transition>
      </Teleport>

      <!-- Empty state -->
      <div v-if="!exLoading && !paginatedExercises.length" class="flex flex-col items-center py-12 text-center">
        <svg class="w-10 h-10 text-slate-300 mb-3" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round">
          <circle cx="11" cy="11" r="8"/><path d="M21 21l-4.35-4.35"/>
        </svg>
        <p class="text-slate-400">{{ lang === 'fr' ? 'Aucun exercice ne correspond aux filtres' : 'No exercises match the filters' }}</p>
      </div>

      <!-- Pagination -->
      <div v-if="totalPages > 1" class="flex items-center justify-center gap-2 mt-6">
        <button @click="currentPage--" :disabled="currentPage === 1" class="btn-secondary px-3 py-1.5 text-sm disabled:opacity-40">
          ← {{ lang === 'fr' ? 'Précédent' : 'Previous' }}
        </button>
        <span class="text-sm text-slate-500">Page {{ currentPage }} / {{ totalPages }}</span>
        <button @click="currentPage++" :disabled="currentPage === totalPages" class="btn-secondary px-3 py-1.5 text-sm disabled:opacity-40">
          {{ lang === 'fr' ? 'Suivant' : 'Next' }} →
        </button>
      </div>
    </div>

  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { exercisesAPI } from '@/services/api'
import LoadingSpinner from '@/components/ui/LoadingSpinner.vue'

// ── État ──────────────────────────────────────────
const allExercises = ref([])
const exLoading = ref(false)
const search = ref('')
const filterMuscle = ref('')
const filterEquipment = ref('')
const selectedExercise = ref(null)
const currentPage = ref(1)
const PAGE_SIZE = 12
const lang = ref('fr')

// ── Listes de filtres ─────────────────────────────
const muscleGroups = computed(() => {
  const s = new Set(allExercises.value.map(e => e.muscle_group).filter(Boolean))
  return [...s].sort()
})

const equipmentList = computed(() => {
  const s = new Set(allExercises.value.map(e => e.equipment).filter(Boolean))
  return [...s].sort()
})

// ── Filtrage & pagination ─────────────────────────
const filteredExercises = computed(() => {
  const q = search.value.toLowerCase()
  return allExercises.value.filter(e => {
    const searchName = lang.value === 'fr'
      ? ((e.name_fr || e.name) + ' ' + (e.name || '')).toLowerCase()
      : (e.name || '').toLowerCase()
    const matchSearch = !q || searchName.includes(q)
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
  'abdominals':   'Abdominaux',  'abductors':  'Abducteurs',
  'adductors':    'Adducteurs',  'biceps':     'Biceps',
  'calves':       'Mollets',     'chest':      'Pectoraux',
  'forearms':     'Avant-bras',  'glutes':     'Fessiers',
  'hamstrings':   'Ischio-jambiers', 'lats':   'Grand dorsal',
  'lower back':   'Bas du dos',  'middle back':'Dos moyen',
  'neck':         'Cou',         'quadriceps': 'Quadriceps',
  'shoulders':    'Épaules',     'traps':      'Trapèzes',
  'triceps':      'Triceps',
}

const equipmentFr = {
  'barbell':          'Barre',         'body only':       'Poids du corps',
  'cable':            'Câble',         'dumbbell':        'Haltères',
  'e-z curl bar':     'Barre EZ',      'exercise ball':   'Ballon fitness',
  'foam roll':        'Rouleau mousse','kettlebells':      'Kettlebell',
  'machine':          'Machine',       'medicine ball':   'Médecine-ball',
  'none':             'Sans matériel', 'other':           'Autre',
  'resistance bands': 'Élastiques',
}

const typeFr = {
  'strength':              'Renforcement',         'stretching':  'Étirements',
  'cardio':                'Cardio',               'powerlifting':'Force athlétique',
  'olympic weightlifting': 'Haltérophilie olympique', 'plyometrics':'Pliométrie',
  'strongman':             'Homme fort',
}

function translateMuscle(val)    { return muscleGroupFr[val?.toLowerCase()] ?? val }
function translateEquipment(val) { return equipmentFr[val?.toLowerCase()]   ?? val }
function translateType(val)      { return typeFr[val?.toLowerCase()]         ?? val }

function exName(ex)        { return lang.value === 'fr' ? (ex.name_fr || ex.name) : ex.name }
function exMuscleLabel(ex) { return lang.value === 'fr' ? (ex.muscle_group_fr || translateMuscle(ex.muscle_group)) : ex.muscle_group }
function exEquipLabel(ex)  { return lang.value === 'fr' ? (ex.equipment_fr   || translateEquipment(ex.equipment))  : ex.equipment }
function exTypeLabel(ex)   { return lang.value === 'fr' ? (ex.type_fr        || translateType(ex.type))            : ex.type }
function exInstructions(ex){ return lang.value === 'fr' ? (ex.instructions_fr || ex.instructions) : ex.instructions }
function levelLabel(l)     { return lang.value === 'en' ? l : ({ beginner: 'Débutant', intermediate: 'Intermédiaire', expert: 'Expert' }[l] || l) }
function filterMuscleLabel(val) { return lang.value === 'fr' ? translateMuscle(val) : val }
function filterEquipLabel(val)  { return lang.value === 'fr' ? translateEquipment(val) : val }

async function loadExercises() {
  exLoading.value = true
  try {
    const res = await exercisesAPI.getAll()
    allExercises.value = res.data
  } catch {
    // silencieux
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

.lang-toggle {
  display: inline-flex;
  align-items: center;
  background: #f1f5f9;
  border-radius: 9999px;
  padding: 3px;
  gap: 2px;
  box-shadow: inset 0 1px 3px rgba(0,0,0,.08);
}
.lang-btn {
  padding: 0.3rem 0.9rem;
  border-radius: 9999px;
  font-size: 0.78rem;
  font-weight: 600;
  color: #94a3b8;
  background: transparent;
  border: none;
  cursor: pointer;
  transition: color 0.2s ease, background 0.2s ease, box-shadow 0.2s ease;
  line-height: 1.4;
  letter-spacing: 0.03em;
}
.lang-btn--active {
  background: white;
  color: #0f4c75;
  box-shadow: 0 1px 4px rgba(0,0,0,.13);
}
</style>
