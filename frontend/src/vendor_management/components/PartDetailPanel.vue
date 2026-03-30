<template>
  <div class="part-detail">
    <!-- Empty state -->
    <div v-if="!part" class="empty-state">
      <div class="es-icon">🔍</div>
      <div class="es-text">Select a part</div>
      <div class="es-sub">Choose a part from the left to view details and compare vendors</div>
    </div>

    <template v-else>
      <!-- Header -->
      <div class="pd-header">
        <div class="pd-title">{{ part.name }}</div>
        <div class="pd-sub" v-if="!selectedSize">Select a size to view vendor options</div>
        <div class="pd-sub" v-else>
          <span class="pd-sub-size">{{ selectedSize }}</span>
          — select a vendor below to proceed
        </div>
      </div>

      <div class="pd-body">
        <!-- Left column: image + sizes -->
        <div class="pd-left">
          <div class="pd-image-wrap">
            <img :src="part.image" :alt="part.name" class="pd-image" />
          </div>

          <div class="pd-sizes-section">
            <div class="pd-sizes-label">Available Sizes</div>
            <div class="pd-sizes-grid">
              <button
                v-for="sizeObj in part.sizes"
                :key="sizeObj.size"
                class="pd-size-btn"
                :class="{ active: selectedSize === sizeObj.size }"
                @click="selectSize(sizeObj)"
              >
                <span class="pd-size-label">{{ sizeObj.size }}</span>
                <span class="pd-size-vendors">
                  <svg width="9" height="9" viewBox="0 0 14 14" fill="none" stroke="currentColor" stroke-width="1.5">
                    <rect x="2" y="4" width="10" height="8" rx="1"/><path d="M5 4V3a2 2 0 014 0v1"/>
                  </svg>
                  {{ sizeObj.suppliers.length }}
                </span>
              </button>
            </div>
          </div>
        </div>

        <!-- Right column: vendor comparison (shown after size selected) -->
        <div class="pd-right" :class="{ visible: !!selectedSize }">
          <div v-if="!selectedSize" class="pd-vendor-empty">
            <div class="pve-icon">🏪</div>
            <div class="pve-text">Select a size to compare vendors</div>
          </div>

          <template v-else>
            <div class="pd-vendors-label">
              Vendors for <strong>{{ selectedSize }}</strong>
            </div>

            <div class="pd-vendor-cards">
              <div
                v-for="v in currentVendors"
                :key="v.vendorId"
                class="pv-card"
                :class="{ 'best-price': v.vendorId === bestPriceId, 'is-selected': selectedVendorId === v.vendorId }"
                @click="selectedVendorId = v.vendorId"
              >
                <div class="pv-top">
                  <div>
                    <div class="pv-name">{{ v.vendor ? v.vendor.name : v.vendorId }}</div>
                    <div class="pv-loc">{{ v.vendor ? v.vendor.location : '' }}</div>
                  </div>
                  <span v-if="v.vendorId === bestPriceId" class="chip pv-best">Best Price</span>
                </div>
                <div class="pv-details">
                  <div class="pv-detail">
                    <span class="pvd-label">Price</span>
                    <span class="pvd-value">₹{{ v.price }}</span>
                  </div>
                  <div class="pv-detail">
                    <span class="pvd-label">Lead Time</span>
                    <span class="pvd-value pv-lead">
                      <span class="pv-dot" :style="{ background: leadColor(v.leadTime) }"></span>
                      {{ v.leadTime }}d
                    </span>
                  </div>
                  <div class="pv-detail">
                    <span class="pvd-label">Last Purchased</span>
                    <span class="pvd-value pvd-date">{{ v.lastPurchased }}</span>
                  </div>
                </div>
                <div v-if="selectedVendorId === v.vendorId" class="pv-selected-mark">
                  <svg width="10" height="10" viewBox="0 0 12 12" fill="none" stroke="currentColor" stroke-width="2">
                    <polyline points="2,6 5,9 10,3"/>
                  </svg>
                  Selected
                </div>
              </div>
            </div>

            <div class="pd-action-bar">
              <button
                class="btn btn-primary pd-procure-btn"
                :disabled="!selectedVendorId"
                @click="confirmVendor"
              >
                Make Procurement Request
              </button>
              <div v-if="!selectedVendorId" class="pd-action-hint">Select a vendor to continue</div>
            </div>
          </template>
        </div>
      </div>
    </template>
  </div>
</template>

<script>
export default {
  name: 'PartDetailPanel',
  props: {
    part:    { type: Object, default: null },
    vendors: { type: Array,  default: () => [] }
  },
  emits: ['select-vendor'],
  data() {
    return {
      selectedSize:     null,
      selectedSizeObj:  null,
      selectedVendorId: null
    }
  },
  watch: {
    part() {
      this.selectedSize     = null
      this.selectedSizeObj  = null
      this.selectedVendorId = null
    }
  },
  computed: {
    currentVendors() {
      if (!this.selectedSizeObj) return []
      return this.selectedSizeObj.suppliers.map(s => ({
        ...s,
        vendor: this.vendors.find(v => v.id === s.vendorId) || null
      }))
    },
    bestPriceId() {
      if (!this.currentVendors.length) return null
      return this.currentVendors.reduce((min, v) => v.price < min.price ? v : min).vendorId
    }
  },
  methods: {
    selectSize(sizeObj) {
      this.selectedSize     = sizeObj.size
      this.selectedSizeObj  = sizeObj
      this.selectedVendorId = null
    },
    leadColor(days) {
      if (days <= 3) return 'var(--green)'
      if (days <= 7) return 'var(--amber)'
      return 'var(--red)'
    },
    confirmVendor() {
      const v = this.currentVendors.find(v => v.vendorId === this.selectedVendorId)
      this.$emit('select-vendor', {
        part:       this.part,
        size:       this.selectedSize,
        vendorId:   this.selectedVendorId,
        vendorName: v?.vendor?.name || this.selectedVendorId,
        price:      v?.price
      })
    }
  }
}
</script>

<style scoped>
.part-detail {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  background: var(--bg);
}

.pd-header {
  padding: 14px 20px;
  background: var(--white);
  border-bottom: 1.5px solid var(--border);
  flex-shrink: 0;
  display: flex;
  align-items: baseline;
  gap: 10px;
}
.pd-title { font-size: 15px; font-weight: 600; color: var(--ink); letter-spacing: -0.2px; }
.pd-sub   { font-size: 11.5px; color: var(--ink-4); }
.pd-sub-size { font-family: 'Geist Mono', monospace; color: var(--blue); font-weight: 600; }

.pd-body {
  flex: 1;
  overflow: hidden;
  display: flex;
  gap: 0;
}

/* ── Left column ── */
.pd-left {
  width: 300px;
  flex-shrink: 0;
  border-right: 1.5px solid var(--border);
  overflow-y: auto;
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 16px;
  background: var(--white);
}

.pd-image-wrap {
  background: white;
  border: 1.5px solid var(--border);
  border-radius: 10px;
  padding: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
}
.pd-image {
  width: 130px;
  height: 160px;
  object-fit: contain;
  border-radius: 4px;
}

.pd-sizes-label {
  font-size: 10.5px;
  font-weight: 600;
  color: var(--ink-4);
  text-transform: uppercase;
  letter-spacing: 0.5px;
  margin-bottom: 8px;
}
.pd-sizes-grid {
  display: flex;
  flex-direction: column;
  gap: 5px;
}
.pd-size-btn {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 12px;
  background: var(--surface);
  border: 1.5px solid var(--border);
  border-radius: 7px;
  cursor: pointer;
  font-family: 'Geist', sans-serif;
  transition: all 0.12s;
  text-align: left;
  width: 100%;
}
.pd-size-btn:hover { border-color: var(--blue); background: var(--blue-dim); }
.pd-size-btn.active { border-color: var(--blue); background: var(--blue-dim); }
.pd-size-label { font-size: 12.5px; font-weight: 500; color: var(--ink); font-family: 'Geist Mono', monospace; }
.pd-size-vendors { display: flex; align-items: center; gap: 3px; font-size: 10.5px; color: var(--ink-4); }
.pd-size-btn:hover .pd-size-vendors,
.pd-size-btn.active .pd-size-vendors { color: var(--blue); }

/* ── Right column ── */
.pd-right {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  background: var(--bg);
}

.pd-vendor-empty {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 8px;
}
.pve-icon { font-size: 28px; opacity: 0.25; }
.pve-text { font-size: 12.5px; color: var(--ink-4); }

.pd-vendors-label {
  padding: 12px 18px 8px;
  font-size: 11px;
  font-weight: 600;
  color: var(--ink-3);
  text-transform: uppercase;
  letter-spacing: 0.4px;
  flex-shrink: 0;
}
.pd-vendors-label strong { color: var(--blue); font-family: 'Geist Mono', monospace; font-size: 12px; }

.pd-vendor-cards {
  flex: 1;
  overflow-y: auto;
  padding: 0 18px 14px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

/* Vendor cards */
.pv-card {
  border: 1.5px solid var(--border);
  border-radius: 8px;
  padding: 11px 13px;
  cursor: pointer;
  transition: all 0.12s;
  background: var(--white);
}
.pv-card:hover       { border-color: var(--ink-4); background: var(--surface); }
.pv-card.best-price  { border-color: var(--green); background: var(--green-dim); }
.pv-card.is-selected { border-color: var(--blue);  background: var(--blue-dim); }
.pv-card.best-price.is-selected { border-color: var(--blue); background: var(--blue-dim); }

.pv-top {
  display: flex; align-items: flex-start; justify-content: space-between; margin-bottom: 8px;
}
.pv-name { font-size: 12.5px; font-weight: 600; color: var(--ink); }
.pv-loc  { font-size: 10.5px; color: var(--ink-4); margin-top: 1px; }
.pv-best { background: var(--green-dim); color: var(--green); flex-shrink: 0; }

.pv-details { display: flex; gap: 16px; }
.pv-detail  { display: flex; flex-direction: column; gap: 1px; }
.pvd-label  { font-size: 9.5px; font-weight: 600; color: var(--ink-4); text-transform: uppercase; letter-spacing: 0.3px; }
.pvd-value  { font-size: 13px; font-weight: 600; color: var(--ink); font-family: 'Geist Mono', monospace; }
.pv-lead    { display: flex; align-items: center; gap: 4px; font-family: 'Geist', sans-serif; font-weight: 500; }
.pv-dot     { width: 6px; height: 6px; border-radius: 50%; flex-shrink: 0; }
.pvd-date   { font-size: 11px; font-weight: 500; color: var(--ink-3); }

.pv-selected-mark {
  display: inline-flex; align-items: center; gap: 4px;
  font-size: 10px; font-weight: 600; color: var(--blue); margin-top: 7px;
}

/* Action bar */
.pd-action-bar {
  padding: 12px 18px;
  border-top: 1.5px solid var(--border);
  background: var(--white);
  flex-shrink: 0;
  display: flex;
  align-items: center;
  gap: 12px;
}
.pd-procure-btn { flex-shrink: 0; }
.pd-procure-btn:disabled { opacity: 0.4; cursor: not-allowed; }
.pd-action-hint { font-size: 11.5px; color: var(--ink-4); }
</style>
