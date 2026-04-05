<template>
  <div class="ph-wrap">

    <!-- Table panel -->
    <div class="ph-main">

      <!-- Sub-header with counts -->
      <div class="ph-header">
        <div class="ph-header-left">
          <span class="ph-count">{{ procurements.length }} requests</span>
          <span class="ph-pill pending">{{ pendingCount }} Pending</span>
          <span class="ph-pill received">{{ receivedCount }} Received</span>
        </div>
      </div>

      <!-- Empty state -->
      <div v-if="loading" class="empty-state">
        <div class="es-icon">⌛</div>
        <div class="es-text">Loading procurement requests</div>
        <div class="es-sub">Fetching vendor orders from the database</div>
      </div>

      <div v-else-if="error" class="empty-state">
        <div class="es-icon">!</div>
        <div class="es-text">Unable to load procurement requests</div>
        <div class="es-sub">{{ error }}</div>
      </div>

      <div v-else-if="procurements.length === 0" class="empty-state">
        <div class="es-icon">📋</div>
        <div class="es-text">No procurement requests</div>
        <div class="es-sub">Submit a procurement request from Part Search & Compare</div>
      </div>

      <!-- Table -->
      <div v-else class="ph-table-wrap">
        <table class="ph-table">
          <colgroup>
            <col style="width: 9%"  />
            <col style="width: 26%" />
            <col style="width: 14%" />
            <col style="width: 22%" />
            <col style="width: 11%" />
            <col style="width: 18%" />
          </colgroup>
          <thead>
            <tr>
              <th>ID</th>
              <th>Part / Specification</th>
              <th>Date</th>
              <th>Vendor</th>
              <th>Lots / Qty</th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody>
            <ProcurementRow
              v-for="req in procurements"
              :key="req.id"
              :req="req"
              :vendor-name="req.vendorName || vendorName(req.vendorId)"
              :selected="selectedId === req.id"
              @select="$emit('select', $event)"
            />
          </tbody>
        </table>
      </div>
    </div>

    <!-- Detail panel -->
    <ProcurementDetailPanel
      :req="selectedReq"
      :vendor="selectedVendor"
      :marking-received="selectedReq ? markingReceivedId === selectedReq.id : false"
      @close="$emit('select', null)"
      @mark-received="$emit('mark-received', $event)"
    />

  </div>
</template>

<script>
import ProcurementRow         from './ProcurementRow.vue'
import ProcurementDetailPanel from './ProcurementDetailPanel.vue'

export default {
  name: 'ProcurementHistory',
  components: { ProcurementRow, ProcurementDetailPanel },
  props: {
    procurements: { type: Array, default: () => [] },
    vendors:      { type: Array, default: () => [] },
    selectedId:   { type: String, default: null },
    markingReceivedId: { type: String, default: null },
    loading:      { type: Boolean, default: false },
    error:        { type: String, default: '' }
  },
  emits: ['select', 'mark-received'],
  computed: {
    pendingCount()  { return this.procurements.filter(r => r.status === 'pending').length },
    receivedCount() { return this.procurements.filter(r => r.status === 'received').length },

    selectedReq() {
      if (!this.selectedId) return null
      return this.procurements.find(r => r.id === this.selectedId) || null
    },
    selectedVendor() {
      if (!this.selectedReq) return null
      return this.vendors.find(v => v.id === this.selectedReq.vendorId) || {
        id: this.selectedReq.vendorId,
        name: this.selectedReq.vendorName || this.selectedReq.vendorId,
        location: '—',
        leadTime: null,
        contact: { phone: '—', email: '—' }
      }
    }
  },
  methods: {
    vendorName(vendorId) {
      return this.vendors.find(v => v.id === vendorId)?.name || '—'
    }
  }
}
</script>

<style scoped>
.ph-wrap {
  flex: 1;
  display: flex;
  overflow: hidden;
}

.ph-main {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

/* Sub-header */
.ph-header {
  display: flex;
  align-items: center;
  padding: 12px 22px;
  border-bottom: 1.5px solid var(--border-2);
  background: var(--white);
  flex-shrink: 0;
  gap: 10px;
}
.ph-header-left {
  display: flex;
  align-items: center;
  gap: 8px;
}
.ph-count {
  font-size: 11.5px;
  font-weight: 600;
  color: var(--ink-3);
  font-family: 'Geist Mono', monospace;
}
.ph-pill {
  font-size: 10px;
  font-weight: 600;
  padding: 2px 8px;
  border-radius: 10px;
}
.ph-pill.pending  { background: var(--amber-dim); color: var(--amber); }
.ph-pill.received { background: var(--green-dim); color: var(--green); }

/* Table */
.ph-table-wrap {
  flex: 1;
  overflow-y: auto;
  padding: 16px 22px;
}
.ph-table {
  width: 100%;
  border-collapse: collapse;
  background: var(--white);
  border: 1.5px solid var(--border);
  border-radius: 8px;
  overflow: hidden;
}
.ph-table th {
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
