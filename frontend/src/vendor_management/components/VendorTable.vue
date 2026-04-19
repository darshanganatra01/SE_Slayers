<template>
  <div class="table-wrap">
    <div v-if="loading" class="empty-state">
      <div class="es-icon">⌛</div>
      <div class="es-text">Loading vendors</div>
      <div class="es-sub">Fetching the vendor directory</div>
    </div>

    <div v-else-if="vendors.length === 0" class="empty-state">
      <div class="es-icon">📦</div>
      <div class="es-text">No vendors found</div>
      <div class="es-sub">Try adjusting your search or filters</div>
    </div>

    <div v-else class="table-scroll">
      <table class="vendor-table">
        <colgroup>
          <col style="width: 20%" />
          <col style="width: 28%" />
          <col style="width: 14%" />
          <col style="width: 16%" />
          <col style="width: 22%" />
        </colgroup>
        <thead>
          <tr>
            <th>Vendor</th>
            <th>Products Sold</th>
            <th>Lead Time</th>
            <th>Location</th>
            <th>Contact</th>
          </tr>
        </thead>
        <tbody>
          <VendorRow
            v-for="vendor in vendors"
            :key="vendor.id"
            :vendor="vendor"
            @select="$emit('select', $event)"
          />
        </tbody>
      </table>
    </div>
  </div>
</template>

<script>
import VendorRow from './VendorRow.vue'

export default {
  name: 'VendorTable',
  components: { VendorRow },
  props: {
    loading: { type: Boolean, default: false },
    vendors: { type: Array, default: () => [] }
  },
  emits: ['select']
}
</script>

<style scoped>
.table-wrap {
  background: var(--white);
  border: 1.5px solid var(--border);
  border-radius: 8px;
  overflow: hidden;
}

.table-scroll {
  overflow-x: auto;
  overflow-y: hidden;
}

.vendor-table {
  width: 100%;
  min-width: 940px;
  border-collapse: collapse;
}

.vendor-table th {
  padding: 9px 12px;
  text-align: left;
  font-size: 10px;
  font-weight: 600;
  color: var(--ink-4);
  text-transform: uppercase;
  letter-spacing: 0.5px;
  background: var(--surface);
  border-bottom: 1.5px solid var(--border);
  white-space: nowrap;
}
</style>
