<template>
  <div v-if="cartStore.items.length === 0" class="container py-16 text-center">
    <p class="text-4xl">🛒</p>
    <h2 class="mt-4 text-xl font-semibold text-foreground">Your cart is empty</h2>
    <p class="mt-1 text-muted-foreground">Browse products and add items to your cart.</p>
    <Button class="mt-4" @click="router.push('/store')">Continue Shopping</Button>
  </div>

  <div v-else class="container py-6">
    <h1 class="mb-4 text-2xl font-bold text-foreground">Shopping Cart</h1>

    <div class="space-y-3">
      <Card v-for="item in cartStore.items" :key="item.sku.skuId">
        <CardContent class="flex items-center gap-4 p-4">
          <div class="flex h-16 w-16 shrink-0 items-center justify-center overflow-hidden rounded-md bg-secondary text-3xl">
            <template v-if="isImagePath(item.product.image)">
              <img :src="processPath(item.product.image)" :alt="item.product.pName" class="h-full w-full object-contain p-1" />
            </template>
            <template v-else>
              {{ item.product.image }}
            </template>
          </div>
          <div class="flex-1 min-w-0">
            <h3 class="font-semibold text-foreground truncate">{{ item.product.pName }}</h3>
            <p class="text-sm text-muted-foreground">{{ formatSpecs(item.sku.specs) }}</p>
          </div>
          <div class="flex items-center gap-2">
            <Button variant="outline" size="icon" class="h-7 w-7" @click="cartStore.updateQuantity(item.sku.skuId, item.quantity - 1)">
              <Minus class="h-3 w-3" />
            </Button>
            <span class="w-8 text-center text-sm font-semibold">{{ item.quantity }}</span>
            <Button variant="outline" size="icon" class="h-7 w-7" @click="cartStore.updateQuantity(item.sku.skuId, item.quantity + 1)">
              <Plus class="h-3 w-3" />
            </Button>
          </div>
          <div class="w-24 text-right">
            <p class="font-bold text-primary">₹{{ (item.sku.currentSell * item.quantity).toLocaleString() }}</p>
            <p class="text-[10px] text-muted-foreground uppercase">₹{{ item.sku.currentSell }} / unit</p>
          </div>
          <Button variant="ghost" size="icon" class="text-destructive" @click="cartStore.removeItem(item.sku.skuId)">
            <Trash2 class="h-4 w-4" />
          </Button>
        </CardContent>
      </Card>
    </div>

    <Card class="mt-6">
      <CardContent class="flex items-center justify-between p-6">
        <div>
          <p class="text-sm text-muted-foreground">Total ({{ cartStore.items.length }} items)</p>
          <p class="text-2xl font-bold text-foreground">₹{{ cartStore.totalPrice.toLocaleString() }}</p>
        </div>
        <Button size="lg" @click="router.push('/store/checkout')">
          Proceed to Buy
        </Button>
      </CardContent>
    </Card>
  </div>
</template>

<script setup lang="ts">
import { watchEffect } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@cd/stores/auth'
import { useCartStore } from '@cd/stores/cart'
import Button from '@cd/components/ui/Button.vue'
import Card from '@cd/components/ui/Card.vue'
import CardContent from '@cd/components/ui/CardContent.vue'
import { Minus, Plus, Trash2 } from 'lucide-vue-next'

const router = useRouter()
const authStore = useAuthStore()
const cartStore = useCartStore()

watchEffect(() => {
  if (!authStore.isAuthenticated) {
    router.replace('/store/login')
  }
})

const isImagePath = (img: string) => {
  return img.startsWith('@') || img.startsWith('/') || img.includes('.')
}

const processPath = (path: string) => {
  if (path.startsWith('@')) {
    return path.replace('@', '/src')
  }
  return path
}

const formatSpecs = (specsString: string) => {
  try {
    const specs = JSON.parse(specsString)
    return specs.size || specsString
  } catch (e) {
    return specsString
  }
}
</script>

