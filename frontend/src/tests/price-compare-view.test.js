import { flushPromises, mount } from '@vue/test-utils'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { createMemoryHistory, createRouter } from 'vue-router'

import { routes } from '../router/index.js'
import PriceCompareView from '../views/customer/PriceCompareView.vue'

vi.mock('../api/priceCompare', () => ({
  fetchPriceCompare: vi.fn()
}))

vi.mock('../api/recommendation.js', () => ({
  fetchMyRecommendations: vi.fn(),
  fetchTrendProducts: vi.fn()
}))

import { fetchPriceCompare } from '../api/priceCompare'
import { fetchMyRecommendations, fetchTrendProducts } from '../api/recommendation.js'

function createTestRouter() {
  return createRouter({
    history: createMemoryHistory(),
    routes: [
      {
        path: '/customer/price-compare',
        name: 'customer-price-compare',
        component: PriceCompareView
      }
    ]
  })
}

describe('price compare route', () => {
  it('registers the price compare view under the customer route', () => {
    const appRoute = routes.find((route) => route.path === '/')
    const customerRoute = appRoute.children.find((route) => route.name === 'customer-price-compare')

    expect(customerRoute.path).toBe('customer/price-compare')
    expect(customerRoute.meta.roles).toEqual(['customer'])
  })
})

describe('PriceCompareView', () => {
  beforeEach(() => {
    vi.resetAllMocks()
    fetchMyRecommendations.mockResolvedValue({
      items: [{ product_id: 1, product_name: '轻量跑鞋', price: 299 }]
    })
    fetchTrendProducts.mockResolvedValue({
      items: [{ product_id: 2, product_name: '城市双肩包', price: 269 }]
    })
  })

  it('shows empty state when product id is missing', async () => {
    const router = createTestRouter()
    await router.push('/customer/price-compare')
    await router.isReady()

    const wrapper = mount(PriceCompareView, {
      global: {
        plugins: [router]
      }
    })

    await flushPromises()

    expect(wrapper.text()).toContain('请选择商品后点击查询')
    expect(fetchPriceCompare).not.toHaveBeenCalled()
  })

  it('renders offers and advice when product id exists', async () => {
    fetchPriceCompare.mockResolvedValue({
      product: {
        product_id: 1,
        name: '轻量跑鞋',
        price: 299,
        brand: '耐克',
        category: '运动鞋服',
        image_url: 'https://example.com/demo.png'
      },
      offers: [
        { platform: '抖音', price: 289.5, delivery_hint: '直播券', coupon_hint: '关注直播间福利' },
        { platform: '京东', price: 319.9, delivery_hint: '次日达/自营', coupon_hint: '可叠加满减券' }
      ],
      best: {
        platform: '抖音',
        price: 289.5,
        saving: 9.5
      },
      advice: '抖音 当前更便宜，预计可省 9.50 元'
    })

    const router = createTestRouter()
    await router.push('/customer/price-compare?product_id=1')
    await router.isReady()

    const wrapper = mount(PriceCompareView, {
      global: {
        plugins: [router]
      }
    })

    await flushPromises()

    expect(fetchPriceCompare).toHaveBeenCalledWith(1)
    expect(fetchMyRecommendations).toHaveBeenCalled()
    expect(fetchTrendProducts).toHaveBeenCalled()
    expect(wrapper.text()).toContain('轻量跑鞋')
    expect(wrapper.text()).toContain('抖音')
    expect(wrapper.text()).toContain('京东')
    expect(wrapper.text()).toContain('预计可省')
  })
})
