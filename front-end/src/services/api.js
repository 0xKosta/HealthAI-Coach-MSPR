import axios from 'axios'
import { isNetworkFailure, useApiStatusStore } from '@/stores/apiStatusStore'

export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 60000,
  headers: { 'Content-Type': 'application/json' }
})

// Clé de stockage du token JWT (partagée avec authStore)
export const TOKEN_KEY = 'healthai_token'

// Attache automatiquement le token JWT à chaque requête sortante
api.interceptors.request.use((config) => {
  const token = localStorage.getItem(TOKEN_KEY)
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// Sur 401, on purge le token : la session est invalide ou expirée.
// La redirection vers /login est gérée par le guard de navigation.
// Absence de réponse (API arrêtée, réseau) → écran « serveur déconnecté ».
api.interceptors.response.use(
  (response) => {
    useApiStatusStore().markOnline()
    return response
  },
  (error) => {
    if (isNetworkFailure(error)) {
      useApiStatusStore().markOffline()
    }
    if (error.response?.status === 401) {
      localStorage.removeItem(TOKEN_KEY)
    }
    return Promise.reject(error)
  }
)

export const authAPI = {
  register: (data) => api.post('/auth/register', data),
  // /auth/login attend un form OAuth2 (username = email) - pas du JSON
  login: (email, password) => {
    const form = new URLSearchParams()
    form.append('username', email)
    form.append('password', password)
    return api.post('/auth/login', form, {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
    })
  },
  me: () => api.get('/auth/me'),
  updateMe: (data) => api.put('/auth/me', data),
  // Profil santé (table users) lié au compte connecté
  getProfile: () => api.get('/auth/me/profile'),
  updateProfile: (data) => api.put('/auth/me/profile', data),
  // Suppression définitive du compte (RGPD - droit à l'effacement)
  deleteAccount: () => api.delete('/auth/me'),
  adminCreateUser: (data) => api.post('/auth/admin/users', data),
  adminUpdateAccount: (profileUserId, data) =>
    api.put(`/auth/admin/users/${profileUserId}`, data),
}

export const usersAPI = {
  getAll: (params) => api.get('/users/', { params }),
  getById: (id) => api.get(`/users/${id}`),
  create: (data) => api.post('/users/', data),
  update: (id, data) => api.put(`/users/${id}`, data),
  delete: (id) => api.delete(`/users/${id}`),
}

export const nutritionAPI = {
  getAll: () => api.get('/nutrition/'),
  create: (data) => api.post('/nutrition/', data)
}

export const exercisesAPI = {
  getAll: () => api.get('/exercises/?limit=1000')
}

export const metricsAPI = {
  getByUser: (userId) => api.get(`/metrics/?user_id=${userId}`)
}

export const aiRequestsAPI = {
  listByUser: (userId, params = {}) =>
    api.get('/ai-requests/', { params: { user_id: userId, ...params } }),
}

export const postsAPI = {
  getFeed: (params = {}) => api.get('/posts/', { params }),
  create: (formData) =>
    api.post('/posts/', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    }),
  toggleLike: (postId) => api.post(`/posts/${postId}/like`),
  getComments: (postId) => api.get(`/posts/${postId}/comments`),
  addComment: (postId, content) =>
    api.post(`/posts/${postId}/comments`, { content }),
  deletePost: (postId) => api.delete(`/posts/${postId}`),
}

export const coachAPI = {
  getAdvice: (userId) => api.post('/coach/advice', { user_id: userId }),
  analyzePhoto: (userId, imageBase64) =>
    api.post('/coach/analyze-photo', { user_id: userId, image_base64: imageBase64 }),
  getWorkoutPlan: (userId, equipment, daysPerWeek) =>
    api.post('/coach/workout-plan', { user_id: userId, equipment, days_per_week: daysPerWeek }),
  getMealPlan: (userId, budgetEuros, allergies = []) =>
    api.post('/coach/meal-plan', {
      user_id: userId,
      budget_euros: budgetEuros,
      allergies,
    }),
  getBiometricTrend: (userId) =>
    api.post('/coach/biometric-trend', { user_id: userId })
}

export default api
