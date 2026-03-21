<template>
  <span class="vendor-tag chip">{{ label }}</span>
</template>

<script>
export default {
  name: 'VendorTag',
  props: {
    label: { type: String, required: true }
  }
}
</script>

<style scoped>
.vendor-tag {
  background: var(--blue-dim);
  color: var(--blue);
}
</style>
