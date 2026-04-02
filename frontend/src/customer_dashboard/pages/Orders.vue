<template>
  <div class="container py-6">
    <h1 class="mb-4 text-2xl font-bold text-foreground">Your Orders</h1>

    <p v-if="isLoading" class="text-muted-foreground">Loading orders...</p>
    <p v-else-if="orders.length === 0" class="text-muted-foreground">No orders yet.</p>

    <div v-else class="space-y-3">
      <Card
        v-for="{ order, items, totalAmount } in orders"
        :key="order.coId"
        class="cursor-pointer transition-shadow hover:shadow-md"
        @click="router.push(`/store/order/${order.coId}`)"
      >
        <CardContent class="p-4">
          <div class="flex flex-wrap items-center justify-between gap-2">
            <div>
              <p class="text-sm text-muted-foreground">
                Order #{{ order.coId }} · {{ order.orderDate }}
              </p>
              <p class="font-semibold text-foreground">
                {{ formatOrderItems(items) }}
              </p>
            </div>
            <div class="flex items-center gap-3">
              <p class="font-bold text-primary">₹{{ totalAmount.toLocaleString() }}</p>
              <Badge :variant="statusVariant(order.status)">{{ order.status }}</Badge>
              <Button variant="ghost" size="icon" title="Invoice" @click.stop="">
                <FileText class="h-4 w-4" />
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { getOrders } from '@cd/data/api'
import Button from '@cd/components/ui/Button.vue'
import Card from '@cd/components/ui/Card.vue'
import CardContent from '@cd/components/ui/CardContent.vue'
import Badge from '@cd/components/ui/Badge.vue'
import { FileText } from 'lucide-vue-next'
import type { BadgeVariants } from '@cd/components/ui/Badge.vue'

const router = useRouter()
const authStore = useAuthStore()

const orders = ref<any[]>([])
const isLoading = ref(true)

onMounted(async () => {
  if (authStore.user?.customer?.cid) {
    try {
      orders.value = await getOrders(authStore.user.customer.cid)
    } catch (err) {
      console.error("Failed to load orders:", err)
    } finally {
      isLoading.value = false
    }
  } else {
    isLoading.value = false
  }
})

const getSpecSize = (specsString: string) => {
  try {
    const specs = JSON.parse(specsString)
    return specs.size || ''
  } catch (e) {
    return specsString
  }
}

const formatOrderItems = (items: any[]) => {
  const uniqueProducts = Array.from(new Set(items.map(i => i.product.pName)))
  const displayProducts = uniqueProducts.slice(0, 3)
  let result = displayProducts.join(', ')
  if (uniqueProducts.length > 3) {
    result += '...'
  }
  return result
}

const statusVariant = (status: string): BadgeVariants['variant'] => {
  switch (status) {
    case 'Delivered': return 'default'
    case 'Shipped': return 'secondary'
    case 'Confirmed': return 'outline'
    default: return 'destructive'
  }
}
</script>
