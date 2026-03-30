<template>
  <div v-if="visible" class="mo" @click.self="$emit('close')">
    <div class="mo-box">

      <!-- Header -->
      <div class="mo-head">
        <div>
          <div class="mo-title">{{ part ? part.name : '' }}</div>
          <div class="mo-size">Size: <strong>{{ size }}</strong></div>
        </div>
        <div class="mo-x" @click="$emit('close')">✕</div>
      </div>

      <!-- Vendor cards -->
      <div class="mo-body">
        <div
          v-for="v in vendors"
          :key="v.vendorId"
          class="sv-card"
          :class="{ 'best-price': v.vendorId === bestPriceId, 'is-selected': selectedVendorId === v.vendorId }"
          @click="selectedVendorId = v.vendorId"
        >
          <div class="sv-card-top">
            <div>
              <div class="sv-name">{{ v.vendor ? v.vendor.name : v.vendorId }}</div>
              <div class="sv-meta">
                {{ v.vendor ? v.vendor.location : '' }}
                <span v-if="v.vendor"> · {{ v.vendor.frequency }}</span>
              </div>
            </div>
            <span v-if="v.vendorId === bestPriceId" class="chip sv-best">Best Price</span>
          </div>

          <div class="sv-details">
            <div class="sv-detail">
              <span class="sv-detail-label">Price</span>
              <span class="sv-detail-value">₹{{ v.price }}</span>
            </div>
            <div class="sv-detail">
              <span class="sv-detail-label">Lead Time</span>
              <span class="sv-detail-value sv-lead">
                <span class="sv-lead-dot" :style="{ background: leadColor(v.leadTime) }"></span>
                {{ v.leadTime }} day{{ v.leadTime !== 1 ? 's' : '' }}
              </span>
            </div>
            <div class="sv-detail">
              <span class="sv-detail-label">Last Purchased</span>
              <span class="sv-detail-value sv-date">{{ v.lastPurchased }}</span>
            </div>
          </div>

          <div v-if="selectedVendorId === v.vendorId" class="sv-selected-badge">
            <svg width="10" height="10" viewBox="0 0 12 12" fill="none" stroke="currentColor" stroke-width="2">
              <polyline points="2,6 5,9 10,3"/>
            </svg>
            Selected
          </div>
        </div>
      </div>

      <!-- Footer -->
      <div class="mo-foot">
        <button class="btn-cancel" @click="$emit('close')">Cancel</button>
        <button
          class="btn btn-primary"
          :disabled="!selectedVendorId"
          @click="confirmVendor"
        >
          Make Procurement Request
        </button>
      </div>

    </div>
  </div>
</template>

<script>
export default {
  name: 'SizeVendorModal',
  props: {
    visible:    { type: Boolean, default: false },
    part:       { type: Object, default: null },
    size:       { type: String, default: '' },
    vendors:    { type: Array, default: () => [] },
    bestPriceId:{ type: String, default: null }
  },
  emits: ['close', 'select-vendor'],
  data() {
    return { selectedVendorId: null }
  },
  watch: {
    visible(val) {
      if (val) this.selectedVendorId = null
    }
  },
  methods: {
    leadColor(days) {
      if (days <= 3) return 'var(--green)'
      if (days <= 7) return 'var(--amber)'
      return 'var(--red)'
    },
    confirmVendor() {
      const vendor = this.vendors.find(v => v.vendorId === this.selectedVendorId)
      this.$emit('select-vendor', {
        part: this.part,
        size: this.size,
        vendorId: this.selectedVendorId,
        vendorName: vendor?.vendor?.name || this.selectedVendorId,
        price: vendor?.price
      })
    }
  }
}
</script>

<style scoped>
.mo {
  position: fixed; inset: 0; background: rgba(0,0,0,.45); z-index: 200;
  display: flex; align-items: center; justify-content: center;
  backdrop-filter: blur(2px);
}
.mo-box {
  background: var(--white); border: 1.5px solid var(--border);
  border-radius: 10px; width: 520px;
  max-height: 86vh; overflow: hidden;
  box-shadow: 0 8px 30px rgba(0,0,0,.14);
  display: flex; flex-direction: column;
}

.mo-head {
  padding: 16px 20px 14px; border-bottom: 1.5px solid var(--border);
  display: flex; justify-content: space-between; align-items: flex-start;
  flex-shrink: 0;
}
.mo-title { font-size: 15px; font-weight: 600; color: var(--ink); letter-spacing: -0.2px; }
.mo-size  { font-size: 11.5px; color: var(--ink-4); margin-top: 2px; font-family: 'Geist Mono', monospace; }
.mo-size strong { color: var(--ink-2); }
.mo-x {
  background: none; border: 1.5px solid var(--border); border-radius: 6px;
  width: 26px; height: 26px; display: flex; align-items: center; justify-content: center;
  color: var(--ink-3); font-size: 12px; cursor: pointer; transition: all 0.12s; flex-shrink: 0;
}
.mo-x:hover { background: var(--ink); color: #fff; border-color: var(--ink); }

.mo-body {
  flex: 1; overflow-y: auto;
  padding: 14px 18px;
  display: flex; flex-direction: column; gap: 10px;
}

/* Vendor card */
.sv-card {
  border: 1.5px solid var(--border);
  border-radius: 8px;
  padding: 12px 14px;
  cursor: pointer;
  transition: all 0.12s;
  position: relative;
}
.sv-card:hover { border-color: var(--ink-4); background: var(--surface); }
.sv-card.best-price { border-color: var(--green); background: var(--green-dim); }
.sv-card.is-selected { border-color: var(--blue); background: var(--blue-dim); }
.sv-card.best-price.is-selected { border-color: var(--blue); background: var(--blue-dim); }

.sv-card-top {
  display: flex; align-items: flex-start; justify-content: space-between; margin-bottom: 10px;
}
.sv-name { font-size: 13px; font-weight: 600; color: var(--ink); }
.sv-meta { font-size: 11px; color: var(--ink-4); margin-top: 1px; }
.sv-best { background: var(--green-dim); color: var(--green); flex-shrink: 0; }

.sv-details { display: flex; gap: 20px; }
.sv-detail  { display: flex; flex-direction: column; gap: 2px; }
.sv-detail-label {
  font-size: 9.5px; font-weight: 600; color: var(--ink-4);
  text-transform: uppercase; letter-spacing: 0.3px;
}
.sv-detail-value {
  font-size: 13px; font-weight: 600; color: var(--ink);
  font-family: 'Geist Mono', monospace;
}
.sv-lead {
  display: flex; align-items: center; gap: 5px;
  font-family: 'Geist', sans-serif; font-weight: 500; color: var(--ink-2);
}
.sv-lead-dot { width: 6px; height: 6px; border-radius: 50%; flex-shrink: 0; }
.sv-date { font-size: 11.5px; font-weight: 500; color: var(--ink-3); }

.sv-selected-badge {
  display: inline-flex; align-items: center; gap: 4px;
  font-size: 10px; font-weight: 600; color: var(--blue);
  margin-top: 8px;
}

.mo-foot {
  padding: 12px 18px; border-top: 1.5px solid var(--border);
  display: flex; justify-content: flex-end; gap: 7px;
  flex-shrink: 0;
}
.btn:disabled { opacity: 0.45; cursor: not-allowed; }
</style>
