import http from './http.js'

export async function fetchMyRecommendations() {
  const response = await http.get('/api/recommendations/me')
  return response.data
}

export async function fetchTrendProducts() {
  const response = await http.get('/api/prediction/trends')
  return {
    ...response.data,
    items: (response.data.items || []).filter((item) => item.trend_label === 'up').slice(0, 5)
  }
}

export async function fetchPreferenceProfile() {
  const response = await http.get('/api/users/portrait')
  return response.data
}

export async function fetchCustomerAiExplanation(payload) {
  const response = await http.post('/api/llm/report', {
    scene: 'customer',
    ...payload
  })
  return response.data
}

export async function recordCustomerAction(payload) {
  const response = await http.post('/api/recommendations/actions', payload)
  return response.data
}
