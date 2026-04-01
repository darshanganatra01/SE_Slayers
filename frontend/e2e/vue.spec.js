import { test, expect } from '@playwright/test'

const buildUser = (role) => ({
  uid: role === 'admin' ? 'USR-ADMIN01' : 'USR-CUST01',
  full_name: role === 'admin' ? 'Metro Business Owner' : 'Sample Customer',
  email: role === 'admin' ? 'owner@metrohardware.com' : 'customer@example.com',
  role,
  is_active: true,
  customer: role === 'customer'
    ? {
        cid: 'CUS-TEST01',
        customer_name: 'Sample Customer',
        email: 'customer@example.com',
        contact: '9999999999',
      }
    : null,
})

const mockAuthApi = async (page) => {
  await page.addInitScript(() => window.localStorage.clear())

  await page.route('**/api/auth/login', async (route) => {
    const payload = route.request().postDataJSON()
    const email = payload.email?.toLowerCase()

    if (email === 'owner@metrohardware.com') {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ token: 'admin-token', user: buildUser('admin') }),
      })
      return
    }

    if (email === 'customer@example.com') {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ token: 'customer-token', user: buildUser('customer') }),
      })
      return
    }

    await route.fulfill({
      status: 401,
      contentType: 'application/json',
      body: JSON.stringify({ message: 'Invalid email or password.' }),
    })
  })

  await page.route('**/api/auth/me', async (route) => {
    const authHeader = route.request().headers().authorization || ''

    if (authHeader === 'Bearer admin-token') {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ user: buildUser('admin') }),
      })
      return
    }

    if (authHeader === 'Bearer customer-token') {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ user: buildUser('customer') }),
      })
      return
    }

    await route.fulfill({
      status: 401,
      contentType: 'application/json',
      body: JSON.stringify({ message: 'Invalid authentication token.' }),
    })
  })
}

test('customer hitting a protected route gets redirected back after login', async ({ page }) => {
  await mockAuthApi(page)

  await page.goto('/store/orders')
  await expect(page).toHaveURL(/\/store\/login\?redirect=%2Fstore%2Forders/)

  await page.getByLabel('Email address').fill('customer@example.com')
  await page.getByLabel('Password').fill('password123')
  await page.getByRole('button', { name: 'Sign In' }).click()

  await expect(page).toHaveURL(/\/store\/orders$/)
  await expect(page.getByRole('heading', { name: 'Your Orders' })).toBeVisible()
})

test('admin login lands in the business dashboard', async ({ page }) => {
  await mockAuthApi(page)

  await page.goto('/login')
  await page.getByLabel('Email address').fill('owner@metrohardware.com')
  await page.getByLabel('Password').fill('password123')
  await page.getByRole('button', { name: 'Sign In' }).click()

  await expect(page).toHaveURL(/\/dashboard$/)
  await expect(page.getByText('Overview')).toBeVisible()
})

test('failed login shows an inline error message', async ({ page }) => {
  await mockAuthApi(page)

  await page.goto('/login')
  await page.getByLabel('Email address').fill('unknown@example.com')
  await page.getByLabel('Password').fill('bad-password')
  await page.getByRole('button', { name: 'Sign In' }).click()

  await expect(page.getByText('Invalid email or password.')).toBeVisible()
})
