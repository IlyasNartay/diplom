import { computed, ref } from 'vue'
import { defineStore } from 'pinia'

export const SESSION_KEY = 'ticketon-auth-session'

export function readAuthSession() {
  if (typeof window === 'undefined') {
    return null
  }

  try {
    const raw = window.localStorage.getItem(SESSION_KEY)
    return raw ? JSON.parse(raw) : null
  } catch {
    return null
  }
}

export function writeAuthSession(session) {
  if (typeof window === 'undefined') {
    return
  }
  window.localStorage.setItem(SESSION_KEY, JSON.stringify(session))
}

export function clearAuthSession() {
  if (typeof window === 'undefined') {
    return
  }
  window.localStorage.removeItem(SESSION_KEY)
}

export const useAuthStore = defineStore('auth', () => {
  const session = ref(readAuthSession())

  const isAuthenticated = computed(() => Boolean(session.value?.access_token))
  const accessToken = computed(() => session.value?.access_token || '')
  const refreshToken = computed(() => session.value?.refresh_token || '')
  const user = computed(() => ({
    user_id: session.value?.user_id || '',
    role: session.value?.role || 'user'
  }))

  function hydrate() {
    session.value = readAuthSession()
  }

  function setSession(payload) {
    session.value = payload
    writeAuthSession(payload)
  }

  function logout() {
    session.value = null
    clearAuthSession()
  }

  return {
    session,
    isAuthenticated,
    accessToken,
    refreshToken,
    user,
    hydrate,
    setSession,
    logout
  }
})
