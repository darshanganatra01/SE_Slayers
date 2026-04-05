<template>
  <div class="dp" :class="{ open: !!req }">
    <template v-if="req">
      <div class="dp-head">
        <div class="dp-close-row">
          <div class="dp-pid">{{ req.id }}</div>
          <button class="dp-close-btn" type="button" @click="$emit('close')">Close ✕</button>
        </div>
        <div class="dp-name">{{ req.partName }}</div>
        <div class="dp-chips-row">
          <span class="chip" :class="statusClass(req.status)">{{ statusLabel(req.status) }}</span>
        </div>
      </div>

      <div class="dp-scroll">
        <div>
          <div class="dp-sec-label">Request Details</div>
          <div class="dp-kv"><span class="k">Product</span><span class="v">{{ req.partName }}</span></div>
          <div class="dp-kv"><span class="k">Specification</span><span class="v mono dp-spec">{{ req.specification }}</span></div>
          <div class="dp-kv"><span class="k">Requested On</span><span class="v">{{ req.date }}</span></div>
        </div>

        <div>
          <div class="dp-sec-label">Purchase Logic</div>
          <div class="dp-kv"><span class="k">Current Buy</span><span class="v mono">{{ currencyLabel(req.currentBuy) }}</span></div>
          <div class="dp-kv"><span class="k">Unit Measurement Buy</span><span class="v mono">{{ countLabel(req.unitMeasurementBuy, 'part') }}</span></div>
          <div class="dp-kv"><span class="k">Lot Size</span><span class="v mono">{{ countLabel(req.lotSize, 'unit') }}</span></div>
          <div class="dp-kv"><span class="k">No. of Lots</span><span class="v mono">{{ countLabel(req.lotCount, 'lot') }}</span></div>
          <div class="dp-kv"><span class="k">Ordered Quantity</span><span class="v mono">{{ countLabel(req.orderedQty, 'part') }}</span></div>
          <div class="dp-kv"><span class="k">Total Cost</span><span class="v mono dp-total">{{ currencyLabel(req.totalCost) }}</span></div>
        </div>

        <div v-if="vendor">
          <div class="dp-sec-label">Vendor</div>
          <div class="dp-kv"><span class="k">Name</span><span class="v">{{ vendor.name }}</span></div>
          <div class="dp-kv"><span class="k">Location</span><span class="v">{{ vendor.location }}</span></div>
          <div class="dp-kv"><span class="k">Phone</span><span class="v mono">{{ vendor.contact?.phone || '—' }}</span></div>
          <div class="dp-kv"><span class="k">Email</span><span class="v">{{ vendor.contact?.email || '—' }}</span></div>
          <div class="dp-kv">
            <span class="k">Lead Time</span>
            <span class="v dp-lead">
              <span class="dp-lead-dot" :style="{ background: leadColor(vendor.leadTime) }"></span>
              {{ leadLabel(vendor.leadTime) }}
            </span>
          </div>
        </div>
      </div>

      <div class="dp-footer">
        <div class="dp-flow-label">Status flow</div>
        <div class="dp-flow">
          <div class="df-step" :class="{ done: true, current: req.status === 'pending' }">Pending</div>
          <div class="df-arrow">›</div>
          <div class="df-step" :class="{ done: req.status === 'received', current: req.status === 'received' }">Received</div>
        </div>

        <button
          v-if="req.status === 'pending'"
          class="dp-action-btn dp-btn-fwd"
          type="button"
          :disabled="markingReceived"
          @click="$emit('mark-received', req.id)"
        >
          {{ markingReceived ? 'Marking order as received...' : '✓ Mark as Order Received' }}
        </button>
        <div v-else class="dp-done-badge">
          <svg width="12" height="12" viewBox="0 0 12 12" fill="none" stroke="currentColor" stroke-width="2">
            <polyline points="2,6 5,9 10,3" />
          </svg>
          Order has been received
        </div>
      </div>
    </template>
  </div>
</template>

<script>
export default {
  name: 'ProcurementDetailPanel',
  props: {
    req: { type: Object, default: null },
    vendor: { type: Object, default: null },
    markingReceived: { type: Boolean, default: false }
  },
  emits: ['close', 'mark-received'],
  methods: {
    statusClass(status) {
      if (status === 'received') return 'chip-received'
      if (status === 'cancelled') return 'chip-cancelled'
      return 'chip-pending'
    },
    statusLabel(status) {
      if (status === 'received') return 'Received'
      if (status === 'cancelled') return 'Cancelled'
      return 'Pending'
    },
    currencyLabel(value) {
      if (value == null) return '—'
      return `₹${Number(value).toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`
    },
    countLabel(value, singular) {
      if (value == null) return '—'
      const noun = Number(value) === 1 ? singular : `${singular}s`
      return `${value} ${noun}`
    },
    leadColor(days) {
      if (days == null) return 'var(--border-2)'
      if (days <= 3) return 'var(--green)'
      if (days <= 7) return 'var(--amber)'
      return 'var(--red)'
    },
    leadLabel(days) {
      if (days == null) return 'Not set'
      return `${days} day${days !== 1 ? 's' : ''}`
    }
  }
}
</script>

<style scoped>
.dp {
  width: 0;
  flex-shrink: 0;
  overflow: hidden;
  background: var(--white);
  border-left: 1.5px solid var(--border);
  display: flex;
  flex-direction: column;
  transition: width 0.24s cubic-bezier(0.4, 0, 0.2, 1);
}

.dp.open { width: 320px; }

.dp-head {
  padding: 14px 18px 12px;
  border-bottom: 1.5px solid var(--border);
  flex-shrink: 0;
}

.dp-close-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 10px;
}

.dp-pid {
  font-family: 'Geist Mono', monospace;
  font-size: 10.5px;
  color: var(--blue);
  font-weight: 600;
}

.dp-close-btn {
  background: none;
  border: 1.5px solid var(--border);
  border-radius: 5px;
  padding: 3px 10px;
  font-size: 10.5px;
  color: var(--ink-3);
  cursor: pointer;
  font-family: 'Geist', sans-serif;
  font-weight: 600;
  transition: all 0.12s;
}

.dp-close-btn:hover {
  background: var(--ink);
  color: #fff;
  border-color: var(--ink);
}

.dp-name {
  font-size: 16px;
  font-weight: 600;
  color: var(--ink);
  letter-spacing: -0.3px;
  margin-bottom: 7px;
}

.dp-chips-row {
  display: flex;
  gap: 5px;
  flex-wrap: wrap;
}

.chip-pending { background: var(--amber-dim); color: var(--amber); }
.chip-received { background: var(--green-dim); color: var(--green); }
.chip-cancelled { background: #fee2e2; color: #b91c1c; }

.dp-scroll {
  flex: 1;
  overflow-y: auto;
  padding: 14px 18px;
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.dp-scroll::-webkit-scrollbar { width: 3px; }
.dp-scroll::-webkit-scrollbar-thumb { background: var(--border-2); }

.dp-sec-label {
  font-size: 9.5px;
  font-weight: 600;
  color: var(--ink-4);
  letter-spacing: 1.5px;
  text-transform: uppercase;
  margin-bottom: 8px;
  display: flex;
  align-items: center;
  gap: 8px;
}

.dp-sec-label::after {
  content: '';
  flex: 1;
  height: 1px;
  background: var(--border-2);
}

.dp-kv {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 12px;
  padding: 4px 0;
  font-size: 12.5px;
}

.dp-kv .k { color: var(--ink-4); }
.dp-kv .v {
  color: var(--ink);
  font-weight: 500;
  text-align: right;
}

.mono { font-family: 'Geist Mono', monospace; }
.dp-spec {
  white-space: normal;
  line-height: 1.5;
}

.dp-total { color: var(--blue); }

.dp-lead {
  display: flex;
  align-items: center;
  gap: 5px;
}

.dp-lead-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  flex-shrink: 0;
}

.dp-footer {
  padding: 12px 18px;
  border-top: 1.5px solid var(--border);
  flex-shrink: 0;
}

.dp-flow-label {
  font-size: 9.5px;
  font-weight: 600;
  color: var(--ink-4);
  letter-spacing: 1.5px;
  text-transform: uppercase;
  margin-bottom: 8px;
}

.dp-flow {
  display: flex;
  align-items: center;
  gap: 4px;
  margin-bottom: 10px;
}

.df-step {
  flex: 1;
  padding: 5px 4px;
  border-radius: 5px;
  border: 1px solid var(--border-2);
  background: var(--surface);
  text-align: center;
  font-size: 9px;
  font-weight: 600;
  font-family: 'Geist', sans-serif;
  letter-spacing: 0.3px;
  text-transform: uppercase;
  color: var(--ink-4);
  transition: all 0.15s;
}

.df-step.done { background: var(--green-dim); border-color: #86efac; color: var(--green); }
.df-step.current { background: var(--ink); border-color: var(--ink); color: #fff; }
.df-arrow { color: var(--ink-4); font-size: 10px; flex-shrink: 0; }

.dp-action-btn {
  width: 100%;
  padding: 9px;
  border-radius: 6px;
  font-family: 'Geist', sans-serif;
  font-weight: 600;
  font-size: 12px;
  cursor: pointer;
  transition: all 0.12s;
  border: none;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 5px;
}

.dp-btn-fwd { background: var(--green); color: #fff; }
.dp-btn-fwd:hover { background: #15803d; }
.dp-action-btn:disabled {
  background: #86efac;
  color: #f8fafc;
  cursor: wait;
  opacity: 0.9;
}

.dp-done-badge {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  font-size: 12px;
  font-weight: 600;
  color: var(--green);
  padding: 8px;
  background: var(--green-dim);
  border-radius: 6px;
}
</style>
