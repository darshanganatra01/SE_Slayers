<template>
  <div class="panel">
    <div class="panel-head">
      <div>
        <div class="panel-title">Pending stock arrivals</div>
        <div class="panel-sub">Pending and received procurement requests</div>
      </div>
      <button
        class="panel-link"
        type="button"
        @click="$emit('go-vendor', { source: 'procurement-history' })"
      >
        View all procurement requests →
      </button>
    </div>
    <div v-if="!orders.length" class="empty-state">No procurement requests yet.</div>
    <div
      v-for="(o, i) in orders"
      :key="i"
      class="por"
      :class="{ received: o.status === 'received' }"
      @click="$emit('go-vendor', { source: 'procurement-history', procurementId: o.procurementId })"
    >
      <div class="por-left">
        <div class="por-name">{{ o.name }}</div>
        <div class="por-detail">{{ o.detail }}</div>
      </div>
      <div class="por-right">
        <div class="por-status" :class="statusClass(o.status)">{{ statusLabel(o.status) }}</div>
        <div class="por-qty">× {{ o.qty }} parts</div>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'PendingArrivals',
  props: {
    orders: { type: Array, default: () => [] }
  },
  emits: ['go-vendor'],
  methods: {
    statusClass(status) {
      return status === 'received' ? 'por-status-received' : 'por-status-pending'
    },
    statusLabel(status) {
      return status === 'received' ? 'Received' : 'Pending'
    }
  }
}
</script>

<style scoped>
.panel {
  background: var(--white);
  border: 1.5px solid var(--border);
  border-radius: 8px;
  overflow: hidden;
}
.panel-head {
  display: flex; align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  border-bottom: 1px solid var(--border);
}
.panel-title { font-size: 13px; font-weight: 600; }
.panel-sub   { font-size: 11.5px; color: var(--ink-4); margin-top: 2px; }
.panel-link  {
  background: none;
  border: none;
  font-size: 12px; font-weight: 500;
  color: var(--blue); cursor: pointer;
  padding: 0;
  font-family: 'Geist', sans-serif;
}
.empty-state {
  padding: 24px 16px;
  font-size: 12.5px;
  color: var(--ink-4);
  text-align: center;
}

.por {
  display: flex; align-items: flex-start;
  padding: 11px 16px;
  border-bottom: 1px solid var(--border-2);
  gap: 10px; cursor: pointer;
  transition: background .1s;
}
.por:last-child { border-bottom: none; }
.por:hover { background: var(--surface); }

.por-left { flex: 1; min-width: 0; }
.por-name   { font-size: 13px; font-weight: 500; }
.por-detail { font-size: 11.5px; color: var(--ink-4); margin-top: 2px; }

.por-right {
  display: flex; flex-direction: column;
  align-items: flex-end; gap: 4px;
}
.por-status {
  padding: 2px 8px;
  border-radius: 999px;
  font-size: 10px;
  font-weight: 600;
}
.por-status-pending {
  background: var(--amber-dim);
  color: var(--amber);
}
.por-status-received {
  background: var(--green-dim);
  color: var(--green);
}
.por-qty { font-size: 12.5px; font-weight: 500; font-variant-numeric: tabular-nums; }
</style>
