import http from './http'

export async function login(payload) {
  const response = await http.post('/api/auth/login', payload)
  return response.data
}

export async function fetchCurrentUser() {
  const response = await http.get('/api/auth/me')
  return response.data
}
