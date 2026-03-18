import { createRouter, createWebHistory } from 'vue-router'
import OverviewDashboard from '../order_management/components/overview.vue'
import OrderManagement   from '../order_management/management.vue'
import CustomerDashboard from '../order_management/components/customer.vue'

const routes = [
  { path: '/',           redirect: '/dashboard' },
  { path: '/dashboard',  component: OverviewDashboard },
  { path: '/orders',     component: OrderManagement },
  { path: '/customers',  component: CustomerDashboard },
  // add as you build:
  // { path: '/inventory', component: () => import('../inventory_management/management.vue') },
  // { path: '/vendors',   component: () => import('../vendor_management/management.vue') },
  // Customer Dashboard Routes (prefixed with /store to avoid conflict):
  {
    path: '/store',
    component: () => import('../customer_dashboard/App.vue'), // Or a layout wrapper if exists
    children: [
      { path: '', name: 'store-index', component: () => import('../customer_dashboard/pages/Index.vue') },
      { path: 'product/:pid', name: 'store-product', component: () => import('../customer_dashboard/pages/ProductDetail.vue') },
      { path: 'cart', name: 'store-cart', component: () => import('../customer_dashboard/pages/Cart.vue') },
      { path: 'checkout', name: 'store-checkout', component: () => import('../customer_dashboard/pages/Checkout.vue') },
      { path: 'orders', name: 'store-orders', component: () => import('../customer_dashboard/pages/Orders.vue') },
      { path: 'order/:coId', name: 'store-order', component: () => import('../customer_dashboard/pages/TransactionDetails.vue') },
      { path: 'login', name: 'store-login', component: () => import('../customer_dashboard/pages/Login.vue') },
      { path: 'register', name: 'store-register', component: () => import('../customer_dashboard/pages/Register.vue') },
      { path: ':pathMatch(.*)*', name: 'store-not-found', component: () => import('../customer_dashboard/pages/NotFound.vue') }
    ]
  }
]

export default createRouter({
  history: createWebHistory(),
  routes
})