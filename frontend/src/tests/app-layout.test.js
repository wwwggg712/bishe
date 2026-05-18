import { describe, expect, it, vi } from 'vitest'
import { mount } from '@vue/test-utils'

import AppLayout from '../layouts/AppLayout.vue'

const push = vi.fn()
const clearSession = vi.fn()

vi.mock('vue-router', () => ({
  useRouter: () => ({
    push
  })
}))

vi.mock('../stores/auth', () => ({
  useAuthStore: () => ({
    role: 'merchant',
    user: { nickname: 'Merchant Demo', username: 'merchant_demo' },
    clearSession
  })
}))

describe('AppLayout', () => {
  it('renders merchant section navigation items without hash anchors', () => {
    const wrapper = mount(AppLayout, {
      global: {
        stubs: {
          RouterView: true,
          RouterLink: {
            props: ['to'],
            template: '<a :href="typeof to === `string` ? to : `${to.path}${to.query ? `?section=${to.query.section}` : ``}`"><slot /></a>'
          }
        }
      }
    })

    const links = wrapper.findAll('a')
    const hrefs = links.map((link) => link.attributes('href'))

    expect(hrefs).toContain('/merchant/dashboard?section=overview')
    expect(hrefs).toContain('/merchant/dashboard?section=core')
    expect(hrefs).toContain('/merchant/dashboard?section=analysis')
    expect(hrefs).toContain('/merchant/dashboard?section=detail')
    expect(hrefs.every((href) => !href.includes('#merchant-'))).toBe(true)
  })

  it('marks merchant navigation as a fixed dashboard directory', () => {
    const wrapper = mount(AppLayout, {
      global: {
        stubs: {
          RouterView: true,
          RouterLink: {
            props: ['to'],
            template: '<a :href="typeof to === `string` ? to : `${to.path}${to.query ? `?section=${to.query.section}` : ``}`"><slot /></a>'
          }
        }
      }
    })

    expect(wrapper.find('aside.app-shell__sidebar--merchant').exists()).toBe(true)
    expect(wrapper.find('nav.app-shell__nav--merchant').exists()).toBe(true)
  })
})
