import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore, defaultRouteForRole } from '../stores/auth'
import { pinia } from '../stores/pinia'
import OverviewDashboard from '../order_management/components/overview.vue'
import OrderManagement   from '../order_management/management.vue'
import CustomerDashboard from '../order_management/components/customer.vue'
import VendorManagement  from '../vendor_management/management.vue'

const loginRoute = () => import('../pages/LoginPage.vue')

export const routes = [
  { path: '/', meta: { hideShell: true }, component: () => import('../pages/LandingPage.vue') },
  { path: '/login', meta: { hideShell: true, guestOnly: true }, component: loginRoute },
  { path: '/dashboard', meta: { requiresAuth: true, allowedRoles: ['admin'] }, component: OverviewDashboard },
  { path: '/orders', meta: { requiresAuth: true, allowedRoles: ['admin'] }, component: OrderManagement },
  { path: '/customers', meta: { requiresAuth: true, allowedRoles: ['admin'] }, component: CustomerDashboard },
  { path: '/vendors', name: 'vendors', meta: { requiresAuth: true, allowedRoles: ['admin'] }, component: VendorManagement },
  { path: '/vendors/:vendorId', name: 'vendor-details', meta: { requiresAuth: true, allowedRoles: ['admin'] }, component: VendorManagement },
  { path: '/inventory', meta: { requiresAuth: true, allowedRoles: ['admin'] }, component: () => import('../inventory_management/inventory.vue') },
  { path: '/demand-forecast', meta: { requiresAuth: true, allowedRoles: ['admin'] }, component: () => import('../inventory_management/DemandForecast.vue') },
  { path: '/ai-feature', meta: { requiresAuth: true, allowedRoles: ['admin'] }, component: () => import('../ai_feature/AIFeature.vue') },
  {
    path: '/store',
    meta: { hideShell: true },
    component: () => import('../customer_dashboard/App.vue'),
    children: [
      { path: '', name: 'store-index', component: () => import('../customer_dashboard/pages/Index.vue') },
      { path: 'product/:pid', name: 'store-product', component: () => import('../customer_dashboard/pages/ProductDetail.vue') },
      { path: 'cart', name: 'store-cart', component: () => import('../customer_dashboard/pages/Cart.vue') },
      { path: 'checkout', name: 'store-checkout', meta: { requiresAuth: true, allowedRoles: ['customer'] }, component: () => import('../customer_dashboard/pages/Checkout.vue') },
      { path: 'orders', name: 'store-orders', meta: { requiresAuth: true, allowedRoles: ['customer'] }, component: () => import('../customer_dashboard/pages/Orders.vue') },
      { path: 'order/:coId', name: 'store-order', meta: { requiresAuth: true, allowedRoles: ['customer'] }, component: () => import('../customer_dashboard/pages/TransactionDetails.vue') },
      { path: 'invoice/:invId', name: 'store-invoice', meta: { requiresAuth: true, allowedRoles: ['customer'] }, component: () => import('../customer_dashboard/pages/InvoiceDetail.vue') },
      { path: 'item/:codId', name: 'store-item', meta: { requiresAuth: true, allowedRoles: ['customer'] }, component: () => import('../customer_dashboard/pages/ItemDetail.vue') },
      { path: 'login', name: 'store-login', meta: { guestOnly: true }, component: loginRoute },
      { path: 'register', name: 'store-register', meta: { guestOnly: true }, component: () => import('../customer_dashboard/pages/Register.vue') },
      { path: ':pathMatch(.*)*', name: 'store-not-found', component: () => import('../customer_dashboard/pages/NotFound.vue') }
    ]
  }
]

export const routeRequiresAuth = (route) => route.matched.some((record) => record.meta.requiresAuth)

export const routeAllowsRole = (route, role) => {
  const restrictedRecords = route.matched.filter((record) => Array.isArray(record.meta.allowedRoles))
  if (restrictedRecords.length === 0) return true
  return restrictedRecords.every((record) => record.meta.allowedRoles.includes(role))
}

export const resolveAuthenticatedRedirect = (router, role, requestedPath) => {
  const fallback = defaultRouteForRole(role)
  if (!requestedPath) return fallback

  const resolved = router.resolve(requestedPath)
  if (!resolved.matched.length) return fallback
  if (resolved.matched.some((record) => record.meta.guestOnly)) return fallback
  if (!routeAllowsRole(resolved, role)) return fallback
  return resolved.fullPath
}

export const getNavigationRedirect = (to, authState, router) => {
  if (to.matched.some((record) => record.meta.guestOnly) && authState.isAuthenticated) {
    const requestedPath = typeof to.query.redirect === 'string' ? to.query.redirect : undefined
    return resolveAuthenticatedRedirect(router, authState.role, requestedPath)
  }

  if (!routeRequiresAuth(to)) {
    return true
  }

  if (!authState.isAuthenticated) {
    const loginPath = to.path.startsWith('/store') ? '/store/login' : '/login'
    return {
      path: loginPath,
      query: { redirect: to.fullPath },
    }
  }

  if (!routeAllowsRole(to, authState.role)) {
    return defaultRouteForRole(authState.role)
  }

  return true
}

export const createAppRouter = (history = createWebHistory()) => {
  const router = createRouter({ history, routes })

  router.beforeEach(async (to) => {
    const authStore = useAuthStore(pinia)
    await authStore.initialize()
    return getNavigationRedirect(
      to,
      { isAuthenticated: authStore.isAuthenticated, role: authStore.role },
      router,
    )
  })

  return router
}

export default createAppRouter()
