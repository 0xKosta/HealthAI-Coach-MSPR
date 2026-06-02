<template>
  <div class="max-w-2xl mx-auto space-y-6 animate-fade-in">
    <div class="flex items-center justify-between gap-4">
      <div>
        <h1 class="text-3xl font-bold text-brand-primary">Nouvel utilisateur</h1>
        <p class="text-slate-600 mt-1">
          Créez le compte (prénom, nom, email) — le profil santé se complète ensuite, comme après une inscription
        </p>
      </div>
      <RouterLink to="/admin" class="btn-secondary">Retour</RouterLink>
    </div>

    <form class="card space-y-6" @submit.prevent="onSubmit">
      <ErrorAlert v-if="formError" :message="formError" />

      <div class="grid grid-cols-1 sm:grid-cols-2 gap-5">
        <div>
          <label class="label" for="first_name">Prénom</label>
          <input
            id="first_name"
            v-model.trim="form.first_name"
            type="text"
            required
            maxlength="50"
            class="input"
            placeholder="ex. Alice"
          />
        </div>
        <div>
          <label class="label" for="last_name">Nom</label>
          <input
            id="last_name"
            v-model.trim="form.last_name"
            type="text"
            required
            maxlength="50"
            class="input"
            placeholder="ex. Martin"
          />
        </div>
        <div class="sm:col-span-2">
          <label class="label" for="email">Email</label>
          <input
            id="email"
            v-model.trim="form.email"
            type="email"
            autocomplete="off"
            required
            class="input"
            placeholder="utilisateur@exemple.com"
          />
        </div>
        <div>
          <label class="label" for="password">Mot de passe</label>
          <input
            id="password"
            v-model="form.password"
            type="password"
            autocomplete="new-password"
            required
            minlength="6"
            class="input"
            placeholder="6 caractères minimum"
          />
        </div>
        <div>
          <label class="label" for="confirm">Confirmer le mot de passe</label>
          <input
            id="confirm"
            v-model="confirmPassword"
            type="password"
            autocomplete="new-password"
            required
            class="input"
            placeholder="••••••••"
          />
        </div>
      </div>

      <p class="text-sm text-slate-500 rounded-xl bg-slate-50 border border-slate-200 px-4 py-3">
        Un profil santé vide sera créé automatiquement. Vous pourrez renseigner âge, poids, taille et objectif
        depuis le dashboard admin ou l'utilisateur pourra les compléter à la connexion.
      </p>

      <div class="flex justify-end gap-3 pt-2">
        <RouterLink to="/admin" class="btn-secondary">Annuler</RouterLink>
        <button type="submit" :disabled="saving || !canSubmit" class="btn-primary">
          <div v-if="saving" class="w-4 h-4 border-2 border-brand-primary border-t-transparent rounded-full animate-spin"></div>
          {{ saving ? 'Création...' : "Créer l'utilisateur" }}
        </button>
      </div>
    </form>
  </div>
</template>

<script setup>
import { ref, reactive, computed } from 'vue'
import { useRouter } from 'vue-router'
import { authAPI } from '@/services/api'
import { useUserStore } from '@/stores/userStore'
import ErrorAlert from '@/components/ui/ErrorAlert.vue'
import { parseApiErrorDetail } from '@/composables/useBiometricValidation'

const router = useRouter()
const userStore = useUserStore()

const form = reactive({
  first_name: '',
  last_name: '',
  email: '',
  password: '',
})
const confirmPassword = ref('')
const saving = ref(false)
const formError = ref('')

const canSubmit = computed(() =>
  Boolean(
    form.first_name.trim() &&
      form.last_name.trim() &&
      form.email.trim() &&
      form.password.length >= 6 &&
      confirmPassword.value
  )
)

async function onSubmit() {
  formError.value = ''
  if (form.password !== confirmPassword.value) {
    formError.value = 'Les mots de passe ne correspondent pas.'
    return
  }

  saving.value = true
  try {
    const res = await authAPI.adminCreateUser({
      first_name: form.first_name,
      last_name: form.last_name,
      email: form.email,
      password: form.password,
    })
    const profileId = res.data.user_id
    userStore.selectUser(profileId)
    router.push(`/admin/dashboard/${profileId}`)
  } catch (e) {
    const detail = e.response?.data?.detail
    formError.value =
      parseApiErrorDetail(detail) || "Erreur lors de la création de l'utilisateur."
  } finally {
    saving.value = false
  }
}
</script>
