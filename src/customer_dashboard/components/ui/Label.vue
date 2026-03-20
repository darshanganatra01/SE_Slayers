<template>
  <label :class="cn('text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70', $attrs.class as string)" :for="$attrs.for as string">
    <slot />
  </label>
</template>
<script setup lang="ts">
import { cn } from '@cd/lib/utils'
</script>
