<script setup>
import { computed, onMounted, ref } from 'vue'

import {
  fetchCustomerAiExplanation,
  fetchMyRecommendations,
  fetchPreferenceProfile,
  fetchTrendProducts,
  recordCustomerAction
} from '../../api/recommendation.js'

const isLoading = ref(true)
const errorMessage = ref('')
const actionMessage = ref('')
const actionInFlightKey = ref('')
const recommendations = ref([])
const trendProducts = ref([])
const customerAiSummary = ref('')
const isGeneratingAi = ref(false)
const customerAiMeta = ref({
  mode: '',
  provider: '',
  model: ''
})
const recommendationPayloadMode = ref('personalized')
const sessionActions = ref([])
const profile = ref({
  user: {
    nickname: '',
    region: ''
  },
  is_cold_start: false,
  top_categories: [],
  top_actions: [],
  recent_activity: [],
  engagement_score: 0,
  top_active_hours: [],
  price_preference: {
    average_price: 0,
    price_band: ''
  },
  profile_tags: []
})

const recommendationMode = computed(() =>
  recommendationPayloadMode.value === 'fallback' ? 'fallback' : 'personalized'
)
const recommendationTitle = computed(() =>
  recommendationMode.value === 'fallback' ? '冷启动推荐' : '猜你喜欢'
)
const recommendationDescription = computed(() =>
  recommendationMode.value === 'fallback'
    ? '当前暂无足够个人行为，先为你展示热门趋势商品。'
    : '结合个人偏好与当前热度生成推荐理由。'
)
const recentActivity = computed(() => (profile.value.recent_activity || []).slice(0, 5))
const portraitTitle = computed(() =>
  profile.value.is_cold_start ? '冷启动用户' : '我的偏好画像'
)
const portraitDescription = computed(() =>
  profile.value.is_cold_start
    ? '暂无个人行为，当前仅展示基础账号信息。'
    : '基于真实行为日志统计你的偏好类目、消费倾向和活跃时段。'
)
const profileHighlights = computed(() => [
  {
    label: '偏好类目',
    value: profile.value.is_cold_start
      ? '暂无个人偏好'
      : (profile.value.top_categories[0]?.category || '综合偏好')
  },
  {
    label: '消费倾向',
    value: profile.value.price_preference.price_band || '待分析'
  },
  {
    label: '活跃时段',
    value: profile.value.is_cold_start
      ? '暂无个人活跃时段'
      : (profile.value.top_active_hours[0] ? `${profile.value.top_active_hours[0].hour}点` : '待分析')
  },
  {
    label: '常驻地区',
    value: profile.value.user.region || '待分析'
  },
  {
    label: '参与度得分',
    value: profile.value.engagement_score || '0'
  }
])
const ACTION_LABELS = {
  view: '浏览',
  favorite: '收藏',
  cart: '加购',
  purchase: '购买'
}

function buildActionKey(productId, actionType) {
  return `${productId}:${actionType}`
}

function pushSessionAction(product, actionType) {
  sessionActions.value = [
    {
      product_id: product.product_id,
      product_name: product.product_name,
      action_type: actionType,
      action_label: ACTION_LABELS[actionType] || actionType,
      time_label: '刚刚'
    },
    ...sessionActions.value.filter(
      (item) => !(item.product_id === product.product_id && item.action_type === actionType)
    )
  ].slice(0, 5)
}

function formatRecentActivityTime(timestamp) {
  if (!timestamp) {
    return '未知时间'
  }

  return timestamp.replace('T', ' ').slice(0, 16)
}

async function loadCustomerHome() {
  isLoading.value = true
  errorMessage.value = ''

  try {
    const [recommendationPayload, trendPayload, profilePayload] = await Promise.all([
      fetchMyRecommendations(),
      fetchTrendProducts(),
      fetchPreferenceProfile()
    ])

    recommendationPayloadMode.value = recommendationPayload.mode || 'personalized'
    recommendations.value = recommendationPayload.items || []
    trendProducts.value = trendPayload.items || []
    profile.value = {
      ...profile.value,
      ...profilePayload
    }
  } catch (error) {
    errorMessage.value = error?.response?.data?.message || '用户推荐数据加载失败，请稍后重试。'
  } finally {
    isLoading.value = false
  }
}

async function handleCustomerAction(productId, actionType) {
  actionInFlightKey.value = buildActionKey(productId, actionType)
  actionMessage.value = ''
  errorMessage.value = ''

  try {
    const product = recommendations.value.find((item) => item.product_id === productId)
    await recordCustomerAction({
      product_id: productId,
      action_type: actionType
    })
    if (product) {
      pushSessionAction(product, actionType)
    }
    actionMessage.value = `已记录${ACTION_LABELS[actionType]}行为`
    await loadCustomerHome()
  } catch (error) {
    errorMessage.value = error?.response?.data?.message || '用户行为记录失败，请稍后重试。'
  } finally {
    actionInFlightKey.value = ''
  }
}

async function handleGenerateAiExplanation() {
  isGeneratingAi.value = true
  errorMessage.value = ''

  try {
    const payload = await fetchCustomerAiExplanation({
      product_name: recommendations.value[0]?.product_name || '热门趋势商品',
      trend_product_name: trendProducts.value[0]?.product_name || '趋势商品',
      preferred_category: profile.value.is_cold_start
        ? '暂无个人偏好'
        : (profile.value.top_categories[0]?.category || '综合偏好'),
      price_band: profile.value.price_preference.price_band || '暂无数据',
      active_hour: profile.value.is_cold_start
        ? '暂无个人活跃时段'
        : (profile.value.top_active_hours[0]
          ? `${profile.value.top_active_hours[0].hour}点`
          : '晚间')
    })
    customerAiSummary.value = payload.summary || 'AI 推荐解释生成成功。'
    customerAiMeta.value = {
      mode: payload.mode || 'fallback',
      provider: payload.provider || 'internal',
      model: payload.model || 'rule-based-fallback'
    }
  } catch (error) {
    errorMessage.value = error?.response?.data?.message || 'AI 推荐解释生成失败，请稍后重试。'
  } finally {
    isGeneratingAi.value = false
  }
}

onMounted(() => {
  loadCustomerHome()
})
</script>

<template>
  <section class="customer-home">
    <header class="customer-home__hero">
      <div>
        <p class="section-kicker">CUSTOMER RECOMMENDATION</p>
        <h2>{{ recommendationTitle }}</h2>
        <p>
          为 {{ profile.user.nickname || '你' }} 聚合推荐清单、趋势上升商品和偏好画像，帮助快速完成浏览决策。
        </p>
      </div>
      <button class="ghost-button" type="button" @click="loadCustomerHome">刷新推荐</button>
    </header>

    <p v-if="errorMessage" class="form-error">{{ errorMessage }}</p>

    <section class="customer-home__grid" :aria-busy="isLoading">
      <article class="dashboard-panel">
        <div class="dashboard-panel__header">
          <div>
            <h3>{{ recommendationTitle }}</h3>
            <p>{{ recommendationDescription }}</p>
          </div>
          <span class="dashboard-panel__badge">{{ recommendations.length }} 条</span>
        </div>

        <p v-if="actionMessage" class="admin-log-preview__note">{{ actionMessage }}</p>

        <ul v-if="recommendations.length" class="recommend-list">
          <li
            v-for="item in recommendations"
            :key="item.product_id"
            class="recommend-list__item"
          >
            <strong>{{ item.product_name }}</strong>
            <span>{{ item.category }}</span>
            <p>{{ item.reason }}</p>
            <div class="customer-action-buttons">
              <button
                class="ghost-button"
                type="button"
                :data-testid="`customer-action-view-${item.product_id}`"
                :disabled="actionInFlightKey === buildActionKey(item.product_id, 'view')"
                @click="handleCustomerAction(item.product_id, 'view')"
              >
                浏览
              </button>
              <button
                class="ghost-button"
                type="button"
                :data-testid="`customer-action-favorite-${item.product_id}`"
                :disabled="actionInFlightKey === buildActionKey(item.product_id, 'favorite')"
                @click="handleCustomerAction(item.product_id, 'favorite')"
              >
                收藏
              </button>
              <button
                class="ghost-button"
                type="button"
                :data-testid="`customer-action-cart-${item.product_id}`"
                :disabled="actionInFlightKey === buildActionKey(item.product_id, 'cart')"
                @click="handleCustomerAction(item.product_id, 'cart')"
              >
                加购
              </button>
              <button
                class="ghost-button"
                type="button"
                :data-testid="`customer-action-purchase-${item.product_id}`"
                :disabled="actionInFlightKey === buildActionKey(item.product_id, 'purchase')"
                @click="handleCustomerAction(item.product_id, 'purchase')"
              >
                购买
              </button>
            </div>
          </li>
        </ul>
        <p v-else class="empty-state">
          {{ recommendationMode === 'fallback' ? '当前暂无可展示的冷启动推荐。' : '暂无个性化推荐，请稍后刷新。' }}
        </p>
      </article>

      <article class="dashboard-panel">
        <div class="dashboard-panel__header">
          <div>
            <h3>趋势上升商品</h3>
            <p>筛选近期热度提升的商品，辅助发现潜力品类。</p>
          </div>
          <span class="dashboard-panel__badge">{{ trendProducts.length }} 个</span>
        </div>

        <ul v-if="trendProducts.length" class="trend-list">
          <li
            v-for="item in trendProducts"
            :key="item.product_id"
            class="trend-list__item"
          >
            <div>
              <strong>{{ item.product_name }}</strong>
              <p>当前热度 {{ item.current_score }}</p>
            </div>
            <span>+{{ item.delta }}</span>
          </li>
        </ul>
        <p v-else class="empty-state">暂无趋势上升商品，请稍后刷新。</p>
      </article>

      <article class="dashboard-panel">
        <div class="dashboard-panel__header">
          <div>
            <h3>{{ portraitTitle }}</h3>
            <p>{{ portraitDescription }}</p>
          </div>
          <span class="dashboard-panel__badge">{{ profile.user.nickname || '画像' }}</span>
        </div>

        <dl class="profile-grid">
          <div
            v-for="item in profileHighlights"
            :key="item.label"
            class="profile-grid__item"
          >
            <dt>{{ item.label }}</dt>
            <dd>{{ item.value }}</dd>
          </div>
        </dl>

        <div v-if="profile.profile_tags?.length" class="profile-tags">
          <span v-for="tag in profile.profile_tags" :key="tag" class="profile-tag">
            {{ tag }}
          </span>
        </div>
      </article>

      <article class="dashboard-panel">
        <div class="dashboard-panel__header">
          <div>
            <h3>AI 推荐解释</h3>
            <p>用自然语言说明为什么推荐给你，以及最近值得关注的趋势商品。</p>
          </div>
          <button
            class="ghost-button"
            type="button"
            data-testid="customer-ai-generate"
            :disabled="isGeneratingAi"
            @click="handleGenerateAiExplanation"
          >
            {{ isGeneratingAi ? '生成中...' : '生成 AI 推荐解释' }}
          </button>
        </div>

        <div v-if="customerAiMeta.mode" class="dashboard-panel__meta-list">
          <span>当前模式：{{ customerAiMeta.mode === 'provider' ? '外部模型' : '内置回退' }}</span>
          <span>模型来源：{{ customerAiMeta.provider }}</span>
          <span>模型名称：{{ customerAiMeta.model }}</span>
        </div>
        <p v-if="customerAiSummary" class="admin-log-preview__note">{{ customerAiSummary }}</p>
        <p v-else class="empty-state">点击按钮后生成 AI 推荐解释，展示推荐结果并非黑盒输出。</p>
      </article>
    </section>

    <section class="customer-activity-grid">
      <article class="dashboard-panel">
        <div class="dashboard-panel__header">
          <div>
            <h3>本次会话刚刚操作</h3>
            <p>用于展示你在本轮演示里刚刚触发的用户行为。</p>
          </div>
          <span class="dashboard-panel__badge">{{ sessionActions.length }} 条</span>
        </div>

        <ul v-if="sessionActions.length" class="recommend-list">
          <li
            v-for="item in sessionActions"
            :key="`${item.product_id}-${item.action_type}`"
            class="recommend-list__item"
          >
            <strong>{{ item.product_name }}</strong>
            <span>{{ item.action_label }}</span>
            <p>{{ item.time_label }}</p>
          </li>
        </ul>
        <p v-else class="empty-state">你还没有进行操作，可先点击浏览、收藏、加购或购买。</p>
      </article>

      <article class="dashboard-panel">
        <div class="dashboard-panel__header">
          <div>
            <h3>最近 5 条画像依据</h3>
            <p>这些是系统用于生成历史画像的个人日志，不等同于你本次演示里刚刚点击的操作。</p>
          </div>
          <span class="dashboard-panel__badge">{{ recentActivity.length }} 条</span>
        </div>

        <ul v-if="recentActivity.length" class="recommend-list">
          <li
            v-for="item in recentActivity"
            :key="item.log_id || `${item.product_id}-${item.action_type}-${item.timestamp}`"
            class="recommend-list__item"
          >
            <strong>{{ item.product_name }}</strong>
            <span>{{ ACTION_LABELS[item.action_type] || item.action_type }}</span>
            <p>{{ formatRecentActivityTime(item.timestamp) }}</p>
          </li>
        </ul>
        <p v-else class="empty-state">当前暂无历史个人行为记录。</p>
      </article>
    </section>
  </section>
</template>
