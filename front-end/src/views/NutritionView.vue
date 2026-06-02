<template>
  <div class="space-y-8 animate-fade-in" @touchstart.passive="onTouchStart" @touchmove="onTouchMove" @touchend.passive="onTouchEnd">

    <div class="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
      <div>
        <h1 class="text-3xl font-bold text-brand-primary">Nutrition</h1>
        <p class="text-slate-600 mt-1">{{ pageSubtitle }}</p>
      </div>
      <div class="flex flex-wrap items-center gap-3">
        <button v-if="isAdminScope" class="btn-secondary" @click="goToUsersList">Changer d'utilisateur</button>
      </div>
    </div>

    <div
      v-if="activeUserId && !userLoading && !userError"
      class="nutrition-nav-row"
    >
      <AdminUserTabs :user-id="activeUserId" />

      <div
        v-if="!isAdminScope"
        class="nutrition-module-nav"
      >
        <p class="nutrition-module-nav__label">Module IA</p>
        <div class="nutrition-tabs" role="tablist" aria-label="Modules nutrition">
          <button
            type="button"
            role="tab"
            :aria-selected="activeTab === 'photo'"
            class="nutrition-tabs__btn"
            :class="{ 'nutrition-tabs__btn--active': activeTab === 'photo' }"
            @click="activeTab = 'photo'"
          >
            <span class="material-symbols-outlined text-[18px] leading-none" aria-hidden="true">photo_camera</span>
            <span class="nutrition-tabs__text">Analyse photo</span>
          </button>
          <button
            type="button"
            role="tab"
            :aria-selected="activeTab === 'meal'"
            class="nutrition-tabs__btn"
            :class="{ 'nutrition-tabs__btn--active': activeTab === 'meal' }"
            @click="activeTab = 'meal'"
          >
            <span class="material-symbols-outlined text-[18px] leading-none" aria-hidden="true">restaurant_menu</span>
            <span class="nutrition-tabs__text">Plan repas</span>
          </button>
        </div>
      </div>
    </div>

    <LoadingSpinner v-if="userLoading" message="Chargement du profil utilisateur..." />
    <ErrorAlert v-else-if="userError" :message="userError" />

    <template v-else-if="isAdminScope && activeUserId">
      <AiRequestHistoryPanel
        variant="admin"
        :user-id="activeUserId"
        request-type="analyze_photo"
        title="Historique nutrition (photos IA)"
        description="Chaque ligne correspond à une photo analysée : aliments, macros et conseil enregistrés."
      />
      <AiRequestHistoryPanel
        variant="admin"
        :user-id="activeUserId"
        request-type="meal_plan"
        title="Historique plans repas IA"
        description="Budget, allergies et plan hebdomadaire généré pour chaque demande."
      />
    </template>

    <template v-else-if="activeUserId">
      <ProfileAiGate
        v-if="currentUser && aiBlocked"
        :title="aiGateTitle"
        :description="aiGateDescription"
        :issues="profileBlocksAi ? profileIssues : []"
        :profile-edit-path="profileBlocksAi ? profileEditPath : ''"
        :cta-label="profileBlocksAi
          ? (hasInvalidProfile ? 'Corriger le profil' : 'Compléter mon profil')
          : ''"
      />

      <!-- ── Onglet analyse photo ── -->
      <template v-else-if="currentUser && activeTab === 'photo'">
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
            <button
              type="button"
              :disabled="!previewUrl || analyzing || !activeUserId"
              class="btn-primary flex-1"
              @click="analyzePhoto"
            >
              <div v-if="analyzing" class="w-4 h-4 border-2 border-brand-primary border-t-transparent rounded-full animate-spin"></div>
              <svg v-else class="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round">
                <circle cx="11" cy="11" r="8"/><path d="M21 21l-4.35-4.35"/>
              </svg>
              {{ analyzing ? 'Analyse en cours...' : 'Analyser le repas' }}
            </button>
            <button v-if="previewUrl" type="button" class="btn-secondary" @click="clearImage">
              <svg class="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round">
                <line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>
              </svg>
              Effacer
            </button>
          </div>
        </div>

        <ErrorAlert v-if="photoError" :message="photoError" />

        <template v-if="photoResult">
          <div class="card animate-slide-up">
            <h2 class="text-xl font-bold text-brand-primary mb-4">Aliments détectés</h2>
            <div v-if="photoResult.foods_detected?.length" class="flex flex-wrap gap-2 mb-6">
              <span
                v-for="food in photoResult.foods_detected"
                :key="food"
                class="inline-flex items-center gap-1.5 px-3 py-1.5 bg-brand-accent/10 border border-brand-accent/20 rounded-full text-sm font-medium text-cyan-700"
              >
                <svg class="w-3 h-3" viewBox="0 0 24 24" fill="currentColor"><circle cx="12" cy="12" r="4"/></svg>
                {{ food }}
              </span>
            </div>
            <p v-else class="text-slate-600 text-sm">Aucun aliment identifié.</p>

            <div v-if="photoResult.macros" class="grid grid-cols-2 sm:grid-cols-4 gap-4">
              <MacroCard label="Calories"  :value="photoResult.macros.calories"   unit="kcal" color="text-amber-600"  bg="bg-brand-warning/10" />
              <MacroCard label="Protéines" :value="photoResult.macros.protein_g"  unit="g"    color="text-brand-accent" bg="bg-brand-accent/10" />
              <MacroCard label="Glucides"  :value="photoResult.macros.carbs_g"    unit="g"    color="text-teal-600"   bg="bg-brand-success/10" />
              <MacroCard label="Lipides"   :value="photoResult.macros.fat_g"      unit="g"    color="text-violet-600" bg="bg-violet-100" />
            </div>
          </div>

          <AIAdviceCard v-if="photoResult.advice" title="Analyse nutritionnelle IA" :content="photoResult.advice" />
        </template>

        <AiRequestHistoryPanel
          v-if="activeUserId && auth.canUseAi"
          ref="photoHistoryRef"
          variant="user"
          :plan="auth.plan"
          :user-id="activeUserId"
          request-type="analyze_photo"
          title="Historique"
        />
      </template>

      <!-- ── Onglet plan repas ── -->
      <template v-else-if="currentUser && activeTab === 'meal'">
        <div class="card">
          <h2 class="text-xl font-bold text-brand-primary mb-2">Plan repas hebdomadaire</h2>
          <p class="text-sm text-slate-600 mb-6">
            Budget et allergies pris en compte pour un plan sur 7 jours adapté à
            <span class="font-medium text-brand-primary">{{ displayName }}</span>.
          </p>

          <div class="grid grid-cols-1 sm:grid-cols-2 gap-6">
            <div>
              <label class="label" for="meal-budget">Budget hebdomadaire (€)</label>
              <input
                id="meal-budget"
                v-model.number="mealForm.budgetEuros"
                type="number"
                min="10"
                max="500"
                step="5"
                class="input"
                :class="{ 'border-brand-error': mealFormError.budget }"
                placeholder="ex. 50"
              />
              <p v-if="mealFormError.budget" class="text-xs text-brand-error mt-1">{{ mealFormError.budget }}</p>
              <p v-else class="text-xs text-slate-500 mt-1">Entre 10 € et 500 € par semaine</p>
            </div>

            <div>
              <label class="label" for="meal-allergies-input">Allergies et intolérances</label>
              <div class="flex gap-2">
                <input
                  id="meal-allergies-input"
                  v-model.trim="allergyInput"
                  type="text"
                  class="input flex-1"
                  placeholder="ex. gluten"
                  maxlength="40"
                  @keydown.enter.prevent="addAllergy"
                />
                <button type="button" class="btn-secondary shrink-0" @click="addAllergy">Ajouter</button>
              </div>
              <div class="flex flex-wrap gap-2 mt-3">
                <button
                  v-for="preset in allergyPresets"
                  :key="preset"
                  type="button"
                  class="text-xs px-2.5 py-1 rounded-full border border-slate-200 text-slate-600 hover:border-brand-accent/50 hover:text-brand-primary transition-colors"
                  @click="addPresetAllergy(preset)"
                >
                  + {{ preset }}
                </button>
              </div>
            </div>
          </div>

          <div v-if="mealForm.allergies.length" class="flex flex-wrap gap-2 mt-4">
            <span
              v-for="item in mealForm.allergies"
              :key="item"
              class="inline-flex items-center gap-1.5 pl-3 pr-1.5 py-1 bg-amber-50 border border-amber-200 rounded-full text-sm text-amber-900"
            >
              {{ item }}
              <button
                type="button"
                class="w-6 h-6 rounded-full hover:bg-amber-100 flex items-center justify-center"
                :aria-label="`Retirer ${item}`"
                @click="removeAllergy(item)"
              >
                <span class="material-symbols-outlined text-[16px] leading-none">close</span>
              </button>
            </span>
          </div>
          <p v-else class="text-sm text-slate-500 mt-4">Aucune allergie renseignée — le plan inclura toutes les familles d'aliments.</p>

          <div class="mt-6 pt-5 border-t border-slate-100 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <p class="text-sm text-slate-600">
              <span class="font-medium text-brand-primary">{{ displayName }}</span>
              · {{ goalLabel(currentUser?.goal) }}
              · {{ mealForm.budgetEuros }} €/semaine
            </p>
            <button
              type="button"
              class="btn-primary shrink-0"
              :disabled="generatingMeal || !canSubmitMeal"
              @click="generateMealPlan"
            >
              <div v-if="generatingMeal" class="w-4 h-4 border-2 border-brand-primary border-t-transparent rounded-full animate-spin"></div>
              <span v-else class="material-symbols-outlined text-[18px] leading-none">auto_awesome</span>
              {{ generatingMeal ? 'Génération...' : 'Générer le plan repas' }}
            </button>
          </div>
        </div>

        <ErrorAlert v-if="mealPlanError" :message="mealPlanError" />

        <div v-if="mealPlan" class="card animate-slide-up">
          <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-5">
            <div>
              <h2 class="text-xl font-bold text-brand-primary">Votre plan repas</h2>
              <p class="text-sm text-slate-600 mt-0.5">
                {{ mealPlan.user_name }} · {{ mealForm.budgetEuros }} €/semaine
                <span v-if="mealForm.allergies.length"> · sans {{ mealForm.allergies.join(', ') }}</span>
              </p>
            </div>
            <button
              type="button"
              class="btn-secondary text-xs shrink-0"
              :disabled="generatingMeal"
              @click="generateMealPlan"
            >
              <span class="material-symbols-outlined text-[16px] leading-none">refresh</span>
              Régénérer
            </button>
          </div>
          <AIAdviceCard title="Plan repas IA (7 jours)" :content="mealPlan.plan" />
        </div>

        <AiRequestHistoryPanel
          v-if="activeUserId && auth.canUseAi"
          ref="mealHistoryRef"
          variant="user"
          :plan="auth.plan"
          :user-id="activeUserId"
          request-type="meal_plan"
          title="Historique"
        />
      </template>
    </template>
  </div>
</template>

<script setup>
import { ref, reactive, computed, defineComponent, h, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useUserStore } from '@/stores/userStore'
import { useAuthStore } from '@/stores/authStore'
import { useDashboardScope } from '@/composables/useDashboardScope'
import { useViewNav } from '@/composables/useViewNav'
import { useDisplayName } from '@/composables/useDisplayName'
import {
  getProfileEditPath,
  hasInvalidProfileData,
  getProfileIssues,
} from '@/composables/useProfileCompletion'
import { useAiGate, PLAN_AI_REQUIRED_MSG } from '@/composables/useAiAccess'
import { parseApiErrorDetail } from '@/composables/useBiometricValidation'
import { coachAPI, usersAPI } from '@/services/api'
import AdminUserTabs from '@/components/layout/AdminUserTabs.vue'
import LoadingSpinner from '@/components/ui/LoadingSpinner.vue'
import ErrorAlert from '@/components/ui/ErrorAlert.vue'
import AIAdviceCard from '@/components/ui/AIAdviceCard.vue'
import ProfileAiGate from '@/components/ui/ProfileAiGate.vue'
import AiRequestHistoryPanel from '@/components/admin/AiRequestHistoryPanel.vue'

const userStore = useUserStore()
const auth = useAuthStore()
const photoHistoryRef = ref(null)
const mealHistoryRef = ref(null)
const { isAdminScope } = useDashboardScope()
const route = useRoute()
const router = useRouter()
const activeUserId = ref(null)
const { onTouchStart, onTouchMove, onTouchEnd } = useViewNav(activeUserId)
const currentUser = ref(null)
const userLoading = ref(false)
const userError = ref('')

const activeTab = ref('photo')

const fileInput = ref(null)
const previewUrl = ref('')
const imageBase64 = ref('')
const dragOver = ref(false)
const analyzing = ref(false)
const photoError = ref('')
const photoResult = ref(null)

const mealForm = reactive({
  budgetEuros: 50,
  allergies: [],
})
const mealFormError = reactive({ budget: '' })
const allergyInput = ref('')
const allergyPresets = ['gluten', 'lactose', 'arachide', 'œuf', 'soja', 'fruits de mer']
const generatingMeal = ref(false)
const mealPlanError = ref('')
const mealPlan = ref(null)

const hasInvalidProfile = computed(() => hasInvalidProfileData(currentUser.value))
const profileEditPath = computed(() =>
  getProfileEditPath(activeUserId.value, { admin: isAdminScope.value })
)
const profileIssues = computed(() => getProfileIssues(currentUser.value))
const { profileBlocksAi, planBlocksAi, aiBlocked, aiGateTitle, aiGateDescription } =
  useAiGate(currentUser)
const displayName = useDisplayName(currentUser)

const pageSubtitle = computed(() => {
  if (isAdminScope.value) {
    return 'Consultation des historiques IA nutrition (photos et plans repas)'
  }
  if (aiBlocked.value) {
    if (planBlocksAi.value) {
      return activeTab.value === 'meal'
        ? 'Passez à Premium pour générer un plan repas IA'
        : 'Passez à Premium pour analyser vos repas par photo'
    }
    if (hasInvalidProfile.value) {
      return 'Corrigez votre profil pour activer les modules nutrition IA'
    }
    return 'Complétez votre profil pour activer les modules nutrition IA'
  }
  if (activeTab.value === 'meal') {
    return 'Plan hebdomadaire personnalisé selon budget, allergies et objectif'
  }
  return "Analysez un repas par photo grâce à l'IA vision"
})

const canSubmitMeal = computed(() => {
  const budget = Number(mealForm.budgetEuros)
  return Number.isFinite(budget) && budget >= 10 && budget <= 500
})

const goalLabels = {
  weight_loss: 'Perte de poids',
  muscle_gain: 'Prise de muscle',
  sleep_improvement: 'Améliorer le sommeil',
  maintenance: 'Maintien',
}

function goalLabel(goal) {
  return goalLabels[goal] || 'Objectif non défini'
}

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

function normalizeAllergy(value) {
  return value.trim().toLowerCase().replace(/\s+/g, ' ')
}

function addAllergy() {
  const value = normalizeAllergy(allergyInput.value)
  if (!value) return
  if (!mealForm.allergies.includes(value)) {
    mealForm.allergies.push(value)
  }
  allergyInput.value = ''
}

function addPresetAllergy(preset) {
  const value = normalizeAllergy(preset)
  if (!mealForm.allergies.includes(value)) {
    mealForm.allergies.push(value)
  }
}

function removeAllergy(item) {
  mealForm.allergies = mealForm.allergies.filter((a) => a !== item)
}

function validateMealForm() {
  mealFormError.budget = ''
  const budget = Number(mealForm.budgetEuros)
  if (!Number.isFinite(budget) || budget < 10 || budget > 500) {
    mealFormError.budget = 'Le budget doit être entre 10 € et 500 €.'
    return false
  }
  return true
}

function handleDrop(e) { dragOver.value = false; const f = e.dataTransfer.files[0]; if (f) loadFile(f) }
function handleFileChange(e) { const f = e.target.files[0]; if (f) loadFile(f) }

function loadFile(file) {
  if (!ALLOWED_IMAGE_TYPES.includes(file.type)) {
    photoError.value = 'Veuillez sélectionner une image JPEG, PNG, WebP ou GIF.'
    return
  }
  if (file.size > MAX_FILE_SIZE) {
    photoError.value = 'Fichier trop volumineux (max 10 Mo).'
    return
  }

  photoError.value = ''
  photoResult.value = null
  const reader = new FileReader()
  reader.onload = (ev) => {
    const bytes = new Uint8Array(ev.target.result)
    if (!isValidImageSignature(bytes)) {
      photoError.value = 'Le fichier ne correspond pas à une image valide.'
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
  previewUrl.value = ''
  imageBase64.value = ''
  photoResult.value = null
  photoError.value = ''
  if (fileInput.value) fileInput.value.value = ''
}

function parseUserIdFromRoute() {
  const parsed = Number(route.params.userId)
  return Number.isInteger(parsed) && parsed > 0 ? parsed : null
}

async function loadUserProfile() {
  if (!activeUserId.value) return
  userLoading.value = true
  userError.value = ''
  try {
    const res = await usersAPI.getById(activeUserId.value)
    currentUser.value = res.data
    userStore.selectUser(activeUserId.value)
    if (aiBlocked.value) {
      clearImage()
      mealPlan.value = null
    }
  } catch (e) {
    const detail = parseApiErrorDetail(e.response?.data?.detail)
    userError.value =
      detail ||
      (e.response?.status === 404
        ? 'Profil utilisateur introuvable.'
        : "Impossible de charger ce profil utilisateur.")
    currentUser.value = null
  } finally {
    userLoading.value = false
  }
}

function goToUsersList() {
  router.push(isAdminScope.value ? '/admin' : '/')
}

async function analyzePhoto() {
  if (!imageBase64.value || !activeUserId.value || aiBlocked.value) return
  analyzing.value = true
  photoError.value = ''
  photoResult.value = null
  try {
    const res = await coachAPI.analyzePhoto(activeUserId.value, imageBase64.value)
    photoResult.value = res.data
    photoHistoryRef.value?.reload()
  } catch (e) {
    const detail = parseApiErrorDetail(e.response?.data?.detail)
    const status = e.response?.status
    if (status === 403) {
      photoError.value = detail || PLAN_AI_REQUIRED_MSG
    } else if (status === 422) {
      photoError.value =
        detail ||
        "Cette image ne correspond pas à un repas. Choisissez une photo de votre assiette ou de vos aliments."
    } else if (status === 429) {
      photoError.value = detail || 'Quota atteint : 10 appels IA par heure.'
    } else {
      photoError.value =
        detail ||
        "Erreur lors de l'analyse. Vérifiez la connexion à l'API."
    }
  } finally {
    analyzing.value = false
  }
}

async function generateMealPlan() {
  if (!activeUserId.value || aiBlocked.value) return
  if (!validateMealForm()) return

  generatingMeal.value = true
  mealPlanError.value = ''
  mealPlan.value = null
  try {
    const res = await coachAPI.getMealPlan(
      activeUserId.value,
      Number(mealForm.budgetEuros),
      [...mealForm.allergies]
    )
    mealPlan.value = res.data
    mealHistoryRef.value?.reload()
  } catch (e) {
    const detail = parseApiErrorDetail(e.response?.data?.detail)
    const status = e.response?.status
    if (status === 403) {
      mealPlanError.value = detail || PLAN_AI_REQUIRED_MSG
    } else if (status === 422) {
      mealPlanError.value = detail || 'Profil incomplet ou données invalides.'
    } else if (status === 429) {
      mealPlanError.value = detail || 'Quota atteint : 10 appels IA par heure.'
    } else {
      mealPlanError.value =
        detail ||
        "Erreur lors de la génération du plan repas. Vérifiez la connexion à l'API."
    }
  } finally {
    generatingMeal.value = false
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

watch(() => route.params.userId, async () => {
  activeUserId.value = parseUserIdFromRoute()
  if (!activeUserId.value) {
    goToUsersList()
    return
  }
  await loadUserProfile()
}, { immediate: true })

watch(() => route.fullPath, async (path, prev) => {
  if (!activeUserId.value || !prev) return
  if (prev.includes('/profile') && !path.includes('/profile')) {
    await loadUserProfile()
  }
})
</script>

<style scoped>
.nutrition-nav-row {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

@media (min-width: 1024px) {
  .nutrition-nav-row {
    flex-direction: row;
    align-items: center;
    justify-content: space-between;
    gap: 1rem;
  }
}

.nutrition-module-nav {
  display: flex;
  flex-direction: column;
  gap: 0.375rem;
  width: 100%;
}

@media (min-width: 640px) {
  .nutrition-module-nav {
    flex-direction: row;
    align-items: center;
    gap: 0.625rem;
    width: auto;
    margin-left: auto;
  }
}

.nutrition-module-nav__label {
  font-size: 0.6875rem;
  font-weight: 600;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  color: #94a3b8;
  margin: 0;
  flex-shrink: 0;
}

.nutrition-tabs {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 0.25rem;
  padding: 0.25rem;
  width: 100%;
  background: white;
  border: 1px solid #e2e8f0;
  border-radius: 0.75rem;
  box-shadow: 0 1px 2px rgb(15 23 42 / 0.04);
}

@media (min-width: 640px) {
  .nutrition-tabs {
    display: inline-flex;
    width: auto;
  }
}

.nutrition-tabs__btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 0.375rem;
  padding: 0.5rem 0.875rem;
  border-radius: 0.5rem;
  font-size: 0.8125rem;
  font-weight: 600;
  color: #64748b;
  transition: background 0.15s, color 0.15s;
}

@media (min-width: 640px) {
  .nutrition-tabs__btn {
    font-size: 0.875rem;
    padding: 0.5rem 1rem;
  }
}

.nutrition-tabs__btn:hover:not(.nutrition-tabs__btn--active) {
  color: #0f172a;
  background: #f8fafc;
}

.nutrition-tabs__btn--active {
  background: #00b4d8;
  color: white;
}

.nutrition-tabs__btn:focus-visible {
  outline: 2px solid rgb(0 180 216 / 0.6);
  outline-offset: 2px;
}

@media (max-width: 380px) {
  .nutrition-tabs__text {
    font-size: 0.75rem;
  }
}
</style>
