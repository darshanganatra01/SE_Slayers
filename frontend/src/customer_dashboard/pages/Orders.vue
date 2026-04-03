<template>
  <div class="container py-6">
    <h1 class="mb-4 text-2xl font-bold text-foreground">Your Orders</h1>

    <div class="mb-6 flex gap-4 border-b">
      <button 
        class="pb-2 text-sm font-medium transition-colors hover:text-primary"
        :class="activeTab === 'orders' ? 'border-b-2 border-primary text-primary' : 'text-muted-foreground'"
        @click="activeTab = 'orders'"
      >
        Order-wise
      </button>
      <button 
        class="pb-2 text-sm font-medium transition-colors hover:text-primary"
        :class="activeTab === 'invoices' ? 'border-b-2 border-primary text-primary' : 'text-muted-foreground'"
        @click="activeTab = 'invoices'"
      >
        Invoice-wise
      </button>
      <button 
        class="pb-2 text-sm font-medium transition-colors hover:text-primary"
        :class="activeTab === 'items' ? 'border-b-2 border-primary text-primary' : 'text-muted-foreground'"
        @click="activeTab = 'items'"
      >
        Item-wise
      </button>
    </div>

    <div v-if="activeTab === 'orders'">
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

    <div v-else-if="activeTab === 'invoices'">
      <p v-if="isLoadingInvoices" class="text-muted-foreground">Loading invoices...</p>
      <p v-else-if="invoices.length === 0" class="text-muted-foreground">No invoices yet.</p>

      <div v-else class="space-y-3">
        <Card
          v-for="inv in invoices"
          :key="inv.cInvId"
          class="cursor-pointer transition-shadow hover:shadow-md"
          @click="router.push(`/store/invoice/${inv.cInvId}`)"
        >
          <CardContent class="p-4">
            <div class="flex flex-wrap items-center justify-between gap-2">
              <div>
                <p class="text-sm text-muted-foreground">
                  Invoice #{{ inv.cInvId }} · Order #{{ inv.coId }} · {{ inv.invoiceDate }}
                </p>
                <p class="font-semibold text-foreground">
                  {{ inv.itemsSummary }}
                </p>
              </div>
              <div class="flex items-center gap-3">
                <p class="font-bold text-primary">₹{{ inv.totalAmount.toLocaleString() }}</p>
                <div class="flex items-center gap-2">
                  <Badge v-if="inv.isReceived" variant="default" class="bg-green-600">Received</Badge>
                  <Badge :variant="statusVariant(inv.status)">{{ inv.status }}</Badge>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>

    <div v-else>
      <p v-if="isLoadingItems" class="text-muted-foreground">Loading items...</p>
      <p v-else-if="items.length === 0" class="text-muted-foreground">No items ordered yet.</p>

      <div v-else class="space-y-3">
        <Card
          v-for="item in items"
          :key="item.codId"
          class="cursor-pointer transition-shadow hover:shadow-md"
          @click="router.push(`/store/item/${item.codId}`)"
        >
          <CardContent class="p-4">
            <div class="flex flex-wrap items-center justify-between gap-2">
              <div class="flex items-center gap-4">
                <div class="h-10 w-10 overflow-hidden rounded-md border bg-muted">
                  <img :src="pImg(item.pName)" class="h-full w-full object-cover" />
                </div>
                <div>
                  <div class="flex items-center gap-2">
                    <p class="font-semibold text-foreground">{{ item.pName }}</p>
                    <span class="text-xs text-muted-foreground">({{ item.specs }})</span>
                  </div>
                  <p class="text-xs text-muted-foreground">
                    Order #{{ item.coId }} · {{ item.orderDate }}
                  </p>
                </div>
              </div>
              <div class="flex items-center gap-4">
                <div class="text-right">
                  <p class="text-xs text-muted-foreground">Quantity</p>
                  <p class="font-bold text-foreground">{{ item.quantity }}</p>
                </div>
                <Badge :variant="statusVariant(item.status)">{{ item.status }}</Badge>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { getOrders, getInvoices, getItems } from '@cd/data/api'
import Button from '@cd/components/ui/Button.vue'
import Card from '@cd/components/ui/Card.vue'
import CardContent from '@cd/components/ui/CardContent.vue'
import Badge from '@cd/components/ui/Badge.vue'
import { FileText } from 'lucide-vue-next'
import type { BadgeVariants } from '@cd/components/ui/Badge.vue'

const router = useRouter()
const authStore = useAuthStore()

const activeTab = ref('orders')
const orders = ref<any[]>([])
const invoices = ref<any[]>([])
const items = ref<any[]>([])
const isLoading = ref(true)
const isLoadingInvoices = ref(true)
const isLoadingItems = ref(true)

onMounted(async () => {
  if (authStore.user?.customer?.cid) {
    const cid = authStore.user.customer.cid
    try {
      // Fetch all in parallel
      const [orderRes, invRes, itemRes] = await Promise.all([
        getOrders(cid),
        getInvoices(cid),
        getItems(cid)
      ])
      orders.value = orderRes
      invoices.value = invRes
      items.value = itemRes
    } catch (err) {
      console.error("Failed to load data:", err)
    } finally {
      isLoading.value = false
      isLoadingInvoices.value = false
      isLoadingItems.value = false
    }
  } else {
    isLoading.value = false
    isLoadingInvoices.value = false
    isLoadingItems.value = false
  }
})

const pImg = (pName: string) => {
  return `/src/customer_dashboard/customer_assets/${pName}.png`.replace("G. I.", "GI")
}

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
    case 'Delivered':
    case 'Completed':
    case 'Paid': return 'default'
    case 'Shipped':
    case 'PartiallyFulfilled':
    case 'PartiallyPaid': return 'secondary'
    case 'Confirmed':
    case 'FullyPacked':
    case 'PartiallyPacked': return 'outline'
    case 'Unpaid': return 'outline'
    default: return 'destructive'
  }
}
</script>
