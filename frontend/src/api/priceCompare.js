import http from './http'

export async function fetchPriceCompare(productId) {
  const response = await http.get('/api/price-compare', {
    params: {
      product_id: productId
    }
  })
  return response.data
}

