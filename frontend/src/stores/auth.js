import { defineStore } from 'pinia'

import { fetchCurrentUser, login as loginRequest } from '../api/auth'
import { clearStoredSession, readStoredSession, writeStoredSession } from '../api/http'

const initialSession = readStoredSession()

export const useAuthStore = defineStore('auth', {
  state: () => ({
    token: initialSession.token,
    user: initialSession.user
  }),
  getters: {
    isAuthenticated: (state) => Boolean(state.token),
    role: (state) => state.user?.role || ''
  },
  actions: {
    setSession(payload) {
      this.token = payload.token || ''
      this.user = payload.user || null
      writeStoredSession({
        token: this.token,
        user: this.user
      })
    },
    clearSession() {
      this.token = ''
      this.user = null
      clearStoredSession()
    },
    async login(credentials) {
      const payload = await loginRequest(credentials)
      this.setSession(payload)
      return payload
    },
    async hydrateUser() {
      if (!this.token) {
        return null
      }

      const payload = await fetchCurrentUser()
      this.setSession({
        token: this.token,
        user: payload.user
      })
      return payload.user
    }
  }
})
