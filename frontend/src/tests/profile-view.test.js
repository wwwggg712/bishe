import { flushPromises, mount } from '@vue/test-utils'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import ProfileView from '../views/customer/ProfileView.vue'

vi.mock('../api/recommendation.js', () => ({
  fetchPreferenceProfile: vi.fn()
}))

import { fetchPreferenceProfile } from '../api/recommendation.js'

describe('profile view', () => {
  beforeEach(() => {
    vi.resetAllMocks()
    fetchPreferenceProfile.mockResolvedValue({
      user: {
        nickname: '小林',
        region: '华东'
      },
      top_categories: [{ category: '智能设备', count: 4, score: 26 }],
      top_actions: [
        { action_type: 'purchase', count: 2, score: 16 },
        { action_type: 'click', count: 2, score: 4 }
      ],
      recent_activity: [
        {
          log_id: 'r1',
          product_id: 1,
          product_name: '智能手表',
          category: '智能设备',
          action_type: 'purchase',
          timestamp: '2026-05-12T10:00:00'
        }
      ],
      engagement_score: 37,
      top_active_hours: [{ hour: 20, count: 3 }],
      price_preference: {
        average_price: 332.5,
        price_band: '中高消费偏好'
      },
      profile_tags: ['智能设备偏好', '20点活跃', '中高消费偏好']
    })
  })

  it('renders action labels and metrics in Chinese without raw english behavior names', async () => {
    const wrapper = mount(ProfileView)

    await flushPromises()

    expect(wrapper.text()).toContain('行为偏好')
    expect(wrapper.text()).toContain('购买')
    expect(wrapper.text()).toContain('点击')
    expect(wrapper.text()).toContain('出现次数 2')
    expect(wrapper.text()).toContain('行为得分 16')
    expect(wrapper.text()).not.toContain('purchase')
    expect(wrapper.text()).not.toContain('click')
    expect(wrapper.text()).not.toContain('按行为得分排序的最近偏好动作')
  })

  it('renders only real customer actions in portrait sections', async () => {
    fetchPreferenceProfile.mockResolvedValue({
      user: {
        nickname: '小林',
        region: '华东'
      },
      top_categories: [{ category: '智能设备', count: 1, score: 8 }],
      top_actions: [{ action_type: 'purchase', count: 1, score: 8 }],
      recent_activity: [
        {
          log_id: 'real-portrait-2',
          product_id: 13,
          product_name: '智能手表',
          category: '智能设备',
          action_type: 'purchase',
          timestamp: '2026-05-13T10:05:00'
        }
      ],
      engagement_score: 8,
      top_active_hours: [{ hour: 10, count: 1 }],
      price_preference: {
        average_price: 599,
        price_band: '高消费偏好'
      },
      profile_tags: ['智能设备偏好', '高消费偏好']
    })

    const wrapper = mount(ProfileView)
    await flushPromises()

    expect(wrapper.text()).toContain('购买')
    expect(wrapper.text()).toContain('智能手表 / 智能设备')
    expect(wrapper.text()).not.toContain('点击')
  })
})
