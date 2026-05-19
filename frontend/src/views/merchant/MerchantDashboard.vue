<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'

import {
  fetchCategories,
  fetchBrands,
  fetchColdProducts,
  fetchFunnel,
  fetchHotProducts,
  fetchMerchantActionSummary,
  fetchMerchantAiAnalysis,
  fetchMerchantBrief,
  fetchMerchantUserBehavior,
  fetchMerchantStrategy,
  fetchOverview,
  fetchPredictionAnomalies,
  recordMerchantAction,
  fetchRegions,
  fetchUserRfm
} from '../../api/analytics.js'
import { deactivateMerchantProduct, fetchMerchantOpsOverview } from '../../api/merchantOps.js'
import { fetchMerchantChartShare, fetchMerchantChartTrend } from '../../api/merchantCharts.js'
import { fetchMerchantSalesForecast } from '../../api/merchantPrediction.js'
import { useAutoRefresh } from '../../composables/useAutoRefresh.js'
import BrandsView from './BrandsView.vue'
import FunnelView from './FunnelView.vue'
import HotProductsView from './HotProductsView.vue'
import MerchantOpsOverview from './MerchantOpsOverview.vue'
import StrategyView from './StrategyView.vue'
import SharePieChart from '../../components/charts/SharePieChart.vue'
import TrendLineChart from '../../components/charts/TrendLineChart.vue'

const route = useRoute()
const isLoading = ref(true)
const errorMessage = ref('')
const overview = ref({
  totals: {
    behavior_count: 0,
    view_count: 0,
    uv: 0,
    purchase_count: 0,
    purchase_rate: 0
  },
  funnel: {
    view: 0,
    click: 0,
    favorite: 0,
    cart: 0,
    purchase: 0
  },
  top_products: [],
  regions: []
})
const strategyItems = ref([])
const anomalyItems = ref([])
const funnel = ref({
  view: 0,
  click: 0,
  favorite: 0,
  cart: 0,
  purchase: 0
})
const hotProducts = ref([])
const coldProducts = ref([])
const regionItems = ref([])
const categoryItems = ref([])
const brandItems = ref([])
const selectedBrandCategory = ref('')
const opsOverview = ref({
  summary: { days: 30, revenue: 0, cost: 0, profit: 0 },
  inventory_items: [],
  delist_suggestions: [],
  inactive_items: [],
  focus_brands: []
})
const deactivatingProductId = ref(0)
const chartShare = ref({ category_share: [], brand_share: [] })
const chartTrend = ref({ days: [], series: [] })
const userRfmItems = ref([])
const briefSummary = ref('正在生成今日经营简报...')
const isGeneratingAi = ref(false)
const merchantAiSummary = ref('')
const merchantAiMeta = ref({
  mode: '',
  provider: '',
  model: ''
})
const merchantUserBehavior = ref({
  preference_changes: [],
  intent_products: []
})
const merchantActionSummary = ref({
  total: 0,
  by_action: {}
})
const merchantActionItems = ref([])
const actionInFlightKey = ref('')
const isRefreshingSnapshot = ref(false)
const salesForecast = ref({
  product: null,
  history: [],
  forecast: [],
  forecast_total: { value: 0, lower: 0, upper: 0 },
  confidence: 'low',
  explain: []
})
const isLoadingForecast = ref(false)

const ACTION_LABELS = {
  focus_watch: '设为重点观察',
  promote: '加入促销',
  restock_priority: '补货优先',
  optimize_detail: '优化详情页'
}

const ACTION_DONE_LABELS = {
  focus_watch: '已设为重点观察',
  promote: '已加入促销',
  restock_priority: '已设为补货优先',
  optimize_detail: '已安排优化详情页'
}

const SECTION_MAP = {
  overview: 'overview',
  core: 'core',
  analysis: 'analysis',
  detail: 'detail'
}

const activeSection = computed(() => {
  const section = route.query.section
  if (typeof section === 'string' && SECTION_MAP[section]) {
    return SECTION_MAP[section]
  }
  return 'overview'
})

const financeCards = computed(() => {
  const days = Number(opsOverview.value?.summary?.days || 30)
  const revenue = Number(opsOverview.value?.summary?.revenue || 0)
  const cost = Number(opsOverview.value?.summary?.cost || 0)
  const profit = Number(opsOverview.value?.summary?.profit || 0)
  const profitCardLabel = profit < 0 ? `近${days}天亏损` : `近${days}天利润`
  const moneyFormatter = (value) => Number(value || 0).toFixed(2)

  return [
    {
      label: `近${days}天收入`,
      value: moneyFormatter(revenue),
      hint: '估算：购买次数×商品售价'
    },
    {
      label: `近${days}天成本`,
      value: moneyFormatter(cost),
      hint: '估算：购买次数×商品成本价'
    },
    {
      label: profitCardLabel,
      value: moneyFormatter(profit),
      hint: profit < 0 ? '亏损=成本-收入' : '利润=收入-成本'
    }
  ]
})

const overviewCards = computed(() => {
  const totals = overview.value.totals
  const purchaseRate = `${((totals.purchase_rate || 0) * 100).toFixed(1)}%`

  return [
    {
      label: '行为总量',
      value: totals.behavior_count,
      hint: '全链路行为次数'
    },
    {
      label: '浏览量',
      value: totals.view_count,
      hint: 'view 行为次数'
    },
    {
      label: '成交笔数',
      value: totals.purchase_count,
      hint: '购买行为次数'
    },
    {
      label: '成交转化率',
      value: purchaseRate,
      hint: '购买行为 / 浏览行为'
    }
  ]
})

function splitBulletItems(raw) {
  const textValue = String(raw || '').trim()
  if (!textValue) {
    return []
  }

  const parts = textValue
    .split(/(?=\d+[）\)]|\bP\d+(?:-\d+)?[-）\)])/i)
    .map((part) => part.trim())
    .filter(Boolean)

  if (parts.length <= 1) {
    return [textValue]
  }

  return parts
}

function normalizeBulletItem(raw) {
  return String(raw || '')
    .replace(/^[\s]*(?:P\d+(?:-\d+)?-\d+[）\)]|P\d+(?:-\d+)?-|P\d+(?:-\d+)?[）\)]|\d+[）\)])[ ]*/i, '')
    .trim()
}

function buildBriefBlocks(raw) {
  const source = String(raw || '')
    .replace(/\r\n/g, '\n')
    .replace(/\r/g, '\n')
    .replace(/[【】]/g, '')
    .replace(/(核心结论|机会点|风险预警|行动清单)\s*[:：]/g, '\n$1：')
    .trim()

  if (!source) {
    return []
  }

  const lines = source
    .split('\n')
    .map((line) => line.trim())
    .filter(Boolean)

  const titleMap = {
    核心结论: '核心结论',
    机会点: '机会点',
    风险预警: '风险预警',
    行动清单: '行动清单'
  }

  const blocks = []
  let currentBlock = null

  for (const line of lines) {
    const headingOnlyMatch = line.match(/^(核心结论|机会点|风险预警|行动清单)\s*[:：]?\s*$/)
    if (headingOnlyMatch) {
      const sectionKey = headingOnlyMatch[1]
      currentBlock = { title: titleMap[sectionKey] || sectionKey, items: [] }
      blocks.push(currentBlock)
      continue
    }

    const headingMatch = line.match(/^(核心结论|机会点|风险预警|行动清单)[:：]\s*(.*)$/)
    if (headingMatch) {
      const sectionKey = headingMatch[1]
      currentBlock = { title: titleMap[sectionKey] || sectionKey, items: [] }
      blocks.push(currentBlock)
      const rest = headingMatch[2].trim()
      if (rest) {
        splitBulletItems(rest)
          .map(normalizeBulletItem)
          .filter(Boolean)
          .forEach((item) => currentBlock.items.push(item))
      }
      continue
    }

    if (!currentBlock) {
      currentBlock = { title: '核心结论', items: [] }
      blocks.push(currentBlock)
    }

    splitBulletItems(line)
      .map(normalizeBulletItem)
      .filter(Boolean)
      .forEach((item) => currentBlock.items.push(item))
  }

  return blocks.filter((block) => block.items.length)
}

const topProduct = computed(() => hotProducts.value[0] || overview.value.top_products[0] || null)
const briefBlocks = computed(() => buildBriefBlocks(briefSummary.value))
const warningStrategies = computed(() => strategyItems.value.filter((item) => (item.purchase_rate || 0) < 0.1))
const opportunityItems = computed(() => hotProducts.value.slice(0, 3))
const riskItems = computed(() => warningStrategies.value.slice(0, 3))
const criticalAnomalies = computed(() => anomalyItems.value.slice(0, 4))
const merchantActionStats = computed(() =>
  Object.entries(merchantActionSummary.value.by_action || {}).map(([actionType, count]) => ({
    actionType,
    label: ACTION_LABELS[actionType] || actionType,
    count
  }))
)

function normalizeFunnel(items = []) {
  return items.reduce(
    (accumulator, item) => {
      accumulator[item.key] = item.value || 0
      return accumulator
    },
    {
      view: 0,
      click: 0,
      favorite: 0,
      cart: 0,
      purchase: 0
    }
  )
}

function buildActionKey(productId, actionType) {
  return `${productId}:${actionType}`
}

function hasExecutedAction(productId, actionType) {
  return merchantActionItems.value.some(
    (item) => item.product_id === productId && item.action_type === actionType
  )
}

function getExecutedActionLabels(productId, actionTypes = []) {
  return actionTypes
    .filter((actionType) => hasExecutedAction(productId, actionType))
    .map((actionType) => ACTION_DONE_LABELS[actionType] || '已执行')
}

function formatBehaviorAction(actionType) {
  if (actionType === 'favorite') {
    return '收藏'
  }
  if (actionType === 'cart') {
    return '加购'
  }
  if (actionType === 'purchase') {
    return '购买'
  }

  return actionType
}

async function handleRecordAction(productId, actionType) {
  actionInFlightKey.value = buildActionKey(productId, actionType)
  errorMessage.value = ''

  try {
    const payload = await recordMerchantAction({
      product_id: productId,
      action_type: actionType
    })
    merchantActionSummary.value = payload.summary || merchantActionSummary.value
    if (payload.action) {
      merchantActionItems.value = [
        payload.action,
        ...merchantActionItems.value.filter(
          (item) => !(item.product_id === payload.action.product_id && item.action_type === payload.action.action_type)
        )
      ].slice(0, 8)
    }
  } catch (error) {
    errorMessage.value = error?.response?.data?.message || '记录运营动作失败，请稍后重试。'
  } finally {
    actionInFlightKey.value = ''
  }
}

const cockpitHighlights = computed(() => [
  {
    title: '热销机会',
    value: opportunityItems.value.length,
    description: topProduct.value
      ? `${topProduct.value.product_name} 当前热度最高，可优先加曝光`
      : '暂无热销机会数据'
  },
  {
    title: '滞销风险',
    value: riskItems.value.length,
    description: riskItems.value.length
      ? '已有商品出现高浏览低转化，建议优先检查详情页和促销策略'
      : '当前未发现明显滞销风险'
  },
  {
    title: '异常预警',
    value: criticalAnomalies.value.length,
    description: criticalAnomalies.value.length
      ? '近期存在异常流量或转化问题，需要重点监控'
      : '当前未出现高优先级异常'
  }
])

const forecastChart = computed(() => {
  const payload = salesForecast.value
  const historyItems = payload?.history || []
  const forecastItems = payload?.forecast || []
  if (!historyItems.length && !forecastItems.length) {
    return { days: [], series: [] }
  }

  const historyDays = historyItems.map((item) => item.date)
  const forecastDays = forecastItems.map((item) => item.date)
  const days = [...historyDays, ...forecastDays]
  const historyData = historyItems.map((item) => item.value).concat(Array.from({ length: forecastItems.length }, () => null))
  const forecastData = Array.from({ length: historyItems.length }, () => null).concat(forecastItems.map((item) => item.value))

  return {
    days,
    series: [
      { name: '历史销量', data: historyData },
      { name: '预测销量', data: forecastData }
    ]
  }
})

function buildForecastFallback(message) {
  return {
    product: null,
    history: [],
    forecast: [],
    forecast_total: { value: 0, lower: 0, upper: 0 },
    confidence: 'low',
    explain: [message]
  }
}

function buildMerchantInsightPayload() {
  const bestProduct = hotProducts.value[0]

  return {
    product_name: bestProduct?.product_name || '暂无重点商品',
    hot_score: bestProduct?.hot_score ?? bestProduct?.count ?? 0,
    purchase_rate: overview.value.totals.purchase_rate || 0,
    anomaly_count: criticalAnomalies.value.length,
    cold_product_count: coldProducts.value.length,
    category_name: categoryItems.value[0]?.category || '综合类目'
  }
}

function buildBriefFallback() {
  const bestProduct = hotProducts.value[0]
  const productName = bestProduct?.product_name || '重点商品'
  const hotScore = bestProduct?.hot_score ?? bestProduct?.count ?? 0
  const purchaseRate = Number(overview.value?.totals?.purchase_rate || 0)
  const purchaseRateText = `${(purchaseRate * 100).toFixed(1)}%`
  const anomalyCount = criticalAnomalies.value.length
  const coldCount = coldProducts.value.length

  const pieces = [
    `今日经营简报（简版）：重点关注${productName}（热度${hotScore}），当前成交转化率${purchaseRateText}。`,
    anomalyCount
      ? `检测到${anomalyCount}条高优先级异常预警，建议优先排查详情页转化链路与流量质量。`
      : '暂无高优先级异常预警，可继续围绕重点商品做曝光和促销。',
  ]

  if (coldCount) {
    pieces.push(`另有${coldCount}个冷门商品可考虑做促销清理或下架评估。`)
  }

  return pieces.join('')
}

async function handleGenerateAiAnalysis() {
  isGeneratingAi.value = true
  errorMessage.value = ''

  try {
    let timeoutId = null
    const timeoutPromise = new Promise((_, reject) => {
      timeoutId = setTimeout(() => reject(new Error('timeout')), 25000)
    })
    const payload = await Promise.race([fetchMerchantAiAnalysis(buildMerchantInsightPayload()), timeoutPromise])
    if (timeoutId) {
      clearTimeout(timeoutId)
    }
    merchantAiSummary.value = payload.summary || 'AI 经营分析生成成功。'
    merchantAiMeta.value = {
      mode: payload.mode || 'fallback',
      provider: payload.provider || 'internal',
      model: payload.model || 'rule-based-fallback'
    }
  } catch (error) {
    errorMessage.value = error?.response?.data?.message || 'AI 经营分析生成失败，请稍后重试。'
    merchantAiSummary.value = '模型响应较慢或暂时不可用，已切换为内置分析口径，请稍后再试。'
    merchantAiMeta.value = {
      mode: 'fallback',
      provider: merchantAiMeta.value.provider || 'internal',
      model: merchantAiMeta.value.model || 'rule-based-fallback'
    }
  } finally {
    isGeneratingAi.value = false
  }
}

async function refreshOverviewSnapshot() {
  isRefreshingSnapshot.value = true
  isLoadingForecast.value = true
  errorMessage.value = ''
  const forecastPromise = fetchMerchantSalesForecast({ days: 30 }).catch((error) =>
    buildForecastFallback(error?.response?.data?.message || '销量预测生成失败，请稍后重试。')
  )

  try {
    const [overviewPayload, brandPayload, opsPayload, sharePayload, trendPayload] = await Promise.all([
      fetchOverview(),
      fetchBrands(selectedBrandCategory.value ? { category: selectedBrandCategory.value } : {}),
      fetchMerchantOpsOverview({ days: 30, low_sales_threshold: 3, brand_top_n: 5 }),
      fetchMerchantChartShare({ top_n: 5 }),
      fetchMerchantChartTrend({ days: 7 })
    ])
    overview.value = {
      ...overview.value,
      ...overviewPayload
    }
    brandItems.value = brandPayload.items || []
    opsOverview.value = opsPayload || opsOverview.value
    chartShare.value = sharePayload || chartShare.value
    chartTrend.value = trendPayload || chartTrend.value
  } catch (error) {
    errorMessage.value = error?.response?.data?.message || '刷新经营摘要失败，请稍后重试。'
  } finally {
    salesForecast.value = (await forecastPromise) || buildForecastFallback('暂无可预测商品：近7/30天购买数据不足')
    isLoadingForecast.value = false
    isRefreshingSnapshot.value = false
  }
}

const autoRefresh = useAutoRefresh(refreshOverviewSnapshot, { defaultEnabled: true, defaultIntervalSec: 60 })

function handleAutoRefreshIntervalChange(event) {
  const nextValue = Number(event?.target?.value)
  if (!Number.isFinite(nextValue) || nextValue <= 0) return
  autoRefresh.intervalSec.value = nextValue
}

async function loadBrandsForCategory(category) {
  const payload = await fetchBrands(category ? { category } : {})
  brandItems.value = payload.items || []
}

async function handleBrandCategoryChange(nextCategory) {
  selectedBrandCategory.value = nextCategory
  await loadBrandsForCategory(nextCategory)
}

async function handleDeactivateProduct(productId) {
  deactivatingProductId.value = productId
  errorMessage.value = ''
  try {
    await deactivateMerchantProduct(productId)
    opsOverview.value = await fetchMerchantOpsOverview({ days: 30, low_sales_threshold: 3, brand_top_n: 5 })
  } catch (error) {
    errorMessage.value = error?.response?.data?.message || '下架失败，请稍后重试。'
  } finally {
    deactivatingProductId.value = 0
  }
}

async function loadDashboard() {
  isLoading.value = true
  isLoadingForecast.value = true
  errorMessage.value = ''
  const forecastPromise = fetchMerchantSalesForecast({ days: 30 }).catch((error) =>
    buildForecastFallback(error?.response?.data?.message || '销量预测生成失败，请稍后重试。')
  )

  try {
    const results = await Promise.allSettled([
      fetchOverview(),
      fetchFunnel(),
      fetchRegions(),
      fetchCategories(),
      fetchBrands(),
      fetchMerchantOpsOverview({ days: 30, low_sales_threshold: 3, brand_top_n: 5 }),
      fetchMerchantChartShare({ top_n: 5 }),
      fetchMerchantChartTrend({ days: 7 }),
      fetchHotProducts(),
      fetchColdProducts(),
      fetchUserRfm(),
      fetchMerchantStrategy(),
      fetchPredictionAnomalies({ severity: 'high' }),
      fetchMerchantActionSummary(),
      fetchMerchantUserBehavior()
    ])

    const [
      overviewResult,
      funnelResult,
      regionResult,
      categoryResult,
      brandResult,
      opsResult,
      shareResult,
      trendResult,
      hotProductResult,
      coldProductResult,
      userRfmResult,
      strategyResult,
      anomalyResult,
      merchantActionResult,
      merchantUserBehaviorResult
    ] = results

    const overviewPayload = overviewResult.status === 'fulfilled' ? overviewResult.value : null
    const funnelPayload = funnelResult.status === 'fulfilled' ? funnelResult.value : { items: [] }
    const regionPayload = regionResult.status === 'fulfilled' ? regionResult.value : { items: [] }
    const categoryPayload = categoryResult.status === 'fulfilled' ? categoryResult.value : { items: [] }
    const brandPayload = brandResult.status === 'fulfilled' ? brandResult.value : { items: [] }
    const opsPayload = opsResult.status === 'fulfilled' ? opsResult.value : null
    const sharePayload = shareResult.status === 'fulfilled' ? shareResult.value : chartShare.value
    const trendPayload = trendResult.status === 'fulfilled' ? trendResult.value : chartTrend.value
    const hotProductPayload = hotProductResult.status === 'fulfilled' ? hotProductResult.value : { items: [] }
    const coldProductPayload = coldProductResult.status === 'fulfilled' ? coldProductResult.value : { items: [] }
    const userRfmPayload = userRfmResult.status === 'fulfilled' ? userRfmResult.value : { items: [] }
    const strategyPayload = strategyResult.status === 'fulfilled' ? strategyResult.value : { items: [] }
    const anomalyPayload = anomalyResult.status === 'fulfilled' ? anomalyResult.value : { items: [] }
    const merchantActionPayload =
      merchantActionResult.status === 'fulfilled'
        ? merchantActionResult.value
        : { summary: { total: 0, by_action: {} }, items: [] }
    const merchantUserBehaviorPayload =
      merchantUserBehaviorResult.status === 'fulfilled'
        ? merchantUserBehaviorResult.value
        : { preference_changes: [], intent_products: [] }

    const criticalFailure = !overviewPayload || !opsPayload
    if (criticalFailure) {
      errorMessage.value = '仪表页部分数据加载失败，请稍后重试。'
    }

    if (overviewPayload) {
      overview.value = {
        ...overview.value,
        ...overviewPayload
      }
    }
    funnel.value = normalizeFunnel(funnelPayload.items || [])
    regionItems.value = regionPayload.items || []
    categoryItems.value = categoryPayload.items || []
    const defaultCategory = categoryItems.value[0]?.category || ''
    const shouldPickDefault = !selectedBrandCategory.value && defaultCategory
    selectedBrandCategory.value = selectedBrandCategory.value || defaultCategory
    brandItems.value = brandPayload.items || []
    if (shouldPickDefault) {
      await loadBrandsForCategory(selectedBrandCategory.value)
    }
    opsOverview.value = opsPayload || opsOverview.value
    chartShare.value = sharePayload || chartShare.value
    chartTrend.value = trendPayload || chartTrend.value
    hotProducts.value = hotProductPayload.items || overviewPayload?.top_products || []
    coldProducts.value = coldProductPayload.items || []
    userRfmItems.value = userRfmPayload.items || []
    strategyItems.value = strategyPayload.items || []
    anomalyItems.value = anomalyPayload.items || []
    merchantActionSummary.value = merchantActionPayload.summary || { total: 0, by_action: {} }
    merchantActionItems.value = merchantActionPayload.items || []
    merchantUserBehavior.value = {
      preference_changes: merchantUserBehaviorPayload.preference_changes || [],
      intent_products: merchantUserBehaviorPayload.intent_products || []
    }

    if (hotProducts.value.length) {
      try {
        const briefPayload = await fetchMerchantBrief({
          scene: 'merchant',
          ...buildMerchantInsightPayload(),
          trend_label: anomalyItems.value.length ? 'warning' : 'up',
        })
        briefSummary.value = briefPayload.summary || buildBriefFallback()
      } catch (error) {
        briefSummary.value = buildBriefFallback()
      }
    } else {
      briefSummary.value = '当前暂无足够数据生成今日经营简报。'
    }
  } catch (error) {
    errorMessage.value = error?.response?.data?.message || '仪表页数据加载失败，请稍后重试。'
    briefSummary.value = hotProducts.value.length ? buildBriefFallback() : '当前暂无足够数据生成今日经营简报。'
  } finally {
    salesForecast.value = (await forecastPromise) || buildForecastFallback('暂无可预测商品：近7/30天购买数据不足')
    isLoadingForecast.value = false
    isLoading.value = false
  }
}

onMounted(() => {
  loadDashboard()
  autoRefresh.lastUpdatedAt.value = new Date().toLocaleTimeString('zh-CN', { hour12: false })
  autoRefresh.countdown.value = autoRefresh.intervalSec.value
})
</script>

<template>
  <section
    v-if="activeSection === 'overview'"
    class="merchant-dashboard merchant-dashboard--panel"
  >
    <header class="merchant-dashboard__hero">
      <div>
        <p class="section-kicker">MERCHANT ANALYTICS</p>
        <h2>经营总览</h2>
        <p>聚合商家当前经营表现，突出今日经营简报、热销机会、滞销风险和异常预警。</p>
      </div>
      <div class="admin-page__actions">
        <label class="ghost-button" style="display: inline-flex; align-items: center; gap: 8px;">
          <input v-model="autoRefresh.enabled.value" type="checkbox" />
          <span>自动刷新</span>
        </label>
        <select
          class="admin-log-preview__page-size"
          :value="autoRefresh.intervalSec"
          @change="handleAutoRefreshIntervalChange"
        >
          <option :value="60">60s</option>
          <option :value="120">120s</option>
        </select>
        <span class="dashboard-panel__badge">下次刷新 {{ autoRefresh.countdown }}s</span>
        <span v-if="autoRefresh.lastUpdatedAt" class="dashboard-panel__badge">
          更新于 {{ autoRefresh.lastUpdatedAt }}
        </span>
        <button
          class="ghost-button"
          type="button"
          :disabled="isRefreshingSnapshot || autoRefresh.isRefreshing"
          @click="autoRefresh.refreshNow(true)"
        >
          {{ isRefreshingSnapshot || autoRefresh.isRefreshing ? '刷新中...' : '刷新数据' }}
        </button>
      </div>
    </header>

    <p v-if="errorMessage" class="form-error">{{ errorMessage }}</p>

    <section class="merchant-brief" :aria-busy="isLoading">
      <article class="merchant-brief__hero-card">
        <div class="merchant-brief__hero-copy">
          <p class="section-kicker">TODAY SUMMARY</p>
          <h3 class="merchant-brief__title">今日经营简报</h3>
          <div class="merchant-brief__summary">
            <section
              v-for="block in briefBlocks"
              :key="block.title"
              class="merchant-brief__summary-block"
            >
              <strong class="merchant-brief__summary-title">{{ block.title }}</strong>
              <ul class="merchant-brief__summary-list">
                <li v-for="(item, index) in block.items" :key="`${block.title}-${index}`">{{ item }}</li>
              </ul>
            </section>
          </div>
        </div>
      </article>

      <div class="merchant-brief__matrix">
        <article
          v-for="item in cockpitHighlights"
          :key="item.title"
          class="merchant-brief__insight-card"
        >
          <span class="merchant-brief__insight-label">{{ item.title }}</span>
          <strong class="merchant-brief__insight-value">{{ item.value }}</strong>
          <p>{{ item.description }}</p>
        </article>
      </div>
    </section>

    <section class="merchant-dashboard__summary merchant-dashboard__summary--triple" :aria-busy="isLoading">
      <article
        v-for="card in financeCards"
        :key="card.label"
        class="metric-card"
      >
        <p class="metric-card__label">{{ card.label }}</p>
        <strong class="metric-card__value">{{ card.value }}</strong>
        <span class="metric-card__hint">{{ card.hint }}</span>
      </article>
    </section>

    <section class="merchant-dashboard__overview-grid" :aria-busy="isLoading">
      <div class="merchant-dashboard__summary">
        <article
          v-for="card in overviewCards"
          :key="card.label"
          class="metric-card"
        >
          <p class="metric-card__label">{{ card.label }}</p>
          <strong class="metric-card__value">{{ card.value }}</strong>
          <span class="metric-card__hint">{{ card.hint }}</span>
        </article>
      </div>

      <FunnelView :funnel="funnel" />
    </section>

    <section class="merchant-dashboard__layer" :aria-busy="isLoading">
      <div class="merchant-dashboard__layer-grid">
        <article class="dashboard-panel merchant-forecast-panel">
          <div class="dashboard-panel__header">
            <div>
              <p class="section-kicker">SALES FORECAST</p>
              <h3>爆火商品销量预测（30天）</h3>
              <p>自动选取近7天购买最多的商品，对未来30天销量进行预测并给出区间。</p>
            </div>
            <span class="dashboard-panel__badge">
              预测总销量 {{ salesForecast.forecast_total?.value ?? 0 }}
            </span>
          </div>

          <div v-if="salesForecast.product" class="merchant-forecast-panel__product">
            <div class="merchant-product-thumb">
              <img
                v-if="salesForecast.product.image_url"
                class="merchant-product-thumb__image"
                :src="salesForecast.product.image_url"
                :alt="salesForecast.product.name"
                width="56"
                height="56"
                loading="lazy"
              />
              <div v-else class="merchant-product-thumb__placeholder">
                {{ String(salesForecast.product.name || '').trim().slice(0, 1) }}
              </div>
            </div>
            <div class="merchant-forecast-panel__product-meta">
              <strong>{{ salesForecast.product.name }}</strong>
              <span>{{ salesForecast.product.category }} / {{ salesForecast.product.brand }}</span>
              <span>
                预测区间 {{ salesForecast.forecast_total?.lower ?? 0 }} - {{ salesForecast.forecast_total?.upper ?? 0 }}
              </span>
            </div>
          </div>

          <p v-if="isLoadingForecast" class="empty-state">预测生成中...</p>
          <template v-else>
            <TrendLineChart
              v-if="forecastChart.days.length"
              :days="forecastChart.days"
              :series="forecastChart.series"
            />
            <p v-else class="empty-state">暂无可预测商品：近7/30天购买数据不足。</p>

            <ul v-if="salesForecast.explain?.length" class="merchant-forecast-panel__explain">
              <li v-for="item in salesForecast.explain" :key="item">
                {{ item }}
              </li>
            </ul>
          </template>
        </article>
      </div>
    </section>

    <section class="merchant-dashboard__layer" :aria-busy="isLoading">
      <div class="merchant-dashboard__layer-grid">
        <BrandsView
          :brands="brandItems"
          :categories="categoryItems"
          :selected-category="selectedBrandCategory"
          @update:selectedCategory="handleBrandCategoryChange"
        />
      </div>
    </section>

    <section class="merchant-dashboard__layer" :aria-busy="isLoading">
      <div class="merchant-dashboard__layer-grid">
        <article class="dashboard-panel">
          <div class="dashboard-panel__header">
            <div>
              <p class="section-kicker">CATEGORY SHARE</p>
              <h3>品类占比</h3>
              <p>按行为量聚合，快速判断当前流量集中在哪些品类。</p>
            </div>
          </div>
          <SharePieChart :items="chartShare.category_share || []" />
        </article>

        <article class="dashboard-panel">
          <div class="dashboard-panel__header">
            <div>
              <p class="section-kicker">BRAND SHARE</p>
              <h3>品牌销量占比</h3>
              <p>按购买次数聚合，直观看到销量冠军品牌。</p>
            </div>
          </div>
          <SharePieChart :items="chartShare.brand_share || []" />
        </article>

        <article class="dashboard-panel">
          <div class="dashboard-panel__header">
            <div>
              <p class="section-kicker">7D TREND</p>
              <h3>近7天趋势</h3>
              <p>浏览与购买的日趋势，辅助判断增长与转化节奏。</p>
            </div>
          </div>
          <TrendLineChart :days="chartTrend.days || []" :series="chartTrend.series || []" />
        </article>
      </div>
    </section>

    <MerchantOpsOverview
      :payload="opsOverview"
      :show-summary-cards="false"
      :on-deactivate="handleDeactivateProduct"
      :is-deactivating-id="deactivatingProductId"
    />
  </section>

  <section
    v-else-if="activeSection === 'core'"
    class="merchant-dashboard merchant-dashboard--panel"
  >
    <section class="merchant-dashboard__layer">
      <div class="merchant-dashboard__layer-head">
        <h3>核心业务</h3>
        <p>优先展示经营联动、动作闭环、机会和风险。</p>
      </div>

      <div class="merchant-dashboard__layer-grid">
        <article class="dashboard-panel merchant-linkage-panel">
          <div class="dashboard-panel__header">
            <div>
              <p class="section-kicker">USER BEHAVIOR SIGNALS</p>
              <h3>最近24小时用户活跃信号</h3>
              <p>展示最近24小时窗口内的收藏、加购、购买信号，不代表与历史基线比较后的变化结果。</p>
            </div>
          </div>

          <div class="merchant-linkage-grid">
            <section class="merchant-linkage-section">
              <h4>最近24小时类目偏好信号</h4>
              <ul v-if="merchantUserBehavior.preference_changes.length" class="strategy-list">
                <li
                  v-for="item in merchantUserBehavior.preference_changes"
                  :key="`${item.category}-${item.top_action}`"
                  class="strategy-list__item"
                >
                  <div class="strategy-list__meta">
                    <strong>{{ item.category }}</strong>
                    <span>{{ formatBehaviorAction(item.top_action) }} {{ item.action_count }} 次</span>
                  </div>
                  <p>{{ item.summary }}</p>
                </li>
              </ul>
              <p v-else class="empty-state">最近24小时暂无明显类目偏好信号。</p>
            </section>

            <section class="merchant-linkage-section">
              <h4>最近24小时高意向商品信号</h4>
              <ul v-if="merchantUserBehavior.intent_products.length" class="strategy-list">
                <li
                  v-for="item in merchantUserBehavior.intent_products"
                  :key="`${item.product_id}-${item.top_action}`"
                  class="strategy-list__item"
                >
                  <div class="strategy-list__meta">
                    <strong>{{ item.product_name }}</strong>
                    <span>{{ formatBehaviorAction(item.top_action) }} {{ item.action_count }} 次</span>
                  </div>
                  <p>{{ item.summary }}</p>
                </li>
              </ul>
              <p v-else class="empty-state">最近24小时暂无明显高意向商品信号。</p>
            </section>
          </div>
        </article>

        <article class="dashboard-panel merchant-action-panel">
          <div class="dashboard-panel__header">
            <div>
              <p class="section-kicker">ACTION LOOP</p>
              <h3>今日已执行运营动作</h3>
              <p>把分析结果转成可见动作，直接展示今天执行了哪些运营决策。</p>
            </div>
            <span class="dashboard-panel__badge">{{ merchantActionSummary.total }} 个动作</span>
          </div>

          <div class="merchant-action-panel__stats">
            <article class="merchant-action-panel__stat">
              <span>今日总执行数</span>
              <strong>{{ merchantActionSummary.total }}</strong>
            </article>
            <article
              v-for="item in merchantActionStats"
              :key="item.actionType"
              class="merchant-action-panel__stat"
            >
              <span>{{ item.label }}</span>
              <strong>{{ item.count }}</strong>
            </article>
          </div>

          <ul v-if="merchantActionItems.length" class="strategy-list">
            <li
              v-for="item in merchantActionItems"
              :key="`${item.product_id}-${item.action_type}-${item.created_at || item.id || 'local'}`"
              class="strategy-list__item"
            >
              <div class="strategy-list__meta">
                <strong>{{ item.product_name || `商品 ${item.product_id}` }}</strong>
                <span>{{ ACTION_LABELS[item.action_type] || item.action_type }}</span>
              </div>
              <p>{{ ACTION_DONE_LABELS[item.action_type] || '已执行运营动作' }}</p>
            </li>
          </ul>
          <p v-else class="empty-state">尚未执行运营动作，点击下方分析卡片中的按钮后会在这里显示。</p>
        </article>

        <article class="dashboard-panel">
          <div class="dashboard-panel__header">
            <div>
              <p class="section-kicker">OPPORTUNITIES</p>
              <h3>热销机会</h3>
              <p>优先关注热度高、可继续放大的商品。</p>
            </div>
            <span class="dashboard-panel__badge">{{ opportunityItems.length }} 个机会</span>
          </div>

          <ul v-if="opportunityItems.length" class="strategy-list">
            <li v-for="item in opportunityItems" :key="item.product_id" class="strategy-list__item">
              <div class="strategy-list__meta">
                <strong>{{ item.product_name }}</strong>
                <span>热度 {{ item.count }}</span>
              </div>
              <p>建议继续加曝光并配合活动页推荐，放大热销势能。</p>
              <div class="merchant-action-buttons">
                <button
                  class="ghost-button"
                  type="button"
                  :data-testid="`merchant-action-focus-${item.product_id}`"
                  :disabled="actionInFlightKey === buildActionKey(item.product_id, 'focus_watch')"
                  @click="handleRecordAction(item.product_id, 'focus_watch')"
                >
                  {{ actionInFlightKey === buildActionKey(item.product_id, 'focus_watch') ? '提交中...' : '设为重点观察' }}
                </button>
                <button
                  class="ghost-button"
                  type="button"
                  :disabled="actionInFlightKey === buildActionKey(item.product_id, 'restock_priority')"
                  @click="handleRecordAction(item.product_id, 'restock_priority')"
                >
                  {{ actionInFlightKey === buildActionKey(item.product_id, 'restock_priority') ? '提交中...' : '补货优先' }}
                </button>
              </div>
              <div v-if="getExecutedActionLabels(item.product_id, ['focus_watch', 'restock_priority']).length" class="merchant-action-tags">
                <span
                  v-for="label in getExecutedActionLabels(item.product_id, ['focus_watch', 'restock_priority'])"
                  :key="`${item.product_id}-${label}`"
                  class="merchant-action-tag"
                >
                  {{ label }}
                </span>
              </div>
            </li>
          </ul>
          <p v-else class="empty-state">暂无可识别的热销机会。</p>
        </article>

        <article class="dashboard-panel">
          <div class="dashboard-panel__header">
            <div>
              <p class="section-kicker">RISKS</p>
              <h3>滞销风险</h3>
              <p>优先处理高浏览低转化商品，降低流量浪费。</p>
            </div>
            <span class="dashboard-panel__badge">{{ riskItems.length }} 个风险</span>
          </div>

          <ul v-if="riskItems.length" class="strategy-list">
            <li v-for="item in riskItems" :key="item.product_id" class="strategy-list__item">
              <div class="strategy-list__meta">
                <strong>{{ item.product_name }}</strong>
                <span>浏览 {{ item.views }} / 转化 {{ ((item.purchase_rate || 0) * 100).toFixed(1) }}%</span>
              </div>
              <p>{{ item.action }}</p>
              <div class="merchant-action-buttons">
                <button
                  class="ghost-button"
                  type="button"
                  :disabled="actionInFlightKey === buildActionKey(item.product_id, 'optimize_detail')"
                  @click="handleRecordAction(item.product_id, 'optimize_detail')"
                >
                  {{ actionInFlightKey === buildActionKey(item.product_id, 'optimize_detail') ? '提交中...' : '优化详情页' }}
                </button>
              </div>
              <div v-if="getExecutedActionLabels(item.product_id, ['optimize_detail']).length" class="merchant-action-tags">
                <span
                  v-for="label in getExecutedActionLabels(item.product_id, ['optimize_detail'])"
                  :key="`${item.product_id}-${label}`"
                  class="merchant-action-tag"
                >
                  {{ label }}
                </span>
              </div>
            </li>
          </ul>
          <p v-else class="empty-state">当前未发现明显滞销风险。</p>
        </article>
      </div>
    </section>
  </section>

  <section
    v-else-if="activeSection === 'analysis'"
    class="merchant-dashboard merchant-dashboard--panel"
  >
    <section class="merchant-dashboard__layer">
      <div class="merchant-dashboard__layer-head">
        <h3>辅助分析</h3>
        <p>补充解释经营判断，保留分析深度但降低视觉权重。</p>
      </div>

      <div class="merchant-dashboard__layer-grid merchant-dashboard__layer-grid--secondary">
        <article class="dashboard-panel">
          <div class="dashboard-panel__header">
            <div>
              <p class="section-kicker">AI BUSINESS ANALYSIS</p>
              <h3>AI 经营分析</h3>
              <p>基于热销、转化和预警生成经营解释与建议。</p>
            </div>
            <button
              class="ghost-button"
              type="button"
              data-testid="merchant-ai-generate"
              :disabled="isGeneratingAi"
              @click="handleGenerateAiAnalysis"
            >
              {{ isGeneratingAi ? '生成中...' : '生成 AI 经营分析' }}
            </button>
          </div>

          <div v-if="merchantAiMeta.mode" class="dashboard-panel__meta-list">
            <span>当前模式：{{ merchantAiMeta.mode === 'provider' ? '外部模型' : '内置回退' }}</span>
            <span>模型来源：{{ merchantAiMeta.provider }}</span>
            <span>模型名称：{{ merchantAiMeta.model }}</span>
          </div>
          <p v-if="merchantAiSummary" class="admin-log-preview__note">{{ merchantAiSummary }}</p>
          <p v-else class="empty-state">点击按钮后生成 AI 经营分析，查看系统给出的经营解释。</p>
        </article>

        <article class="dashboard-panel">
          <div class="dashboard-panel__header">
            <div>
              <p class="section-kicker">ALERTS</p>
              <h3>异常预警</h3>
              <p>聚焦高风险流量和转化异常，便于快速排查。</p>
            </div>
            <span class="dashboard-panel__badge">{{ criticalAnomalies.length }} 条预警</span>
          </div>

          <ul v-if="criticalAnomalies.length" class="admin-log-list">
            <li v-for="item in criticalAnomalies" :key="`${item.type}-${item.target}`" class="admin-log-list__item">
              <div class="admin-log-list__meta">
                <span class="admin-status-pill" :data-status="item.severity">
                  {{ item.severity }}
                </span>
                <strong>{{ item.target }}</strong>
              </div>
              <p>{{ item.reason }}</p>
            </li>
          </ul>
          <p v-else class="empty-state">当前暂无高优先级异常预警。</p>
        </article>

        <article class="dashboard-panel">
          <div class="dashboard-panel__header">
            <div>
              <p class="section-kicker">CATEGORY HEAT</p>
              <h3>类目热点</h3>
              <p>观察高活跃类目，辅助安排选品与投放。</p>
            </div>
            <span class="dashboard-panel__badge">{{ categoryItems.length }} 个类目</span>
          </div>

          <ul v-if="categoryItems.length" class="region-list__items">
            <li
              v-for="item in categoryItems"
              :key="item.category"
              class="region-list__item"
            >
              <span>{{ item.category }}</span>
              <strong>{{ item.count }}</strong>
            </li>
          </ul>
          <p v-else class="empty-state">暂无类目热点数据。</p>
        </article>

        <article class="dashboard-panel">
          <div class="dashboard-panel__header">
            <div>
              <p class="section-kicker">USER SEGMENT</p>
              <h3>简化用户分层</h3>
              <p>基于最近活跃、购买频次和金额的分层统计，用于识别高价值、潜力和待激活用户。</p>
            </div>
            <span class="dashboard-panel__badge">{{ userRfmItems.length }} 个用户样本</span>
          </div>

          <ul v-if="userRfmItems.length" class="strategy-list">
            <li v-for="item in userRfmItems" :key="item.user_id" class="strategy-list__item">
              <div class="strategy-list__meta">
                <strong>用户 {{ item.user_id }}</strong>
                <span>频次 {{ item.frequency }} / 消费 {{ item.monetary }}</span>
              </div>
              <p>{{ item.rfm_label }}</p>
            </li>
          </ul>
          <p v-else class="empty-state">当前暂无用户价值分层数据。</p>
        </article>
      </div>
    </section>
  </section>

  <section
    v-else
    class="merchant-dashboard merchant-dashboard--panel"
  >
    <section class="merchant-dashboard__layer">
      <div class="merchant-dashboard__layer-head">
        <h3>详细分析</h3>
        <p>用于答辩追问时补充说明证据，不再占据首页第一优先级。</p>
      </div>

      <div class="merchant-dashboard__layer-grid merchant-dashboard__layer-grid--detail">
        <HotProductsView
          :products="hotProducts"
          :regions="regionItems"
        />
        <FunnelView :funnel="funnel" />
        <article class="dashboard-panel">
          <div class="dashboard-panel__header">
            <div>
              <p class="section-kicker">COLD PRODUCTS</p>
              <h3>冷门商品</h3>
              <p>识别近期热度偏低商品，便于及时促销。</p>
            </div>
            <span class="dashboard-panel__badge">{{ coldProducts.length }} 个待关注</span>
          </div>

          <ul v-if="coldProducts.length" class="strategy-list">
            <li v-for="item in coldProducts" :key="item.product_id" class="strategy-list__item">
              <div class="strategy-list__meta">
                <strong>{{ item.product_name }}</strong>
                <span>热度 {{ item.hot_score ?? item.count ?? 0 }}</span>
              </div>
              <p>近期曝光和互动偏低，建议结合活动或推荐位提升关注度。</p>
              <div class="merchant-action-buttons">
                <button
                  class="ghost-button"
                  type="button"
                  :disabled="actionInFlightKey === buildActionKey(item.product_id, 'promote')"
                  @click="handleRecordAction(item.product_id, 'promote')"
                >
                  {{ actionInFlightKey === buildActionKey(item.product_id, 'promote') ? '提交中...' : '加入促销' }}
                </button>
              </div>
              <div v-if="getExecutedActionLabels(item.product_id, ['promote']).length" class="merchant-action-tags">
                <span
                  v-for="label in getExecutedActionLabels(item.product_id, ['promote'])"
                  :key="`${item.product_id}-${label}`"
                  class="merchant-action-tag"
                >
                  {{ label }}
                </span>
              </div>
            </li>
          </ul>
          <p v-else class="empty-state">当前暂无明显冷门商品。</p>
        </article>
        <StrategyView :items="strategyItems" />
      </div>
    </section>
  </section>
</template>
