<template>
  <div v-if="visible" class="mo" @click.self="handleClose">
    <div class="mo-box">
      <div class="mo-head">
        <div>
          <div class="mo-title">{{ modalTitle }}</div>
          <div class="mo-sub">{{ modalSubtitle }}</div>
        </div>
        <button class="mo-x" type="button" @click="handleClose">✕</button>
      </div>

      <div class="mo-steps">
        <div class="mo-step" :class="{ active: step === 1 }">1. Details & Products</div>
        <div class="mo-step" :class="{ active: step === 2 }">2. Specification Pricing</div>
      </div>

      <div class="mo-body">
        <template v-if="step === 1">
          <div class="mo-grid">
            <div class="fg mo-span-2">
              <label class="fl">Vendor Name</label>
              <input
                v-model.trim="form.name"
                class="fi"
                type="text"
                placeholder="e.g. Khedut Engineering Works"
              />
            </div>

            <div class="fg">
              <label class="fl">Prefix</label>
              <div class="mo-prefix">{{ prefixPreview || 'Auto-generated from vendor name' }}</div>
            </div>

            <div class="fg">
              <label class="fl">Lead Time</label>
              <input
                v-model.trim="form.leadTime"
                class="fi"
                type="number"
                min="0"
                step="1"
                placeholder="e.g. 4"
              />
            </div>

            <div class="fg">
              <label class="fl">Phone No</label>
              <input
                v-model.trim="form.phone"
                class="fi"
                type="text"
                inputmode="tel"
                placeholder="e.g. +91 98765 43210"
              />
              <div v-if="phoneError" class="mo-field-error">{{ phoneError }}</div>
            </div>

            <div class="fg">
              <label class="fl">Email Address</label>
              <input
                v-model.trim="form.email"
                class="fi"
                type="email"
                placeholder="e.g. sales@vendor.com"
              />
            </div>

            <div class="fg mo-span-2">
              <label class="fl">Address</label>
              <textarea
                v-model.trim="form.address"
                class="fi mo-textarea"
                rows="2"
                placeholder="Enter the vendor address"
              />
            </div>

          </div>

          <div class="mo-section">
            <div class="mo-section-head">
              <div>
                <div class="mo-section-title">Products Sold</div>
                <div class="mo-section-sub">Select every product this vendor can supply. Selected boxes stay highlighted with a tick.</div>
              </div>
              <div class="mo-selected-count">{{ form.productIds.length }} selected</div>
            </div>

            <div v-if="partsLoading" class="mo-state">
              <div class="es-icon">⌛</div>
              <div class="es-text">Loading product catalog</div>
              <div class="es-sub">Fetching products and specifications</div>
            </div>

            <div v-else-if="!partsCatalog.length" class="mo-state">
              <div class="es-icon">📦</div>
              <div class="es-text">No products available</div>
              <div class="es-sub">The catalog is empty right now.</div>
            </div>

            <div v-else class="mo-parts-grid">
              <button
                v-for="part in partsCatalog"
                :key="part.id"
                class="mo-part-card"
                :class="{ selected: isSelected(part.id) }"
                type="button"
                @click="toggleProduct(part.id)"
              >
                <div class="mo-part-media">
                  <img v-if="part.image" :src="part.image" :alt="part.name" class="mo-part-image" />
                  <div v-else class="mo-part-placeholder">IMG</div>
                </div>
                <div class="mo-part-copy">
                  <div class="mo-part-name">{{ part.name }}</div>
                  <div class="mo-part-meta">
                    {{ part.sizes.length }} specification{{ part.sizes.length === 1 ? '' : 's' }}
                  </div>
                </div>
                <div v-if="isSelected(part.id)" class="mo-part-check">
                  <svg width="12" height="12" viewBox="0 0 12 12" fill="none" stroke="currentColor" stroke-width="2">
                    <polyline points="2,6 5,9 10,3"/>
                  </svg>
                </div>
              </button>
            </div>
          </div>
        </template>

        <template v-else>
          <div class="mo-section-head mo-section-head-tight">
            <div>
              <div class="mo-section-title">Selected Part Pricing</div>
              <div class="mo-section-sub">Leave a price blank for any specification the vendor does not sell.</div>
            </div>
          </div>

          <div v-if="saveError" class="mo-error">{{ saveError }}</div>

          <div v-if="!selectedParts.length" class="mo-state">
            <div class="es-icon">📦</div>
            <div class="es-text">No products selected</div>
            <div class="es-sub">Go back and choose at least one product, or save this vendor without product mappings.</div>
          </div>

          <div v-else class="mo-pricing-list">
            <section
              v-for="part in selectedParts"
              :key="part.id"
              class="mo-pricing-card"
            >
              <div class="mo-pricing-head">
                <div>
                  <div class="mo-pricing-title">{{ part.name }}</div>
                  <div class="mo-pricing-sub">
                    {{ part.sizes.length }} specification{{ part.sizes.length === 1 ? '' : 's' }}
                  </div>
                </div>
              </div>

              <div v-if="!part.sizes.length" class="mo-pricing-empty">
                No specifications are available for this part yet. It will still stay mapped to the vendor.
              </div>

              <div v-else class="mo-pricing-rows">
                <div
                  v-for="size in part.sizes"
                  :key="`${part.id}-${size.key}`"
                  class="mo-pricing-row"
                >
                  <div class="mo-pricing-copy">
                    <div class="mo-pricing-size">{{ size.size }}</div>
                    <div v-if="size.spec" class="mo-pricing-spec">{{ size.spec }}</div>
                  </div>

                  <label class="mo-price-field">
                    <span class="mo-price-currency">₹</span>
                    <input
                      class="fi mo-price-input"
                      type="number"
                      min="0"
                      step="0.01"
                      inputmode="decimal"
                      :value="priceValue(part.id, size.key)"
                      placeholder="Leave blank"
                      @input="setPrice(part.id, size.key, $event.target.value)"
                    />
                  </label>
                </div>
              </div>
            </section>
          </div>
        </template>
      </div>

      <div class="mo-foot">
        <button
          class="btn-cancel"
          type="button"
          :disabled="saving"
          @click="step === 1 ? handleClose() : goBack()"
        >
          {{ step === 1 ? 'Cancel' : 'Back' }}
        </button>

        <button
          v-if="step === 1"
          class="btn btn-primary"
          type="button"
          :disabled="!canContinue"
          @click="goNext"
        >
          Continue to Pricing
        </button>

        <button
          v-else
          class="btn btn-primary"
          type="button"
          :disabled="saving || !canSubmit"
          @click="submit"
        >
          {{ saving ? savingLabel : submitLabel }}
        </button>
      </div>
    </div>
  </div>
</template>

<script>
const buildPrefix = (name = '') => name
  .trim()
  .split(/\s+/)
  .filter(Boolean)
  .map((word) => word[0])
  .join('')
  .toUpperCase()

const phoneDigits = (value = '') => {
  let digits = String(value).replace(/\D/g, '')
  if (digits.length === 12 && digits.startsWith('91')) {
    digits = digits.slice(2)
  }
  return digits
}

const isValidPhoneNumber = (value = '') => {
  const trimmed = String(value).trim()
  if (!trimmed) return true
  return phoneDigits(trimmed).length === 10
}

export default {
  name: 'AddVendorModal',
  props: {
    visible: { type: Boolean, default: false },
    mode: { type: String, default: 'add' },
    partsCatalog: { type: Array, default: () => [] },
    partsLoading: { type: Boolean, default: false },
    initialVendor: { type: Object, default: null },
    saving: { type: Boolean, default: false },
    saveError: { type: String, default: '' }
  },
  emits: ['close', 'save'],
  data() {
    return {
      step: 1,
      form: this.buildFormState()
    }
  },
  watch: {
    visible: {
      immediate: true,
      handler(isVisible) {
        if (isVisible) {
          this.resetState()
        }
      }
    },
    initialVendor() {
      if (this.visible) {
        this.resetState()
      }
    },
    mode() {
      if (this.visible) {
        this.resetState()
      }
    }
  },
  computed: {
    modalTitle() {
      return this.mode === 'edit' ? 'Edit Vendor' : 'Add Vendor'
    },
    modalSubtitle() {
      if (this.step === 1) {
        return this.mode === 'edit'
          ? 'Update the vendor details and product mapping'
          : 'Capture vendor details and choose their products'
      }
      return 'Enter specification-wise buy prices for the selected products'
    },
    prefixPreview() {
      return buildPrefix(this.form.name)
    },
    phoneError() {
      return isValidPhoneNumber(this.form.phone)
        ? ''
        : 'Phone number must be 10 digits. +91 in front is okay.'
    },
    canContinue() {
      return Boolean(this.form.name.trim()) && !this.phoneError
    },
    canSubmit() {
      return Boolean(this.form.name.trim()) && !this.phoneError
    },
    submitLabel() {
      return this.mode === 'edit' ? 'Update Vendor' : 'Save Vendor'
    },
    savingLabel() {
      return this.mode === 'edit' ? 'Updating Vendor...' : 'Saving Vendor...'
    },
    selectedParts() {
      const fallbackProducts = new Map(
        (this.initialVendor?.products || []).map((product) => [
          String(product.id),
          { id: String(product.id), name: product.name || 'Unknown Part', image: null, sizes: [] }
        ])
      )

      return this.form.productIds.map((productId) =>
        this.partsCatalog.find((part) => part.id === productId)
        || fallbackProducts.get(productId)
        || { id: productId, name: 'Unknown Part', image: null, sizes: [] }
      )
    }
  },
  methods: {
    buildFormState() {
      const vendor = this.initialVendor || {}
      const selectedFromProducts = Array.isArray(vendor.products)
        ? vendor.products.map((product) => String(product.id)).filter(Boolean)
        : []
      const selectedFromPrices = Array.isArray(vendor.priceEntries)
        ? vendor.priceEntries.map((entry) => String(entry.productId)).filter(Boolean)
        : []
      const productIds = [...new Set([...selectedFromProducts, ...selectedFromPrices])]
      const prices = {}

      for (const entry of vendor.priceEntries || []) {
        const mapKey = this.priceMapKey(entry.productId, entry.key)
        prices[mapKey] = entry.price == null ? '' : String(entry.price)
      }

      return {
        name: vendor.name || '',
        phone: vendor.contact?.phone && vendor.contact.phone !== '—' ? vendor.contact.phone : '',
        email: vendor.contact?.email && vendor.contact.email !== '—' ? vendor.contact.email : '',
        address: vendor.location && vendor.location !== '—' ? vendor.location : '',
        leadTime: vendor.leadTime == null ? '' : String(vendor.leadTime),
        productIds,
        prices
      }
    },
    resetState() {
      this.step = 1
      this.form = this.buildFormState()
    },
    handleClose() {
      if (this.saving) return
      this.$emit('close')
    },
    goNext() {
      if (!this.canContinue) return
      this.step = 2
    },
    goBack() {
      if (this.saving) return
      this.step = 1
    },
    isSelected(productId) {
      return this.form.productIds.includes(String(productId))
    },
    toggleProduct(productId) {
      const normalizedId = String(productId)
      if (this.isSelected(normalizedId)) {
        this.form.productIds = this.form.productIds.filter((id) => id !== normalizedId)
        return
      }
      this.form.productIds = [...this.form.productIds, normalizedId]
    },
    priceMapKey(productId, sizeKey) {
      return `${String(productId)}::${String(sizeKey)}`
    },
    priceValue(productId, sizeKey) {
      return this.form.prices[this.priceMapKey(productId, sizeKey)] || ''
    },
    setPrice(productId, sizeKey, value) {
      this.form.prices = {
        ...this.form.prices,
        [this.priceMapKey(productId, sizeKey)]: value
      }
    },
    submit() {
      const prices = []

      for (const part of this.selectedParts) {
        for (const size of part.sizes || []) {
          prices.push({
            productId: part.id,
            key: size.key,
            specs: size.specs || {},
            price: this.priceValue(part.id, size.key)
          })
        }
      }

      this.$emit('save', {
        name: this.form.name.trim(),
        phone: this.form.phone.trim(),
        email: this.form.email.trim(),
        address: this.form.address.trim(),
        leadTime: this.form.leadTime === '' ? null : Number(this.form.leadTime),
        productIds: [...this.form.productIds],
        prices
      })
    }
  }
}
</script>

<style scoped>
.mo {
  position: fixed;
  inset: 0;
  background: rgba(15, 23, 42, 0.45);
  z-index: 200;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 18px;
  backdrop-filter: blur(4px);
}

.mo-box {
  width: min(1080px, 100%);
  max-height: calc(100vh - 36px);
  display: flex;
  flex-direction: column;
  background: var(--white);
  border: 1.5px solid var(--border);
  border-radius: 14px;
  box-shadow: 0 18px 44px rgba(15, 23, 42, 0.18);
  overflow: hidden;
}

.mo-head {
  padding: 18px 22px 14px;
  border-bottom: 1.5px solid var(--border);
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
}

.mo-title {
  font-size: 18px;
  font-weight: 600;
  color: var(--ink);
  letter-spacing: -0.3px;
}

.mo-sub {
  margin-top: 4px;
  font-size: 12px;
  color: var(--ink-4);
}

.mo-x {
  width: 32px;
  height: 32px;
  border: 1.5px solid var(--border);
  border-radius: 8px;
  background: var(--white);
  color: var(--ink-4);
  cursor: pointer;
  transition: all 0.12s;
}

.mo-x:hover {
  border-color: var(--ink-3);
  color: var(--ink);
}

.mo-steps {
  display: flex;
  gap: 8px;
  padding: 12px 22px;
  border-bottom: 1.5px solid var(--border);
  background: var(--surface);
}

.mo-step {
  padding: 7px 10px;
  border-radius: 999px;
  border: 1px solid var(--border);
  color: var(--ink-4);
  font-size: 11px;
  font-weight: 600;
  letter-spacing: 0.2px;
}

.mo-step.active {
  background: var(--blue-dim);
  border-color: var(--blue);
  color: var(--blue);
}

.mo-body {
  flex: 1;
  overflow-y: auto;
  padding: 22px;
  display: flex;
  flex-direction: column;
  gap: 22px;
  background: linear-gradient(180deg, #ffffff 0%, #f8fafc 100%);
}

.mo-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 14px;
}

.mo-span-2 {
  grid-column: 1 / -1;
}

.mo-prefix {
  min-height: 42px;
  display: flex;
  align-items: center;
  padding: 0 12px;
  border: 1.5px dashed var(--border-2);
  border-radius: 9px;
  background: var(--surface);
  color: var(--ink-3);
  font-size: 12px;
  font-weight: 600;
  letter-spacing: 0.6px;
  text-transform: uppercase;
}

.mo-field-error {
  margin-top: 6px;
  font-size: 11px;
  color: #dc2626;
}

.mo-textarea {
  min-height: 76px;
  resize: vertical;
  padding-top: 10px;
}

.mo-section {
  background: var(--white);
  border: 1.5px solid var(--border);
  border-radius: 12px;
  padding: 18px;
}

.mo-section-head,
.mo-section-head-tight {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 14px;
}

.mo-section-head-tight {
  margin-bottom: 0;
}

.mo-section-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--ink);
}

.mo-section-sub {
  margin-top: 4px;
  font-size: 11.5px;
  color: var(--ink-4);
  line-height: 1.4;
}

.mo-selected-count {
  flex-shrink: 0;
  padding: 6px 10px;
  border-radius: 999px;
  background: var(--blue-dim);
  color: var(--blue);
  font-size: 11px;
  font-weight: 600;
}

.mo-state {
  padding: 26px 12px 10px;
}

.mo-parts-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(170px, 1fr));
  gap: 12px;
}

.mo-part-card {
  position: relative;
  text-align: left;
  border: 1.5px solid var(--border);
  border-radius: 12px;
  background: var(--white);
  padding: 14px;
  display: flex;
  flex-direction: column;
  gap: 12px;
  cursor: pointer;
  transition: all 0.14s;
}

.mo-part-card:hover {
  transform: translateY(-1px);
  border-color: var(--blue);
  box-shadow: 0 10px 18px rgba(59, 130, 246, 0.08);
}

.mo-part-card.selected {
  border-color: var(--blue);
  background: linear-gradient(180deg, #eff6ff 0%, #ffffff 100%);
}

.mo-part-media {
  width: 100%;
  aspect-ratio: 1.25;
  border-radius: 10px;
  background: var(--surface);
  border: 1px solid var(--border);
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
}

.mo-part-image {
  width: 100%;
  height: 100%;
  object-fit: contain;
}

.mo-part-placeholder {
  font-size: 12px;
  font-weight: 700;
  color: var(--ink-4);
  letter-spacing: 1px;
}

.mo-part-copy {
  min-width: 0;
}

.mo-part-name {
  font-size: 12.5px;
  font-weight: 600;
  color: var(--ink);
  line-height: 1.35;
}

.mo-part-meta {
  margin-top: 4px;
  font-size: 10.5px;
  color: var(--ink-4);
}

.mo-part-check {
  position: absolute;
  top: 10px;
  right: 10px;
  width: 24px;
  height: 24px;
  border-radius: 999px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--blue);
  color: #fff;
}

.mo-error {
  margin-top: 14px;
  padding: 12px 14px;
  border: 1.5px solid #fca5a5;
  background: #fee2e2;
  border-radius: 8px;
  color: #b91c1c;
  font-size: 12px;
}

.mo-pricing-list {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.mo-pricing-card {
  background: var(--white);
  border: 1.5px solid var(--border);
  border-radius: 12px;
  overflow: hidden;
}

.mo-pricing-head {
  padding: 14px 16px;
  border-bottom: 1.5px solid var(--border-2);
  background: var(--surface);
}

.mo-pricing-title {
  font-size: 13.5px;
  font-weight: 600;
  color: var(--ink);
}

.mo-pricing-sub {
  margin-top: 3px;
  font-size: 11px;
  color: var(--ink-4);
}

.mo-pricing-empty {
  padding: 14px 16px;
  color: var(--ink-4);
  font-size: 12px;
}

.mo-pricing-rows {
  display: flex;
  flex-direction: column;
}

.mo-pricing-row {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 230px;
  gap: 14px;
  align-items: center;
  padding: 14px 16px;
  border-top: 1px solid var(--border-2);
}

.mo-pricing-row:first-child {
  border-top: none;
}

.mo-pricing-size {
  font-size: 13px;
  font-weight: 600;
  color: var(--ink);
  font-family: 'Geist Mono', monospace;
}

.mo-pricing-spec {
  margin-top: 4px;
  font-size: 11px;
  color: var(--ink-4);
  line-height: 1.4;
}

.mo-price-field {
  display: flex;
  align-items: center;
  border: 1.5px solid var(--border);
  border-radius: 10px;
  background: var(--white);
  overflow: hidden;
}

.mo-price-currency {
  padding: 0 12px;
  color: var(--ink-4);
  font-size: 12px;
  font-weight: 600;
  border-right: 1px solid var(--border-2);
  height: 100%;
  display: inline-flex;
  align-items: center;
}

.mo-price-input {
  border: none;
  min-height: 42px;
  box-shadow: none;
}

.mo-foot {
  padding: 14px 22px;
  border-top: 1.5px solid var(--border);
  background: var(--white);
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 10px;
}

@media (max-width: 900px) {
  .mo {
    padding: 10px;
  }

  .mo-grid {
    grid-template-columns: 1fr;
  }

  .mo-span-2 {
    grid-column: auto;
  }

  .mo-pricing-row {
    grid-template-columns: 1fr;
  }

  .mo-price-field {
    width: 100%;
  }
}
</style>
