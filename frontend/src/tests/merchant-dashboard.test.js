import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'

import { flushPromises, mount } from '@vue/test-utils'
import { beforeEach, describe, expect, it, vi } from 'vitest'

const mockRoute = {
  query: {}
}

vi.mock('vue-router', async () => {
  const actual = await vi.importActual('vue-router')
  return {
    ...actual,
    useRoute: () => mockRoute
  }
})

import { routes } from '../router/index.js'
import MerchantDashboard from '../views/merchant/MerchantDashboard.vue'

vi.mock('../api/analytics.js', () => ({
  fetchOverview: vi.fn(),
  fetchFunnel: vi.fn(),
  fetchRegions: vi.fn(),
  fetchCategories: vi.fn(),
  fetchBrands: vi.fn(),
  fetchHotProducts: vi.fn(),
  fetchColdProducts: vi.fn(),
  fetchUserRfm: vi.fn(),
  fetchMerchantUserBehavior: vi.fn(),
  fetchMerchantActionSummary: vi.fn(),
  fetchMerchantAiAnalysis: vi.fn(),
  recordMerchantAction: vi.fn(),
  fetchMerchantStrategy: vi.fn(),
  fetchPredictionAnomalies: vi.fn(),
  fetchMerchantBrief: vi.fn()
}))

import {
  fetchCategories,
  fetchBrands,
  fetchColdProducts,
  fetchFunnel,
  fetchHotProducts,
  fetchMerchantActionSummary,
  fetchMerchantAiAnalysis,
  fetchMerchantUserBehavior,
  fetchMerchantStrategy,
  fetchOverview,
  fetchPredictionAnomalies,
  recordMerchantAction,
  fetchMerchantBrief,
  fetchRegions,
  fetchUserRfm
} from '../api/analytics.js'

describe('merchant dashboard route', () => {
  it('registers the merchant dashboard view under the merchant route', () => {
    const appRoute = routes.find((route) => route.path === '/')
    const merchantRoute = appRoute.children.find((route) => route.name === 'merchant-dashboard')

    expect(merchantRoute.component).toBe(MerchantDashboard)
    expect(merchantRoute.meta.roles).toEqual(['merchant'])
  })
})

describe('merchant dashboard', () => {
  beforeEach(() => {
    mockRoute.query = {}
    fetchOverview.mockResolvedValue({
      totals: {
        behavior_count: 1280,
        view_count: 860,
        uv: 420,
        purchase_count: 64,
        purchase_rate: 0.0744
      },
      top_products: [
        { product_id: 1, product_name: '轻量跑鞋', count: 186, hot_score: 640 },
        { product_id: 2, product_name: '城市双肩包', count: 132, hot_score: 438 }
      ],
      regions: [{ region: '华东', count: 460 }]
    })
    fetchFunnel.mockResolvedValue({
      items: [
        { key: 'view', label: '浏览', value: 1280 },
        { key: 'click', label: '点击', value: 530 },
        { key: 'favorite', label: '收藏', value: 210 },
        { key: 'cart', label: '加购', value: 96 },
        { key: 'purchase', label: '购买', value: 64 }
      ]
    })
    fetchRegions.mockResolvedValue({
      items: [
        { region: '华东', count: 460 },
        { region: '华南', count: 325 }
      ]
    })
    fetchCategories.mockResolvedValue({
      items: [
        { category: '运动鞋', count: 520 },
        { category: '箱包', count: 330 }
      ]
    })
    fetchBrands.mockResolvedValue({
      items: [
        { brand: '云步', count: 480 },
        { brand: '活力穿', count: 210 }
      ]
    })
    fetchHotProducts.mockResolvedValue({
      items: [
        { product_id: 1, product_name: '轻量跑鞋', count: 186, hot_score: 640 },
        { product_id: 2, product_name: '城市双肩包', count: 132, hot_score: 438 }
      ]
    })
    fetchColdProducts.mockResolvedValue({
      items: [
        { product_id: 9, product_name: '瑜伽弹力带', count: 12, hot_score: 18 }
      ]
    })
    fetchUserRfm.mockResolvedValue({
      items: [
        { user_id: 1, frequency: 3, monetary: 688, rfm_label: '高价值用户' },
        { user_id: 2, frequency: 1, monetary: 199, rfm_label: '潜力转化用户' }
      ]
    })
    fetchMerchantStrategy.mockResolvedValue({
      items: [
        {
          product_id: 1,
          product_name: '轻量跑鞋',
          action: '建议优化详情页并尝试限时促销，提升成交效率',
          purchase_rate: 0.0832,
          views: 68
        }
      ]
    })
    fetchPredictionAnomalies.mockResolvedValue({
      items: [
        {
          type: 'traffic_spike_low_conversion',
          target: '轻量跑鞋',
          severity: 'high',
          reason: '轻量跑鞋 最近浏览量从 2 增长到 6，但转化率未同步提升，疑似高流量低转化。'
        }
      ]
    })
    fetchMerchantBrief.mockResolvedValue({
      summary: '今日经营简报显示轻量跑鞋热度持续走高，但浏览转化仍偏低，建议优先优化详情页并结合限时促销提升成交效率。'
    })
    fetchMerchantAiAnalysis.mockResolvedValue({
      summary: 'AI 认为当前经营重点应放在轻量跑鞋，优先优化详情页并关注高流量低转化风险。',
      mode: 'provider',
      provider: 'openai-compatible',
      model: 'deepseek-chat'
    })
    fetchMerchantActionSummary.mockResolvedValue({
      summary: {
        total: 0,
        by_action: {}
      },
      items: []
    })
    fetchMerchantUserBehavior.mockResolvedValue({
      preference_changes: [
        {
          category: '运动鞋',
          top_action: 'cart',
          action_count: 2,
          summary: '运动鞋最近加购行为更活跃'
        }
      ],
      intent_products: [
        {
          product_id: 1,
          product_name: '轻量跑鞋',
          top_action: 'purchase',
          action_count: 1,
          summary: '轻量跑鞋最近购买较多，值得重点关注'
        }
      ]
    })
    recordMerchantAction.mockResolvedValue({
      action: {
        product_id: 1,
        action_type: 'focus_watch',
        status: 'recorded'
      },
      summary: {
        total: 1,
        by_action: {
          focus_watch: 1
        }
      }
    })
  })

  it('defaults to overview panel and hides other merchant panels', async () => {
    const wrapper = mount(MerchantDashboard, {
      global: {
        stubs: {
          RouterLink: true
        }
      }
    })

    await flushPromises()

    expect(wrapper.text()).toContain('经营总览')
    expect(wrapper.text()).toContain('今日经营简报')
    expect(wrapper.text()).toContain('热销机会')
    expect(wrapper.text()).toContain('行为总量')
    expect(wrapper.text()).toContain('浏览量')
    expect(wrapper.text()).toContain('品牌热度')
    expect(wrapper.text()).toContain('轻量跑鞋热度持续走高')
    expect(wrapper.text()).toContain('1280')
    expect(wrapper.text()).toContain('860')
    expect(wrapper.text()).toContain('7.4%')
    expect(wrapper.text()).toContain('轻量跑鞋')
    expect(wrapper.text()).not.toContain('用户行为变化')
    expect(wrapper.text()).not.toContain('AI 经营分析')
    expect(wrapper.text()).not.toContain('转化漏斗')
    wrapper.unmount()
  })

  it('renders only the selected core panel when section=core', async () => {
    mockRoute.query = { section: 'core' }

    const wrapper = mount(MerchantDashboard, {
      global: {
        stubs: {
          RouterLink: true
        }
      }
    })

    await flushPromises()

    expect(wrapper.text()).toContain('核心业务')
    expect(wrapper.text()).toContain('最近24小时用户活跃信号')
    expect(wrapper.text()).toContain('最近24小时高意向商品信号')
    expect(wrapper.text()).toContain('今日已执行运营动作')
    expect(wrapper.text()).toContain('热销机会')
    expect(wrapper.text()).not.toContain('用户行为变化')
    expect(wrapper.text()).not.toContain('今日经营简报')
    expect(wrapper.text()).not.toContain('AI 经营分析')
    expect(wrapper.text()).not.toContain('转化漏斗')
    wrapper.unmount()
  })

  it('renders only the selected analysis panel when section=analysis', async () => {
    mockRoute.query = { section: 'analysis' }

    const wrapper = mount(MerchantDashboard, {
      global: {
        stubs: {
          RouterLink: true
        }
      }
    })

    await flushPromises()

    expect(wrapper.text()).toContain('辅助分析')
    expect(wrapper.text()).toContain('AI 经营分析')
    expect(wrapper.text()).toContain('异常预警')
    expect(wrapper.text()).toContain('类目热点')
    expect(wrapper.text()).toContain('简化用户分层')
    expect(wrapper.text()).not.toContain('通过 RFM 识别高价值与潜力用户')
    expect(wrapper.text()).not.toContain('今日经营简报')
    expect(wrapper.text()).not.toContain('用户行为变化')
    expect(wrapper.text()).not.toContain('转化漏斗')
    wrapper.unmount()
  })

  it('renders event-level funnel wording in detail section', async () => {
    mockRoute.query = { section: 'detail' }

    const wrapper = mount(MerchantDashboard, {
      global: {
        stubs: {
          RouterLink: true
        }
      }
    })

    await flushPromises()

    expect(wrapper.text()).toContain('转化漏斗')
    expect(wrapper.text()).toContain('事件级经营转化指标')
    expect(wrapper.text()).toContain('购买行为 / 浏览行为')
    expect(wrapper.text()).not.toContain('浏览到购买')
    expect(wrapper.text()).toContain('冷门商品')
    expect(wrapper.text()).not.toContain('今日经营简报')
    expect(wrapper.text()).not.toContain('用户行为变化')
    expect(wrapper.text()).not.toContain('AI 经营分析')
    wrapper.unmount()
  })

  it('defines sticky merchant sidebar and active panel styles in theme css', () => {
    const themeCssPath = resolve(process.cwd(), 'src/styles/theme.css')
    const themeCss = readFileSync(themeCssPath, 'utf8')

    expect(themeCss).toContain('.app-shell__sidebar--merchant')
    expect(themeCss).toContain('position: sticky;')
    expect(themeCss).toContain('top: 0;')
    expect(themeCss).toContain('.app-shell__nav-link.router-link-exact-active')
    expect(themeCss).toContain('background: linear-gradient(135deg, #2563eb 0%, #3b82f6 100%);')
    expect(themeCss).toContain('color: #ffffff;')
    expect(themeCss).toContain('box-shadow: 0 10px 24px rgba(37, 99, 235, 0.28);')
    expect(themeCss).toContain('transform: translateX(4px);')
    expect(themeCss).toContain('.merchant-dashboard--panel')
    expect(themeCss).toContain('min-height: calc(100vh - 140px);')
  })

  it('renders merchant ai analysis entry and result', async () => {
    mockRoute.query = { section: 'analysis' }

    const wrapper = mount(MerchantDashboard, {
      global: {
        stubs: {
          RouterLink: true
        }
      }
    })

    await flushPromises()

    expect(wrapper.text()).toContain('AI 经营分析')
    expect(wrapper.text()).toContain('生成 AI 经营分析')
    expect(wrapper.text()).not.toContain('当前经营重点应放在轻量跑鞋')

    await wrapper.find('button[data-testid="merchant-ai-generate"]').trigger('click')
    await flushPromises()

    expect(fetchMerchantAiAnalysis).toHaveBeenCalledWith(
      expect.objectContaining({
        product_name: '轻量跑鞋',
        hot_score: 640,
        purchase_rate: 0.0744,
        anomaly_count: 1,
        category_name: '运动鞋'
      })
    )
    expect(wrapper.text()).toContain('当前经营重点应放在轻量跑鞋')
    expect(wrapper.text()).toContain('当前模式：外部模型')
    expect(wrapper.text()).toContain('模型来源：openai-compatible')
    expect(wrapper.text()).toContain('模型名称：deepseek-chat')
    wrapper.unmount()
  })

  it('uses the same merchant-scoped metrics for brief and ai summaries', async () => {
    mockRoute.query = { section: 'analysis' }

    const wrapper = mount(MerchantDashboard, {
      global: {
        stubs: {
          RouterLink: true
        }
      }
    })

    await flushPromises()

    expect(fetchMerchantBrief).toHaveBeenCalledWith(
      expect.objectContaining({
        product_name: '轻量跑鞋',
        hot_score: 640,
        purchase_rate: 0.0744
      })
    )

    await wrapper.find('button[data-testid="merchant-ai-generate"]').trigger('click')
    await flushPromises()

    expect(fetchMerchantAiAnalysis).toHaveBeenCalledWith(
      expect.objectContaining({
        product_name: '轻量跑鞋',
        hot_score: 640,
        purchase_rate: 0.0744
      })
    )
    wrapper.unmount()
  })

  it('renders merchant user behavior linkage sections', async () => {
    mockRoute.query = { section: 'core' }

    const wrapper = mount(MerchantDashboard, {
      global: {
        stubs: {
          RouterLink: true
        }
      }
    })

    await flushPromises()

    expect(fetchMerchantUserBehavior).toHaveBeenCalled()
    expect(wrapper.text()).toContain('最近24小时用户活跃信号')
    expect(wrapper.text()).toContain('展示最近24小时窗口内的收藏、加购、购买信号，不代表与历史基线比较后的变化结果。')
    expect(wrapper.text()).toContain('最近24小时类目偏好信号')
    expect(wrapper.text()).toContain('最近24小时高意向商品信号')
    expect(wrapper.text()).toContain('运动鞋最近加购行为更活跃')
    expect(wrapper.text()).toContain('轻量跑鞋最近购买较多，值得重点关注')
    wrapper.unmount()
  })

  it('renders merchant user behavior empty states', async () => {
    mockRoute.query = { section: 'core' }
    fetchMerchantUserBehavior.mockResolvedValueOnce({
      preference_changes: [],
      intent_products: []
    })

    const wrapper = mount(MerchantDashboard, {
      global: {
        stubs: {
          RouterLink: true
        }
      }
    })

    await flushPromises()

    expect(wrapper.text()).toContain('最近24小时暂无明显类目偏好信号。')
    expect(wrapper.text()).toContain('最近24小时暂无明显高意向商品信号。')
    wrapper.unmount()
  })

  it('records merchant operational actions and shows executed state', async () => {
    mockRoute.query = { section: 'core' }

    const wrapper = mount(MerchantDashboard, {
      global: {
        stubs: {
          RouterLink: true
        }
      }
    })

    await flushPromises()

    expect(wrapper.text()).toContain('今日已执行运营动作')
    expect(wrapper.text()).toContain('设为重点观察')

    await wrapper.find('button[data-testid="merchant-action-focus-1"]').trigger('click')
    await flushPromises()

    expect(recordMerchantAction).toHaveBeenCalled()
    expect(wrapper.text()).toContain('已设为重点观察')
    wrapper.unmount()
  })
})
