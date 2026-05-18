<script setup>
import { ref } from 'vue'

const props = defineProps({
  jobs: {
    type: Array,
    default: () => []
  },
  isRunning: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['run-job'])

const activeJobName = ref('')

const statusLabelMap = {
  running: '运行中',
  idle: '空闲',
  success: '成功',
  failed: '失败'
}

function resolveStatusLabel(status) {
  return statusLabelMap[status] || '待执行'
}

async function handleRun(jobName) {
  activeJobName.value = jobName

  try {
    await emit('run-job', jobName)
  } finally {
    activeJobName.value = ''
  }
}
</script>

<template>
  <article class="dashboard-panel">
    <div class="dashboard-panel__header">
      <div>
        <p class="section-kicker">TASK STATUS</p>
        <h3>任务状态</h3>
        <p>管理日志模拟、聚合分析和报告生成任务。</p>
      </div>
      <span class="dashboard-panel__badge">{{ jobs.length }} 个任务</span>
    </div>

    <ul v-if="jobs.length" class="admin-job-list">
      <li v-for="job in jobs" :key="job.name" class="admin-job-list__item">
        <div class="admin-job-list__meta">
          <div>
            <strong>{{ job.title }}</strong>
            <p>{{ job.schedule }} · 最近执行 {{ job.lastRunAt }}</p>
          </div>
          <span class="admin-status-pill" :data-status="job.status">
            {{ resolveStatusLabel(job.status) }}
          </span>
        </div>

        <button
          class="ghost-button"
          type="button"
          :disabled="isRunning || activeJobName === job.name"
          @click="handleRun(job.name)"
        >
          {{ activeJobName === job.name ? '触发中...' : '立即执行' }}
        </button>
      </li>
    </ul>
    <p v-else class="empty-state">当前暂无任务配置，请先初始化调度任务。</p>
  </article>
</template>
