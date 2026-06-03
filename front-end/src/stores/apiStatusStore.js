import { defineStore } from 'pinia'
import { ref } from 'vue'
import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

export const OFFLINE_MESSAGE =
  'Le serveur est momentanément indisponible. Merci de patienter ou de réessayer plus tard.'

export function isNetworkFailure(error) {
  if (!error || error.response) return false
  const code = error.code
  return (
    code === 'ERR_NETWORK' ||
    code === 'ECONNABORTED' ||
    error.message === 'Network Error'
  )
}

export const useApiStatusStore = defineStore('apiStatus', () => {
  const online = ref(true)
  const checking = ref(false)
  let pollTimer = null

  function markOffline() {
    online.value = false
  }

  function markOnline() {
    online.value = true
  }

  async function checkHealth() {
    checking.value = true
    try {
      await axios.get(`${API_BASE_URL}/health`, { timeout: 5000 })
      markOnline()
      return true
    } catch {
      markOffline()
      return false
    } finally {
      checking.value = false
    }
  }

  function startPolling(intervalMs = 20000) {
    stopPolling()
    void checkHealth()
    pollTimer = setInterval(() => {
      void checkHealth()
    }, intervalMs)
  }

  function stopPolling() {
    if (pollTimer) {
      clearInterval(pollTimer)
      pollTimer = null
    }
  }

  return {
    online,
    checking,
    markOffline,
    markOnline,
    checkHealth,
    startPolling,
    stopPolling,
  }
})
