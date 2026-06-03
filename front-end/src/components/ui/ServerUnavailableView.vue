<template>
  <div
    class="fixed inset-0 z-[100] flex items-center justify-center bg-brand-light px-4 py-12"
    role="alert"
    aria-live="assertive"
  >
    <div class="w-full max-w-md text-center">
      <img
        src="/healthai-coach-logo-horizontal-transparent-exact.svg"
        alt="HealthAI Coach"
        class="h-24 mx-auto object-contain mb-8"
        @error="(e) => (e.target.style.display = 'none')"
      />

      <div class="card text-left">
        <div class="flex items-start gap-3 mb-4">
          <span class="material-symbols-outlined text-brand-error text-3xl shrink-0">cloud_off</span>
          <div>
            <h1 class="text-xl font-bold text-brand-primary">Serveur déconnecté</h1>
            <p class="text-slate-600 text-sm mt-1">{{ message }}</p>
          </div>
        </div>

        <button
          type="button"
          class="btn-primary w-full justify-center"
          :disabled="checking"
          @click="$emit('retry')"
        >
          <span
            v-if="checking"
            class="w-4 h-4 border-2 border-brand-primary border-t-transparent rounded-full animate-spin"
          />
          {{ checking ? 'Vérification…' : 'Réessayer' }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { OFFLINE_MESSAGE } from '@/stores/apiStatusStore'

defineProps({
  message: { type: String, default: OFFLINE_MESSAGE },
  checking: { type: Boolean, default: false },
})

defineEmits(['retry'])
</script>
