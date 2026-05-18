<script setup>
import { computed, onMounted, ref } from 'vue'

import { fetchJobs, fetchPredictionAnomalies, fetchSystemOverview, runJob } from '../../api/admin.js'
import TaskManagerView from './TaskManagerView.vue'
import UserManagerView from './UserManagerView.vue'

const isLoading = ref(true)
const isTriggeringJob = ref(false)
const errorMessage = ref('')
const actionMessage = ref('')
const overview = ref({
  metrics: {
    logCount: 0,
    userCount: 0,
    productCount: 0,
    activeJobs: 0
  },
  logs: [],
  users: []
})
const jobs = ref([])
const anomalies = ref([])

const overviewCards = computed(() => [
  {
    label: '日志总量',
    value: overview.value.metrics.logCount,
    hint: '近阶段累计行为日志'
  },
  {
    label: '平台用户数',
    value: overview.value.metrics.userCount,
    hint: '包含管理员、商家与用户'
  },
  {
    label: '商品总数',
    value: overview.value.metrics.productCount,
    hint: '基础商品主数据规模'
  },
  {
    label: '活跃任务',
    value: overview.value.metrics.activeJobs,
    hint: '当前处于运行中的任务'
  }
])

async function loadAdminOverview() {
  isLoading.value = true
  errorMessage.value = ''

  try {
    const [overviewPayload, jobsPayload, anomaliesPayload] = await Promise.all([
      fetchSystemOverview(),
      fetchJobs(),
      fetchPredictionAnomalies()
    ])

    overview.value = {
      ...overview.value,
      ...overviewPayload,
      metrics: {
        ...overview.value.metrics,
        ...(overviewPayload.metrics || {})
      },
      logs: overviewPayload.logs || [],
      users: overviewPayload.users || []
    }
    jobs.value = jobsPayload.jobs || []
    anomalies.value = anomaliesPayload.items || []
  } catch (error) {
    errorMessage.value = error?.response?.data?.message || '管理员总览数据加载失败，请稍后重试。'
  } finally {
    isLoading.value = false
  }
}

async function handleRunJob(jobName) {
  isTriggeringJob.value = true
  actionMessage.value = ''

  try {
    const payload = await runJob(jobName)
    actionMessage.value = payload.message || `任务 ${jobName} 已触发。`
  } catch (error) {
    actionMessage.value = error?.response?.data?.message || '任务触发失败，请稍后重试。'
  } finally {
    isTriggeringJob.value = false
  }
}

onMounted(() => {
  loadAdminOverview()
})
</script>

<template>
  <section class="admin-overview">
    <header class="admin-overview__hero">
      <div>
        <p class="section-kicker">ADMIN CONSOLE</p>
        <h2>系统总览</h2>
        <p>集中查看平台指标、任务状态与系统日志，支持管理员快速掌控运行情况。</p>
      </div>
      <button class="ghost-button" type="button" @click="loadAdminOverview">刷新控制台</button>
    </header>

    <p v-if="errorMessage" class="form-error">{{ errorMessage }}</p>
    <p v-else-if="actionMessage" class="admin-action-message">{{ actionMessage }}</p>

    <section class="admin-overview__summary" :aria-busy="isLoading">
      <article
        v-for="card in overviewCards"
        :key="card.label"
        class="metric-card"
      >
        <p class="metric-card__label">{{ card.label }}</p>
        <strong class="metric-card__value">{{ card.value }}</strong>
        <span class="metric-card__hint">{{ card.hint }}</span>
      </article>
    </section>

    <section class="admin-overview__grid">
      <TaskManagerView
        :jobs="jobs"
        :is-running="isTriggeringJob"
        @run-job="handleRunJob"
      />

      <article class="dashboard-panel">
        <div class="dashboard-panel__header">
          <div>
            <p class="section-kicker">SYSTEM LOG</p>
            <h3>系统日志</h3>
            <p>关注关键任务执行记录与平台运行事件。</p>
          </div>
          <span class="dashboard-panel__badge">{{ overview.logs.length }} 条</span>
        </div>

        <ul v-if="overview.logs.length" class="admin-log-list">
          <li v-for="item in overview.logs" :key="item.id" class="admin-log-list__item">
            <div class="admin-log-list__meta">
              <span class="admin-status-pill" :data-status="item.level?.toLowerCase()">
                {{ item.level }}
              </span>
              <strong>{{ item.timestamp }}</strong>
            </div>
            <p>{{ item.message }}</p>
          </li>
        </ul>
        <p v-else class="empty-state">当前暂无系统日志，可在执行任务后刷新查看。</p>
      </article>

      <article class="dashboard-panel">
        <div class="dashboard-panel__header">
          <div>
            <p class="section-kicker">ANOMALIES</p>
            <h3>异常预警</h3>
            <p>集中查看高浏览低转化、地区流量异常等平台级风险信号。</p>
          </div>
          <span class="dashboard-panel__badge">{{ anomalies.length }} 条</span>
        </div>

        <ul v-if="anomalies.length" class="admin-log-list">
          <li v-for="item in anomalies" :key="`${item.type}-${item.target}`" class="admin-log-list__item">
            <div class="admin-log-list__meta">
              <span class="admin-status-pill" :data-status="item.severity">
                {{ item.severity }}
              </span>
              <strong>{{ item.target }}</strong>
            </div>
            <p>{{ item.reason }}</p>
          </li>
        </ul>
        <p v-else class="empty-state">当前暂无异常预警。</p>
      </article>

      <UserManagerView :users="overview.users" />
    </section>
  </section>
</template>
