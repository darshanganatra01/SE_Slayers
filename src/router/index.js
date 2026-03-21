import { createRouter, createWebHistory } from 'vue-router'
import OverviewDashboard from '../order_management/components/overview.vue'
import OrderManagement   from '../order_management/management.vue'
import CustomerDashboard from '../order_management/components/customer.vue'
import VendorManagement  from '../vendor_management/management.vue'

const routes = [
  { path: '/',           redirect: '/dashboard' },
  { path: '/dashboard',  component: OverviewDashboard },
  { path: '/orders',     component: OrderManagement },
  { path: '/customers',  component: CustomerDashboard },
  { path: '/vendors',    component: VendorManagement },
  // add as you build:
  // { path: '/inventory', component: () => import('../inventory_management/management.vue') },
]

export default createRouter({
  history: createWebHistory(),
  routes
})