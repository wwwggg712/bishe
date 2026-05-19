import http from './http'

export async function fetchMerchantOpsOverview(params = {}) {
  const response = await http.get('/api/merchant/ops/overview', { params })
  return response.data
}

export async function deactivateMerchantProduct(productId) {
  const response = await http.post(`/api/merchant/products/${productId}/deactivate`)
  return response.data
}

