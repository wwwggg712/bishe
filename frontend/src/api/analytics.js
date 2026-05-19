import http from './http'

export async function fetchOverview() {
  const response = await http.get('/api/analytics/overview')
  return response.data
}

export async function fetchFunnel() {
  const response = await http.get('/api/analytics/funnel')
  return response.data
}

export async function fetchRegions() {
  const response = await http.get('/api/analytics/regions')
  return response.data
}

export async function fetchCategories() {
  const response = await http.get('/api/analytics/categories')
  return response.data
}

export async function fetchBrands(params = {}) {
  const response = await http.get('/api/analytics/brands', { params })
  return response.data
}

export async function fetchHotProducts() {
  const response = await http.get('/api/analytics/products/hot')
  return response.data
}

export async function fetchColdProducts() {
  const response = await http.get('/api/analytics/products/cold')
  return response.data
}

export async function fetchUserRfm() {
  const response = await http.get('/api/analytics/users/rfm')
  return response.data
}

export async function fetchMerchantUserBehavior() {
  const response = await http.get('/api/analytics/merchant/user-behavior')
  return response.data
}

export async function fetchMerchantStrategy() {
  const response = await http.get('/api/strategy/merchant')
  return response.data
}

export async function fetchPredictionAnomalies(params = {}) {
  const response = await http.get('/api/prediction/anomalies', { params })
  return response.data
}

export async function fetchMerchantBrief(payload) {
  const response = await http.post('/api/llm/report', payload, {
    timeout: 12000
  })
  return response.data
}

export async function fetchMerchantAiAnalysis(payload) {
  const response = await http.post('/api/llm/report', {
    scene: 'merchant',
    ...payload
  }, {
    timeout: 25000
  })
  return response.data
}

export async function fetchMerchantActionSummary() {
  const response = await http.get('/api/strategy/actions/summary')
  return response.data
}

export async function recordMerchantAction(payload) {
  const response = await http.post('/api/strategy/actions', payload)
  return response.data
}
