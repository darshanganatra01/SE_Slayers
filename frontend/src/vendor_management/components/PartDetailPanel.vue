<template>
  <div class="part-detail">
    <div v-if="!part && !loading && !error" class="empty-state">
      <div class="es-icon">🔍</div>
      <div class="es-text">Select a part</div>
      <div class="es-sub">Choose a product from the left to see all available specifications and compare vendors</div>
    </div>

    <div v-else-if="loading" class="empty-state">
      <div class="es-icon">⌛</div>
      <div class="es-text">Loading vendor matches</div>
      <div class="es-sub">Finding vendors for the exact product and specification</div>
    </div>

    <div v-else-if="error" class="empty-state">
      <div class="es-icon">!</div>
      <div class="es-text">Unable to load vendor matches</div>
      <div class="es-sub">{{ error }}</div>
    </div>

    <template v-else-if="part">
      <div class="pd-header">
        <div>
          <div class="pd-title">{{ part.name }}</div>
          <div v-if="selectedSpec" class="pd-sub">
            <span class="pd-sub-size">{{ selectedSpec.size }}</span>
            <span v-if="selectedSpec.spec"> · {{ selectedSpec.spec }}</span>
            <span class="pd-sub-copy"> · select a vendor below to proceed</span>
          </div>
          <div v-else class="pd-sub">Choose a specification to compare vendors</div>
        </div>
      </div>

      <div class="pd-body">
        <div class="pd-left">
          <div class="pd-image-wrap">
            <img v-if="part.image" :src="part.image" :alt="part.name" class="pd-image" />
            <div v-else class="pd-image-placeholder">
              <div class="pd-image-icon">IMG</div>
              <div class="pd-image-text">Product image placeholder</div>
            </div>
          </div>

          <div class="pd-specs-heading">Available Specifications</div>
          <div class="pd-spec-list">
            <button
              v-for="size in sizes"
              :key="size.key"
              class="pd-spec-card"
              :class="{ selected: selectedSpecKey === size.key }"
              type="button"
              @click="$emit('select-spec', size.key)"
            >
              <div class="pd-spec-copy">
                <div class="pd-spec-title">{{ size.size }}</div>
                <div v-if="size.spec" class="pd-spec-sub">{{ size.spec }}</div>
              </div>
              <div class="pd-spec-count">{{ size.suppliers.length }}</div>
            </button>
          </div>
        </div>

        <div class="pd-right">
          <div class="pd-vendors-label">
            <span v-if="selectedSpec">
              Vendors for <span class="pd-vendors-spec">{{ selectedSpec.specification || selectedSpec.size }}</span>
            </span>
            <span v-else>Choose a specification to compare vendors</span>
          </div>

          <div v-if="selectedSpec && !comparisonSuppliers.length" class="pd-vendor-empty">
            <div class="pve-icon">🏪</div>
            <div class="pve-text">No priced vendor matches found</div>
            <div class="pve-sub">This SKU exists, but no vendor pricing rows match the same product and exact specification yet.</div>
          </div>

          <div v-else-if="!selectedSpec" class="pd-vendor-empty">
            <div class="pve-icon">📏</div>
            <div class="pve-text">Select a specification</div>
            <div class="pve-sub">Once you pick a size/spec on the left, all vendors selling that exact spec will appear here.</div>
          </div>

          <template v-else>
            <div class="pd-vendor-cards">
              <div
                v-for="v in comparisonSuppliers"
                :key="v.vendorId"
                class="pv-card"
                :class="{
                  'best-price': v.vendorId === bestPriceId,
                  'is-selected': selectedVendorId === v.vendorId
                }"
                @click="selectedVendorId = v.vendorId"
              >
                <div class="pv-top">
                  <div>
                    <div class="pv-name">{{ v.vendor ? v.vendor.name : v.vendorId }}</div>
                    <div class="pv-loc">{{ v.vendor ? v.vendor.location : '' }}</div>
                  </div>
                  <div class="pv-chips">
                    <span v-if="v.vendorId === bestPriceId" class="chip pv-best">Best Price</span>
                  </div>
                </div>
                <div class="pv-details">
                  <div class="pv-detail">
                    <span class="pvd-label">Current Buy</span>
                    <span class="pvd-value">{{ priceLabel(v.price) }}</span>
                  </div>
                  <div class="pv-detail">
                    <span class="pvd-label">Lead Time</span>
                    <span class="pvd-value pv-lead">
                      <span class="pv-dot" :style="{ background: leadColor(v.leadTime) }"></span>
                      {{ leadLabel(v.leadTime) }}
                    </span>
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
    part: { type: Object, default: null },
    selectedSpecKey: { type: String, default: null },
    selection: { type: Object, default: null },
    loading: { type: Boolean, default: false },
    error: { type: String, default: '' }
  },
  emits: ['select-spec', 'select-vendor'],
  data() {
    return {
      selectedVendorId: null
    }
  },
  watch: {
    selection() {
      this.selectedVendorId = null
    },
    part() {
      this.selectedVendorId = null
    },
    selectedSpecKey() {
      this.selectedVendorId = null
    }
  },
  computed: {
    sizes() {
      return Array.isArray(this.part?.sizes) ? this.part.sizes : []
    },
    selectedSpec() {
      if (!this.selectedSpecKey) return null
      return this.sizes.find((size) => size.key === this.selectedSpecKey) || null
    },
    sourceSku() {
      return this.selection?.sourceSku?.skuId ? this.selection.sourceSku : null
    },
    comparisonSuppliers() {
      return Array.isArray(this.selection?.suppliers) ? this.selection.suppliers : []
    },
    bestPriceId() {
      const pricedVendors = this.comparisonSuppliers.filter((vendor) => typeof vendor.price === 'number')
      if (!pricedVendors.length) return null
      return pricedVendors.reduce((min, vendor) => vendor.price < min.price ? vendor : min).vendorId
    }
  },
  methods: {
    leadColor(days) {
      if (days == null) return 'var(--border-2)'
      if (days <= 3) return 'var(--green)'
      if (days <= 7) return 'var(--amber)'
      return 'var(--red)'
    },
    leadLabel(days) {
      if (days == null) return 'Not set'
      return `${days}d`
    },
    priceLabel(price) {
      if (typeof price !== 'number') return '—'
      return `₹${price.toLocaleString('en-IN')}`
    },
    confirmVendor() {
      const vendor = this.comparisonSuppliers.find((candidate) => candidate.vendorId === this.selectedVendorId)
      if (!vendor || !this.selectedSpec) return

      this.$emit('select-vendor', {
        partId: this.part?.id || this.sourceSku?.pid || this.sourceSku?.productId || '',
        partName: this.part?.name || this.sourceSku?.name || '',
        specification: this.selectedSpec.specification || this.selectedSpec.size || '',
        vendorId: vendor.vendorId,
        vendorName: vendor.vendor?.name || vendor.vendorId,
        skuId: vendor.skuId || '',
        currentBuy: vendor.currentBuy ?? vendor.price ?? null,
        unitMeasurementBuy: vendor.unitMeasurementBuy ?? null,
        lotSize: vendor.lotSize ?? null,
        leadTime: vendor.leadTime ?? null
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
}
.pd-title { font-size: 15px; font-weight: 600; color: var(--ink); letter-spacing: -0.2px; }
.pd-sub   { font-size: 11.5px; color: var(--ink-4); margin-top: 2px; }
.pd-sub-size { font-family: 'Geist Mono', monospace; color: var(--blue); font-weight: 600; }
.pd-sub-copy { color: var(--ink-4); }

.pd-body {
  flex: 1;
  overflow: hidden;
  display: flex;
  gap: 0;
}

.pd-left {
  width: 340px;
  flex-shrink: 0;
  border-right: 1.5px solid var(--border);
  overflow-y: auto;
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 14px;
  background: var(--white);
}

.pd-image-wrap {
  background: white;
  border: 1.5px solid var(--border);
  border-radius: 10px;
  overflow: hidden;
  height: 230px;
  display: flex;
  align-items: center;
  justify-content: center;
}
.pd-image {
  width: 100%;
  height: 100%;
  object-fit: contain;
}
.pd-image-placeholder {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 6px;
  color: var(--ink-4);
  font-size: 12px;
}
.pd-image-icon {
  width: 44px;
  height: 44px;
  display: grid;
  place-items: center;
  border-radius: 10px;
  background: var(--surface);
  border: 1px solid var(--border);
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.08em;
}

.pd-specs-heading {
  font-size: 11px;
  font-weight: 700;
  color: var(--ink-4);
  text-transform: uppercase;
  letter-spacing: 0.08em;
}

.pd-spec-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.pd-spec-card {
  width: 100%;
  border: 1.5px solid var(--border);
  border-radius: 10px;
  background: var(--surface);
  padding: 12px 13px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  text-align: left;
  cursor: pointer;
  transition: all 0.12s;
}
.pd-spec-card:hover {
  border-color: var(--ink-4);
  background: #f8fafc;
}
.pd-spec-card.selected {
  border-color: var(--blue);
  background: var(--blue-dim);
}
.pd-spec-copy {
  min-width: 0;
}
.pd-spec-title {
  font-size: 13px;
  font-weight: 600;
  color: var(--ink);
  font-family: 'Geist Mono', monospace;
}
.pd-spec-sub {
  margin-top: 4px;
  font-size: 11px;
  color: var(--ink-4);
}
.pd-spec-count {
  flex-shrink: 0;
  font-size: 11px;
  color: var(--ink-4);
  font-family: 'Geist Mono', monospace;
}

.pd-right {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.pd-vendors-label {
  padding: 16px 18px 0;
  font-size: 13px;
  font-weight: 600;
  color: var(--ink);
}
.pd-vendors-spec {
  font-family: 'Geist Mono', monospace;
  color: var(--blue);
}

.pd-vendor-empty {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 6px;
  color: var(--ink-4);
  text-align: center;
  padding: 24px;
}
.pve-icon { font-size: 20px; }
.pve-text { font-size: 14px; font-weight: 600; color: var(--ink-3); }
.pve-sub { font-size: 12px; max-width: 360px; line-height: 1.5; }

.pd-vendor-cards {
  flex: 1;
  overflow-y: auto;
  padding: 14px 18px 18px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.pv-card {
  background: var(--white);
  border: 1.5px solid var(--border);
  border-radius: 12px;
  padding: 14px;
  cursor: pointer;
  transition: border-color 0.12s, background 0.12s, box-shadow 0.12s;
}
.pv-card:hover {
  border-color: var(--ink-4);
  background: var(--surface);
}
.pv-card.best-price {
  border-color: #86efac;
  background: #dcfce7;
}
.pv-card.is-selected {
  border-color: var(--blue);
  background: var(--blue-dim);
}
.pv-card.best-price.is-selected {
  border-color: #16a34a;
  background: linear-gradient(180deg, #dcfce7 0%, #dbeafe 100%);
}

.pv-top {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 10px;
}
.pv-name {
  font-size: 14px;
  font-weight: 600;
  color: var(--ink);
}
.pv-loc {
  font-size: 11px;
  color: var(--ink-4);
  margin-top: 3px;
}
.pv-chips {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-wrap: wrap;
  justify-content: flex-end;
}
.chip {
  display: inline-flex;
  align-items: center;
  border-radius: 999px;
  padding: 4px 8px;
  font-size: 10px;
  font-weight: 600;
}
.pv-best {
  background: #bbf7d0;
  color: #166534;
}

.pv-details {
  margin-top: 12px;
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px 14px;
}
.pv-detail {
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.pvd-label {
  font-size: 10px;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: var(--ink-4);
}
.pvd-value {
  font-size: 12px;
  font-weight: 600;
  color: var(--ink);
}
.pv-lead {
  display: inline-flex;
  align-items: center;
  gap: 6px;
}
.pv-dot {
  width: 8px;
  height: 8px;
  border-radius: 999px;
  display: inline-block;
}
.pv-selected-mark {
  margin-top: 12px;
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 11px;
  font-weight: 600;
  color: var(--blue);
}

.pd-action-bar {
  border-top: 1.5px solid var(--border);
  padding: 12px 18px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  flex-shrink: 0;
  background: var(--surface);
}
.pd-action-hint {
  font-size: 11px;
  color: var(--ink-4);
}

.empty-state {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 6px;
  text-align: center;
  padding: 28px;
}
.es-text {
  font-size: 15px;
  font-weight: 600;
  color: var(--ink);
}
.es-sub {
  font-size: 12px;
  color: var(--ink-4);
  max-width: 420px;
  line-height: 1.5;
}

@media (max-width: 960px) {
  .pd-body {
    flex-direction: column;
  }

  .pd-left {
    width: 100%;
    border-right: none;
    border-bottom: 1.5px solid var(--border);
  }

  .pv-details {
    grid-template-columns: 1fr;
  }

  .pd-action-bar {
    flex-direction: column;
    align-items: stretch;
  }
}
</style>
