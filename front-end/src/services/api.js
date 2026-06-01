import axios from 'axios'

const api = axios.create({
  baseURL: 'http://localhost:8000',
  timeout: 60000,
  headers: { 'Content-Type': 'application/json' }
})

export const usersAPI = {
  getAll: (params) => api.get('/users/', { params }),
  getById: (id) => api.get(`/users/${id}`)
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

export const coachAPI = {
  getAdvice: (userId) => api.post('/coach/advice', { user_id: userId }),
  analyzePhoto: (userId, imageBase64) =>
    api.post('/coach/analyze-photo', { user_id: userId, image_base64: imageBase64 }),
  getWorkoutPlan: (userId, equipment, daysPerWeek) =>
    api.post('/coach/workout-plan', { user_id: userId, equipment, days_per_week: daysPerWeek }),
  getBiometricTrend: (userId) =>
    api.post('/coach/biometric-trend', { user_id: userId })
}

export default api
