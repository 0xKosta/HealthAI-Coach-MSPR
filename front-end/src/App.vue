<template>
  <div class="min-h-screen bg-brand-light">
    <Navbar v-if="showChrome" />
    <main :class="showChrome ? 'pt-20 pb-16 sm:pt-16 sm:pb-0' : ''">
      <div :class="showChrome ? 'max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8' : ''">
        <RouterView v-slot="{ Component }">
          <Transition name="page" mode="out-in">
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

const route = useRoute()
const auth = useAuthStore()

// Pas de navbar sur les pages d'authentification ni l'écran "sans profil"
const showChrome = computed(
  () => auth.isAuthenticated && !route.meta.public && route.name !== 'NoProfile'
)
</script>

<style>
.page-enter-active,
.page-leave-active {
  transition: opacity 0.2s ease, transform 0.2s ease;
}
.page-enter-from { opacity: 0; transform: translateY(8px); }
.page-leave-to   { opacity: 0; transform: translateY(-8px); }
</style>
