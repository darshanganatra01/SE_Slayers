<template>
  <div class="container py-6">
    <div class="mb-8 flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
      <div>
        <h2 class="text-lg font-medium text-muted-foreground">
          {{ greeting }},
          <span class="text-foreground font-bold">{{ authStore.user?.full_name || 'shopper' }}</span>
        </h2>
        <p class="text-sm text-muted-foreground">
          {{ authStore.isAuthenticated ? 'Welcome back to Metro Hardware' : 'Browse freely, then sign in when you are ready to checkout.' }}
        </p>
      </div>
      <div class="relative w-full max-w-sm">
        <Search class="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
        <Input
          type="search"
          placeholder="Search products..."
          class="pl-9"
          v-model="searchQuery"
        />
      </div>
    </div>

    <h1 class="mb-4 text-2xl font-bold text-foreground">Product Catalog</h1>

    <div class="mb-6 flex flex-wrap gap-2">
      <Button
        v-for="cat in allCategories"
        :key="cat"
        :variant="activeCategory === cat ? 'default' : 'outline'"
        size="sm"
        @click="activeCategory = cat"
      >
        {{ cat }}
      </Button>
    </div>


    <div v-if="filtered.length > 0" class="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-4">
      <ProductCard
        v-for="product in filtered"
        :key="product.pid"
        :product="product"
      />
    </div>
    <div v-else class="py-12 text-center text-muted-foreground">
      No products found matching your search.
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { fetchProducts, fetchCategories } from '@cd/data/api'
import type { Product } from '@cd/types'
import ProductCard from '@cd/components/ProductCard.vue'
import Button from '@cd/components/ui/Button.vue'
import Input from '@cd/components/ui/Input.vue'
import { Search } from 'lucide-vue-next'

const authStore = useAuthStore()

const activeCategory = ref('All')
const searchQuery = ref('')
const products = ref<Product[]>([])
const categories = ref<string[]>([])

const allCategories = computed(() => ['All', ...categories.value])

onMounted(async () => {
  try {
    const [productsData, categoriesData] = await Promise.all([
      fetchProducts(),
      fetchCategories()
    ])
    products.value = productsData
    categories.value = categoriesData
  } catch (err) {
    console.error("Failed to load catalog data", err)
  }
})


const greeting = computed(() => {
  const hour = new Date().getHours()
  if (hour < 12) return 'Good morning'
  if (hour < 18) return 'Good afternoon'
  return 'Good evening'
})

const filtered = computed(() => {
  let result = products.value

  if (activeCategory.value !== 'All') {
    result = result.filter(p => p.category === activeCategory.value)
  }

  if (searchQuery.value) {
    const query = searchQuery.value.toLowerCase()
    result = result.filter(p => p.pName.toLowerCase().includes(query))
  }

  return result
})

</script>
