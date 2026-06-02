<template>
  <div class="space-y-8 animate-fade-in" @touchstart.passive="onTouchStart" @touchend.passive="onTouchEnd">
    <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
      <div>
        <h1 class="text-3xl font-bold text-brand-primary">Utilisateurs (Admin)</h1>
        <p class="text-slate-600 mt-1">Sélectionnez un profil pour ouvrir son dashboard puis ses tendances biométriques</p>
      </div>
      <div class="flex flex-wrap items-center gap-3 shrink-0">
        <p class="text-sm text-slate-500">{{ totalUsers }} profils</p>
        <RouterLink to="/admin/users/new" class="btn-primary">
          <span class="material-symbols-outlined text-[18px] leading-none">person_add</span>
          Ajouter un utilisateur
        </RouterLink>
      </div>
    </div>

    <div class="flex flex-col sm:flex-row sm:flex-wrap sm:items-center gap-3">
      <div class="relative flex-1 sm:max-w-md min-w-[200px]">
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

      <div class="relative sm:w-44">
        <select v-model="filterPlan" class="select h-10 text-sm appearance-none pr-9 bg-white">
          <option value="">Tous les plans</option>
          <option value="free">Gratuit</option>
          <option value="premium">Premium</option>
          <option value="premium_plus">Premium+</option>
        </select>
        <svg class="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400 pointer-events-none" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><polyline points="6 9 12 15 18 9"/></svg>
      </div>

      <div class="relative sm:w-52">
        <select v-model="filterDate" class="select h-10 text-sm appearance-none pr-9 bg-white">
          <option value="id_asc">Toutes les dates</option>
          <option value="created_desc">Plus récents</option>
          <option value="created_asc">Plus anciens</option>
        </select>
        <svg class="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400 pointer-events-none" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><polyline points="6 9 12 15 18 9"/></svg>
      </div>

      <div class="view-toggle shrink-0 sm:ml-auto" role="group" aria-label="Mode d'affichage">
        <button
          type="button"
          class="view-btn"
          :class="viewMode === 'grid' ? 'view-btn--active' : ''"
          title="Vue grille — 9 profils par page"
          @click="setViewMode('grid')"
        >
          <svg class="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><rect x="3" y="3" width="7" height="7" rx="1"/><rect x="14" y="3" width="7" height="7" rx="1"/><rect x="3" y="14" width="7" height="7" rx="1"/><rect x="14" y="14" width="7" height="7" rx="1"/></svg>
          <span class="hidden sm:inline">Grille</span>
        </button>
        <button
          type="button"
          class="view-btn"
          :class="viewMode === 'list' ? 'view-btn--active' : ''"
          title="Vue liste — 50 profils par page"
          @click="setViewMode('list')"
        >
          <svg class="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M8 6h13M8 12h13M8 18h13M3 6h.01M3 12h.01M3 18h.01"/></svg>
          <span class="hidden sm:inline">Liste</span>
        </button>
      </div>
    </div>

    <LoadingSpinner v-if="loading" message="Chargement des personnes..." />
    <ErrorAlert v-else-if="error" :message="error" />

    <template v-else>
      <!-- Vue grille -->
      <div
        v-if="users.length && viewMode === 'grid'"
        class="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-3 gap-4 lg:gap-5"
      >
        <button
          v-for="user in users"
          :key="user.id"
          type="button"
          class="user-card group"
          @click="openDashboard(user.id)"
        >
          <div class="user-card__header" :class="cardHeaderClass(user.gender)">
            <div class="user-card__header-pattern" aria-hidden="true"></div>
            <PlanBadgeLight
              v-if="user.plan"
              :plan="user.plan"
              :role="user.role || 'user'"
              size="md"
              class="absolute top-2.5 right-2.5 z-10"
            />
          </div>

          <div class="user-card__body">
            <div
              class="user-card__avatar"
              :class="avatarBg(user.gender)"
            >
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

            <p class="user-card__name">
              {{ formatProfileDisplayName(user) }}
            </p>

            <div class="user-card__chips">
              <span class="user-chip user-chip--muted">
                {{ user.gender ? genderLabel(user.gender) : 'Profil incomplet' }}
              </span>
              <span class="user-chip" :class="goalChipClass(user.goal)">
                {{ goalLabel(user.goal) }}
              </span>
            </div>

            <div class="user-card__footer">
              <span class="user-card__date">
                <span class="material-symbols-outlined text-[15px] leading-none opacity-70">calendar_today</span>
                {{ formatCreatedAt(user.created_at) }}
              </span>
              <span class="user-card__cta">
                Ouvrir
                <svg class="w-3.5 h-3.5 transition-transform group-hover:translate-x-0.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"><path d="M5 12h14M13 6l6 6-6 6"/></svg>
              </span>
            </div>
          </div>
        </button>
      </div>

      <!-- Vue liste -->
      <div v-else-if="users.length && viewMode === 'list'" class="card overflow-hidden p-0">
        <div
          class="hidden lg:grid lg:grid-cols-[2.5rem_minmax(0,1.4fr)_5.5rem_minmax(0,1fr)_7rem_5.5rem_2.5rem_1.25rem] gap-3 px-4 py-2.5 bg-slate-50 border-b border-slate-200 text-[11px] font-semibold text-slate-500 uppercase tracking-wide"
        >
          <span aria-hidden="true"></span>
          <span>Nom</span>
          <span>Genre</span>
          <span>Objectif</span>
          <span>Plan</span>
          <span>Créé le</span>
          <span class="text-center">Modifier</span>
          <span aria-hidden="true"></span>
        </div>

        <button
          v-for="user in users"
          :key="user.id"
          type="button"
          class="w-full text-left border-b border-slate-100 last:border-b-0 hover:bg-slate-50 transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-inset focus-visible:ring-brand-accent/40"
          @click="openDashboard(user.id)"
        >
          <!-- Desktop -->
          <div
            class="hidden lg:grid lg:grid-cols-[2.5rem_minmax(0,1.4fr)_5.5rem_minmax(0,1fr)_7rem_5.5rem_2.5rem_1.25rem] gap-3 items-center px-4 py-3"
          >
            <div
              class="w-8 h-8 rounded-full flex items-center justify-center shrink-0"
              :class="avatarBg(user.gender)"
            >
              <svg
                v-if="user.gender === 'female'"
                class="w-4 h-4 text-pink-600"
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
                class="w-4 h-4 text-sky-700"
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
            <p class="font-medium text-brand-primary truncate">
              {{ formatProfileDisplayName(user) }}
            </p>
            <p class="text-sm text-slate-500 truncate">
              {{ user.gender ? genderLabel(user.gender) : '—' }}
            </p>
            <p class="text-sm text-slate-600 truncate">
              {{ goalLabel(user.goal) }}
            </p>
            <div class="flex items-center min-w-0">
              <PlanBadgeLight
                v-if="user.plan"
                :plan="user.plan"
                :role="user.role || 'user'"
              />
              <span v-else class="text-xs text-slate-400">—</span>
            </div>
            <p class="text-sm text-slate-500 tabular-nums">
              {{ formatCreatedAt(user.created_at) }}
            </p>
            <button
              type="button"
              class="list-edit-btn justify-self-center"
              title="Modifier le profil"
              :aria-label="`Modifier le profil de ${formatProfileDisplayName(user)}`"
              @click.stop="openProfileEdit(user.id)"
            >
              <span class="material-symbols-outlined text-[20px] leading-none">edit</span>
            </button>
            <svg class="w-4 h-4 text-slate-400 justify-self-end" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><polyline points="9 18 15 12 9 6"/></svg>
          </div>

          <!-- Mobile -->
          <div class="flex items-center gap-3 px-4 py-3 lg:hidden">
            <div
              class="w-8 h-8 rounded-full flex items-center justify-center shrink-0"
              :class="avatarBg(user.gender)"
            >
              <svg
                v-if="user.gender === 'female'"
                class="w-4 h-4 text-pink-600"
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
                class="w-4 h-4 text-sky-700"
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
            <div class="min-w-0 flex-1">
              <p class="font-medium text-brand-primary truncate">
                {{ formatProfileDisplayName(user) }}
              </p>
              <p class="text-xs text-slate-500 mt-0.5 truncate">
                {{ user.gender ? genderLabel(user.gender) : 'Profil non renseigné' }}
                · {{ goalLabel(user.goal) }}
                · {{ formatCreatedAt(user.created_at) }}
              </p>
            </div>
            <PlanBadgeLight
              v-if="user.plan"
              :plan="user.plan"
              :role="user.role || 'user'"
              class="shrink-0"
            />
            <button
              type="button"
              class="list-edit-btn shrink-0"
              title="Modifier le profil"
              aria-label="Modifier le profil"
              @click.stop="openProfileEdit(user.id)"
            >
              <span class="material-symbols-outlined text-[20px] leading-none">edit</span>
            </button>
            <svg class="w-4 h-4 text-slate-400 shrink-0" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><polyline points="9 18 15 12 9 6"/></svg>
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
        <span class="text-sm text-slate-600">
          Page {{ currentPage }} / {{ totalPages }}
          <span class="text-slate-400">· {{ pageSize }}/page</span>
        </span>
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
import PlanBadgeLight from '@/components/ui/PlanBadgeLight.vue'
import { formatProfileDisplayName } from '@/composables/useDisplayName'

const userStore = useUserStore()
const router = useRouter()
const VIEW_MODE_KEY = 'healthai-admin-users-view-mode'

function readStoredViewMode() {
  const stored = localStorage.getItem(VIEW_MODE_KEY)
  return stored === 'list' || stored === 'grid' ? stored : 'grid'
}

const currentPage = ref(1)
const viewMode = ref(readStoredViewMode())
const PAGE_SIZE_GRID = 9
const PAGE_SIZE_LIST = 50
const users = ref([])
const totalUsers = ref(0)
const loading = ref(false)
const error = ref('')
const search = ref('')
const filterPlan = ref('')
const filterDate = ref('id_asc')
const touchStart = ref({ x: 0, y: 0 })

const pageSize = computed(() => (viewMode.value === 'list' ? PAGE_SIZE_LIST : PAGE_SIZE_GRID))

const totalPages = computed(() => {
  const pages = Math.ceil(totalUsers.value / pageSize.value)
  return Math.max(1, pages)
})

function setViewMode(mode) {
  if (viewMode.value === mode) return
  viewMode.value = mode
  localStorage.setItem(VIEW_MODE_KEY, mode)
  currentPage.value = 1
  loadUsersPage()
}

async function loadUsersPage() {
  loading.value = true
  error.value = ''
  try {
    const params = {
      skip: (currentPage.value - 1) * pageSize.value,
      limit: pageSize.value,
    }
    if (search.value) params.q = search.value
    if (filterPlan.value) params.plan = filterPlan.value
    if (filterDate.value) params.sort = filterDate.value
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

function openProfileEdit(userId) {
  userStore.selectUser(userId)
  router.push(`/admin/dashboard/${userId}/profile`)
}

function avatarBg(gender) {
  if (gender === 'female') return 'bg-pink-100'
  if (gender === 'male') return 'bg-sky-100'
  return 'bg-slate-100'
}

function cardHeaderClass(gender) {
  if (gender === 'female') return 'user-card__header--female'
  if (gender === 'male') return 'user-card__header--male'
  return 'user-card__header--neutral'
}

function goalChipClass(goal) {
  return {
    weight_loss: 'user-chip--rose',
    muscle_gain: 'user-chip--amber',
    sleep_improvement: 'user-chip--indigo',
    maintenance: 'user-chip--teal',
  }[goal] || 'user-chip--slate'
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

function formatCreatedAt(dateStr) {
  if (!dateStr) return '—'
  return new Intl.DateTimeFormat('fr-FR', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
  }).format(new Date(dateStr))
}

onMounted(async () => {
  await loadUsersPage()
})

watch(currentPage, loadUsersPage)
watch([search, filterPlan, filterDate], () => {
  if (currentPage.value !== 1) {
    currentPage.value = 1
    return
  }
  loadUsersPage()
})
</script>

<style scoped>
.list-edit-btn {
  @apply inline-flex items-center justify-center p-1.5 rounded-lg text-slate-500
         hover:text-brand-accent hover:bg-brand-accent/10 transition-colors
         focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-accent/40;
}

.view-toggle {
  @apply inline-flex rounded-xl border border-slate-200 bg-white p-1 gap-0.5;
}

.view-btn {
  @apply inline-flex items-center gap-1.5 px-3 py-2 rounded-lg text-sm font-medium text-slate-600
         hover:bg-slate-50 transition-colors;
}

.view-btn--active {
  @apply bg-brand-accent text-white hover:bg-brand-accent;
}

/* Cartes utilisateur — cover + avatar overlap (tendance admin 2025/26) */
.user-card {
  @apply relative overflow-hidden rounded-2xl border border-slate-200/90 bg-white text-left
         shadow-sm transition-all duration-300 ease-out
         focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-accent/40;
}

.user-card:hover {
  @apply border-brand-accent/35 shadow-lg shadow-brand-accent/[0.08] -translate-y-1;
}

.user-card__header {
  @apply relative h-[3.75rem];
}

.user-card__header-pattern {
  @apply absolute inset-0 opacity-[0.35];
  background-image: radial-gradient(circle at 20% 80%, rgba(255, 255, 255, 0.9) 0%, transparent 45%),
    radial-gradient(circle at 85% 15%, rgba(255, 255, 255, 0.55) 0%, transparent 40%);
}

.user-card__header--male {
  background: linear-gradient(135deg, #dbeafe 0%, #7dd3fc 52%, #0284c7 100%);
}

.user-card__header--female {
  background: linear-gradient(135deg, #fce7f3 0%, #f9a8d4 52%, #db2777 100%);
}

.user-card__header--neutral {
  background: linear-gradient(135deg, #f1f5f9 0%, #cbd5e1 52%, #64748b 100%);
}

.user-card__body {
  @apply relative px-4 pb-4 pt-0 text-center;
}

.user-card__avatar {
  @apply -mt-7 mx-auto flex h-[3.25rem] w-[3.25rem] items-center justify-center rounded-2xl
         ring-[3px] ring-white shadow-md transition-transform duration-300 group-hover:scale-105;
}

.user-card__name {
  @apply mt-3 font-semibold text-brand-primary leading-snug line-clamp-2 text-[15px];
}

.user-card__chips {
  @apply mt-2.5 flex flex-wrap items-center justify-center gap-1.5;
}

.user-chip {
  @apply inline-flex max-w-[9.5rem] truncate rounded-full px-2.5 py-0.5 text-[11px] font-medium;
}

.user-chip--muted {
  @apply bg-slate-100 text-slate-600 text-[10px] font-semibold uppercase tracking-wide;
}

.user-chip--rose {
  @apply bg-rose-50 text-rose-700 ring-1 ring-rose-100;
}

.user-chip--amber {
  @apply bg-amber-50 text-amber-800 ring-1 ring-amber-100;
}

.user-chip--indigo {
  @apply bg-indigo-50 text-indigo-700 ring-1 ring-indigo-100;
}

.user-chip--teal {
  @apply bg-teal-50 text-teal-700 ring-1 ring-teal-100;
}

.user-chip--slate {
  @apply bg-slate-50 text-slate-500 ring-1 ring-slate-100;
}

.user-card__footer {
  @apply mt-4 flex items-center justify-between gap-2 border-t border-slate-100 pt-3;
}

.user-card__date {
  @apply inline-flex items-center gap-1 text-[11px] text-slate-400 tabular-nums;
}

.user-card__cta {
  @apply inline-flex items-center gap-0.5 text-[11px] font-semibold text-brand-accent
         opacity-0 translate-x-1 transition-all duration-300 group-hover:opacity-100 group-hover:translate-x-0;
}
</style>
