<template>
  <tr class="vendor-row" @click="$emit('select', vendor.id)">
    <td>
      <div class="vr-name">{{ vendor.name }}</div>
      <div class="vr-id">{{ vendor.id }}</div>
    </td>

    <td>
      <div class="vr-parts">
        <VendorTag v-for="part in visibleParts" :key="part" :label="part" />
        <span v-if="extraCount > 0" class="vr-extra">+{{ extraCount }}</span>
        <span v-if="vendor.parts.length === 0" class="vr-empty">No products mapped</span>
      </div>
    </td>

    <td>
      <div class="vr-lead">
        <span class="vr-lead-dot" :style="{ background: leadColor }"></span>
        {{ leadLabel }}
      </div>
    </td>

    <td>{{ vendor.location }}</td>

    <td>
      <div class="vr-phone">{{ vendor.contact.phone }}</div>
      <div class="vr-email">{{ vendor.contact.email }}</div>
    </td>
  </tr>
</template>

<script>
import VendorTag from './VendorTag.vue'

export default {
  name: 'VendorRow',
  components: { VendorTag },
  props: {
    vendor: { type: Object, required: true }
  },
  emits: ['select'],
  computed: {
    visibleParts() {
      return this.vendor.parts.slice(0, 2)
    },
    extraCount() {
      return Math.max(0, this.vendor.parts.length - 2)
    },
    leadLabel() {
      if (this.vendor.leadTime == null) return 'Not set'
      return `${this.vendor.leadTime} day${this.vendor.leadTime !== 1 ? 's' : ''}`
    },
    leadColor() {
      if (this.vendor.leadTime == null) return 'var(--border-2)'
      if (this.vendor.leadTime <= 3) return 'var(--green)'
      if (this.vendor.leadTime <= 7) return 'var(--amber)'
      return 'var(--red)'
    }
  }
}
</script>

<style scoped>
.vendor-row td {
  padding: 11px 12px;
  border-bottom: 1px solid var(--border-2);
  vertical-align: middle;
  font-size: 12.5px;
  color: var(--ink-2);
  white-space: nowrap;
}
.vendor-row:hover td {
  background: var(--surface);
  cursor: pointer;
}

.vr-name {
  font-weight: 600;
  color: var(--ink);
  font-size: 12.5px;
  line-height: 1.3;
}
.vr-id {
  font-size: 10.5px;
  color: var(--ink-4);
  font-family: 'Geist Mono', monospace;
  margin-top: 2px;
}

.vr-parts {
  display: flex;
  align-items: center;
  gap: 4px;
  flex-wrap: wrap;
}
.vr-extra {
  font-size: 10px;
  font-weight: 600;
  color: var(--ink-4);
  background: var(--surface);
  border: 1px solid var(--border-2);
  padding: 1px 5px;
  border-radius: 4px;
}
.vr-empty { font-size: 11px; color: var(--ink-4); }
.vr-lead {
  display: inline-flex;
  align-items: center;
  gap: 6px;
}
.vr-lead-dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  flex-shrink: 0;
}

.vr-phone {
  font-size: 12px;
  color: var(--ink-2);
  font-family: 'Geist Mono', monospace;
  line-height: 1.3;
}
.vr-email {
  font-size: 10.5px;
  color: var(--ink-4);
  margin-top: 2px;
}
</style>
