<template>
  <div
    v-if="visible"
    class="rounded-xl border border-brand-accent/30 bg-brand-accent/10 px-4 py-3 flex flex-col sm:flex-row sm:items-center gap-3"
    role="region"
    aria-label="Installer l'application"
  >
    <div class="flex-1 text-sm text-slate-700">
      <p class="font-semibold text-brand-primary">Installer HealthAI Coach</p>
      <p v-if="isIos" class="mt-1">
        Sur iPhone : touchez
        <span class="font-medium">Partager</span>
        puis
        <span class="font-medium">Sur l'écran d'accueil</span>.
      </p>
      <p v-else class="mt-1">
        Ajoutez l'app à votre écran d'accueil pour une expérience plein écran (Android / iOS).
      </p>
    </div>
    <div class="flex gap-2 shrink-0">
      <button
        v-if="canInstall"
        type="button"
        class="btn-primary text-sm"
        @click="install"
      >
        Installer
      </button>
      <button
        type="button"
        class="btn-secondary text-sm"
        aria-label="Masquer l'invite d'installation"
        @click="dismiss"
      >
        Plus tard
      </button>
    </div>
  </div>
</template>

<script setup>
import { onMounted, onUnmounted, ref } from 'vue'

const DISMISS_KEY = 'healthai_pwa_install_dismissed'

const visible = ref(false)
const canInstall = ref(false)
const isIos = ref(false)
let deferredPrompt = null

function isStandalone() {
  return (
    window.matchMedia('(display-mode: standalone)').matches ||
    window.navigator.standalone === true
  )
}

function detectIos() {
  return /iphone|ipad|ipod/i.test(navigator.userAgent)
}

function dismiss() {
  localStorage.setItem(DISMISS_KEY, '1')
  visible.value = false
}

async function install() {
  if (!deferredPrompt) return
  deferredPrompt.prompt()
  await deferredPrompt.userChoice
  deferredPrompt = null
  canInstall.value = false
  visible.value = false
}

function onBeforeInstallPrompt(event) {
  event.preventDefault()
  deferredPrompt = event
  canInstall.value = true
  if (!localStorage.getItem(DISMISS_KEY) && !isStandalone()) {
    visible.value = true
  }
}

onMounted(() => {
  isIos.value = detectIos()
  if (isStandalone() || localStorage.getItem(DISMISS_KEY)) return
  if (isIos.value) {
    visible.value = true
    return
  }
  window.addEventListener('beforeinstallprompt', onBeforeInstallPrompt)
})

onUnmounted(() => {
  window.removeEventListener('beforeinstallprompt', onBeforeInstallPrompt)
})
</script>
