<template>
  <Card
    class="cursor-pointer transition-shadow hover:shadow-md"
    @click="navigateToProduct"
  >
    <CardContent class="p-4">
      <div class="mb-3 flex h-32 items-center justify-center overflow-hidden rounded-md bg-secondary text-5xl">
        <template v-if="isImagePath">
          <img :src="processedImagePath" :alt="product.pName" class="h-full w-full object-contain p-2" />
        </template>
        <template v-else>
          {{ product.image }}
        </template>
      </div>
      <h3 class="text-sm font-semibold text-foreground line-clamp-2 h-10">{{ product.pName }}</h3>
      <p class="mt-1 text-xs text-muted-foreground">{{ product.category }}</p>
      <p class="mt-2 text-lg font-bold text-primary">₹{{ productPrice }}</p>
    </CardContent>
  </Card>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import type { Product, SKU } from '@cd/types'
import Card from '@cd/components/ui/Card.vue'
import CardContent from '@cd/components/ui/CardContent.vue'

const props = defineProps<{
  product: Product
  sku: SKU
}>()

const router = useRouter()

const isImagePath = computed(() => {
  const img = props.product.image
  return img.startsWith('@') || img.startsWith('/') || img.includes('.')
})

const processedImagePath = computed(() => {
  if (props.product.image.startsWith('@')) {
    return props.product.image.replace('@', '/src')
  }
  return props.product.image
})

const navigateToProduct = () => {
  router.push(`/store/product/${props.product.pid}`)
}

const productPrice = computed(() => {
  return props.sku.currentSell.toLocaleString()
})
</script>

