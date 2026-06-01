import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { usersAPI } from '@/services/api'

export const useUserStore = defineStore('user', () => {
  const users = ref([])
  const selectedUserId = ref(null)
  const loading = ref(false)
  const error = ref(null)

  const selectedUser = computed(() =>
    users.value.find(u => u.id === selectedUserId.value) || null
  )

  async function fetchUsers() {
    loading.value = true
    error.value = null
    try {
      const res = await usersAPI.getAll()
      users.value = [...res.data].sort((a, b) => a.id - b.id)
      if (users.value.length && !selectedUserId.value) {
        selectedUserId.value = users.value[0].id
      }
    } catch (e) {
      error.value = 'Impossible de charger les utilisateurs.'
    } finally {
      loading.value = false
    }
  }

  function selectUser(id) {
    selectedUserId.value = id
  }

  return { users, selectedUserId, selectedUser, loading, error, fetchUsers, selectUser }
})
