<template>
  <div class="container max-w-3xl py-6">
    <Button variant="ghost" size="sm" @click="router.push('/store/orders')" class="mb-4">
      ← Back to Orders
    </Button>

    <div v-if="!orderData" class="container py-10 text-center text-muted-foreground">Order not found.</div>

    <template v-else>
      <h1 class="mb-1 text-2xl font-bold text-foreground">Order #{{ orderData.order.coId }}</h1>
      <p class="mb-6 text-sm text-muted-foreground">Placed on {{ orderData.order.orderDate }}</p>

      <Card class="mb-6">
        <CardHeader><CardTitle>Order Timeline</CardTitle></CardHeader>
        <CardContent>
          <OrderTimeline :status="orderData.order.status" :orderDate="orderData.order.orderDate" />
        </CardContent>
      </Card>

      <Card class="mb-6">
        <CardHeader><CardTitle>Items</CardTitle></CardHeader>
        <CardContent class="p-0">
          <div class="w-full overflow-auto">
            <table class="w-full caption-bottom text-sm">
              <thead class="[&_tr]:border-b">
                <tr class="border-b transition-colors hover:bg-muted/50">
                  <th class="h-12 px-4 text-left align-middle font-medium text-muted-foreground">Item</th>
                  <th class="h-12 px-4 text-center align-middle font-medium text-muted-foreground">Qty</th>
                  <th class="h-12 px-4 text-center align-middle font-medium text-muted-foreground">Delivered</th>
                  <th class="h-12 px-4 text-right align-middle font-medium text-muted-foreground">Price</th>
                </tr>
              </thead>
              <tbody class="[&_tr:last-child]:border-0">
                <tr v-for="item in orderData.items" :key="item.cDetailId" class="border-b transition-colors hover:bg-muted/50">
                  <td class="p-4 align-middle">
                    <div class="font-medium text-foreground">{{ item.product.pName }}</div>
                    <div class="text-xs text-muted-foreground">{{ getSpecSize(item.sku.specs) }}</div>
                  </td>
                  <td class="p-4 align-middle text-center">{{ item.orderedQty }}</td>
                  <td class="p-4 align-middle text-center">{{ item.deliveredQty }}</td>
                  <td class="p-4 align-middle text-right">₹{{ (item.salePrice * item.orderedQty).toLocaleString() }}</td>
                </tr>
                <tr class="border-b transition-colors hover:bg-muted/50">
                  <td colspan="3" class="p-4 align-middle font-bold">Total</td>
                  <td class="p-4 align-middle text-right font-bold">₹{{ orderData.totalAmount.toLocaleString() }}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader><CardTitle>Transaction Info</CardTitle></CardHeader>
        <CardContent class="space-y-3 text-sm">
          <div class="flex items-center justify-between">
            <span class="text-muted-foreground">Invoice</span>
            <div class="flex items-center gap-2">
              <span class="font-medium">{{ orderData.invoice.cInvId }}</span>
              <Badge :variant="orderData.invoice.status === 'Paid' ? 'default' : 'secondary'">{{ orderData.invoice.status }}</Badge>
              <Button variant="ghost" size="icon" class="h-7 w-7"><FileText class="h-3.5 w-3.5" /></Button>
            </div>
          </div>
          <div class="flex items-center justify-between">
            <span class="text-muted-foreground">Delivery Challan</span>
            <div class="flex items-center gap-2">
              <span class="font-medium">DC-{{ orderData.order.coId }}</span>
              <Button variant="ghost" size="icon" class="h-7 w-7"><Truck class="h-3.5 w-3.5" /></Button>
            </div>
          </div>
          <div v-if="orderData.invoice.status === 'Paid'" class="flex items-center justify-between">
            <span class="text-muted-foreground">UPI Transaction ID</span>
            <span class="font-medium font-mono text-xs">UPI{{ orderData.order.coId }}XYZ{{ randomSuffix }}</span>
          </div>
        </CardContent>
      </Card>
    </template>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@cd/stores/auth'
import { getOrdersWithDetails } from '@cd/data/mockData'
import Button from '@cd/components/ui/Button.vue'
import Card from '@cd/components/ui/Card.vue'
import CardContent from '@cd/components/ui/CardContent.vue'
import CardHeader from '@cd/components/ui/CardHeader.vue'
import CardTitle from '@cd/components/ui/CardTitle.vue'
import Badge from '@cd/components/ui/Badge.vue'
import OrderTimeline from '@cd/components/OrderTimeline.vue'
import { FileText, Truck } from 'lucide-vue-next'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()

const coId = computed(() => route.params.coId as string)

if (!authStore.isAuthenticated) {
  router.replace('/store/login')
}

const orders = getOrdersWithDetails()
const orderData = computed(() => orders.find(o => o.order.coId === coId.value))
const randomSuffix = Math.floor(Math.random() * 9000 + 1000)

const getSpecSize = (specsString: string) => {
  try {
    const specs = JSON.parse(specsString)
    return specs.size || ''
  } catch (e) {
    return specsString
  }
}
</script>
