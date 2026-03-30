import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'index',
      component: () => import('../pages/Index.vue')
    },
    {
      path: '/product/:pid',
      name: 'product',
      component: () => import('../pages/ProductDetail.vue')
    },
    {
      path: '/cart',
      name: 'cart',
      component: () => import('../pages/Cart.vue')
    },
    {
      path: '/checkout',
      name: 'checkout',
      component: () => import('../pages/Checkout.vue')
    },
    {
      path: '/orders',
      name: 'orders',
      component: () => import('../pages/Orders.vue')
    },
    {
      path: '/order/:coId',
      name: 'order',
      component: () => import('../pages/TransactionDetails.vue')
    },
    {
      path: '/login',
      name: 'login',
      component: () => import('../pages/Login.vue')
    },
    {
      path: '/register',
      name: 'register',
      component: () => import('../pages/Register.vue')
    },
    {
      path: '/:pathMatch(.*)*',
      name: 'not-found',
      component: () => import('../pages/NotFound.vue')
    }
  ]
})

export default router
