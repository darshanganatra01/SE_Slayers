<template>
  <header class="sticky top-0 z-50 border-b bg-card">
    <div class="container flex h-14 items-center justify-between">
      <RouterLink to="/store" class="flex items-center gap-2 text-lg font-bold text-primary">
        <div class="logo">
          <img src="/metro-removebg-preview.png" style="width:160px; height:auto; object-fit:contain; display:block; margin-top:-30px; margin-bottom:-30px;"/>
        </div>
      </RouterLink>

      <div class="flex items-center gap-2">
        <Button variant="ghost" size="sm" as-child>
          <RouterLink to="/store/cart">
            <ShoppingCart class="mr-1 h-4 w-4" />
            Cart
            <span
              v-if="cartStore.totalItems > 0"
              class="absolute -right-1 -top-1 flex h-5 w-5 items-center justify-center rounded-full bg-primary text-[10px] font-bold text-primary-foreground"
            >
              {{ cartStore.totalItems }}
            </span>
          </RouterLink>
        </Button>

        <template v-if="authStore.isAuthenticated">
          <Button variant="ghost" size="sm" as-child>
          <RouterLink to="/store/orders">
            <Package class="mr-1 h-4 w-4" />
            Orders
          </RouterLink>
        </Button>
          <Button variant="ghost" size="icon" @click="handleLogout" title="Logout">
            <LogOut class="h-4 w-4" />
          </Button>
        </template>

        <template v-else>
          <Button variant="outline" size="sm" as-child>
            <RouterLink to="/login">Sign In</RouterLink>
          </Button>
          <Button size="sm" as-child>
            <RouterLink to="/store/register">Register</RouterLink>
          </Button>
        </template>
      </div>
    </div>
  </header>
</template>

<script setup lang="ts">
import { RouterLink, useRouter } from 'vue-router'
import { ShoppingCart, Package, LogOut } from 'lucide-vue-next'
import { useAuthStore } from '@/stores/auth'
import { useCartStore } from '@cd/stores/cart'
import Button from '@cd/components/ui/Button.vue'

const authStore = useAuthStore()
const cartStore = useCartStore()
const router = useRouter()

const handleLogout = () => {
  authStore.logout()
  router.push('/login')
}
</script>
