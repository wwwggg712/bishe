<script setup>
import { onMounted, ref } from 'vue'

import { cleanupAdminLogs, fetchJobs, runJob } from '../../api/admin.js'
import { generateSimulationBulk, generateSimulationOnce } from '../../api/simulation.js'
import TaskManagerView from './TaskManagerView.vue'

const jobs = ref([])
const isRunning = ref(false)
const simulationAction = ref('')
const errorMessage = ref('')
const actionMessage = ref('')
const keepLast = ref(20000)

async function loadJobs() {
  const payload = await fetchJobs()
  jobs.value = payload.jobs || []
}

async function handleRunJob(jobName) {
  isRunning.value = true
  errorMessage.value = ''
  actionMessage.value = ''
  try {
    await runJob(jobName)
    await loadJobs()
  } catch (error) {
    errorMessage.value = error?.response?.data?.message || '任务触发失败，请稍后重试。'
  } finally {
    isRunning.value = false
  }
}

async function handleGenerateBulk() {
  simulationAction.value = 'bulk'
  errorMessage.value = ''
  actionMessage.value = ''
  try {
    const response = await generateSimulationBulk()
    actionMessage.value = `已快速生成 ${response.generated_count || 0} 条日志。`
    await loadJobs()
  } catch (error) {
    errorMessage.value = error?.response?.data?.message || '批量日志生成失败，请稍后重试。'
  } finally {
    simulationAction.value = ''
  }
}

async function handleGenerateOnce() {
  simulationAction.value = 'once'
  errorMessage.value = ''
  actionMessage.value = ''
  try {
    const response = await generateSimulationOnce()
    actionMessage.value = `已生成 ${response.generated_count || 0} 条日志。`
    await loadJobs()
  } catch (error) {
    errorMessage.value = error?.response?.data?.message || '日志生成失败，请稍后重试。'
  } finally {
    simulationAction.value = ''
  }
}

async function handleCleanupLogs() {
  simulationAction.value = 'cleanup'
  errorMessage.value = ''
  actionMessage.value = ''
  const value = Number(keepLast.value)
  if (!Number.isFinite(value) || value <= 0) {
    errorMessage.value = '保留条数必须是正整数。'
    simulationAction.value = ''
    return
  }

  try {
    const response = await cleanupAdminLogs(value)
    actionMessage.value = `已清理 ${response.deleted_count || 0} 条日志，当前保留 ${response.kept_count || 0} 条。`
  } catch (error) {
    errorMessage.value = error?.response?.data?.message || '日志清理失败，请稍后重试。'
  } finally {
    simulationAction.value = ''
  }
}

onMounted(async () => {
  await loadJobs()
})
</script>

<template>
  <section class="admin-page">
    <header class="admin-page__header">
      <div>
        <p class="section-kicker">ADMIN TASKS</p>
        <h2>任务管理</h2>
        <p>独立查看和执行日志模拟、聚合分析等后台任务。</p>
      </div>
    </header>

    <p v-if="errorMessage" class="form-error">{{ errorMessage }}</p>
    <p v-else-if="actionMessage" class="admin-action-message">{{ actionMessage }}</p>
    <article class="dashboard-panel">
      <div class="dashboard-panel__header">
        <div>
          <p class="section-kicker">LOG OPERATIONS</p>
          <h3>日志生成与清理</h3>
          <p>用于毕设演示的行为日志批量生成与手动清理入口。</p>
        </div>
        <span class="dashboard-panel__badge">手动触发</span>
      </div>

      <div class="admin-page__actions">
        <button
          class="primary-button"
          type="button"
          data-testid="admin-generate-bulk"
          :disabled="simulationAction === 'bulk' || simulationAction === 'once'"
          @click="handleGenerateBulk"
        >
          {{ simulationAction === 'bulk' ? '生成中...' : '快速生成 2000 条' }}
        </button>
        <button
          class="primary-button"
          type="button"
          :disabled="simulationAction === 'bulk' || simulationAction === 'once'"
          @click="handleGenerateOnce"
        >
          {{ simulationAction === 'once' ? '生成中...' : '立即生成一批' }}
        </button>
      </div>

      <div class="admin-job-cleanup">
        <label class="form-label">
          保留最新
          <input v-model="keepLast" class="form-input" type="number" min="1" step="1" />
          条
        </label>
        <button
          class="ghost-button"
          type="button"
          :disabled="simulationAction === 'cleanup'"
          @click="handleCleanupLogs"
        >
          {{ simulationAction === 'cleanup' ? '清理中...' : '清理日志' }}
        </button>
      </div>
    </article>
    <TaskManagerView :jobs="jobs" :is-running="isRunning" @run-job="handleRunJob" />
  </section>
</template>
