<template>
  <div v-if="visible" class="mo" @click.self="$emit('close')">
    <div class="mo-box">
      <div class="mo-head">
        <div class="mo-title">Procurement Request</div>
        <button class="mo-x" type="button" @click="$emit('close')">✕</button>
      </div>

      <div class="mo-body">
        <div class="mo-row">
          <div class="fg">
            <label class="fl">Product Name</label>
            <input class="fi fi-readonly" :value="form.partName" readonly />
          </div>
          <div class="fg">
            <label class="fl">Specification</label>
            <input class="fi fi-readonly" :value="form.specification" readonly />
          </div>
        </div>

        <div class="fg">
          <label class="fl">Selected Vendor</label>
          <input class="fi fi-readonly" :value="vendorDisplayName" readonly />
        </div>

        <div class="mo-metrics">
          <div class="mo-metric">
            <div class="mo-metric-label">Current Buy</div>
            <div class="mo-metric-value">{{ currencyLabel(form.currentBuy) }}</div>
            <div class="mo-metric-sub">Price for one part</div>
          </div>
          <div class="mo-metric">
            <div class="mo-metric-label">Unit Measurement Buy</div>
            <div class="mo-metric-value">{{ countLabel(form.unitMeasurementBuy, 'part') }}</div>
            <div class="mo-metric-sub">Parts per vendor unit</div>
          </div>
          <div class="mo-metric">
            <div class="mo-metric-label">Lot Size</div>
            <div class="mo-metric-value">{{ countLabel(form.lotSize, 'unit') }}</div>
            <div class="mo-metric-sub">Minimum vendor units per lot</div>
          </div>
        </div>

        <div class="mo-lots">
          <div>
            <div class="mo-section-label">No. of Lots</div>
            <div class="mo-lots-sub">Increase or decrease the lots to order</div>
          </div>

          <div class="mo-stepper">
            <button
              class="mo-stepper-btn"
              type="button"
              :disabled="safeLotCount <= 1"
              @click="adjustLots(-1)"
            >
              −
            </button>
            <input
              class="fi mo-stepper-input"
              type="number"
              min="1"
              step="1"
              v-model.number="form.lotCount"
              @blur="normalizeLots"
            />
            <button class="mo-stepper-btn" type="button" @click="adjustLots(1)">+</button>
          </div>
        </div>

        <div class="mo-summary">
          <div class="mo-summary-row">
            <span>Total Quantity</span>
            <strong>{{ countLabel(totalQuantity, 'part') }}</strong>
          </div>
          <div class="mo-summary-row">
            <span>Total Cost</span>
            <strong class="mo-total">{{ currencyLabel(totalCost) }}</strong>
          </div>
          <div class="mo-summary-note">
            {{ safeLotCount }} lot{{ safeLotCount !== 1 ? 's' : '' }} ×
            {{ countLabel(form.lotSize, 'unit') }} ×
            {{ countLabel(form.unitMeasurementBuy, 'part') }} ×
            {{ currencyLabel(form.currentBuy) }}
          </div>
        </div>

        <div v-if="!canSubmit" class="mo-warning">
          Procurement pricing is incomplete for this vendor specification.
        </div>
      </div>

      <div class="mo-foot">
        <button class="btn-cancel" type="button" @click="$emit('close')">Cancel</button>
        <button
          class="btn btn-primary"
          type="button"
          :disabled="!canSubmit || submitting"
          @click="submit"
        >
          {{ submitting ? 'Submitting...' : 'Submit Request' }}
        </button>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'ProcurementModal',
  props: {
    visible: { type: Boolean, default: false },
    vendors: { type: Array, default: () => [] },
    prefill: { type: Object, default: null },
    submitting: { type: Boolean, default: false }
  },
  emits: ['close', 'submit'],
  data() {
    return {
      form: this.emptyForm()
    }
  },
  watch: {
    visible(value) {
      if (value) {
        this.resetForm()
      }
    },
    prefill: {
      deep: true,
      handler() {
        if (this.visible) {
          this.resetForm()
        }
      }
    }
  },
  computed: {
    safeLotCount() {
      return Number.isInteger(this.form.lotCount) && this.form.lotCount > 0 ? this.form.lotCount : 1
    },
    vendorDisplayName() {
      if (!this.form.vendorId) return '—'
      return this.form.vendorName
        || this.vendors.find((vendor) => vendor.id === this.form.vendorId)?.name
        || this.form.vendorId
    },
    totalQuantity() {
      if (!this.hasCompletePricing) return null
      return this.safeLotCount * this.form.lotSize * this.form.unitMeasurementBuy
    },
    totalCost() {
      if (this.totalQuantity == null || this.form.currentBuy == null) return null
      return this.totalQuantity * this.form.currentBuy
    },
    hasCompletePricing() {
      return (
        this.form.currentBuy != null
        && this.form.unitMeasurementBuy != null
        && this.form.unitMeasurementBuy > 0
        && this.form.lotSize != null
        && this.form.lotSize > 0
      )
    },
    canSubmit() {
      return Boolean(
        this.form.skuId
        && this.form.vendorId
        && this.safeLotCount > 0
        && this.hasCompletePricing
      )
    }
  },
  methods: {
    emptyForm() {
      return {
        skuId: '',
        partName: '',
        specification: '',
        vendorId: '',
        vendorName: '',
        currentBuy: null,
        unitMeasurementBuy: null,
        lotSize: null,
        lotCount: 1
      }
    },
    resetForm() {
      const next = this.emptyForm()

      if (this.prefill) {
        next.skuId = this.prefill.skuId || ''
        next.partName = this.prefill.partName || ''
        next.specification = this.prefill.specification || ''
        next.vendorId = this.prefill.vendorId || ''
        next.vendorName = this.prefill.vendorName || ''
        next.currentBuy = Number.isFinite(Number(this.prefill.currentBuy)) ? Number(this.prefill.currentBuy) : null
        next.unitMeasurementBuy = Number.isInteger(Number(this.prefill.unitMeasurementBuy))
          ? Number(this.prefill.unitMeasurementBuy)
          : null
        next.lotSize = Number.isInteger(Number(this.prefill.lotSize))
          ? Number(this.prefill.lotSize)
          : null
      }

      this.form = next
    },
    adjustLots(delta) {
      const nextValue = this.safeLotCount + delta
      this.form.lotCount = nextValue < 1 ? 1 : nextValue
    },
    normalizeLots() {
      this.form.lotCount = this.safeLotCount
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
    submit() {
      if (!this.canSubmit || this.submitting) return

      this.$emit('submit', {
        skuId: this.form.skuId,
        vendorId: this.form.vendorId,
        lotCount: this.safeLotCount,
        partName: this.form.partName,
        specification: this.form.specification,
        vendorName: this.vendorDisplayName,
        totalCost: this.totalCost
      })
    }
  }
}
</script>

<style scoped>
.mo {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.45);
  z-index: 200;
  display: flex;
  align-items: center;
  justify-content: center;
  backdrop-filter: blur(2px);
}

.mo-box {
  width: min(640px, calc(100vw - 32px));
  max-height: 88vh;
  overflow-y: auto;
  background: var(--white);
  border: 1.5px solid var(--border);
  border-radius: 12px;
  box-shadow: 0 12px 36px rgba(0, 0, 0, 0.14);
}

.mo-head {
  padding: 18px 20px 14px;
  border-bottom: 1.5px solid var(--border);
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.mo-title {
  font-size: 16px;
  font-weight: 600;
  color: var(--ink);
  letter-spacing: -0.2px;
}

.mo-x {
  width: 28px;
  height: 28px;
  border: 1.5px solid var(--border);
  border-radius: 7px;
  background: none;
  color: var(--ink-3);
  font-size: 12px;
  cursor: pointer;
  transition: all 0.12s;
}

.mo-x:hover {
  background: var(--ink);
  border-color: var(--ink);
  color: #fff;
}

.mo-body {
  padding: 18px 20px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.mo-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 10px;
}

.fi-readonly {
  background: var(--surface) !important;
  color: var(--ink-2) !important;
  cursor: default;
  border-color: var(--border-2) !important;
}

.mo-metrics {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 10px;
}

.mo-metric {
  border: 1.5px solid var(--border);
  border-radius: 10px;
  background: var(--surface);
  padding: 12px;
}

.mo-metric-label {
  font-size: 10px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  color: var(--ink-4);
}

.mo-metric-value {
  margin-top: 6px;
  font-size: 15px;
  font-weight: 600;
  color: var(--ink);
  font-family: 'Geist Mono', monospace;
}

.mo-metric-sub {
  margin-top: 5px;
  font-size: 11px;
  color: var(--ink-4);
  line-height: 1.4;
}

.mo-lots {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  padding: 14px 0 4px;
}

.mo-section-label {
  font-size: 11px;
  font-weight: 600;
  color: var(--ink);
}

.mo-lots-sub {
  margin-top: 3px;
  font-size: 11px;
  color: var(--ink-4);
}

.mo-stepper {
  display: flex;
  align-items: center;
  gap: 6px;
}

.mo-stepper-btn {
  width: 34px;
  height: 34px;
  border: 1.5px solid var(--border);
  border-radius: 8px;
  background: var(--white);
  color: var(--ink);
  font-size: 18px;
  cursor: pointer;
  transition: all 0.12s;
}

.mo-stepper-btn:hover:not(:disabled) {
  border-color: var(--blue);
  color: var(--blue);
}

.mo-stepper-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.mo-stepper-input {
  width: 88px;
  text-align: center;
  font-family: 'Geist Mono', monospace;
  appearance: textfield;
  -moz-appearance: textfield;
}

.mo-stepper-input::-webkit-outer-spin-button,
.mo-stepper-input::-webkit-inner-spin-button {
  -webkit-appearance: none;
  margin: 0;
}

.mo-summary {
  border: 1.5px solid var(--border);
  border-radius: 10px;
  padding: 14px;
  background: var(--white);
}

.mo-summary-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  font-size: 13px;
  color: var(--ink-2);
}

.mo-summary-row + .mo-summary-row {
  margin-top: 8px;
}

.mo-total {
  color: var(--blue);
  font-size: 15px;
  font-family: 'Geist Mono', monospace;
}

.mo-summary-note {
  margin-top: 10px;
  padding-top: 10px;
  border-top: 1px solid var(--border-2);
  font-size: 11px;
  color: var(--ink-4);
  line-height: 1.5;
}

.mo-warning {
  padding: 10px 12px;
  border: 1px solid #fdba74;
  border-radius: 8px;
  background: #fff7ed;
  color: #c2410c;
  font-size: 12px;
}

.mo-foot {
  padding: 12px 20px;
  border-top: 1.5px solid var(--border);
  display: flex;
  justify-content: flex-end;
  gap: 8px;
}

@media (max-width: 720px) {
  .mo-row,
  .mo-metrics {
    grid-template-columns: 1fr;
  }

  .mo-lots {
    flex-direction: column;
    align-items: stretch;
  }

  .mo-stepper {
    justify-content: space-between;
  }
}
</style>
