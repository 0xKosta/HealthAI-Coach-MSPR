<template>
  <div class="space-y-8 animate-fade-in">

    <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
      <div>
        <h1 class="text-3xl font-bold text-brand-primary">Analyse Nutritionnelle</h1>
        <p class="text-slate-600 mt-1">Analysez un repas par photo grâce à l'IA vision</p>
      </div>
      <UserSelector v-if="userStore.users.length" v-model="userStore.selectedUserId" :users="userStore.users" />
    </div>

    <!-- Zone upload -->
    <div class="card">
      <h2 class="text-xl font-bold text-brand-primary mb-5">Photo du repas</h2>

      <div
        class="relative border-2 border-dashed rounded-2xl transition-all duration-200 cursor-pointer"
        :class="dragOver
          ? 'border-brand-accent bg-brand-accent/5'
          : 'border-slate-200 hover:border-brand-accent/50 hover:bg-brand-light'"
        @dragover.prevent="dragOver = true"
        @dragleave="dragOver = false"
        @drop.prevent="handleDrop"
        @click="fileInput?.click()"
      >
        <input ref="fileInput" type="file" accept="image/jpeg,image/png,image/webp,image/gif" class="hidden" @change="handleFileChange" />

        <div v-if="!previewUrl" class="flex flex-col items-center justify-center py-14 text-center px-6">
          <div class="w-16 h-16 rounded-2xl bg-brand-accent/10 border border-brand-accent/20 flex items-center justify-center mb-4">
            <svg class="w-8 h-8 text-brand-accent/60" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round">
              <rect x="3" y="3" width="18" height="18" rx="2"/><circle cx="8.5" cy="8.5" r="1.5"/>
              <polyline points="21 15 16 10 5 21"/>
            </svg>
          </div>
          <p class="text-brand-text font-medium">Glissez une image ici ou cliquez pour parcourir</p>
          <p class="text-slate-600 text-sm mt-1">JPG, PNG, WebP — max 10 Mo</p>
        </div>

        <div v-else class="relative flex items-center justify-center min-h-[280px] max-h-[28rem] p-6 bg-slate-50/80 rounded-xl overflow-hidden">
          <img
            :src="previewUrl"
            alt="Aperçu du repas"
            class="max-w-full max-h-[24rem] w-auto h-auto object-contain rounded-lg"
          />
          <div class="absolute inset-0 bg-brand-primary/30 flex items-center justify-center opacity-0 hover:opacity-100 transition-opacity rounded-xl">
            <p class="text-sm text-white font-medium bg-brand-primary/70 px-4 py-2 rounded-lg">Cliquer pour changer</p>
          </div>
        </div>
      </div>

      <div class="flex flex-col sm:flex-row gap-3 mt-4">
        <button @click="analyzePhoto" :disabled="!previewUrl || analyzing || !userStore.selectedUserId" class="btn-primary flex-1">
          <div v-if="analyzing" class="w-4 h-4 border-2 border-brand-primary border-t-transparent rounded-full animate-spin"></div>
          <svg v-else class="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round">
            <circle cx="11" cy="11" r="8"/><path d="M21 21l-4.35-4.35"/>
          </svg>
          {{ analyzing ? 'Analyse en cours...' : 'Analyser le repas' }}
        </button>
        <button v-if="previewUrl" @click="clearImage" class="btn-secondary">
          <svg class="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round">
            <line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>
          </svg>
          Effacer
        </button>
      </div>
    </div>

    <ErrorAlert v-if="error" :message="error" />

    <template v-if="result">
      <!-- Aliments détectés -->
      <div class="card animate-slide-up">
        <h2 class="text-xl font-bold text-brand-primary mb-4">Aliments détectés</h2>
        <div v-if="result.foods_detected?.length" class="flex flex-wrap gap-2 mb-6">
          <span
            v-for="food in result.foods_detected" :key="food"
            class="inline-flex items-center gap-1.5 px-3 py-1.5 bg-brand-accent/10 border border-brand-accent/20 rounded-full text-sm font-medium text-cyan-700"
          >
            <svg class="w-3 h-3" viewBox="0 0 24 24" fill="currentColor"><circle cx="12" cy="12" r="4"/></svg>
            {{ food }}
          </span>
        </div>
        <p v-else class="text-slate-600 text-sm">Aucun aliment identifié.</p>

        <!-- Macros -->
        <div v-if="result.macros" class="grid grid-cols-2 sm:grid-cols-4 gap-4">
          <MacroCard label="Calories"  :value="result.macros.calories"   unit="kcal" color="text-amber-600"  bg="bg-brand-warning/10" />
          <MacroCard label="Protéines" :value="result.macros.protein_g"  unit="g"    color="text-brand-accent" bg="bg-brand-accent/10" />
          <MacroCard label="Glucides"  :value="result.macros.carbs_g"    unit="g"    color="text-teal-600"   bg="bg-brand-success/10" />
          <MacroCard label="Lipides"   :value="result.macros.fat_g"      unit="g"    color="text-violet-600" bg="bg-violet-100" />
        </div>
      </div>

      <!-- Analyse IA — fond bleu nuit -->
      <AIAdviceCard v-if="result.advice" title="Analyse nutritionnelle IA" :content="result.advice" />
    </template>
  </div>
</template>

<script setup>
import { ref, defineComponent, h } from 'vue'
import { useUserStore } from '@/stores/userStore'
import { coachAPI } from '@/services/api'
import UserSelector from '@/components/ui/UserSelector.vue'
import ErrorAlert from '@/components/ui/ErrorAlert.vue'
import AIAdviceCard from '@/components/ui/AIAdviceCard.vue'

const userStore = useUserStore()
const fileInput = ref(null)
const previewUrl = ref('')
const imageBase64 = ref('')
const dragOver = ref(false)
const analyzing = ref(false)
const error = ref('')
const result = ref(null)

const MAX_FILE_SIZE = 10 * 1024 * 1024
const ALLOWED_IMAGE_TYPES = ['image/jpeg', 'image/png', 'image/webp', 'image/gif']

function isValidImageSignature(bytes) {
  if (bytes.length < 12) return false
  if (bytes[0] === 0xFF && bytes[1] === 0xD8 && bytes[2] === 0xFF) return true
  if (bytes[0] === 0x89 && bytes[1] === 0x50 && bytes[2] === 0x4E && bytes[3] === 0x47) return true
  if (bytes[0] === 0x47 && bytes[1] === 0x49 && bytes[2] === 0x46) return true
  if (
    bytes[0] === 0x52 && bytes[1] === 0x49 && bytes[2] === 0x46 && bytes[3] === 0x46 &&
    bytes[8] === 0x57 && bytes[9] === 0x45 && bytes[10] === 0x42 && bytes[11] === 0x50
  ) return true
  return false
}

function handleDrop(e) { dragOver.value = false; const f = e.dataTransfer.files[0]; if (f) loadFile(f) }
function handleFileChange(e) { const f = e.target.files[0]; if (f) loadFile(f) }

function loadFile(file) {
  if (!ALLOWED_IMAGE_TYPES.includes(file.type)) {
    error.value = 'Veuillez sélectionner une image JPEG, PNG, WebP ou GIF.'
    return
  }
  if (file.size > MAX_FILE_SIZE) {
    error.value = 'Fichier trop volumineux (max 10 Mo).'
    return
  }

  error.value = ''; result.value = ''
  const reader = new FileReader()
  reader.onload = (ev) => {
    const bytes = new Uint8Array(ev.target.result)
    if (!isValidImageSignature(bytes)) {
      error.value = 'Le fichier ne correspond pas à une image valide.'
      return
    }

    const dataReader = new FileReader()
    dataReader.onload = (e) => {
      previewUrl.value = e.target.result
      imageBase64.value = e.target.result.split(',')[1]
    }
    dataReader.readAsDataURL(file)
  }
  reader.readAsArrayBuffer(file)
}

function clearImage() {
  previewUrl.value = ''; imageBase64.value = ''; result.value = null; error.value = ''
  if (fileInput.value) fileInput.value.value = ''
}

async function analyzePhoto() {
  if (!imageBase64.value || !userStore.selectedUserId) return
  analyzing.value = true; error.value = ''; result.value = null
  try {
    const res = await coachAPI.analyzePhoto(userStore.selectedUserId, imageBase64.value)
    result.value = res.data
  } catch {
    error.value = "Erreur lors de l'analyse. Vérifiez la connexion à l'API."
  } finally {
    analyzing.value = false
  }
}

const MacroCard = defineComponent({
  props: { label: String, value: [String, Number], unit: String, color: String, bg: String },
  setup(props) {
    return () => h('div', { class: `rounded-xl p-4 text-center border border-slate-100 ${props.bg}` }, [
      h('p', { class: `text-2xl font-bold ${props.color}` }, props.value ?? '—'),
      h('p', { class: 'text-xs text-slate-600 mt-0.5' }, `${props.label} (${props.unit})`),
    ])
  },
})
</script>
