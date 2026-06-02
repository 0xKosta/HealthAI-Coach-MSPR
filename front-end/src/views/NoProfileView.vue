<template>
  <div class="max-w-lg mx-auto">
    <div class="card text-center py-12">
      <div class="w-16 h-16 mx-auto rounded-2xl bg-brand-warning/15 border border-brand-warning/30 flex items-center justify-center mb-5">
        <svg class="w-8 h-8 text-amber-600" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round">
          <circle cx="12" cy="12" r="10" /><path d="M12 8v4M12 16h.01" />
        </svg>
      </div>
      <h1 class="text-2xl font-bold text-brand-primary mb-2">Profil santé non configuré</h1>
      <p class="text-slate-600 mb-1">
        Bonjour {{ auth.currentUser?.first_name }}, votre compte est bien créé.
      </p>
      <p class="text-slate-600 mb-6">
        Aucun profil santé n'est encore associé à ce compte. Le dashboard
        personnalisé sera disponible une fois votre profil santé renseigné.
      </p>
      <button class="btn-secondary" @click="auth.logout(); $router.push('/login')">
        Se déconnecter
      </button>
    </div>
  </div>
</template>

<script setup>
import { useAuthStore } from '@/stores/authStore'
const auth = useAuthStore()
</script>
