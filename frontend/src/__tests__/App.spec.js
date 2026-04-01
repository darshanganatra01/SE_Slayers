import { describe, expect, it } from 'vitest'
import { createMemoryHistory } from 'vue-router'

import { createAppRouter, getNavigationRedirect, resolveAuthenticatedRedirect } from '../router'

describe('auth route guards', () => {
  it('redirects unauthenticated admin traffic to the shared login page', async () => {
    const router = createAppRouter(createMemoryHistory())
    const target = router.resolve('/dashboard')

    expect(getNavigationRedirect(target, { isAuthenticated: false, role: null }, router)).toEqual({
      path: '/login',
      query: { redirect: '/dashboard' },
    })
  })

  it('redirects unauthenticated customer-only traffic to the store login path', async () => {
    const router = createAppRouter(createMemoryHistory())
    const target = router.resolve('/store/orders')

    expect(getNavigationRedirect(target, { isAuthenticated: false, role: null }, router)).toEqual({
      path: '/store/login',
      query: { redirect: '/store/orders' },
    })
  })

  it('sends customers away from admin-only routes', async () => {
    const router = createAppRouter(createMemoryHistory())
    const target = router.resolve('/dashboard')

    expect(getNavigationRedirect(target, { isAuthenticated: true, role: 'customer' }, router)).toBe('/store')
  })

  it('sends admins away from customer-only routes', async () => {
    const router = createAppRouter(createMemoryHistory())
    const target = router.resolve('/store/orders')

    expect(getNavigationRedirect(target, { isAuthenticated: true, role: 'admin' }, router)).toBe('/dashboard')
  })

  it('keeps authenticated customers off guest-only pages and restores valid redirects', async () => {
    const router = createAppRouter(createMemoryHistory())
    const target = router.resolve('/login?redirect=/store/orders')

    expect(getNavigationRedirect(target, { isAuthenticated: true, role: 'customer' }, router)).toBe('/store/orders')
  })
})

describe('resolveAuthenticatedRedirect', () => {
  it('returns the requested protected customer route when the role can access it', () => {
    const router = createAppRouter(createMemoryHistory())

    expect(resolveAuthenticatedRedirect(router, 'customer', '/store/orders')).toBe('/store/orders')
  })

  it('falls back to the role home when the requested path is not allowed', () => {
    const router = createAppRouter(createMemoryHistory())

    expect(resolveAuthenticatedRedirect(router, 'customer', '/dashboard')).toBe('/store')
    expect(resolveAuthenticatedRedirect(router, 'admin', '/store/orders')).toBe('/dashboard')
  })
})
