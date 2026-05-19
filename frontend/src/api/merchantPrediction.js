import http from './http'

export async function fetchMerchantSalesForecast(params = {}) {
  const response = await http.get('/api/merchant/prediction/sales-forecast', { params })
  return response.data
}
