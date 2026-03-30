<template>
  <div class="container max-w-2xl py-6">
    <h1 class="mb-4 text-2xl font-bold text-foreground">Checkout</h1>

    <div class="space-y-4">
      <Card>
        <CardHeader><div class="text-base font-semibold leading-none tracking-tight">Delivery Address</div></CardHeader>
        <CardContent>
          <RadioGroup v-model="selectedAddress" class="space-y-3">
            <div v-for="addr in mockAddresses" :key="addr.id" class="flex items-start gap-3">
              <RadioGroupItem :value="addr.id" :id="addr.id" class="mt-1" />
              <Label :for="addr.id" class="cursor-pointer">
                <p class="font-semibold">{{ addr.label }}</p>
                <p class="text-sm text-muted-foreground">
                  {{ addr.line1 }}, {{ addr.line2 }}, {{ addr.city }}, {{ addr.state }} – {{ addr.pincode }}
                </p>
              </Label>
            </div>
          </RadioGroup>
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
          <RadioGroup v-model="paymentMode" class="space-y-3">
            <div class="flex items-start gap-3">
              <RadioGroupItem value="immediate" id="pay-now" class="mt-1" />
              <Label for="pay-now" class="cursor-pointer">
                <p class="font-semibold">Pay Immediately</p>
                <p class="text-sm text-muted-foreground">UPI / Bank Transfer</p>
              </Label>
            </div>
            <div class="flex items-start gap-3">
              <RadioGroupItem value="credit" id="pay-credit" class="mt-1" />
              <Label for="pay-credit" class="cursor-pointer">
                <p class="font-semibold">Pay on Credit</p>
                <p class="text-sm text-muted-foreground">Pay on or before the credit period</p>
              </Label>
            </div>
          </RadioGroup>
        </CardContent>
      </Card>

      <Button size="lg" class="w-full" @click="handlePlaceOrder">
        Place Order — ₹{{ cartStore.totalPrice.toLocaleString() }}
      </Button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watchEffect } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@cd/stores/auth'
import { useCartStore } from '@cd/stores/cart'
import { mockAddresses } from '@cd/data/mockData'
import Button from '@cd/components/ui/Button.vue'
import Card from '@cd/components/ui/Card.vue'
import CardHeader from '@cd/components/ui/CardHeader.vue'
import CardContent from '@cd/components/ui/CardContent.vue'
import RadioGroup from '@cd/components/ui/RadioGroup.vue'
import RadioGroupItem from '@cd/components/ui/RadioGroupItem.vue'
import Label from '@cd/components/ui/Label.vue'

const router = useRouter()
const authStore = useAuthStore()
const cartStore = useCartStore()

watchEffect(() => {
  if (!authStore.isAuthenticated) {
    router.replace('/store/login')
  } else if (cartStore.items.length === 0) {
    router.replace('/store/cart')
  }
})

const selectedAddress = ref(mockAddresses[0].id)
const paymentMode = ref<'credit' | 'immediate'>('immediate')

const handlePlaceOrder = () => {
  cartStore.clearCart()
  alert('Order placed successfully!')
  router.push('/store/orders')
}
</script>
