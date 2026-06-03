import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { authAPI, TOKEN_KEY } from '@/services/api'
import { isNetworkFailure, OFFLINE_MESSAGE } from '@/stores/apiStatusStore'

export const useAuthStore = defineStore('auth', () => {
  const token = ref(localStorage.getItem(TOKEN_KEY) || '')
  const currentUser = ref(null)
  const loading = ref(false)
  const error = ref('')

  const isAuthenticated = computed(() => !!token.value)
  const isAdmin = computed(() => currentUser.value?.role === 'admin')
  const canUseAi = computed(() => !!currentUser.value?.can_use_ai)
  const plan = computed(() => currentUser.value?.plan ?? 'free')
  // Profil santé lié (users.id) - cible du dashboard utilisateur
  const profileId = computed(() => currentUser.value?.user_id ?? null)

  function setToken(value) {
    token.value = value || ''
    if (value) {
      localStorage.setItem(TOKEN_KEY, value)
    } else {
      localStorage.removeItem(TOKEN_KEY)
    }
  }

  async function login(email, password) {
    loading.value = true
    error.value = ''
    try {
      const res = await authAPI.login(email, password)
      setToken(res.data.access_token)
      await fetchMe()
      return true
    } catch (e) {
      error.value = isNetworkFailure(e)
        ? OFFLINE_MESSAGE
        : e.response?.status === 401
          ? 'Email ou mot de passe incorrect.'
          : "Erreur de connexion. Vérifiez l'API."
      setToken('')
      currentUser.value = null
      return false
    } finally {
      loading.value = false
    }
  }

  async function register(payload) {
    loading.value = true
    error.value = ''
    try {
      const res = await authAPI.register(payload)
      setToken(res.data.access_token)
      await fetchMe()
      return true
    } catch (e) {
      error.value = isNetworkFailure(e)
        ? OFFLINE_MESSAGE
        : e.response?.status === 409
          ? 'Un compte existe déjà avec cet email.'
          : "Impossible de créer le compte. Vérifiez les champs."
      setToken('')
      currentUser.value = null
      return false
    } finally {
      loading.value = false
    }
  }

  async function fetchMe() {
    if (!token.value) {
      currentUser.value = null
      return null
    }
    try {
      const res = await authAPI.me()
      currentUser.value = res.data
      return res.data
    } catch {
      // Token invalide/expiré → on déconnecte proprement
      setToken('')
      currentUser.value = null
      return null
    }
  }

  function logout() {
    setToken('')
    currentUser.value = null
  }

  return {
    token,
    currentUser,
    loading,
    error,
    isAuthenticated,
    isAdmin,
    canUseAi,
    plan,
    profileId,
    login,
    register,
    fetchMe,
    logout,
  }
})
