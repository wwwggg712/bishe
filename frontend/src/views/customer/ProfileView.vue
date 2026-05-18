<script setup>
import { computed, onMounted, ref } from 'vue'

import { fetchPreferenceProfile } from '../../api/recommendation.js'

const isLoading = ref(true)
const errorMessage = ref('')
const profile = ref({
  user: {
    nickname: '',
    region: ''
  },
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

const ACTION_LABELS = {
  view: '浏览',
  click: '点击',
  favorite: '收藏',
  cart: '加购',
  purchase: '购买'
}

const topActionItems = computed(() =>
  (profile.value.top_actions || []).map((item) => ({
    ...item,
    action_label: ACTION_LABELS[item.action_type] || item.action_type
  }))
)

const recentActivityItems = computed(() =>
  (profile.value.recent_activity || []).map((item) => ({
    ...item,
    action_label: ACTION_LABELS[item.action_type] || item.action_type
  }))
)

const profileFields = computed(() => [
  { label: '用户昵称', value: profile.value.user.nickname || '未设置' },
  { label: '偏好类目', value: profile.value.top_categories[0]?.category || '综合偏好' },
  { label: '消费倾向', value: profile.value.price_preference.price_band || '待分析' },
  { label: '活跃时段', value: profile.value.top_active_hours[0] ? `${profile.value.top_active_hours[0].hour}点` : '待分析' },
  { label: '常驻地区', value: profile.value.user.region || '待分析' },
  { label: '参与度得分', value: profile.value.engagement_score || '0' }
])

async function loadProfile() {
  isLoading.value = true
  errorMessage.value = ''

  try {
    const payload = await fetchPreferenceProfile()
    profile.value = {
      ...profile.value,
      ...payload
    }
  } catch (error) {
    errorMessage.value = error?.response?.data?.message || '偏好画像加载失败，请稍后重试。'
  } finally {
    isLoading.value = false
  }
}

onMounted(() => {
  loadProfile()
})
</script>

<template>
  <section class="customer-page">
    <header class="customer-page__header">
      <div>
        <p class="section-kicker">PROFILE PORTRAIT</p>
        <h2>个人画像</h2>
        <p>展示基于当前登录用户生成的偏好标签，便于解释推荐结果来源。</p>
      </div>
      <button class="ghost-button" type="button" @click="loadProfile">刷新画像</button>
    </header>

    <p v-if="errorMessage" class="form-error">{{ errorMessage }}</p>

    <div class="dashboard-panel" :aria-busy="isLoading">
      <dl class="profile-grid">
        <div
          v-for="item in profileFields"
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

      <div class="profile-details-grid">
        <article class="dashboard-panel">
          <div class="dashboard-panel__header">
            <div>
              <h3>行为偏好</h3>
              <p>展示历史画像中的高频行为类型，并区分出现次数与行为得分。</p>
            </div>
          </div>
          <ul v-if="topActionItems.length" class="trend-list">
            <li v-for="item in topActionItems" :key="item.action_type" class="trend-list__item">
              <div>
                <strong>{{ item.action_label }}</strong>
                <p>出现次数 {{ item.count }}</p>
              </div>
              <span>行为得分 {{ item.score }}</span>
            </li>
          </ul>
        </article>

        <article class="dashboard-panel">
          <div class="dashboard-panel__header">
            <div>
              <h3>最近行为</h3>
              <p>展示用于生成推荐和画像的最新日志片段。</p>
            </div>
          </div>
          <ul v-if="recentActivityItems.length" class="admin-log-list">
            <li v-for="item in recentActivityItems" :key="item.log_id" class="admin-log-list__item">
              <div class="admin-log-list__meta">
                <span class="admin-status-pill" data-status="info">{{ item.action_label }}</span>
                <strong>{{ item.timestamp }}</strong>
              </div>
              <p>{{ item.product_name }} / {{ item.category }}</p>
            </li>
          </ul>
        </article>
      </div>
    </div>
  </section>
</template>
