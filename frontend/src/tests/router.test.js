import { beforeEach, describe, expect, it } from 'vitest'
import { createPinia, setActivePinia } from 'pinia'

import { attachAuthToken } from '../api/http'
import { createAppRouter, resolveAuthRedirect, routes } from '../router/index.js'
import { useAuthStore } from '../stores/auth'

describe('auth store', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
  })

  it('stores token and role after login success', () => {
    const store = useAuthStore()

    store.setSession({
      token: 'demo-token',
      user: { id: 1, role: 'merchant', username: 'merchant_demo' }
    })

    expect(store.token).toBe('demo-token')
    expect(store.user.role).toBe('merchant')
    expect(store.isAuthenticated).toBe(true)
  })
})

describe('http auth config', () => {
  it('attaches bearer token when one exists', () => {
    const config = attachAuthToken({ headers: {} }, 'demo-token')

    expect(config.headers.Authorization).toBe('Bearer demo-token')
  })
})

describe('router auth rules', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
  })

  it('declares login route and protected app shell', () => {
    expect(routes.some((route) => route.path === '/login')).toBe(true)
    expect(routes.some((route) => route.path === '/')).toBe(true)
    expect(routes.find((route) => route.path === '/').meta.requiresAuth).toBe(true)
  })

  it('registers the admin log preview page under the admin route', () => {
    const appRoute = routes.find((route) => route.path === '/')
    const logRoute = appRoute.children.find((route) => route.name === 'admin-log-preview')

    expect(logRoute.path).toBe('admin/logs')
    expect(logRoute.meta.roles).toEqual(['admin'])
  })

  it('redirects guests away from protected routes', () => {
    const store = useAuthStore()

    expect(
      resolveAuthRedirect(
        { path: '/merchant/dashboard', fullPath: '/merchant/dashboard', meta: { requiresAuth: true } },
        store
      )
    ).toBe('/login?redirect=%2Fmerchant%2Fdashboard')
  })

  it('redirects signed-in users away from login', () => {
    const store = useAuthStore()
    store.setSession({
      token: 'demo-token',
      user: { id: 1, role: 'merchant', username: 'merchant_demo' }
    })

    expect(resolveAuthRedirect({ path: '/login', fullPath: '/login', meta: {} }, store)).toBe('/')
  })

  it('defines scroll behavior for merchant hash navigation', () => {
    const router = createAppRouter()

    expect(typeof router.options.scrollBehavior).toBe('function')

    const scrollTarget = router.options.scrollBehavior(
      { path: '/merchant/dashboard', hash: '#merchant-core', meta: {} },
      { path: '/merchant/dashboard', hash: '', meta: {} },
      null
    )

    expect(scrollTarget).toEqual({
      el: '#merchant-core',
      top: 16,
      behavior: 'smooth'
    })
  })
})
