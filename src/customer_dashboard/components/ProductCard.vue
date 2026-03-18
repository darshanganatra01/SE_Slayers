<template>
  <Card
    class="cursor-pointer transition-shadow hover:shadow-md"
    @click="navigateToProduct"
  >
    <CardContent class="p-4">
      <div class="mb-3 flex h-28 items-center justify-center rounded-md bg-secondary text-5xl">
        {{ product.image }}
      </div>
      <h3 class="text-sm font-semibold text-foreground line-clamp-2">{{ product.pName }}</h3>
      <p class="mt-1 text-xs text-muted-foreground">{{ product.category }}</p>
      <p class="mt-2 text-lg font-bold text-primary">₹{{ productPrice }}</p>
      <p v-if="sku.stockQty < 10" class="mt-1 text-xs text-destructive">
        Only {{ sku.stockQty }} left
      </p>
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

const navigateToProduct = () => {
  router.push(`/store/product/${props.product.pid}`)
}

const productPrice = computed(() => {
  return props.sku.currentSell.toLocaleString()
})
</script>
