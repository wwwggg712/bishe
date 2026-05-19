<script setup>
import { computed, onMounted, ref } from 'vue'

import { fetchAdminLogMetrics } from '../../api/admin.js'
import { useAutoRefresh } from '../../composables/useAutoRefresh.js'
import TrendBarChart from '../../components/charts/TrendBarChart.vue'

const isLoading = ref(true)
const errorMessage = ref('')
const selectedCategory = ref('')
const payload = ref({
  summary: {
    total_logs: 0,
    latest_timestamp: '暂无数据',
    last_minute_added: 0
  },
  action_breakdown: [],
  category_breakdown: [],
  selected_category: '',
  brand_breakdown: []
})

function normalizePayload(data = {}) {
  return {
    summary: {
      total_logs: data.summary?.total_logs || 0,
      latest_timestamp: data.summary?.latest_timestamp || '暂无数据',
      last_minute_added: data.summary?.last_minute_added || 0
    },
    action_breakdown: data.action_breakdown || [],
    category_breakdown: data.category_breakdown || [],
    selected_category: data.selected_category || '',
    brand_breakdown: data.brand_breakdown || []
  }
}

const summaryCards = computed(() => [
  {
    label: '日志总量',
    value: payload.value.summary.total_logs,
    hint: 'behavior_logs 表累计条数'
  },
  {
    label: '最近写入时间',
    value: payload.value.summary.latest_timestamp,
    hint: '最新一条日志的时间戳'
  },
  {
    label: '最近1分钟新增',
    value: payload.value.summary.last_minute_added,
    hint: '用于答辩演示“实时变化”'
  }
])

async function loadMetrics() {
  isLoading.value = true
  errorMessage.value = ''

  try {
    const metrics = await fetchAdminLogMetrics(
      selectedCategory.value ? { category: selectedCategory.value } : {}
    )
    const normalized = normalizePayload(metrics)
    payload.value = normalized
    if (!selectedCategory.value) {
      selectedCategory.value = normalized.selected_category
      return
    }
    if (normalized.selected_category && normalized.selected_category !== selectedCategory.value) {
      selectedCategory.value = normalized.selected_category
    }
  } catch (error) {
    errorMessage.value = error?.response?.data?.message || '日志统计加载失败，请稍后重试。'
  } finally {
    isLoading.value = false
  }
}

const autoRefresh = useAutoRefresh(loadMetrics, { defaultEnabled: true, defaultIntervalSec: 60 })

function handleAutoRefreshIntervalChange(event) {
  const nextValue = Number(event?.target?.value)
  if (!Number.isFinite(nextValue) || nextValue <= 0) return
  autoRefresh.intervalSec.value = nextValue
}

function handleCategoryChange(event) {
  selectedCategory.value = event?.target?.value || ''
  autoRefresh.refreshNow(true)
}

onMounted(() => {
  autoRefresh.refreshNow(true)
})
</script>

<template>
  <section class="admin-page">
    <header class="admin-page__header admin-overview__hero">
      <div>
        <p class="section-kicker">LOG MONITOR</p>
        <h2>日志实时统计</h2>
        <p>不展示原始明细日志，通过统计指标证明日志在后台持续写入并驱动分析结果刷新。</p>
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
        <button class="ghost-button" type="button" @click="autoRefresh.refreshNow(true)">刷新数据</button>
      </div>
    </header>

    <p v-if="errorMessage" class="form-error">{{ errorMessage }}</p>

    <section class="admin-overview__summary" :aria-busy="isLoading">
      <article v-for="card in summaryCards" :key="card.label" class="metric-card">
        <p class="metric-card__label">{{ card.label }}</p>
        <strong class="metric-card__value">{{ card.value }}</strong>
        <span class="metric-card__hint">{{ card.hint }}</span>
      </article>
    </section>

    <section class="admin-log-preview__grid">
      <article class="dashboard-panel">
        <div class="dashboard-panel__header">
          <div>
            <p class="section-kicker">ACTION BREAKDOWN</p>
            <h3>行为分布</h3>
            <p>快速查看当前日志中五类行为的大致分布情况。</p>
          </div>
          <span class="dashboard-panel__badge">{{ payload.summary.total_logs }} 条日志</span>
        </div>

        <ul v-if="payload.action_breakdown.length" class="region-list__items">
          <li
            v-for="item in payload.action_breakdown"
            :key="item.action_type"
            class="region-list__item"
          >
            <span>{{ item.action_type }}</span>
            <strong>{{ item.count }}</strong>
          </li>
        </ul>
        <p v-else class="empty-state">当前暂无行为日志，请先在任务管理页启动模拟任务。</p>
      </article>

      <article class="dashboard-panel">
        <div class="dashboard-panel__header">
          <div>
            <p class="section-kicker">CATEGORY & BRAND</p>
            <h3>品类 → 品牌热度</h3>
            <p>先看热门品类，再看该品类下品牌热度，避免只看品牌难以理解。</p>
          </div>
          <div style="display: inline-flex; align-items: center; gap: 8px;">
            <select
              class="admin-log-preview__page-size"
              :value="selectedCategory"
              :disabled="!payload.category_breakdown.length"
              @change="handleCategoryChange"
            >
              <option v-if="!payload.category_breakdown.length" value="">暂无品类</option>
              <option
                v-for="item in payload.category_breakdown"
                :key="item.category"
                :value="item.category"
              >
                {{ item.category }}
              </option>
            </select>
            <span class="dashboard-panel__badge">{{ payload.brand_breakdown.length }} 个品牌</span>
          </div>
        </div>

        <ul v-if="payload.category_breakdown.length" class="region-list__items" style="margin-bottom: 18px;">
          <li
            v-for="item in payload.category_breakdown"
            :key="item.category"
            class="region-list__item"
          >
            <span>{{ item.category }}</span>
            <strong>{{ item.count }}</strong>
          </li>
        </ul>

        <TrendBarChart
          v-if="payload.brand_breakdown.length"
          :items="payload.brand_breakdown"
          label-key="brand"
        />
        <p v-else class="empty-state">暂无品牌数据</p>
      </article>
    </section>
  </section>
</template>
