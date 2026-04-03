import { computed, ref } from 'vue'
import { defineStore } from 'pinia'

const TOKEN_STORAGE_KEY = 'se_slayers.auth.token'
const USER_STORAGE_KEY = 'se_slayers.auth.user'

const defaultHeaders = {
  'Content-Type': 'application/json',
}

const parseStoredUser = () => {
  const raw = localStorage.getItem(USER_STORAGE_KEY)
  if (!raw) return null

  try {
    return JSON.parse(raw)
  } catch {
    localStorage.removeItem(USER_STORAGE_KEY)
    return null
  }
}

const buildAuthHeaders = (token) => ({
  ...defaultHeaders,
  ...(token ? { Authorization: `Bearer ${token}` } : {}),
})

const readErrorMessage = async (response) => {
  try {
    const payload = await response.json()
    return payload.message || 'Something went wrong.'
  } catch {
    return 'Something went wrong.'
  }
}

const mergeHeaders = (options = {}, extraHeaders = {}) => ({
  ...(options.body ? defaultHeaders : {}),
  ...(options.headers || {}),
  ...extraHeaders,
})

export const defaultRouteForRole = (role) => role === 'admin' ? '/dashboard' : '/store'

export const useAuthStore = defineStore('auth', () => {
  const token = ref(localStorage.getItem(TOKEN_STORAGE_KEY) || '')
  const user = ref(parseStoredUser())
  const initialized = ref(false)
  const initializePromise = ref(null)

  const isAuthenticated = computed(() => Boolean(token.value && user.value))
  const role = computed(() => user.value?.role || null)

  const persistSession = (nextToken, nextUser) => {
    token.value = nextToken
    user.value = nextUser
    localStorage.setItem(TOKEN_STORAGE_KEY, nextToken)
    localStorage.setItem(USER_STORAGE_KEY, JSON.stringify(nextUser))
  }

  const clearSession = () => {
    token.value = ''
    user.value = null
    localStorage.removeItem(TOKEN_STORAGE_KEY)
    localStorage.removeItem(USER_STORAGE_KEY)
  }

  const request = async (path, options = {}) => {
    const response = await fetch(path, {
      ...options,
      headers: mergeHeaders(options),
    })

    if (!response.ok) {
      throw new Error(await readErrorMessage(response))
    }

    return response.status === 204 ? null : response.json()
  }

  const initialize = async () => {
    if (initialized.value) return
    if (!token.value) {
      clearSession()
      initialized.value = true
      return
    }

    if (!initializePromise.value) {
      initializePromise.value = request('/api/auth/me', {
        method: 'GET',
        headers: buildAuthHeaders(token.value),
      })
        .then((payload) => {
          user.value = payload.user
          localStorage.setItem(USER_STORAGE_KEY, JSON.stringify(payload.user))
        })
        .catch(() => {
          clearSession()
        })
        .finally(() => {
          initialized.value = true
          initializePromise.value = null
        })
    }

    await initializePromise.value
  }

  const login = async (email, password) => {
    const payload = await request('/api/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    })

    persistSession(payload.token, payload.user)
    initialized.value = true
    return payload.user
  }

  const register = async ({ full_name, email, password, contact }) => {
    const payload = await request('/api/auth/register', {
      method: 'POST',
      body: JSON.stringify({ full_name, email, password, contact }),
    })

    persistSession(payload.token, payload.user)
    initialized.value = true
    return payload.user
  }

  const logout = () => {
    clearSession()
    initialized.value = true
  }

  const authenticatedRequest = async (path, options = {}) => {
    await initialize()

    if (!token.value) {
      throw new Error('You are not authenticated.')
    }

    try {
      return await request(path, {
        ...options,
        headers: mergeHeaders(options, buildAuthHeaders(token.value)),
      })
    } catch (error) {
      if (
        error.message === 'Invalid authentication token.' ||
        error.message === 'Your session has expired. Please sign in again.' ||
        error.message === 'Missing authentication token.'
      ) {
        clearSession()
      }
      throw error
    }
  }

  return {
    token,
    user,
    role,
    initialized,
    isAuthenticated,
    initialize,
    login,
    register,
    logout,
    clearSession,
    authenticatedRequest,
    defaultRouteForRole,
  }
})
