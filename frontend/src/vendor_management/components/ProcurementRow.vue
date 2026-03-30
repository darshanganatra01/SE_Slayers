<template>
  <tr
    class="pr-row"
    :class="{ selected, received: req.status === 'received' }"
    @click="$emit('select', req.id)"
  >
    <!-- ID -->
    <td class="pr-id">{{ req.id }}</td>

    <!-- Part + Size -->
    <td>
      <div class="pr-part">{{ req.partName }}</div>
      <div class="pr-size">{{ req.size }}</div>
    </td>

    <!-- Date -->
    <td class="pr-date">{{ req.date }}</td>

    <!-- Vendor -->
    <td class="pr-vendor">{{ vendorName }}</td>

    <!-- Qty -->
    <td class="pr-qty">{{ req.quantity ? req.quantity + ' pcs' : '—' }}</td>


    <!-- Status -->
    <td>
      <span class="chip pr-status" :class="statusClass">{{ statusLabel }}</span>
    </td>
  </tr>
</template>

<script>
export default {
  name: 'ProcurementRow',
  props: {
    req:        { type: Object, required: true },
    vendorName: { type: String, default: '—' },
    selected:   { type: Boolean, default: false }
  },
  emits: ['select'],
  computed: {
    statusClass() {
      return this.req.status === 'received' ? 's-received' : 's-pending'
    },
    statusLabel() {
      return this.req.status === 'received' ? 'Received' : 'Pending'
    }
  }
}
</script>

<style scoped>
.pr-row td {
  padding: 10px 12px;
  border-bottom: 1px solid var(--border-2);
  vertical-align: middle;
  font-size: 12.5px;
  color: var(--ink-2);
  white-space: nowrap;
  cursor: pointer;
}
.pr-row:hover td { background: var(--surface); }
.pr-row.selected td { background: var(--blue-dim); }

.pr-id {
  font-family: 'Geist Mono', monospace;
  font-size: 11px;
  color: var(--blue);
  font-weight: 600;
}

.pr-part {
  font-weight: 600;
  color: var(--ink);
  font-size: 12.5px;
}
.pr-size {
  font-size: 10.5px;
  color: var(--ink-4);
  font-family: 'Geist Mono', monospace;
  margin-top: 1px;
}

.pr-date   { color: var(--ink-3); font-size: 12px; }
.pr-vendor { font-weight: 500; color: var(--ink); }
.pr-qty    { font-family: 'Geist Mono', monospace; font-size: 12px; }

/* Status chips */
.s-pending  { background: var(--amber-dim); color: var(--amber); }
.s-received { background: var(--green-dim); color: var(--green); }
</style>
