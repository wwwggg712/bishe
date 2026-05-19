import http from './http'

export async function fetchMerchantChartShare(params = {}) {
  const response = await http.get('/api/merchant/charts/share', { params })
  return response.data
}

export async function fetchMerchantChartTrend(params = {}) {
  const response = await http.get('/api/merchant/charts/trend', { params })
  return response.data
}

