import { flushPromises, mount } from '@vue/test-utils'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { routes } from '../router/index.js'
import AdminOverview from '../views/admin/AdminOverview.vue'

vi.mock('../api/admin.js', () => ({
  fetchJobs: vi.fn(),
  fetchPredictionAnomalies: vi.fn(),
  fetchSystemOverview: vi.fn(),
  runJob: vi.fn()
}))

import { fetchJobs, fetchPredictionAnomalies, fetchSystemOverview, runJob } from '../api/admin.js'

describe('admin overview route', () => {
  it('registers the admin overview view under the admin route', () => {
    const appRoute = routes.find((route) => route.path === '/')
    const adminRoute = appRoute.children.find((route) => route.name === 'admin-overview')

    expect(adminRoute.component).toBe(AdminOverview)
    expect(adminRoute.meta.roles).toEqual(['admin'])
  })
})

describe('admin overview', () => {
  beforeEach(() => {
    fetchSystemOverview.mockResolvedValue({
      metrics: {
        logCount: 18240,
        userCount: 386,
        productCount: 128,
        activeJobs: 4
      },
      logs: [
        {
          id: 'log-1',
          level: 'INFO',
          message: '日志模拟任务已完成新一轮批处理',
          timestamp: '2026-05-12 10:15:00'
        }
      ]
    })

    fetchJobs.mockResolvedValue({
      jobs: [
        {
          name: 'simulation-daily',
          title: '日志模拟任务',
          status: 'running',
          schedule: '每 30 分钟',
          lastRunAt: '2026-05-12 10:00:00'
        },
        {
          name: 'analytics-hourly',
          title: '聚合分析任务',
          status: 'idle',
          schedule: '每 1 小时',
          lastRunAt: '2026-05-12 09:30:00'
        }
      ]
    })
    fetchPredictionAnomalies.mockResolvedValue({
      items: [
        {
          type: 'traffic_spike_low_conversion',
          target: '爆款跑鞋',
          severity: 'high',
          reason: '爆款跑鞋 最近浏览量从 2 增长到 6，但转化率未同步提升，疑似高流量低转化。'
        },
        {
          type: 'region_traffic_spike',
          target: '华东',
          severity: 'medium',
          reason: '华东 地区近期浏览量从 1 上升到 3，建议关注区域投放和库存配置。'
        }
      ]
    })

    runJob.mockResolvedValue({
      message: '任务已触发'
    })
  })

  it('renders system overview, task status and system log sections with loaded data', async () => {
    const wrapper = mount(AdminOverview)

    await flushPromises()

    expect(wrapper.text()).toContain('系统总览')
    expect(wrapper.text()).toContain('任务状态')
    expect(wrapper.text()).toContain('系统日志')
    expect(wrapper.text()).toContain('异常预警')
    expect(wrapper.text()).toContain('18240')
    expect(wrapper.text()).toContain('日志模拟任务')
    expect(wrapper.text()).toContain('聚合分析任务')
    expect(wrapper.text()).toContain('日志模拟任务已完成新一轮批处理')
    expect(wrapper.text()).toContain('爆款跑鞋')
    expect(wrapper.text()).toContain('华东')
  })
})
