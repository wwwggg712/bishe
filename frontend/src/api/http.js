import axios from 'axios'

export const AUTH_STORAGE_KEY = 'ecommerce-intelligent-analysis-auth'

export function readStoredSession() {
  if (typeof window === 'undefined') {
    return { token: '', user: null }
  }

  try {
    const raw = window.localStorage.getItem(AUTH_STORAGE_KEY)

    if (!raw) {
      return { token: '', user: null }
    }

    const parsed = JSON.parse(raw)

    return {
      token: parsed.token || '',
      user: parsed.user || null
    }
  } catch {
    return { token: '', user: null }
  }
}

export function writeStoredSession(session) {
  if (typeof window === 'undefined') {
    return
  }

  window.localStorage.setItem(AUTH_STORAGE_KEY, JSON.stringify(session))
}

export function clearStoredSession() {
  if (typeof window === 'undefined') {
    return
  }

  window.localStorage.removeItem(AUTH_STORAGE_KEY)
}

export function attachAuthToken(config, token) {
  const nextConfig = {
    ...config,
    headers: {
      ...(config.headers || {})
    }
  }

  if (token) {
    nextConfig.headers.Authorization = `Bearer ${token}`
  }

  return nextConfig
}

export function resolveApiBaseUrl() {
  return import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:5000'
}

const http = axios.create({
  baseURL: resolveApiBaseUrl(),
  timeout: 10000
})

http.interceptors.request.use((config) => {
  const { token } = readStoredSession()
  return attachAuthToken(config, token)
})

http.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error?.response?.status === 401) {
      clearStoredSession()
    }

    return Promise.reject(error)
  }
)

export default http
