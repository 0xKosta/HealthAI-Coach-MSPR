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
        <h1 class="text-2xl font-bold text-brand-primary mb-1">Connexion</h1>
        <p class="text-slate-600 text-sm mb-6">Accédez à votre espace santé personnalisé</p>

        <ErrorAlert v-if="auth.error" :message="auth.error" class="mb-4" />

        <form class="space-y-4" @submit.prevent="onSubmit">
          <div>
            <label class="label" for="email">Email</label>
            <input
              id="email"
              v-model.trim="email"
              type="email"
              autocomplete="email"
              required
              class="input"
              placeholder="vous@exemple.com"
            />
          </div>

          <div>
            <label class="label" for="password">Mot de passe</label>
            <input
              id="password"
              v-model="password"
              type="password"
              autocomplete="current-password"
              required
              class="input"
              placeholder="••••••••"
            />
          </div>

          <button type="submit" :disabled="auth.loading" class="btn-primary w-full justify-center">
            <div v-if="auth.loading" class="w-4 h-4 border-2 border-brand-primary border-t-transparent rounded-full animate-spin"></div>
            {{ auth.loading ? 'Connexion...' : 'Se connecter' }}
          </button>
        </form>

        <p class="text-sm text-slate-600 mt-6 text-center">
          Pas encore de compte ?
          <RouterLink to="/register" class="text-brand-accent font-medium hover:underline">Créer un compte</RouterLink>
        </p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/authStore'
import { resolvePostAuthRoute } from '@/router/redirect'
import ErrorAlert from '@/components/ui/ErrorAlert.vue'

const auth = useAuthStore()
const router = useRouter()
const route = useRoute()

const email = ref('')
const password = ref('')

async function onSubmit() {
  const ok = await auth.login(email.value, password.value)
  if (!ok) return
  const redirect = typeof route.query.redirect === 'string' ? route.query.redirect : null
  router.push(redirect || resolvePostAuthRoute(auth))
}
</script>
