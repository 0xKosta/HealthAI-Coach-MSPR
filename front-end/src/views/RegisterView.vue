<template>
  <div class="min-h-screen flex items-center justify-center bg-brand-light px-4 py-12">
    <div class="w-full max-w-md">
      <div class="flex justify-center mb-6 -mt-10">
        <img
          src="/healthai-coach-logo-horizontal-transparent-exact.svg"
          alt="HealthAI Coach"
          class="h-32 object-contain"
          @error="(e) => (e.target.style.display = 'none')"
        />
      </div>

      <div class="card">
        <h1 class="text-2xl font-bold text-brand-primary mb-1">Créer un compte</h1>
        <p class="text-slate-600 text-sm mb-6">Rejoignez votre coach santé personnalisé</p>

        <ErrorAlert v-if="auth.error" :message="auth.error" class="mb-4" />
        <ErrorAlert v-if="localError" :message="localError" class="mb-4" />

        <form class="space-y-4" @submit.prevent="onSubmit">
          <div class="grid grid-cols-2 gap-3">
            <div>
              <label class="label" for="first_name">Prénom</label>
              <input id="first_name" v-model.trim="form.first_name" type="text" required class="input" placeholder="Alice" />
            </div>
            <div>
              <label class="label" for="last_name">Nom</label>
              <input id="last_name" v-model.trim="form.last_name" type="text" required class="input" placeholder="Martin" />
            </div>
          </div>

          <div>
            <label class="label" for="email">Email</label>
            <input id="email" v-model.trim="form.email" type="email" autocomplete="email" required class="input" placeholder="vous@exemple.com" />
          </div>

          <div>
            <label class="label" for="password">Mot de passe</label>
            <input id="password" v-model="form.password" type="password" autocomplete="new-password" required minlength="6" class="input" placeholder="6 caractères minimum" />
          </div>

          <div>
            <label class="label" for="confirm">Confirmer le mot de passe</label>
            <input id="confirm" v-model="confirm" type="password" autocomplete="new-password" required class="input" placeholder="••••••••" />
          </div>

          <button type="submit" :disabled="auth.loading" class="btn-primary w-full justify-center">
            <div v-if="auth.loading" class="w-4 h-4 border-2 border-brand-primary border-t-transparent rounded-full animate-spin"></div>
            {{ auth.loading ? 'Création...' : 'Créer mon compte' }}
          </button>
        </form>

        <p class="text-sm text-slate-600 mt-6 text-center">
          Déjà inscrit ?
          <RouterLink to="/login" class="text-brand-accent font-medium hover:underline">Se connecter</RouterLink>
        </p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/authStore'
import { resolvePostAuthRoute } from '@/router/redirect'
import ErrorAlert from '@/components/ui/ErrorAlert.vue'

const auth = useAuthStore()
const router = useRouter()

const form = reactive({ first_name: '', last_name: '', email: '', password: '' })
const confirm = ref('')
const localError = ref('')

async function onSubmit() {
  localError.value = ''
  if (form.password !== confirm.value) {
    localError.value = 'Les mots de passe ne correspondent pas.'
    return
  }
  const ok = await auth.register({ ...form })
  if (!ok) return
  router.push(resolvePostAuthRoute(auth))
}
</script>
