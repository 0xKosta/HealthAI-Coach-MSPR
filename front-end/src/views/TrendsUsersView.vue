<template>
  <div class="space-y-8 animate-fade-in" @touchstart.passive="onTouchStart" @touchend.passive="onTouchEnd">
    <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
      <div>
        <h1 class="text-3xl font-bold text-brand-primary">Utilisateurs (Admin)</h1>
        <p class="text-slate-600 mt-1">Sélectionnez un profil pour ouvrir son dashboard puis ses tendances biométriques</p>
      </div>
      <p class="text-sm text-slate-500">{{ totalUsers }} profils</p>
    </div>

    <div class="flex items-center">
      <div class="relative w-full sm:max-w-md">
        <svg class="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round">
          <circle cx="11" cy="11" r="8" />
          <path d="M21 21l-4.35-4.35" />
        </svg>
        <input
          v-model.trim="search"
          type="text"
          placeholder="Rechercher par nom ou prénom..."
          class="input h-10 pl-9 text-sm bg-white"
        />
      </div>
    </div>

    <LoadingSpinner v-if="loading" message="Chargement des personnes..." />
    <ErrorAlert v-else-if="error" :message="error" />

    <template v-else>
      <div v-if="users.length" class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <button
          v-for="user in users"
          :key="user.id"
          class="bg-white border border-slate-200 rounded-[2rem] text-left hover:border-brand-accent hover:shadow-md transition-all duration-200"
          @click="openDashboard(user.id)"
        >
          <div class="flex items-stretch min-h-[118px]">
            <div class="w-24 shrink-0 border-r border-slate-200 flex items-center justify-center rounded-l-[2rem] bg-slate-50">
              <div class="w-11 h-11 rounded-full flex items-center justify-center" :class="avatarBg(user.gender)">
                <svg
                  v-if="user.gender === 'female'"
                  class="w-6 h-6 text-pink-600"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  stroke-width="1.8"
                  stroke-linecap="round"
                >
                  <circle cx="12" cy="8" r="4" />
                  <path d="M12 12v9M9 18h6" />
                </svg>
                <svg
                  v-else
                  class="w-6 h-6 text-sky-700"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  stroke-width="1.8"
                  stroke-linecap="round"
                >
                  <circle cx="10" cy="14" r="5" />
                  <path d="M14 10l6-6M16 4h4v4" />
                </svg>
              </div>
            </div>
            <div class="px-4 py-4 flex flex-col justify-center min-w-0">
              <p class="font-semibold text-brand-primary truncate">{{ user.name }}</p>
              <p class="text-sm text-slate-500 mt-1">{{ user.gender ? genderLabel(user.gender) : 'Profil non renseigné' }}</p>
              <p class="text-sm text-slate-600 mt-2">
                <span class="font-medium text-slate-700">Objectif :</span> {{ goalLabel(user.goal) }}
              </p>
            </div>
          </div>
        </button>
      </div>

      <div v-else class="card text-center py-12">
        <p class="text-brand-secondary font-medium">Aucun profil utilisateur disponible</p>
      </div>

      <div v-if="totalPages > 1" class="flex flex-col items-center justify-center gap-2">
        <p class="text-xs text-slate-500 sm:hidden">Glisser gauche/droite pour changer de page</p>
        <div class="flex items-center justify-center gap-3">
        <button @click="goPrevPage" :disabled="currentPage === 1 || loading" class="btn-secondary px-3 py-1.5 text-sm disabled:opacity-40">
          ← Précédent
        </button>
        <span class="text-sm text-slate-600">Page {{ currentPage }} / {{ totalPages }}</span>
        <button @click="goNextPage" :disabled="currentPage === totalPages || loading" class="btn-secondary px-3 py-1.5 text-sm disabled:opacity-40">
          Suivant →
        </button>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '@/stores/userStore'
import { usersAPI } from '@/services/api'
import LoadingSpinner from '@/components/ui/LoadingSpinner.vue'
import ErrorAlert from '@/components/ui/ErrorAlert.vue'

const userStore = useUserStore()
const router = useRouter()
const currentPage = ref(1)
const PAGE_SIZE = 16
const users = ref([])
const totalUsers = ref(0)
const loading = ref(false)
const error = ref('')
const search = ref('')
const touchStart = ref({ x: 0, y: 0 })

const totalPages = computed(() => {
  const pages = Math.ceil(totalUsers.value / PAGE_SIZE)
  return Math.max(1, pages)
})

async function loadUsersPage() {
  loading.value = true
  error.value = ''
  try {
    const params = {
      skip: (currentPage.value - 1) * PAGE_SIZE,
      limit: PAGE_SIZE,
    }
    if (search.value) params.q = search.value
    const res = await usersAPI.getAll(params)
    users.value = res.data
    totalUsers.value = Number(res.headers['x-total-count'] ?? users.value.length)
    if (currentPage.value > totalPages.value) {
      currentPage.value = totalPages.value
    }
  } catch {
    error.value = 'Impossible de charger les profils utilisateurs.'
  } finally {
    loading.value = false
  }
}

function goPrevPage() {
  if (currentPage.value <= 1 || loading.value) return
  currentPage.value -= 1
}

function goNextPage() {
  if (currentPage.value >= totalPages.value || loading.value) return
  currentPage.value += 1
}

function onTouchStart(event) {
  const touch = event.changedTouches?.[0]
  if (!touch) return
  touchStart.value = { x: touch.clientX, y: touch.clientY }
}

function onTouchEnd(event) {
  const touch = event.changedTouches?.[0]
  if (!touch) return
  const dx = touch.clientX - touchStart.value.x
  const dy = touch.clientY - touchStart.value.y
  const isHorizontalSwipe = Math.abs(dx) > 55 && Math.abs(dx) > Math.abs(dy) * 1.2
  if (!isHorizontalSwipe) return
  if (dx < 0) {
    goNextPage()
  } else {
    goPrevPage()
  }
}

function openDashboard(userId) {
  userStore.selectUser(userId)
  router.push(`/admin/dashboard/${userId}`)
}

function avatarBg(gender) {
  if (gender === 'female') return 'bg-pink-100'
  if (gender === 'male') return 'bg-sky-100'
  return 'bg-slate-100'
}

function genderLabel(gender) {
  return {
    male: 'Homme',
    female: 'Femme',
    other: 'Autre',
  }[gender] || 'Non précisé'
}

function goalLabel(goal) {
  return {
    weight_loss: 'Perte de poids',
    muscle_gain: 'Prise de muscle',
    sleep_improvement: 'Améliorer le sommeil',
    maintenance: 'Maintien',
  }[goal] || 'Non défini'
}

onMounted(async () => {
  await loadUsersPage()
})

watch(currentPage, loadUsersPage)
watch(search, () => {
  if (currentPage.value !== 1) {
    currentPage.value = 1
    return
  }
  loadUsersPage()
})
</script>
