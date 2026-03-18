<template>
  <div class="container py-6">
    <Button variant="ghost" size="sm" @click="router.back()" class="mb-4">
      ← Back
    </Button>

    <div v-if="!data" class="container py-10 text-center text-muted-foreground">
      Product not found.
    </div>

    <div v-else class="grid gap-6 md:grid-cols-2">
      <div class="flex h-64 items-center justify-center rounded-lg bg-secondary text-8xl">
        {{ data.product.image }}
      </div>

      <div class="space-y-4">
        <div>
          <p class="text-sm text-muted-foreground">{{ data.product.category }}</p>
          <h1 class="text-2xl font-bold text-foreground">{{ data.product.pName }}</h1>
        </div>

        <p class="text-3xl font-bold text-primary">₹{{ productPrice }}</p>

        <div class="flex items-center gap-3">
          <Button variant="outline" size="icon" @click="qty = Math.max(1, qty - 1)">
            <Minus class="h-4 w-4" />
          </Button>
          <span class="w-10 text-center text-lg font-semibold">{{ qty }}</span>
          <Button variant="outline" size="icon" @click="qty = Math.min(data.sku.stockQty, qty + 1)">
            <Plus class="h-4 w-4" />
          </Button>
          <span class="text-sm text-muted-foreground">({{ data.sku.stockQty }} in stock)</span>
        </div>

        <div class="flex gap-3">
          <Button @click="handleAdd" class="flex-1">
            <ShoppingCart class="mr-2 h-4 w-4" /> Add to Cart
          </Button>
          <Button @click="handleBuyNow" variant="secondary" class="flex-1">
            <Zap class="mr-2 h-4 w-4" /> Buy Now
          </Button>
        </div>
      </div>
    </div>

    <Card v-if="data" class="mt-6">
      <CardContent class="p-6">
        <h2 class="mb-2 text-lg font-semibold">Item Details</h2>
        <p class="text-sm text-muted-foreground">{{ data.sku.specs }}</p>
        <div class="mt-3 grid grid-cols-2 gap-2 text-sm">
          <div><span class="text-muted-foreground">SKU:</span> {{ data.sku.skuId }}</div>
          <div><span class="text-muted-foreground">Unit:</span> {{ data.product.unitMeasurement }}</div>
        </div>
      </CardContent>
    </Card>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watchEffect } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@cd/stores/auth'
import { useCartStore } from '@cd/stores/cart'
import { getProductWithSku } from '@cd/data/mockData'
import Button from '@cd/components/ui/Button.vue'
import Card from '@cd/components/ui/Card.vue'
import CardContent from '@cd/components/ui/CardContent.vue'
import { Minus, Plus, ShoppingCart, Zap } from 'lucide-vue-next'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()
const cartStore = useCartStore()

watchEffect(() => {
  if (!authStore.isAuthenticated) {
    router.replace('/login')
  }
})

const pid = computed(() => route.params.pid as string)
const data = computed(() => getProductWithSku(pid.value))

const qty = ref(1)

const productPrice = computed(() => data.value?.sku.currentSell.toLocaleString() || '0')

const handleAdd = () => {
  if (data.value) {
    cartStore.addItem(data.value.product, data.value.sku, qty.value)
    alert(`${data.value.product.pName} added to cart`)
  }
}

const handleBuyNow = () => {
  if (data.value) {
    cartStore.addItem(data.value.product, data.value.sku, qty.value)
    router.push('/store/cart')
  }
}
</script>
