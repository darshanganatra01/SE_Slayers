<template>
  <div :class="cn('grid gap-2', $attrs.class as string)">
    <slot />
  </div>
</template>
<script setup lang="ts">
import { provide, computed } from 'vue'
import { cn } from '@cd/lib/utils'

const props = defineProps<{ modelValue: string }>()
const emit = defineEmits(['update:modelValue'])

provide('radioGroupValue', computed(() => props.modelValue))
provide('radioGroupUpdate', (val: string) => emit('update:modelValue', val))
</script>
