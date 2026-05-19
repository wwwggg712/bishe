import { flushPromises, mount } from '@vue/test-utils'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { routes } from '../router/index.js'
import CustomerHome from '../views/customer/CustomerHome.vue'

function mountCustomerHome() {
  return mount(CustomerHome, {
    global: {
      stubs: {
        RouterLink: {
          props: ['to'],
          template: '<a><slot /></a>'
        }
      }
    }
  })
}

vi.mock('../api/recommendation.js', () => ({
  fetchMyRecommendations: vi.fn(),
  fetchTrendProducts: vi.fn(),
  fetchPreferenceProfile: vi.fn(),
  fetchCustomerAiExplanation: vi.fn(),
  recordCustomerAction: vi.fn()
}))

import {
  fetchMyRecommendations,
  fetchCustomerAiExplanation,
  fetchPreferenceProfile,
  fetchTrendProducts,
  recordCustomerAction
} from '../api/recommendation.js'

describe('customer home route', () => {
  it('registers the customer home view under the customer route', () => {
    const appRoute = routes.find((route) => route.path === '/')
    const customerRoute = appRoute.children.find((route) => route.name === 'customer-home')

    expect(customerRoute.component).toBe(CustomerHome)
    expect(customerRoute.meta.roles).toEqual(['customer'])
  })
})

describe('customer home', () => {
  beforeEach(() => {
    vi.resetAllMocks()
    fetchMyRecommendations.mockResolvedValue({
      items: [
        {
          product_id: 1,
          product_name: '轻量跑鞋',
          category: '运动鞋服',
          reason: '该商品属于你偏好的 运动鞋服 类目，且近期热度表现较好'
        }
      ]
    })
    fetchTrendProducts.mockResolvedValue({
      items: [
        {
          product_id: 2,
          product_name: '城市双肩包',
          current_score: 128,
          delta: 42,
          trend_label: 'up'
        }
      ]
    })
    fetchPreferenceProfile.mockResolvedValue({
      user: {
        nickname: '小林',
        region: '华东'
      },
      top_categories: [
        { category: '智能设备', count: 4, score: 26 },
        { category: '运动鞋服', count: 3, score: 11 }
      ],
      top_actions: [
        { action_type: 'purchase', count: 2, score: 16 },
        { action_type: 'click', count: 2, score: 4 }
      ],
      recent_activity: [
        { log_id: 'r1', product_name: '智能手表', action_type: 'purchase', timestamp: '2026-05-12T10:00:00' }
      ],
      engagement_score: 37,
      top_active_hours: [
        { hour: 20, count: 3 },
        { hour: 21, count: 2 }
      ],
      price_preference: {
        average_price: 332.5,
        price_band: '中高消费偏好'
      },
      profile_tags: ['智能设备偏好', '20点活跃', '中高消费偏好']
    })
    fetchCustomerAiExplanation.mockResolvedValue({
      summary: 'AI 判断你最近更偏好运动鞋服与中高消费区间，轻量跑鞋与城市双肩包值得继续关注。',
      mode: 'fallback',
      provider: 'internal',
      model: 'rule-based-fallback'
    })
    recordCustomerAction.mockResolvedValue({
      message: '用户行为记录成功',
      log: { product_id: 1, action_type: 'favorite' }
    })
  })

  it('renders recommendations, trend products and preference profile sections', async () => {
    const wrapper = mountCustomerHome()

    await flushPromises()

    expect(wrapper.text()).toContain('猜你喜欢')
    expect(wrapper.text()).toContain('趋势上升商品')
    expect(wrapper.text()).toContain('我的偏好画像')
    expect(wrapper.text()).toContain('轻量跑鞋')
    expect(wrapper.text()).toContain('城市双肩包')
    expect(wrapper.text()).toContain('智能设备')
    expect(wrapper.text()).toContain('中高消费偏好')
    expect(wrapper.text()).toContain('20点')
    expect(wrapper.text()).toContain('37')
  })

  it('stays in cold start when only simulated history exists for the user', async () => {
    fetchMyRecommendations.mockResolvedValue({
      mode: 'fallback',
      items: [
        {
          product_id: 1,
          product_name: '轻量跑鞋',
          category: '运动鞋',
          reason: '该商品近期热度较高，适合作为当前阶段的冷启动推荐'
        }
      ]
    })
    fetchPreferenceProfile.mockResolvedValue({
      user: { nickname: '小林', region: '华东' },
      is_cold_start: true,
      top_categories: [],
      top_actions: [],
      recent_activity: [],
      engagement_score: 0,
      top_active_hours: [],
      price_preference: { average_price: 0, price_band: '暂无数据' },
      profile_tags: []
    })

    const wrapper = mountCustomerHome()
    await flushPromises()

    expect(wrapper.text()).toContain('冷启动推荐')
    expect(wrapper.text()).toContain('冷启动用户')
    expect(wrapper.text()).toContain('最近 5 条画像依据')
    expect(wrapper.text()).toContain('当前暂无历史个人行为记录。')
  })

  it('renders customer ai explanation entry and result', async () => {
    const wrapper = mountCustomerHome()

    await flushPromises()

    expect(wrapper.text()).toContain('AI 推荐解释')
    expect(wrapper.text()).toContain('生成 AI 推荐解释')
    expect(wrapper.text()).not.toContain('你最近更偏好运动鞋服与中高消费区间')

    await wrapper.find('button[data-testid="customer-ai-generate"]').trigger('click')
    await flushPromises()

    expect(wrapper.text()).toContain('你最近更偏好运动鞋服与中高消费区间')
    expect(wrapper.text()).toContain('当前模式：内置回退')
    expect(wrapper.text()).toContain('模型来源：internal')
    expect(wrapper.text()).toContain('模型名称：rule-based-fallback')
  })

  it('renders cold-start portrait copy and fallback recommendations when no personal behavior exists', async () => {
    fetchMyRecommendations.mockResolvedValue({
      mode: 'fallback',
      items: [
        {
          product_id: 1,
          product_name: '轻量跑鞋',
          category: '运动鞋',
          reason: '该商品近期热度较高，适合作为当前阶段的冷启动推荐'
        }
      ]
    })
    fetchPreferenceProfile.mockResolvedValue({
      user: { nickname: '小林', region: '华东' },
      is_cold_start: true,
      top_categories: [],
      top_actions: [],
      recent_activity: [],
      engagement_score: 0,
      top_active_hours: [],
      price_preference: { average_price: 0, price_band: '暂无数据' },
      profile_tags: []
    })

    const wrapper = mountCustomerHome()
    await flushPromises()

    expect(wrapper.text()).toContain('冷启动推荐')
    expect(wrapper.text()).toContain('当前暂无足够个人行为，先为你展示热门趋势商品。')
    expect(wrapper.text()).toContain('冷启动用户')
    expect(wrapper.text()).toContain('暂无个人行为，当前仅展示基础账号信息。')
    expect(wrapper.text()).toContain('暂无个人行为')
  })

  it('keeps ai explanation available during cold start with safe fallback payload', async () => {
    fetchMyRecommendations.mockResolvedValue({
      mode: 'fallback',
      items: []
    })
    fetchPreferenceProfile.mockResolvedValue({
      user: { nickname: '小林', region: '华东' },
      is_cold_start: true,
      top_categories: [],
      top_actions: [],
      recent_activity: [],
      engagement_score: 0,
      top_active_hours: [],
      price_preference: { average_price: 0, price_band: '暂无数据' },
      profile_tags: []
    })

    const wrapper = mountCustomerHome()
    await flushPromises()

    await wrapper.find('button[data-testid="customer-ai-generate"]').trigger('click')
    await flushPromises()

    expect(fetchCustomerAiExplanation).toHaveBeenCalledWith({
      product_name: '热门趋势商品',
      trend_product_name: '城市双肩包',
      preferred_category: '暂无个人偏好',
      price_band: '暂无数据',
      active_hour: '暂无个人活跃时段'
    })
  })

  it('renders session activity panel and recent personal activity panel', async () => {
    fetchPreferenceProfile.mockResolvedValue({
      user: { nickname: '小林', region: '华东' },
      is_cold_start: false,
      top_categories: [{ category: '运动服饰', count: 2, score: 6 }],
      top_actions: [{ action_type: 'favorite', count: 1, score: 3 }],
      recent_activity: [
        {
          log_id: 'r-1',
          product_id: 2,
          product_name: '透气训练T恤',
          category: '运动服饰',
          action_type: 'favorite',
          timestamp: '2026-05-13T10:20:00'
        }
      ],
      engagement_score: 3,
      top_active_hours: [{ hour: 20, count: 1 }],
      price_preference: { average_price: 129, price_band: '大众消费偏好' },
      profile_tags: ['运动服饰偏好']
    })

    const wrapper = mountCustomerHome()
    await flushPromises()

    expect(wrapper.text()).toContain('本次会话刚刚操作')
    expect(wrapper.text()).toContain('最近 5 条画像依据')
    expect(wrapper.text()).toContain('这些是系统用于生成历史画像的个人日志，不等同于你本次演示里刚刚点击的操作。')
    expect(wrapper.text()).toContain('透气训练T恤')
    expect(wrapper.text()).toContain('收藏')
  })

  it('shows freshly recorded actions in the session activity panel', async () => {
    fetchMyRecommendations
      .mockResolvedValueOnce({
        mode: 'fallback',
        items: [
          {
            product_id: 1,
            product_name: '轻量跑鞋',
            category: '运动鞋',
            reason: '该商品近期热度较高，适合作为当前阶段的冷启动推荐'
          }
        ]
      })
      .mockResolvedValueOnce({
        mode: 'personalized',
        items: [
          {
            product_id: 2,
            product_name: '透气训练T恤',
            category: '运动服饰',
            reason: '该商品属于你偏好的 运动服饰 类目，且近期热度表现较好'
          }
        ]
      })

    fetchPreferenceProfile
      .mockResolvedValueOnce({
        user: { nickname: '小林', region: '华东' },
        is_cold_start: true,
        top_categories: [],
        top_actions: [],
        recent_activity: [],
        engagement_score: 0,
        top_active_hours: [],
        price_preference: { average_price: 0, price_band: '暂无数据' },
        profile_tags: []
      })
      .mockResolvedValueOnce({
        user: { nickname: '小林', region: '华东' },
        is_cold_start: false,
        top_categories: [{ category: '运动鞋', count: 1, score: 3 }],
        top_actions: [{ action_type: 'favorite', count: 1, score: 3 }],
        recent_activity: [
          {
            log_id: 'r-2',
            product_id: 1,
            product_name: '轻量跑鞋',
            category: '运动鞋',
            action_type: 'favorite',
            timestamp: '2026-05-13T10:30:00'
          }
        ],
        engagement_score: 3,
        top_active_hours: [{ hour: 20, count: 1 }],
        price_preference: { average_price: 299, price_band: '中高消费偏好' },
        profile_tags: ['运动鞋偏好']
      })

    const wrapper = mountCustomerHome()
    await flushPromises()

    expect(wrapper.text()).toContain('你还没有进行操作')

    await wrapper.find('button[data-testid="customer-action-favorite-1"]').trigger('click')
    await flushPromises()

    expect(wrapper.text()).toContain('轻量跑鞋')
    expect(wrapper.text()).toContain('刚刚')
    expect(wrapper.text()).toContain('收藏')
    expect(wrapper.text()).toContain('最近 5 条画像依据')
  })

  it('records customer actions and refreshes recommendation data', async () => {
    fetchMyRecommendations
      .mockResolvedValueOnce({
        mode: 'fallback',
        items: [
          {
            product_id: 1,
            product_name: '轻量跑鞋',
            category: '运动鞋',
            reason: '该商品近期热度较高，适合作为当前阶段的冷启动推荐'
          }
        ]
      })
      .mockResolvedValueOnce({
        mode: 'personalized',
        items: [
          {
            product_id: 2,
            product_name: '透气训练T恤',
            category: '运动服饰',
            reason: '该商品属于你偏好的 运动服饰 类目，且近期热度表现较好'
          }
        ]
      })
    fetchPreferenceProfile
      .mockResolvedValueOnce({
        user: { nickname: '小林', region: '华东' },
        is_cold_start: true,
        top_categories: [],
        top_actions: [],
        recent_activity: [],
        engagement_score: 0,
        top_active_hours: [],
        price_preference: { average_price: 0, price_band: '暂无数据' },
        profile_tags: []
      })
      .mockResolvedValueOnce({
        user: { nickname: '小林', region: '华东' },
        is_cold_start: false,
        top_categories: [{ category: '运动服饰', count: 1, score: 3 }],
        top_actions: [{ action_type: 'favorite', count: 1, score: 3 }],
        recent_activity: [],
        engagement_score: 3,
        top_active_hours: [{ hour: 20, count: 1 }],
        price_preference: { average_price: 129, price_band: '大众消费偏好' },
        profile_tags: ['运动服饰偏好']
      })

    const wrapper = mountCustomerHome()
    await flushPromises()

    expect(wrapper.text()).toContain('冷启动推荐')
    expect(wrapper.text()).toContain('冷启动用户')
    expect(wrapper.find('[data-testid="customer-action-view-1"]').exists()).toBe(true)
    expect(wrapper.find('[data-testid="customer-action-favorite-1"]').exists()).toBe(true)
    expect(wrapper.find('[data-testid="customer-action-cart-1"]').exists()).toBe(true)
    expect(wrapper.find('[data-testid="customer-action-purchase-1"]').exists()).toBe(true)

    await wrapper.find('button[data-testid="customer-action-favorite-1"]').trigger('click')
    await flushPromises()

    expect(recordCustomerAction).toHaveBeenCalledWith({ product_id: 1, action_type: 'favorite' })
    expect(fetchMyRecommendations).toHaveBeenCalledTimes(2)
    expect(fetchPreferenceProfile).toHaveBeenCalledTimes(2)
    expect(wrapper.text()).toContain('已记录收藏行为')
    expect(wrapper.text()).not.toContain('冷启动推荐')
    expect(wrapper.text()).not.toContain('冷启动用户')
    expect(wrapper.text()).toContain('最近 5 条画像依据')
    expect(wrapper.text()).toContain('透气训练T恤')
  })
})
