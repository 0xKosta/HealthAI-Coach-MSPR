<template>
  <div class="max-w-2xl mx-auto space-y-6 animate-fade-in">
    <div class="flex items-center justify-between gap-4">
      <div>
        <h1 class="text-3xl font-bold text-brand-primary">
          {{ isAdminEdit ? 'Modifier le profil' : 'Mon profil santé' }}
        </h1>
        <p class="text-slate-600 mt-1">
          <template v-if="isAdminEdit">
            {{ adminDisplayName || 'Utilisateur' }} — l'IMC est calculé automatiquement
          </template>
          <template v-else>
            Complétez vos informations - l'IMC est calculé automatiquement
          </template>
        </p>
      </div>
      <RouterLink :to="dashboardLink" class="btn-secondary">Retour</RouterLink>
    </div>

    <LoadingSpinner v-if="loading" message="Chargement du profil..." />
    <ErrorAlert v-else-if="loadError" :message="loadError" />

    <form v-else class="card space-y-6" @submit.prevent="onSubmit">
      <ProfileDataWarning
        v-if="loadedProfileIssues.length"
        :issues="loadedProfileIssues"
      />
      <ErrorAlert v-if="formError" :message="formError" />

      <div class="grid grid-cols-1 sm:grid-cols-2 gap-5">
        <!-- Âge -->
        <div>
          <label class="label" for="age">Âge</label>
          <input
            id="age"
            v-model.number="form.age"
            type="number"
            :min="limits.age.min"
            :max="limits.age.max"
            class="input"
            :class="{ 'border-brand-error': fieldErrors.age }"
            placeholder="ex. 30"
            @input="clearFieldError('age')"
          />
          <p v-if="fieldErrors.age" class="text-xs text-brand-error mt-1">{{ fieldErrors.age }}</p>
        </div>

        <!-- Genre -->
        <div>
          <label class="label" for="gender">Genre</label>
          <select id="gender" v-model="form.gender" class="select">
            <option :value="null">Non précisé</option>
            <option value="male">Homme</option>
            <option value="female">Femme</option>
            <option value="other">Autre</option>
          </select>
        </div>

        <!-- Poids -->
        <div>
          <label class="label" for="weight">Poids (kg)</label>
          <input
            id="weight"
            v-model.number="form.weight_kg"
            type="number"
            :min="limits.weight_kg.min"
            :max="limits.weight_kg.max"
            step="0.1"
            class="input"
            :class="{ 'border-brand-error': fieldErrors.weight_kg }"
            placeholder="ex. 68.5"
            @input="clearFieldError('weight_kg')"
          />
          <p v-if="fieldErrors.weight_kg" class="text-xs text-brand-error mt-1">{{ fieldErrors.weight_kg }}</p>
        </div>

        <!-- Taille -->
        <div>
          <label class="label" for="height">Taille (cm)</label>
          <input
            id="height"
            v-model.number="form.height_cm"
            type="number"
            :min="limits.height_cm.min"
            :max="limits.height_cm.max"
            step="0.1"
            class="input"
            :class="{ 'border-brand-error': fieldErrors.height_cm }"
            placeholder="ex. 172"
            @input="clearFieldError('height_cm')"
          />
          <p v-if="fieldErrors.height_cm" class="text-xs text-brand-error mt-1">{{ fieldErrors.height_cm }}</p>
        </div>

        <!-- Masse grasse -->
        <div>
          <label class="label" for="bodyfat">Masse grasse (%)<span class="text-slate-400 font-normal"> — optionnel</span></label>
          <input id="bodyfat" v-model.number="form.body_fat_pct" type="number" min="0" max="100" step="0.1" class="input" placeholder="ex. 22" />
        </div>

        <!-- Objectif -->
        <div>
          <label class="label" for="goal">Objectif</label>
          <select id="goal" v-model="form.goal" class="select">
            <option :value="null">Non défini</option>
            <option value="weight_loss">Perte de poids</option>
            <option value="muscle_gain">Prise de muscle</option>
            <option value="sleep_improvement">Améliorer le sommeil</option>
            <option value="maintenance">Maintien</option>
          </select>
        </div>
      </div>

      <p v-if="fieldErrors.bmi" class="text-sm text-brand-error">{{ fieldErrors.bmi }}</p>

      <!-- IMC calculé -->
      <div
        class="flex items-center justify-between rounded-xl bg-brand-light border px-4 py-3"
        :class="fieldErrors.bmi ? 'border-brand-error' : 'border-slate-200'"
      >
        <div>
          <p class="text-sm font-medium text-brand-primary">IMC (calculé automatiquement)</p>
          <p class="text-xs text-slate-500">Basé sur le poids et la taille</p>
        </div>
        <div class="text-right">
          <p class="text-2xl font-bold" :class="bmiColor">{{ bmi ?? '—' }}</p>
          <p v-if="bmiCategory" class="text-xs text-slate-600">{{ bmiCategory }}</p>
        </div>
      </div>

      <div class="flex justify-end gap-3 pt-2">
        <RouterLink :to="dashboardLink" class="btn-secondary">Annuler</RouterLink>
        <button type="submit" :disabled="saving || !isFormValid" class="btn-primary">
          <div v-if="saving" class="w-4 h-4 border-2 border-brand-primary border-t-transparent rounded-full animate-spin"></div>
          {{ saving ? 'Enregistrement...' : 'Enregistrer' }}
        </button>
      </div>
    </form>

    <!-- Zone de danger : compte utilisateur -->
    <div v-if="!loading && !isAdminEdit" class="card border-brand-error/30 bg-brand-error/5">
      <h2 class="text-lg font-bold text-brand-error">Supprimer mon compte</h2>
      <p class="text-sm text-slate-600 mt-1">
        Cette action est définitive. Toutes vos données seront supprimées et ne pourront pas être récupérées.
      </p>
      <button type="button" class="btn-danger mt-4" @click="confirmOpen = true">
        <span class="material-symbols-outlined text-[18px] leading-none">delete</span>
        Supprimer mon compte
      </button>
    </div>

    <!-- Zone de danger : profil admin (édition uniquement) -->
    <div v-if="!loading && isAdminEdit" class="card border-brand-error/30 bg-brand-error/5">
      <h2 class="text-lg font-bold text-brand-error">Supprimer ce profil</h2>
      <p class="text-sm text-slate-600 mt-1">
        Suppression définitive du profil santé, des mesures, séances et historique associés.
        <span v-if="hasLinkedAccount"> Le compte lié sera également supprimé.</span>
      </p>
      <button type="button" class="btn-danger mt-4" @click="confirmOpen = true">
        <span class="material-symbols-outlined text-[18px] leading-none">delete</span>
        Supprimer ce profil
      </button>
    </div>

    <!-- Modale de confirmation -->
    <div
      v-if="confirmOpen"
      class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50"
      @click.self="closeConfirm"
    >
      <div class="bg-white rounded-2xl shadow-xl max-w-md w-full p-6 space-y-4 animate-fade-in">
        <div class="flex items-center gap-3">
          <div class="w-11 h-11 rounded-xl bg-brand-error/10 flex items-center justify-center shrink-0">
            <span class="material-symbols-outlined text-brand-error">warning</span>
          </div>
          <h3 class="text-lg font-bold text-brand-primary">{{ confirmTitle }}</h3>
        </div>
        <p class="text-sm text-slate-600">
          <template v-if="isAdminEdit">
            La suppression de <strong>{{ adminDisplayName || `l'utilisateur #${targetUserId}` }}</strong> est
            <strong>définitive</strong>. Toutes les données santé (mesures, séances, historique) seront
            <strong>perdues</strong>.
          </template>
          <template v-else>
            La suppression est <strong>définitive</strong>. Toutes vos données (profil, mesures,
            séances, historique) seront <strong>perdues</strong> et ne pourront pas être récupérées.
          </template>
        </p>
        <ErrorAlert v-if="deleteError" :message="deleteError" />
        <div class="flex justify-end gap-3 pt-2">
          <button type="button" class="btn-secondary" :disabled="deleting" @click="closeConfirm">Annuler</button>
          <button type="button" class="btn-danger" :disabled="deleting" @click="onDelete">
            <div v-if="deleting" class="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
            {{ deleting ? 'Suppression...' : 'Supprimer définitivement' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { authAPI, usersAPI } from '@/services/api'
import { useAuthStore } from '@/stores/authStore'
import { formatProfileDisplayName } from '@/composables/useDisplayName'
import LoadingSpinner from '@/components/ui/LoadingSpinner.vue'
import ErrorAlert from '@/components/ui/ErrorAlert.vue'
import ProfileDataWarning from '@/components/ui/ProfileDataWarning.vue'
import {
  BIOMETRIC_LIMITS,
  computeBmi,
  validateBiometricForm,
  parseApiErrorDetail,
} from '@/composables/useBiometricValidation'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()

const isAdminEdit = computed(() => route.name === 'AdminProfile')

const targetUserId = computed(() => {
  if (!isAdminEdit.value) return null
  const id = Number(route.params.userId)
  return Number.isFinite(id) ? id : null
})

const loading = ref(true)
const loadError = ref('')
const saving = ref(false)
const formError = ref('')
const loadedProfileIssues = ref([])
const fieldErrors = reactive({})

const limits = BIOMETRIC_LIMITS

const confirmOpen = ref(false)
const deleting = ref(false)
const deleteError = ref('')

const profileName = ref('')
const adminDisplayName = ref('')
const hasLinkedAccount = ref(false)

const form = reactive({
  age: null,
  gender: null,
  weight_kg: null,
  height_cm: null,
  body_fat_pct: null,
  goal: null,
})

const dashboardLink = computed(() => {
  if (isAdminEdit.value && targetUserId.value) {
    return `/admin/dashboard/${targetUserId.value}`
  }
  return auth.profileId ? `/dashboard/${auth.profileId}` : '/'
})

const confirmTitle = computed(() =>
  isAdminEdit.value
    ? 'Supprimer ce profil ?'
    : 'Êtes-vous sûr de supprimer votre compte ?'
)

const bmi = computed(() => {
  const value = computeBmi(form.weight_kg, form.height_cm)
  return value != null ? value.toFixed(1) : null
})

const isFormValid = computed(() => {
  const { formError: err } = validateBiometricForm(form)
  return !err
})

const bmiCategory = computed(() => {
  if (bmi.value == null) return ''
  const b = Number(bmi.value)
  if (b < 18.5) return 'Insuffisant'
  if (b < 25) return 'Normal'
  if (b < 30) return 'Surpoids'
  return 'Obésité'
})

const bmiColor = computed(() => {
  if (bmi.value == null) return 'text-slate-400'
  const b = Number(bmi.value)
  if (b < 18.5) return 'text-brand-warning'
  if (b < 25) return 'text-teal-600'
  if (b < 30) return 'text-amber-600'
  return 'text-brand-error'
})

function clearFieldError(key) {
  delete fieldErrors[key]
  if (key === 'weight_kg' || key === 'height_cm') {
    delete fieldErrors.bmi
  }
}

function validate() {
  if (form.body_fat_pct != null && (form.body_fat_pct < 0 || form.body_fat_pct > 100)) {
    return 'La masse grasse doit être comprise entre 0 et 100.'
  }
  const result = validateBiometricForm(form)
  Object.keys(fieldErrors).forEach((k) => delete fieldErrors[k])
  Object.assign(fieldErrors, result.fieldErrors)
  return result.formError
}

function clean(value) {
  return value === '' || value === undefined || Number.isNaN(value) ? null : value
}

function applyProfileToForm(p) {
  form.age = p.age ?? null
  form.gender = p.gender ?? null
  form.weight_kg = p.weight_kg ?? null
  form.height_cm = p.height_cm ?? null
  form.body_fat_pct = p.body_fat_pct ?? null
  form.goal = p.goal ?? null
  loadedProfileIssues.value = Array.isArray(p.profile_issues) ? p.profile_issues : []
}

async function loadProfile() {
  loading.value = true
  loadError.value = ''
  try {
    if (isAdminEdit.value) {
      if (!targetUserId.value) {
        loadError.value = 'Identifiant utilisateur invalide.'
        return
      }
      const res = await usersAPI.getById(targetUserId.value)
      const p = res.data
      profileName.value = p.name
      adminDisplayName.value = formatProfileDisplayName(p)
      hasLinkedAccount.value = Boolean(p.first_name || p.last_name)
      applyProfileToForm(p)
    } else {
      const res = await authAPI.getProfile()
      applyProfileToForm(res.data)
    }
  } catch (e) {
    loadError.value =
      e.response?.status === 404
        ? (isAdminEdit.value ? 'Profil introuvable.' : "Aucun profil santé lié à ce compte.")
        : 'Impossible de charger le profil.'
  } finally {
    loading.value = false
  }
}

function buildPayload() {
  return {
    name: profileName.value.trim(),
    age: clean(form.age),
    gender: clean(form.gender),
    weight_kg: clean(form.weight_kg),
    height_cm: clean(form.height_cm),
    body_fat_pct: clean(form.body_fat_pct),
    goal: clean(form.goal),
  }
}

async function onSubmit() {
  formError.value = validate()
  if (formError.value) return

  saving.value = true
  try {
    loadedProfileIssues.value = []
    if (isAdminEdit.value) {
      await usersAPI.update(targetUserId.value, buildPayload())
    } else {
      await authAPI.updateProfile({
        age: clean(form.age),
        gender: clean(form.gender),
        weight_kg: clean(form.weight_kg),
        height_cm: clean(form.height_cm),
        body_fat_pct: clean(form.body_fat_pct),
        goal: clean(form.goal),
      })
    }
    router.push(dashboardLink.value)
  } catch (e) {
    const detail = e.response?.data?.detail
    formError.value =
      parseApiErrorDetail(detail) || "Erreur lors de l'enregistrement du profil."
  } finally {
    saving.value = false
  }
}

function closeConfirm() {
  if (deleting.value) return
  confirmOpen.value = false
  deleteError.value = ''
}

async function onDelete() {
  deleting.value = true
  deleteError.value = ''
  try {
    if (isAdminEdit.value) {
      await usersAPI.delete(targetUserId.value)
      router.push('/admin')
    } else {
      await authAPI.deleteAccount()
      auth.logout()
      router.push('/login')
    }
  } catch (e) {
    deleteError.value =
      e.response?.data?.detail ||
      (isAdminEdit.value
        ? 'Erreur lors de la suppression du profil.'
        : 'Erreur lors de la suppression du compte.')
    deleting.value = false
  }
}

watch(
  () => route.params.userId,
  () => {
    if (isAdminEdit.value) loadProfile()
  }
)

onMounted(loadProfile)
</script>
