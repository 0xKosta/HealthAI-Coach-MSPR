<template>
  <div class="min-h-screen bg-brand-light">
    <Navbar v-if="showChrome" />
    <main :class="showChrome ? 'pt-20 pb-16 sm:pt-16 sm:pb-0' : ''">
      <div :class="showChrome ? 'max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8' : ''">
        <RouterView v-slot="{ Component }">
          <Transition :name="transitionName" mode="out-in">
            <component :is="Component" />
          </Transition>
        </RouterView>
      </div>
    </main>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import Navbar from '@/components/layout/Navbar.vue'
import { useAuthStore } from '@/stores/authStore'
import { transitionName } from '@/router/transition'

const route = useRoute()
const auth = useAuthStore()

// Pas de navbar sur les pages d'authentification ni l'écran "sans profil"
const showChrome = computed(
  () => auth.isAuthenticated && !route.meta.public && route.name !== 'NoProfile'
)
</script>

<style>
/* Seul le contenu central est animé : les navbars (fixed) restent intactes. */

/* Transition par défaut : léger fondu vertical */
.page-enter-active,
.page-leave-active {
  transition: opacity 0.2s ease, transform 0.2s ease;
}
.page-enter-from { opacity: 0; transform: translateY(8px); }
.page-leave-to   { opacity: 0; transform: translateY(-8px); }

/* Navigation entre vues partagées : glissement horizontal (suit le swipe) */
.slide-left-enter-active,
.slide-left-leave-active,
.slide-right-enter-active,
.slide-right-leave-active {
  transition: opacity 0.25s ease, transform 0.25s ease;
}
/* En avant : la nouvelle vue arrive de la droite, l'ancienne part à gauche */
.slide-left-enter-from { opacity: 0; transform: translateX(28px); }
.slide-left-leave-to   { opacity: 0; transform: translateX(-28px); }
/* En arrière : l'inverse */
.slide-right-enter-from { opacity: 0; transform: translateX(-28px); }
.slide-right-leave-to   { opacity: 0; transform: translateX(28px); }
</style>
