<template>
  <div class="container max-w-3xl py-6">
    <Button variant="ghost" size="sm" @click="router.push('/store/orders')" class="mb-4">
      ← Back to Items
    </Button>

    <div v-if="isLoading" class="flex h-64 items-center justify-center">
      <p class="text-muted-foreground">Loading item details...</p>
    </div>

    <div v-else-if="!itemData" class="py-12 text-center">
      <h2 class="text-xl font-semibold">Item not found</h2>
      <p class="text-muted-foreground text-sm">We couldn't find the item you're looking for.</p>
    </div>

    <div v-else class="space-y-6">
      <div class="flex items-start justify-between border-b pb-4">
        <div>
          <h1 class="text-2xl font-bold text-foreground">{{ itemData.product.pName }}</h1>
          <p class="text-sm text-muted-foreground">Order #{{ itemData.coId }} · Item #{{ itemData.codId }}</p>
        </div>
        <Badge :variant="itemData.timeline[1].completed ? 'default' : 'secondary'">
          {{ itemData.timeline[1].completed ? 'Shipped' : 'Confirmed' }}
        </Badge>
      </div>

      <div class="grid gap-6 md:grid-cols-3">
        <div class="md:col-span-2 space-y-6">
          <Card>
            <CardHeader><CardTitle>Status Timeline</CardTitle></CardHeader>
            <CardContent class="pt-2">
              <div class="relative space-y-8 before:absolute before:left-[11px] before:top-2 before:h-[calc(100%-16px)] before:w-[2px] before:bg-muted">
                <div v-for="(step, idx) in itemData.timeline" :key="idx" class="relative flex items-start gap-4">
                  <div 
                    class="z-10 flex h-6 w-6 shrink-0 items-center justify-center rounded-full border-2 bg-background transition-colors"
                    :class="step.completed ? 'border-primary bg-primary text-primary-foreground' : 'border-muted bg-background'"
                  >
                    <Check v-if="step.completed" class="h-3 w-3" />
                  </div>
                  <div>
                    <p class="font-semibold leading-none" :class="step.completed ? 'text-foreground' : 'text-muted-foreground'">
                      {{ step.status }}
                      <span v-if="step.qty > 0" class="ml-2 inline-flex items-center rounded-full bg-primary/10 px-2 py-0.5 text-xs font-medium text-primary">
                        {{ step.qty }} {{ step.qty === 1 ? 'unit' : 'units' }}
                      </span>
                    </p>
                    <p v-if="step.date" class="mt-1 text-xs text-muted-foreground">
                      {{ step.date }}
                    </p>
                    <p v-else-if="!step.completed" class="mt-1 text-xs italic text-muted-foreground">
                      Pending...
                    </p>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader><CardTitle>Item Specification</CardTitle></CardHeader>
            <CardContent>
              <div class="rounded-lg border bg-muted/30 p-4">
                <p class="text-sm font-medium text-foreground">{{ itemData.product.specs || 'No specific variations' }}</p>
              </div>
            </CardContent>
          </Card>
        </div>

        <div class="space-y-6">
          <Card>
            <CardHeader><CardTitle>Ordered Item</CardTitle></CardHeader>
            <CardContent class="space-y-4">
              <div class="flex justify-between text-sm">
                <span class="text-muted-foreground">Quantity</span>
                <span class="font-semibold">{{ itemData.quantity }}</span>
              </div>
              <div class="flex justify-between text-sm">
                <span class="text-muted-foreground">Subtotal</span>
                <span class="font-semibold">₹{{ itemData.amount.toLocaleString() }}</span>
              </div>
            </CardContent>
          </Card>

          <div class="rounded-lg border bg-primary/5 p-4 text-center">
            <p class="text-xs font-medium text-primary uppercase tracking-wider">Help & Support</p>
            <p class="mt-1 text-xs text-muted-foreground">Issue with this item? Contact support at support@seslayers.com</p>
            <Button variant="outline" size="sm" class="mt-3 w-full text-xs">Request Support</Button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { getItemDetails } from '@cd/data/api'
import Button from '@cd/components/ui/Button.vue'
import Card from '@cd/components/ui/Card.vue'
import CardHeader from '@cd/components/ui/CardHeader.vue'
import CardTitle from '@cd/components/ui/CardTitle.vue'
import CardContent from '@cd/components/ui/CardContent.vue'
import Badge from '@cd/components/ui/Badge.vue'
import { Check } from 'lucide-vue-next'

const route = useRoute()
const router = useRouter()
const itemData = ref<any>(null)
const isLoading = ref(true)

onMounted(async () => {
  const codId = route.params.codId as string
  try {
    const data = await getItemDetails(codId)
    itemData.value = data
  } catch (err) {
    console.error("Failed to load item info:", err)
  } finally {
    isLoading.value = false
  }
})
</script>

<style scoped>
.container {
  min-height: calc(100vh - 120px);
}
</style>
