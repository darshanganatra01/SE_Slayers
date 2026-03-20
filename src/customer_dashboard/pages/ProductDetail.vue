<template>
  <div class="container py-6">
    <Button variant="ghost" size="sm" @click="router.back()" class="mb-4">
      ← Back
    </Button>

    <div v-if="!data" class="container py-10 text-center text-muted-foreground">
      Product not found.
    </div>

    <div v-else class="space-y-8">
      <!-- Header Section -->
      <div class="flex flex-col gap-8 md:flex-row">
        <div class="flex aspect-square w-full max-w-sm items-center justify-center overflow-hidden rounded-xl bg-secondary md:w-1/3 text-8xl">
          <template v-if="isImagePath">
            <img :src="productImage" :alt="data.product.pName" class="h-full w-full object-contain p-4" />
          </template>
          <template v-else>
            {{ data.product.image }}
          </template>
        </div>

        <div class="flex flex-col justify-center space-y-4">
          <div>
            <p class="text-sm font-medium uppercase tracking-wider text-primary">{{ data.product.category }}</p>
            <h1 class="text-3xl font-bold tracking-tight text-foreground md:text-4xl">{{ data.product.pName }}</h1>
            <p class="mt-2 text-muted-foreground">Unit: {{ data.product.unitMeasurement }}</p>
          </div>
        </div>
      </div>

      <!-- Variants Table -->
      <Card class="overflow-hidden">
        <div class="overflow-x-auto">
          <table class="w-full text-left text-sm">
            <thead class="bg-muted/50 text-muted-foreground">
              <tr>
                <th class="px-4 py-3 font-semibold">Specifications</th>
                <th class="px-4 py-3 font-semibold text-right">Price</th>
                <th class="px-4 py-3 font-semibold text-center">Quantity</th>
                <th class="px-4 py-3 font-semibold text-right">Actions</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-border">
              <tr v-for="sku in data.skus" :key="sku.skuId" class="hover:bg-muted/30 transition-colors">
                <td class="px-4 py-4">
                  <div class="flex flex-col gap-1">
                    <span class="font-medium text-foreground">{{ formatSpecs(sku.specs).size }}</span>
                    <div v-if="formatSpecs(sku.specs).other" class="text-xs text-muted-foreground">
                      <span v-for="(val, key) in formatSpecs(sku.specs).other" :key="key" class="mr-2">
                         {{ key }}: {{ val }}
                      </span>
                    </div>
                    <div class="flex items-center gap-2 mt-1">
                      <span class="text-[10px] text-muted-foreground uppercase">SKU: {{ sku.skuId }}</span>
                      <span v-if="getCartQty(sku.skuId) > 0" class="inline-flex items-center rounded-md bg-orange-100 px-2 py-0.5 text-[10px] font-medium text-orange-600 border border-orange-200">
                        {{ getCartQty(sku.skuId) }} in cart
                      </span>
                    </div>
                  </div>
                </td>
                <td class="px-4 py-4 text-right">
                  <span class="text-lg font-bold text-foreground">₹{{ sku.currentSell.toLocaleString() }}</span>
                </td>
                <td class="px-4 py-4">
                  <div class="flex items-center justify-center gap-2">
                    <Button variant="outline" size="icon" class="h-8 w-8" @click="updateQty(sku.skuId, -1)">
                      <Minus class="h-3 w-3" />
                    </Button>
                    <span class="w-8 text-center font-semibold">{{ quantities[sku.skuId] || 1 }}</span>
                    <Button variant="outline" size="icon" class="h-8 w-8" @click="updateQty(sku.skuId, 1)">
                      <Plus class="h-3 w-3" />
                    </Button>
                  </div>
                </td>
                <td class="px-4 py-4 text-right">
                  <div class="flex justify-end gap-2">
                    <Button size="sm" @click="handleAdd(sku)" class="h-9">
                      <ShoppingCart class="mr-2 h-4 w-4" /> Add
                    </Button>
                    <Button size="sm" variant="secondary" @click="handleBuyNow(sku)" class="h-9">
                      <Zap class="mr-2 h-4 w-4" /> Buy
                    </Button>
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </Card>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watchEffect, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@cd/stores/auth'
import { useCartStore } from '@cd/stores/cart'
import { getProductWithSku } from '@cd/data/mockData'
import Button from '@cd/components/ui/Button.vue'
import Card from '@cd/components/ui/Card.vue'
import { Minus, Plus, ShoppingCart, Zap } from 'lucide-vue-next'
import type { SKU } from '@cd/types'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()
const cartStore = useCartStore()

watchEffect(() => {
  if (!authStore.isAuthenticated) {
    router.replace('/store/login')
  }
})

const pid = computed(() => route.params.pid as string)
const data = computed(() => getProductWithSku(pid.value))

const isImagePath = computed(() => {
  const img = data.value?.product.image
  return img && (img.startsWith('@') || img.startsWith('/') || img.includes('.'))
})

// State for quantities per SKU
const quantities = ref<Record<string, number>>({})

// Initialize quantities when data changes
watchEffect(() => {
  if (data.value) {
    data.value.skus.forEach(sku => {
      if (!quantities.value[sku.skuId]) {
        quantities.value[sku.skuId] = 1
      }
    })
  }
})

const updateQty = (skuId: string, delta: number) => {
  const current = quantities.value[skuId] || 1
  quantities.value[skuId] = Math.max(1, current + delta)
}

const getCartQty = (skuId: string) => {
  const item = cartStore.items.find(i => i.sku.skuId === skuId)
  return item ? item.quantity : 0
}

const productImage = computed(() => {
  if (!data.value?.product.image) return ''
  // Handle paths starting with @
  if (data.value.product.image.startsWith('@')) {
    // In a real Vite project, you might need to use new URL() or import()
    // For mock data, we'll assume the path is relative to src or similar
    // However, since we're using <img> tag, we might need a direct URL.
    // Assuming Vite resolves these in templates, but for safety in mock:
    return data.value.product.image.replace('@', '/src')
  }
  return data.value.product.image
})

const formatSpecs = (specsString: string) => {
  try {
    const specs = JSON.parse(specsString)
    const { size, ...other } = specs
    return { size: size || 'Standard', other: Object.keys(other).length > 0 ? other : null }
  } catch (e) {
    return { size: specsString, other: null }
  }
}

const handleAdd = (sku: SKU) => {
  if (data.value) {
    const qty = quantities.value[sku.skuId] || 1
    cartStore.addItem(data.value.product, sku, qty)
    alert(`${data.value.product.pName} (${formatSpecs(sku.specs).size}) added to cart`)
  }
}

const handleBuyNow = (sku: SKU) => {
  if (data.value) {
    const qty = quantities.value[sku.skuId] || 1
    cartStore.addItem(data.value.product, sku, qty)
    router.push('/store/cart')
  }
}
</script>

