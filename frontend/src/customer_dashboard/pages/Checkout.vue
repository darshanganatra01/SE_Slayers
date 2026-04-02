<template>
  <div class="container max-w-2xl py-6">
    <h1 class="mb-4 text-2xl font-bold text-foreground">Checkout</h1>

    <div class="space-y-4">
      <Card>
        <CardHeader><div class="text-base font-semibold leading-none tracking-tight">Delivery Address</div></CardHeader>
        <CardContent>
          <div class="flex items-start gap-3">
            <Home class="mt-1 h-4 w-4 text-muted-foreground" />
            <div>
              <p class="font-semibold">{{ authStore.user?.full_name }}</p>
              <p class="text-sm text-muted-foreground">
                {{ authStore.user?.customer?.location || 'No address provided' }}
                <span v-if="authStore.user?.customer?.pincode"> – {{ authStore.user?.customer?.pincode }}</span>
              </p>
              <p class="mt-1 text-xs text-muted-foreground">Contact: {{ authStore.user?.customer?.contact || 'N/A' }}</p>
            </div>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader><div class="text-base font-semibold leading-none tracking-tight">Order Summary</div></CardHeader>
        <CardContent class="space-y-2">
          <div v-for="item in cartStore.items" :key="item.sku.skuId" class="flex justify-between text-sm">
            <span>{{ item.product.pName }} × {{ item.quantity }}</span>
            <span class="font-medium">₹{{ (item.sku.currentSell * item.quantity).toLocaleString() }}</span>
          </div>
          <div class="border-t pt-2 flex justify-between font-bold">
            <span>Total</span>
            <span>₹{{ cartStore.totalPrice.toLocaleString() }}</span>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader><div class="text-base font-semibold leading-none tracking-tight">Payment</div></CardHeader>
        <CardContent>
          <div class="flex items-center gap-3 py-2">
            <CreditCard class="h-5 w-5 text-primary" />
            <div>
              <p class="font-semibold">Pay on credit</p>
              <p class="text-sm text-muted-foreground">Make payment before the credit period</p>
            </div>
          </div>
        </CardContent>
      </Card>

      <Button size="lg" class="w-full" @click="handlePlaceOrder" :disabled="isLoading">
        <span v-if="isLoading">Processing...</span>
        <span v-else>Place Order — ₹{{ cartStore.totalPrice.toLocaleString() }}</span>
      </Button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watchEffect } from 'vue'
import { useRouter } from 'vue-router'
import { useCartStore } from '@cd/stores/cart'
import { useAuthStore } from '@/stores/auth'
import { placeOrder } from '@cd/data/api'
import Button from '@cd/components/ui/Button.vue'
import Card from '@cd/components/ui/Card.vue'
import CardHeader from '@cd/components/ui/CardHeader.vue'
import CardContent from '@cd/components/ui/CardContent.vue'
import { Home, CreditCard } from 'lucide-vue-next'

const router = useRouter()
const cartStore = useCartStore()
const authStore = useAuthStore()

watchEffect(() => {
  if (cartStore.items.length === 0) {
    router.replace('/store/cart')
  }
})

const isLoading = ref(false)

const handlePlaceOrder = async () => {
  if (!authStore.user?.customer?.cid) {
    alert("You must be logged in as a valid customer.")
    return
  }

  const itemsPayload = cartStore.items.map(item => ({
    skuId: item.sku.skuId,
    quantity: item.quantity
  }))

  isLoading.value = true
  try {
    const res = await placeOrder(authStore.user.customer.cid, itemsPayload)
    cartStore.clearCart()
    alert(`Order placed successfully!\nOrder ID: ${res.order_id}`)
    router.push('/store/orders')
  } catch (err) {
    console.error("Failed to place order:", err)
    alert("There was an error placing your order. Please try again.")
  } finally {
    isLoading.value = false
  }
}
</script>

