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
            <div v-if="Object.keys(commonSpecs).length > 0" class="mt-4 flex flex-wrap gap-x-4 gap-y-1 text-sm">
              <span v-for="(val, key) in commonSpecs" :key="key" class="text-muted-foreground">
                <span class="font-semibold text-foreground">{{ key }}:</span> {{ val }}
              </span>
            </div>
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
                    <div v-if="getCartQty(sku.skuId) > 0" class="mt-1">
                      <span class="inline-flex items-center rounded-md bg-orange-100 px-2 py-0.5 text-[10px] font-medium text-orange-600 border border-orange-200">
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
                    <input
                      type="number"
                      v-model.number="quantities[sku.skuId]"
                      class="w-12 h-8 rounded-md border border-input bg-background px-1 py-1 text-sm text-center focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring [appearance:textfield] [&::-webkit-outer-spin-button]:appearance-none [&::-webkit-inner-spin-button]:appearance-none font-semibold"
                      min="0"
                    />
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
import { ref, computed, watchEffect } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useCartStore } from '@cd/stores/cart'
import { getProductWithSku } from '@cd/data/mockData'
import Button from '@cd/components/ui/Button.vue'
import Card from '@cd/components/ui/Card.vue'
import { Minus, Plus, ShoppingCart, Zap } from 'lucide-vue-next'
import type { SKU } from '@cd/types'

const route = useRoute()
const router = useRouter()
const cartStore = useCartStore()

const pid = computed(() => route.params.pid as string)
const data = computed(() => getProductWithSku(pid.value))

const commonSpecs = computed(() => {
  if (!data.value || data.value.skus.length === 0) return {}
  
  const allSpecs = data.value.skus.map(sku => {
    try {
      return JSON.parse(sku.specs)
    } catch (e) {
      return {}
    }
  })

  if (allSpecs.length === 0) return {}
  
  const common: Record<string, any> = {}
  const keys = Object.keys(allSpecs[0])

  keys.forEach(key => {
    const value = allSpecs[0][key]
    const isCommon = allSpecs.every(s => s[key] === value)
    if (isCommon) {
      common[key] = value
    }
  })

  return common
})

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
      if (quantities.value[sku.skuId] === undefined) {
        quantities.value[sku.skuId] = 0
      }
    })
  }
})

const updateQty = (skuId: string, delta: number) => {
  const current = quantities.value[skuId] || 0
  quantities.value[skuId] = Math.max(0, current + delta)
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
    
    const filteredOther: Record<string, any> = {}
    Object.keys(other).forEach(key => {
      // Only include in 'other' if it's not a common spec
      if (!commonSpecs.value[key]) {
        filteredOther[key] = other[key]
      }
    })

    // If size is common, we might want to display it as 'Standard' or hide it, 
    // but usually size is the differentiator. 
    // If it IS common, we'll mark it as such.
    const displaySize = commonSpecs.value.size ? 'Standard' : (size || 'Standard')

    return { 
      size: displaySize, 
      other: Object.keys(filteredOther).length > 0 ? filteredOther : null 
    }
  } catch (e) {
    return { size: specsString, other: null }
  }
}

const handleAdd = (sku: SKU) => {
  const qty = quantities.value[sku.skuId] || 0
  if (qty <= 0) {
    alert("Please select a quantity greater than 0")
    return
  }
  if (data.value) {
    cartStore.addItem(data.value.product, sku, qty)
    alert(`${data.value.product.pName} (${formatSpecs(sku.specs).size}) added to cart`)
  }
}

const handleBuyNow = (sku: SKU) => {
  const qty = quantities.value[sku.skuId] || 0
  if (qty <= 0) {
    alert("Please select a quantity greater than 0")
    return
  }
  if (data.value) {
    cartStore.addItem(data.value.product, sku, qty)
    router.push('/store/cart')
  }
}
</script>
