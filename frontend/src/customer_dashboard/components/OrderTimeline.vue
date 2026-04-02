<template>
  <div class="flex items-center justify-center gap-0 w-full">
    <div v-for="(step, i) in steps" :key="step.label" class="flex items-center">
      <div class="flex flex-col items-center">
        <div
          :class="[
            'flex h-[38.4px] w-[38.4px] items-center justify-center rounded-full text-xs font-bold',
            step.completed ? 'bg-success text-success-foreground' : 'bg-muted text-muted-foreground'
          ]"
        >
          <Check v-if="step.completed" class="h-[19.2px] w-[19.2px]" />
          <span v-else>{{ i + 1 }}</span>
        </div>
        <span class="mt-1 text-xs font-medium text-foreground">{{ step.label }}</span>
        <span v-if="step.date" class="text-[10px] text-muted-foreground">{{ step.date }}</span>
      </div>
      <div
        v-if="i < steps.length - 1"
        :class="['mx-1 h-0.5 w-10 sm:w-16', step.completed ? 'bg-success' : 'bg-muted']"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { Check } from 'lucide-vue-next'

const props = defineProps<{
  status: string
  orderDate: string
}>()

const steps = computed(() => [
  { label: 'Order Placed', date: props.orderDate, completed: true },
  {
    label: 'Shipped',
    date: ['Shipped', 'Delivered'].includes(props.status) ? props.orderDate : undefined,
    completed: ['Shipped', 'Delivered'].includes(props.status),
  },
  {
    label: 'Delivered',
    date: props.status === 'Delivered' ? props.orderDate : undefined,
    completed: props.status === 'Delivered',
  },
])
</script>
