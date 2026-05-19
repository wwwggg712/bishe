import { beforeEach, describe, expect, it, vi } from 'vitest'
import { flushPromises, mount } from '@vue/test-utils'

vi.mock('../api/admin.js', () => ({
  fetchAdminUsers: vi.fn(),
  fetchJobs: vi.fn(),
  fetchAdminLogPreview: vi.fn(),
  fetchAdminLogMetrics: vi.fn(),
  fetchAdminAlgorithmPipeline: vi.fn(),
  fetchSimulationTasks: vi.fn(),
  runJob: vi.fn(),
  cleanupAdminLogs: vi.fn()
}))

vi.mock('../api/simulation.js', () => ({
  generateSimulationBulk: vi.fn(),
  generateSimulationOnce: vi.fn(),
  startSimulationTask: vi.fn(),
  stopSimulationTask: vi.fn()
}))

import {
  fetchAdminAlgorithmPipeline,
  fetchAdminLogMetrics,
  fetchAdminUsers,
  fetchJobs,
  cleanupAdminLogs,
  fetchSimulationTasks,
  runJob
} from '../api/admin.js'
import {
  generateSimulationBulk,
  generateSimulationOnce,
  startSimulationTask,
  stopSimulationTask
} from '../api/simulation.js'
import AdminLogPreviewPage from '../views/admin/AdminLogPreviewPage.vue'
import AdminTasksPage from '../views/admin/AdminTasksPage.vue'
import AdminUsersPage from '../views/admin/AdminUsersPage.vue'

describe('admin standalone pages', () => {
  beforeEach(() => {
    fetchJobs.mockResolvedValue({
      jobs: [
        {
          name: 'scheduled_simulation',
          title: '日志模拟任务',
          schedule: '每5分钟',
          lastRunAt: '2026-05-12 10:00:00',
          status: 'running'
        }
      ]
    })
    fetchSimulationTasks.mockResolvedValue({
      tasks: [
        {
          id: 1,
          name: 'scheduled_simulation',
          task_type: 'simulation',
          status: 'running',
          lastRunAt: '2026-05-12T10:00:00'
        }
      ]
    })
    runJob.mockResolvedValue({ message: '任务已触发' })
    cleanupAdminLogs.mockResolvedValue({
      total_before: 1280,
      kept_count: 500,
      deleted_count: 780
    })
    startSimulationTask.mockResolvedValue({
      generated_count: 20,
      task: { status: 'running' }
    })
    stopSimulationTask.mockResolvedValue({
      task: { status: 'stopped' }
    })
    generateSimulationOnce.mockResolvedValue({
      generated_count: 20,
      preview: []
    })
    generateSimulationBulk.mockResolvedValue({
      generated_count: 2000,
      preview: []
    })
    fetchAdminUsers.mockResolvedValue({
      total: 3,
      users: [
        { id: 1, role: 'admin', status: 'active', nickname: '管理员A' },
        { id: 2, role: 'merchant', status: 'active', nickname: '商家A' },
        { id: 3, role: 'customer', status: 'active', nickname: '用户A' }
      ]
    })
    fetchAdminLogMetrics.mockResolvedValue({
      summary: {
        total_logs: 1280,
        latest_timestamp: '2026-05-13T15:00:00',
        last_minute_added: 20
      },
      action_breakdown: [
        { action_type: '浏览', count: 620 },
        { action_type: '点击', count: 280 }
      ],
      category_breakdown: [
        { category: '运动鞋', count: 680 },
        { category: '运动服', count: 240 }
      ],
      selected_category: '运动鞋',
      brand_breakdown: [
        { brand: '云步', count: 520 },
        { brand: '活力穿', count: 180 }
      ]
    })
    fetchAdminAlgorithmPipeline.mockResolvedValue({
      log_input: {
        total_logs: 1280,
        action_type_count: 5,
        latest_timestamp: '2026-05-13T15:00:00'
      },
      aggregation: {
        behavior_count: 1280,
        view_count: 620,
        purchase_count: 96,
        region_count: 4
      },
      scoring: {
        weight_rule: 'view=1, click=2, favorite=3, cart=5, purchase=8',
        hot_product_count: 10,
        cold_product_count: 10
      },
      portrait_and_recommendation: {
        real_action_logs: 48,
        cold_start_state: '已进入个性化',
        recommendation_mode: 'personalized'
      },
      anomalies: {
        high_risk_count: 2,
        medium_risk_count: 3,
        window_rule: '最近2天 vs 前3天'
      },
      segmentation: {
        high_value_users: 6,
        potential_users: 18,
        inactive_users: 23
      },
      ai_meta: {
        mode: 'provider',
        provider: 'openai-compatible',
        model: 'deepseek-chat'
      }
    })
  })

  it('renders admin tasks page with live jobs', async () => {
    const wrapper = mount(AdminTasksPage)
    await flushPromises()

    expect(wrapper.text()).toContain('任务管理')
    expect(wrapper.text()).toContain('日志模拟任务')
    expect(wrapper.text()).toContain('日志生成与清理')
    expect(wrapper.text()).toContain('保留最新')
    expect(wrapper.text()).toContain('快速生成 2000 条')
    expect(wrapper.text()).toContain('立即生成一批')
    expect(wrapper.text()).toContain('立即执行')
  })

  it('renders and triggers the 2000-log shortcut from the admin task page', async () => {
    const wrapper = mount(AdminTasksPage)
    await flushPromises()

    expect(wrapper.text()).toContain('快速生成 2000 条')

    await wrapper.find('button[data-testid="admin-generate-bulk"]').trigger('click')
    await flushPromises()

    expect(generateSimulationBulk).toHaveBeenCalled()
  })

  it('renders admin users page with real user data', async () => {
    const wrapper = mount(AdminUsersPage)
    await flushPromises()

    expect(wrapper.text()).toContain('用户管理')
    expect(wrapper.text()).toContain('管理员')
    expect(wrapper.text()).toContain('商家')
    expect(wrapper.text()).toContain('用户')
    expect(wrapper.text()).toContain('3 个账号')
  })

  it('renders admin log preview page with summary and metrics', async () => {
    const wrapper = mount(AdminLogPreviewPage)
    await flushPromises()

    expect(wrapper.text()).toContain('日志实时统计')
    expect(wrapper.text()).toContain('日志总量')
    expect(wrapper.text()).toContain('最近1分钟新增')
    expect(wrapper.text()).toContain('品类 → 品牌热度')
    expect(wrapper.text()).toContain('运动鞋')
    expect(wrapper.text()).toContain('云步')
    expect(wrapper.text()).toContain('1280')
    expect(wrapper.text()).toContain('20')
    expect(fetchAdminAlgorithmPipeline).not.toHaveBeenCalled()
    expect(fetchAdminLogMetrics).toHaveBeenCalled()
    wrapper.unmount()
  })
})
