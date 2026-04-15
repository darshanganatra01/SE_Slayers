<template>
  <div class="container max-w-3xl py-6">
    <Button variant="ghost" size="sm" @click="router.push('/store/orders')" class="mb-4">
      ← Back to Orders
    </Button>

    <div v-if="isLoading" class="container py-10 text-center text-muted-foreground">Loading...</div>
    <div v-else-if="!orderData" class="container py-10 text-center text-muted-foreground">Order not found.</div>

    <template v-else>
      <div class="flex items-center justify-between mb-1">
        <h1 class="text-2xl font-bold text-foreground">Order #{{ orderData.order.coId }}</h1>
        <Badge :variant="orderData.order.status === 'Fulfilled' ? 'default' : (orderData.order.status === 'Partially Fulfilled' ? 'secondary' : 'outline')">
          {{ orderData.order.status }}
        </Badge>
      </div>
      <p class="mb-6 text-sm text-muted-foreground">Placed on {{ orderData.order.orderDate }}</p>

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
          <div v-if="!orderData.invoices || orderData.invoices.length === 0" class="text-muted-foreground text-center py-2">
            No invoices generated yet.
          </div>
          <div v-for="inv in orderData.invoices" :key="inv.cInvId" class="flex items-center justify-between py-1 border-b last:border-0">
            <span class="text-muted-foreground">Invoice #{{ inv.cInvId }}</span>
            <div class="flex items-center gap-2">
              <Badge :variant="inv.status === 'Paid' ? 'default' : 'secondary'">{{ inv.status }}</Badge>
              <Button variant="ghost" size="icon" class="h-8 w-8" @click="router.push(`/store/invoice/${inv.cInvId}`)">
                <FileText class="h-4 w-4" />
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>
    </template>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { getOrderDetails } from '@cd/data/api'
import Button from '@cd/components/ui/Button.vue'
import Card from '@cd/components/ui/Card.vue'
import CardContent from '@cd/components/ui/CardContent.vue'
import CardHeader from '@cd/components/ui/CardHeader.vue'
import CardTitle from '@cd/components/ui/CardTitle.vue'
import Badge from '@cd/components/ui/Badge.vue'

import { FileText } from 'lucide-vue-next'

const route = useRoute()
const router = useRouter()

const coId = computed(() => route.params.coId as string)

const orderData = ref<any>(null)
const isLoading = ref(true)

onMounted(async () => {
  try {
    orderData.value = await getOrderDetails(coId.value)
  } catch (e) {
    console.error("Failed to load order details", e)
  } finally {
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
</script>
