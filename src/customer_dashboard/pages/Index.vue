<template>
  <div class="container py-6">
    <h1 class="mb-4 text-2xl font-bold text-foreground">Product Catalog</h1>

    <div class="mb-6 flex flex-wrap gap-2">
      <Button
        v-for="cat in categories"
        :key="cat"
        :variant="activeCategory === cat ? 'default' : 'outline'"
        size="sm"
        @click="activeCategory = cat"
      >
        {{ cat }}
      </Button>
    </div>

    <div class="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-4">
      <ProductCard
        v-for="product in filtered"
        :key="product.pid"
        :product="product"
        :sku="getSku(product.pid)"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watchEffect } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@cd/stores/auth'
import { products, skus, categories } from '@cd/data/mockData'
import ProductCard from '@cd/components/ProductCard.vue'
import Button from '@cd/components/ui/Button.vue'

const router = useRouter()
const authStore = useAuthStore()

watchEffect(() => {
  if (!authStore.isAuthenticated) {
    router.replace('/login')
  }
})

const activeCategory = ref('All')

const filtered = computed(() => {
  return activeCategory.value === 'All'
    ? products
    : products.filter(p => p.category === activeCategory.value)
})

const getSku = (pid: string) => {
  return skus.find(s => s.pid === pid)!
}
</script>
