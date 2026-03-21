<template>
  <div :class="cn('relative aspect-square h-4 w-4 shrink-0', $attrs.class as string)">
    <input
      type="radio"
      :id="id"
      :value="value"
      :checked="isChecked"
      @change="updateValue"
      class="peer absolute inset-0 m-0 h-full w-full cursor-pointer opacity-0"
    />
    <div class="pointer-events-none flex h-full w-full items-center justify-center rounded-full border border-primary bg-background text-primary peer-focus-visible:ring-2 peer-focus-visible:ring-ring peer-focus-visible:ring-offset-2 peer-disabled:cursor-not-allowed peer-disabled:opacity-50">
      <span v-if="isChecked" class="h-2.5 w-2.5 rounded-full bg-current"></span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { inject, computed, Ref } from 'vue'
import { cn } from '@cd/lib/utils'

const props = defineProps<{ value: string; id?: string }>()

const groupValue = inject<Ref<string>>('radioGroupValue')!
const triggerUpdate = inject<(val: string) => void>('radioGroupUpdate')!

const isChecked = computed(() => groupValue.value === props.value)

const updateValue = () => {
  triggerUpdate(props.value)
}
</script>
