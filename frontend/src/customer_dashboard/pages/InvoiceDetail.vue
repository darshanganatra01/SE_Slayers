<template>
  <div class="container max-w-3xl py-6">
    <Button variant="ghost" size="sm" @click="router.push('/store/orders')" class="mb-4">
      ← Back to Orders
    </Button>

    <div v-if="isLoading" class="container py-10 text-center text-muted-foreground">Loading...</div>
    <div v-else-if="!invoiceData" class="container py-10 text-center text-muted-foreground">Invoice not found.</div>

    <template v-else>
      <div class="mb-6">
        <h1 class="mb-1 text-2xl font-bold text-foreground">Invoice #{{ invoiceData.invoice.cInvId }}</h1>
        <p class="text-sm text-muted-foreground">Issued on {{ invoiceData.invoice.invoiceDate }} · Order #{{ invoiceData.invoice.coId }}</p>
      </div>

      <Card class="mb-6">
        <CardHeader><CardTitle>Items</CardTitle></CardHeader>
        <CardContent class="p-0">
          <div class="w-full overflow-auto">
            <table class="w-full caption-bottom text-sm">
              <thead class="[&_tr]:border-b">
                <tr class="border-b transition-colors hover:bg-muted/50">
                  <th class="h-12 px-4 text-left align-middle font-medium text-muted-foreground">Item</th>
                  <th class="h-12 px-4 text-center align-middle font-medium text-muted-foreground">Ordered</th>
                  <th class="h-12 px-4 text-center align-middle font-medium text-muted-foreground">Delivered</th>
                  <th class="h-12 px-4 text-right align-middle font-medium text-muted-foreground">Price</th>
                  <th class="h-12 px-4 text-right align-middle font-medium text-muted-foreground">Amount</th>
                </tr>
              </thead>
              <tbody class="[&_tr:last-child]:border-0">
                <tr v-for="item in invoiceData.items" :key="item.cDetailId" class="border-b transition-colors hover:bg-muted/50">
                  <td class="p-4 align-middle">
                    <div class="font-medium text-foreground">{{ item.product.pName }}</div>
                    <div class="text-xs text-muted-foreground">{{ item.sku.specs }}</div>
                  </td>
                  <td class="p-4 align-middle text-center">{{ item.orderedQty }}</td>
                  <td class="p-4 align-middle text-center">{{ item.deliveredQty }}</td>
                  <td class="p-4 align-middle text-right">₹{{ item.salePrice.toLocaleString() }}</td>
                  <td class="p-4 align-middle text-right">₹{{ item.amount.toLocaleString() }}</td>
                </tr>
                <tr class="border-b transition-colors hover:bg-muted/50 font-bold">
                  <td colspan="4" class="p-4 align-middle">Total</td>
                  <td class="p-4 align-middle text-right">₹{{ invoiceData.invoice.totalAmount.toLocaleString() }}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader><CardTitle>Status Info</CardTitle></CardHeader>
        <CardContent class="space-y-4 text-sm">
          <div class="flex items-center justify-between">
            <span class="text-muted-foreground">Payment Status</span>
            <Badge :variant="invoiceData.invoice.status === 'Paid' ? 'default' : 'secondary'">{{ invoiceData.invoice.status }}</Badge>
          </div>
          
          <div v-if="invoiceData.invoice.receipt" class="flex flex-col gap-2 rounded-lg bg-green-50 p-3 text-green-700 dark:bg-green-950/30 dark:text-green-400">
            <div class="flex items-center justify-between">
              <span class="font-medium">Delivery Status</span>
              <Badge variant="default" class="bg-green-600">Received</Badge>
            </div>
            <p class="text-xs">
              Marked as received on {{ invoiceData.invoice.receipt.receivedDate }} by {{ invoiceData.invoice.receipt.receivedBy }}
            </p>
          </div>
          <div v-else class="pt-2">
            <Button 
              class="w-full" 
              :loading="isConfirming" 
              @click="handleConfirmReceipt"
            >
              Confirm Receipt
            </Button>
            <p class="mt-2 text-center text-xs text-muted-foreground italic">
              Please confirm only after you have physically received the items.
            </p>
          </div>
        </CardContent>
      </Card>
    </template>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { getInvoiceDetails, confirmReceipt } from '@cd/data/api'
import { useAuthStore } from '@/stores/auth'
import Button from '@cd/components/ui/Button.vue'
import Card from '@cd/components/ui/Card.vue'
import CardContent from '@cd/components/ui/CardContent.vue'
import CardHeader from '@cd/components/ui/CardHeader.vue'
import CardTitle from '@cd/components/ui/CardTitle.vue'
import Badge from '@cd/components/ui/Badge.vue'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()

const invId = computed(() => route.params.invId as string)
const invoiceData = ref<any>(null)
const isLoading = ref(true)
const isConfirming = ref(false)

const loadData = async () => {
  try {
    isLoading.value = true
    invoiceData.value = await getInvoiceDetails(invId.value)
  } catch (e) {
    console.error("Failed to load invoice details", e)
  } finally {
    isLoading.value = false
  }
}

onMounted(loadData)

const handleConfirmReceipt = async () => {
  if (!authStore.user?.uid) return
  
  isConfirming.value = true
  try {
    await confirmReceipt(invId.value, authStore.user.uid)
    await loadData() // Refresh
  } catch (err) {
    alert(err instanceof Error ? err.message : "Failed to confirm receipt")
  } finally {
    isConfirming.value = false
  }
}
</script>
