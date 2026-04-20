<template>
  <div v-if="visible" class="mo" @click.self="handleClose">
    <div class="mo-box">
      <div class="mo-head">
        <div>
          <div class="mo-title">{{ modalTitle }}</div>
          <div class="mo-sub">{{ modalSubtitle }}</div>
        </div>
        <button class="mo-x" type="button" :disabled="saving" @click="handleClose">✕</button>
      </div>

      <div class="mo-steps">
        <div class="mo-step" :class="{ active: step === 1 }">1. Details & Vendors</div>
        <div class="mo-step" :class="{ active: step === 2 }">2. Stock & Sell Price</div>
        <div class="mo-step" :class="{ active: step === 3 }">3. Vendor Buy Prices</div>
      </div>

      <div class="mo-body">
        <template v-if="step === 1">
          <div class="mo-grid">
            <div class="fg mo-span-2">
              <label class="fl">Product Name</label>
              <input
                v-model.trim="form.name"
                class="fi"
                type="text"
                placeholder="e.g. SS Step Nipple"
              />
            </div>

            <div class="fg">
              <label class="fl">Category</label>
              <input
                v-model.trim="form.category"
                class="fi"
                type="text"
                list="inventory-part-categories"
                placeholder="e.g. Pipe Fittings"
              />
              <datalist id="inventory-part-categories">
                <option v-for="category in categories" :key="category" :value="category"></option>
              </datalist>
            </div>

            <div class="fg">
              <label class="fl">Product Image</label>
              <label class="mo-upload">
                <input
                  ref="imageInput"
                  class="mo-upload-input"
                  type="file"
                  accept=".png,.jpg,.jpeg,.webp,.avif"
                  @change="handleImageChange"
                />
                <span class="mo-upload-label">{{ form.imageFile ? 'Change image' : 'Choose image' }}</span>
                <span class="mo-upload-sub">{{ imageLabel }}</span>
              </label>
            </div>

            <div class="fg">
              <label class="fl">Unit Measurement Buy</label>
              <input
                v-model.trim="form.unitMeasurementBuy"
                class="fi"
                type="number"
                min="1"
                step="1"
                placeholder="e.g. 1"
              />
            </div>

            <div class="fg">
              <label class="fl">Lot Size Buy</label>
              <input
                v-model.trim="form.lotSizeBuy"
                class="fi"
                type="number"
                min="1"
                step="1"
                placeholder="e.g. 1"
              />
            </div>
          </div>

          <div class="mo-section">
            <div class="mo-section-head">
              <div>
                <div class="mo-section-title">Specifications</div>
                <div class="mo-section-sub">Add every spec or variant for this product. Each one will become a SKU template.</div>
              </div>
              <button class="mo-inline-btn" type="button" @click="addSpec">+ Add Spec</button>
            </div>

            <div class="mo-spec-list">
              <div v-for="(spec, index) in form.specs" :key="spec.id" class="mo-spec-card">
                <div class="mo-spec-index">Spec {{ index + 1 }}</div>
                <div v-if="spec.isExisting" class="mo-spec-label">{{ spec.label }}</div>
                <input
                  v-else
                  v-model.trim="spec.label"
                  class="fi"
                  type="text"
                  placeholder='e.g. 1" x 0.75" x 7"'
                />
                <button
                  v-if="form.specs.length > 1"
                  class="mo-remove-btn"
                  type="button"
                  @click="removeSpec(spec.id)"
                >
                  Remove
                </button>
              </div>
            </div>
          </div>

          <div class="mo-section">
            <div class="mo-section-head">
              <div>
                <div class="mo-section-title">Vendors</div>
                <div class="mo-section-sub">Select the vendors that sell this product. Each vendor will get its own row for every specification you add.</div>
              </div>
              <div class="mo-selected-count">{{ form.vendorIds.length }} selected</div>
            </div>

            <div v-if="vendorsLoading" class="mo-state">
              <div class="es-icon">⌛</div>
              <div class="es-text">Loading vendors</div>
              <div class="es-sub">Fetching the active vendor list</div>
            </div>

            <div v-else-if="!vendors.length" class="mo-state">
              <div class="es-icon">🏪</div>
              <div class="es-text">No vendors available</div>
              <div class="es-sub">Add at least one vendor before creating a new part.</div>
            </div>

            <div v-else class="mo-vendor-grid">
              <button
                v-for="vendor in vendors"
                :key="vendor.id"
                class="mo-vendor-card"
                :class="{ selected: isVendorSelected(vendor.id) }"
                type="button"
                @click="toggleVendor(vendor.id)"
              >
                <div class="mo-vendor-copy">
                  <div class="mo-vendor-name">{{ vendor.name }}</div>
                  <div class="mo-vendor-meta">
                    <span>{{ vendor.location || '—' }}</span>
                    <span v-if="vendor.leadTime != null">· {{ vendor.leadTime }}d</span>
                  </div>
                </div>
                <div class="mo-vendor-markers">
                  <span v-if="isVendorSelected(vendor.id)" class="mo-check">
                    <svg width="12" height="12" viewBox="0 0 12 12" fill="none" stroke="currentColor" stroke-width="2">
                      <polyline points="2,6 5,9 10,3"/>
                    </svg>
                  </span>
                </div>
              </button>
            </div>
          </div>

          <div v-if="form.imagePreview" class="mo-preview">
            <div class="mo-preview-label">Image Preview</div>
            <img :src="form.imagePreview" :alt="form.name || 'Product preview'" class="mo-preview-image" />
          </div>
        </template>

        <template v-else-if="step === 2">
          <div class="mo-section-head mo-section-head-tight">
            <div>
              <div class="mo-section-title">Stock, Threshold, and Sell Price</div>
              <div class="mo-section-sub">Sell price is included here because the order and customer flows already depend on it.</div>
            </div>
          </div>

          <div class="mo-pricing-list">
            <section v-for="spec in form.specs" :key="spec.id" class="mo-pricing-card">
              <div class="mo-pricing-head">
                <div class="mo-pricing-title">{{ spec.label || 'Unnamed specification' }}</div>
              </div>

              <div class="mo-stock-grid">
                <div class="fg">
                  <label class="fl">Current Stock Quantity</label>
                  <input
                    v-model.trim="spec.stockQty"
                    class="fi"
                    type="number"
                    min="0"
                    step="1"
                    placeholder="0"
                  />
                </div>

                <div class="fg">
                  <label class="fl">Threshold</label>
                  <input
                    v-model.trim="spec.threshold"
                    class="fi"
                    type="number"
                    min="0"
                    step="1"
                    placeholder="0"
                  />
                </div>

                <div class="fg">
                  <label class="fl">Sell Price (₹)</label>
                  <input
                    v-model.trim="spec.sellPrice"
                    class="fi"
                    type="number"
                    min="0"
                    step="0.01"
                    placeholder="0.00"
                  />
                </div>
              </div>
            </section>
          </div>
        </template>

        <template v-else>
          <div class="mo-section-head mo-section-head-tight">
            <div>
              <div class="mo-section-title">Vendor-wise Unit Buy Prices</div>
              <div class="mo-section-sub">Enter the unit buy price each selected vendor charges for every specification.</div>
            </div>
          </div>

          <div v-if="saveError" class="mo-error">{{ saveError }}</div>

          <div class="mo-pricing-list">
            <section v-for="vendor in selectedVendors" :key="vendor.id" class="mo-pricing-card">
              <div class="mo-pricing-head">
                <div>
                  <div class="mo-pricing-title">{{ vendor.name }}</div>
                  <div class="mo-pricing-sub">{{ vendor.location || '—' }}</div>
                </div>
              </div>

              <div class="mo-pricing-rows">
                <div v-for="spec in form.specs" :key="`${vendor.id}-${spec.id}`" class="mo-pricing-row">
                  <div class="mo-pricing-copy">
                    <div class="mo-pricing-size">{{ spec.label || 'Unnamed specification' }}</div>
                  </div>

                  <label class="mo-price-field">
                    <span class="mo-price-currency">₹</span>
                    <input
                      class="fi mo-price-input"
                      type="number"
                      min="0"
                      step="0.01"
                      inputmode="decimal"
                      :value="spec.vendorPrices[String(vendor.id)] || ''"
                      placeholder="0.00"
                      @input="setVendorPrice(spec.id, vendor.id, $event.target.value)"
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
          v-if="step !== 3"
          class="btn btn-primary"
          type="button"
          :disabled="step === 1 ? !canContinueStepOne : !canContinueStepTwo"
          @click="goNext"
        >
          {{ step === 1 ? 'Continue to Stock' : 'Continue to Vendor Prices' }}
        </button>

        <button
          v-else
          class="btn btn-primary"
          :class="{ 'btn-primary-loading': saving }"
          type="button"
          :disabled="saving || !canSubmitAction"
          @click="submit"
        >
          {{ saving ? savingLabel : submitLabel }}
        </button>
      </div>
    </div>
  </div>
</template>

<script>
const buildSpec = (id, vendorIds = [], overrides = {}) => ({
  id,
  label: '',
  stockQty: '',
  threshold: '',
  sellPrice: '',
  isExisting: false,
  vendorPrices: Object.fromEntries(vendorIds.map((vendorId) => [String(vendorId), ''])),
  ...overrides
})

const normalizeVendorPrices = (vendorPrices = {}, vendorIds = []) => Object.fromEntries(
  [...vendorIds]
    .map((vendorId) => String(vendorId))
    .sort((left, right) => left.localeCompare(right))
    .map((vendorId) => [vendorId, String(vendorPrices?.[vendorId] ?? '')])
)

const snapshotForm = (form = {}) => JSON.stringify({
  id: String(form.id ?? ''),
  name: String(form.name ?? '').trim(),
  category: String(form.category ?? '').trim(),
  unitMeasurementBuy: String(form.unitMeasurementBuy ?? ''),
  lotSizeBuy: String(form.lotSizeBuy ?? ''),
  vendorIds: [...(form.vendorIds || [])]
    .map((vendorId) => String(vendorId))
    .sort((left, right) => left.localeCompare(right)),
  specs: (form.specs || []).map((spec) => ({
    label: String(spec.label ?? '').trim(),
    stockQty: String(spec.stockQty ?? ''),
    threshold: String(spec.threshold ?? ''),
    sellPrice: String(spec.sellPrice ?? ''),
    isExisting: Boolean(spec.isExisting),
    vendorPrices: normalizeVendorPrices(spec.vendorPrices, form.vendorIds || [])
  })),
  hasNewImage: Boolean(form.imageFile)
})

export default {
  name: 'AddPartModal',
  props: {
    visible: { type: Boolean, default: false },
    mode: { type: String, default: 'add' },
    initialData: { type: Object, default: null },
    categories: { type: Array, default: () => [] },
    vendors: { type: Array, default: () => [] },
    vendorsLoading: { type: Boolean, default: false },
    saving: { type: Boolean, default: false },
    saveError: { type: String, default: '' }
  },
  emits: ['close', 'save'],
  data() {
    return {
      step: 1,
      nextSpecId: 2,
      initialSnapshot: '',
      form: this.createFormState()
    }
  },
  computed: {
    isEditMode() {
      return this.mode === 'edit'
    },
    modalTitle() {
      return this.isEditMode ? 'Edit Part' : 'Add Part'
    },
    modalSubtitle() {
      if (this.step === 1) {
        return this.isEditMode
          ? 'Update the product details, variants, and vendor mapping'
          : 'Capture the product details, variants, and vendor mapping'
      }
      if (this.step === 2) {
        return this.isEditMode
          ? 'Update stock, threshold, and sell price for each specification'
          : 'Set stock, threshold, and sell price for each specification'
      }
      return this.isEditMode
        ? 'Update vendor-wise buy prices for every specification'
        : 'Set vendor-wise buy prices for every specification'
    },
    imageLabel() {
      return this.form.imageFile?.name || 'PNG, JPG, JPEG, WEBP, or AVIF'
    },
    selectedVendors() {
      return this.form.vendorIds
        .map((vendorId) => this.vendors.find((vendor) => String(vendor.id) === String(vendorId)))
        .filter(Boolean)
    },
    canContinueStepOne() {
      return Boolean(
        this.form.name.trim()
        && this.form.category.trim()
        && this.form.vendorIds.length
        && this.form.specs.every((spec) => spec.label.trim())
        && Number(this.form.unitMeasurementBuy) >= 1
        && Number(this.form.lotSizeBuy) >= 1
      )
    },
    canContinueStepTwo() {
      return this.form.specs.every((spec) =>
        spec.label.trim()
        && spec.stockQty !== ''
        && spec.threshold !== ''
        && spec.sellPrice !== ''
      )
    },
    canSubmit() {
      if (this.selectedVendors.length === 0) return false
      if (this.isEditMode) {
        return this.form.specs.every((spec) =>
          this.form.vendorIds.some((vendorId) => spec.vendorPrices[String(vendorId)] !== '')
        )
      }
      return this.form.specs.every((spec) =>
        this.form.vendorIds.every((vendorId) => spec.vendorPrices[String(vendorId)] !== '')
      )
    },
    hasChanges() {
      if (!this.isEditMode) return true
      return snapshotForm(this.form) !== this.initialSnapshot
    },
    canSubmitAction() {
      return this.canSubmit && (!this.isEditMode || this.hasChanges)
    },
    submitLabel() {
      return this.isEditMode ? 'Update Part' : 'Add Part'
    },
    savingLabel() {
      return this.isEditMode ? 'Updating Part....' : 'Adding Part....'
    }
  },
  watch: {
    visible: {
      immediate: true,
      handler(isVisible) {
        if (isVisible) {
          this.resetState(this.initialData)
        }
      }
    },
    initialData(nextValue) {
      if (this.visible) {
        this.resetState(nextValue)
      }
    },
    vendors() {
      if (this.visible) {
        this.syncVendors()
      }
    }
  },
  beforeUnmount() {
    this.revokePreview()
  },
  methods: {
    createFormState() {
      return {
        id: '',
        name: '',
        category: '',
        imageFile: null,
        imagePreview: '',
        unitMeasurementBuy: '1',
        lotSizeBuy: '1',
        vendorIds: [],
        specs: [buildSpec(1)]
      }
    },
    createFormStateFromInitial(initialData) {
      if (!initialData) {
        return this.createFormState()
      }

      const vendorIds = Array.isArray(initialData.vendorIds)
        ? initialData.vendorIds.map((vendorId) => String(vendorId))
        : []
      const specs = Array.isArray(initialData.specs) && initialData.specs.length
        ? initialData.specs.map((spec, index) => buildSpec(index + 1, vendorIds, {
          label: spec.label || '',
          stockQty: String(spec.stockQty ?? ''),
          threshold: String(spec.threshold ?? ''),
          sellPrice: String(spec.sellPrice ?? ''),
          isExisting: Boolean(spec.isExisting),
          vendorPrices: Object.fromEntries(
            vendorIds.map((vendorId) => {
              const vendorPrice = Array.isArray(spec.vendorPrices)
                ? spec.vendorPrices.find((price) => String(price.vendorId) === vendorId)
                : null
              const priceValue = vendorPrice?.unitBuyPrice
              return [vendorId, priceValue == null ? '' : String(priceValue)]
            })
          )
        }))
        : [buildSpec(1, vendorIds)]

      return {
        id: String(initialData.id ?? ''),
        name: initialData.name || '',
        category: initialData.category || '',
        imageFile: null,
        imagePreview: initialData.image || '',
        unitMeasurementBuy: String(initialData.unitMeasurementBuy ?? '1'),
        lotSizeBuy: String(initialData.lotSizeBuy ?? '1'),
        vendorIds,
        specs
      }
    },
    revokePreview() {
      if (this.form.imagePreview && this.form.imagePreview.startsWith('blob:')) {
        URL.revokeObjectURL(this.form.imagePreview)
      }
    },
    resetState(initialData = null) {
      this.revokePreview()
      this.step = 1
      this.form = this.createFormStateFromInitial(initialData)
      this.nextSpecId = this.form.specs.length + 1
      this.initialSnapshot = snapshotForm(this.form)
    },
    handleClose() {
      if (this.saving) return
      this.$emit('close')
    },
    goNext() {
      if (this.step === 1 && !this.canContinueStepOne) return
      if (this.step === 2 && !this.canContinueStepTwo) return
      this.step += 1
    },
    goBack() {
      if (this.saving || this.step === 1) return
      this.step -= 1
    },
    addSpec() {
      this.form.specs = [...this.form.specs, buildSpec(this.nextSpecId, this.form.vendorIds)]
      this.nextSpecId += 1
    },
    removeSpec(specId) {
      if (this.form.specs.length === 1) return
      this.form.specs = this.form.specs.filter((spec) => spec.id !== specId)
    },
    handleImageChange(event) {
      const file = event.target?.files?.[0]
      this.revokePreview()
      if (!file) {
        this.form.imageFile = null
        this.form.imagePreview = ''
        return
      }
      this.form.imageFile = file
      this.form.imagePreview = URL.createObjectURL(file)
    },
    isVendorSelected(vendorId) {
      return this.form.vendorIds.includes(String(vendorId))
    },
    toggleVendor(vendorId) {
      const normalizedId = String(vendorId)
      if (this.isVendorSelected(normalizedId)) {
        this.form.vendorIds = this.form.vendorIds.filter((id) => id !== normalizedId)
      } else {
        this.form.vendorIds = [...this.form.vendorIds, normalizedId]
      }
      this.syncVendors()
    },
    syncVendors() {
      const availableVendorIds = new Set(this.vendors.map((vendor) => String(vendor.id)))
      this.form.vendorIds = this.form.vendorIds.filter((vendorId) => availableVendorIds.has(vendorId))
      this.form.specs = this.form.specs.map((spec) => ({
        ...spec,
        vendorPrices: Object.fromEntries(
          this.form.vendorIds.map((vendorId) => [vendorId, spec.vendorPrices[vendorId] || ''])
        )
      }))
    },
    setVendorPrice(specId, vendorId, value) {
      this.form.specs = this.form.specs.map((spec) =>
        spec.id === specId
          ? {
            ...spec,
            vendorPrices: {
              ...spec.vendorPrices,
              [String(vendorId)]: value
            }
          }
          : spec
      )
    },
    submit() {
      if (!this.canSubmitAction) return
      this.$emit('save', {
        id: this.form.id,
        name: this.form.name.trim(),
        category: this.form.category.trim(),
        imageFile: this.form.imageFile,
        unitMeasurementBuy: this.form.unitMeasurementBuy,
        lotSizeBuy: this.form.lotSizeBuy,
        vendorIds: [...this.form.vendorIds],
        specs: this.form.specs.map((spec) => ({
          label: spec.label.trim(),
          stockQty: spec.stockQty,
          threshold: spec.threshold,
          sellPrice: spec.sellPrice,
          isExisting: Boolean(spec.isExisting),
          vendorPrices: { ...spec.vendorPrices }
        }))
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
  width: min(1100px, 100%);
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

.mo-x:hover:not(:disabled) {
  border-color: var(--ink-3);
  color: var(--ink);
}

.mo-x:disabled {
  opacity: 0.55;
  cursor: not-allowed;
}

.mo-steps {
  display: flex;
  gap: 8px;
  padding: 12px 22px;
  border-bottom: 1.5px solid var(--border);
  background: var(--surface);
  flex-wrap: wrap;
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

.fg {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.fl {
  font-size: 11.5px;
  font-weight: 600;
  color: var(--ink-3);
}

.fi {
  width: 100%;
  box-sizing: border-box;
  min-height: 42px;
  padding: 10px 12px;
  border: 1.5px solid var(--border);
  border-radius: 10px;
  background: var(--white);
  color: var(--ink);
  font-size: 12.5px;
  font-family: 'Geist', sans-serif;
  outline: none;
}

.fi:focus {
  border-color: var(--blue);
  box-shadow: 0 0 0 2px rgba(37, 99, 235, 0.08);
}

.mo-upload {
  min-height: 42px;
  border: 1.5px dashed var(--border-2);
  border-radius: 10px;
  background: var(--white);
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  padding: 10px 12px;
  cursor: pointer;
}

.mo-upload-input {
  display: none;
}

.mo-upload-label {
  font-size: 12px;
  font-weight: 600;
  color: var(--blue);
}

.mo-upload-sub {
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-size: 11px;
  color: var(--ink-4);
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

.mo-inline-btn {
  border: 1.5px solid var(--border);
  border-radius: 9px;
  background: var(--white);
  color: var(--blue);
  font-size: 12px;
  font-weight: 600;
  padding: 8px 12px;
  cursor: pointer;
  white-space: nowrap;
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

.mo-spec-list,
.mo-pricing-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.mo-spec-card,
.mo-pricing-card {
  border: 1.5px solid var(--border);
  border-radius: 12px;
  background: var(--white);
  overflow: hidden;
}

.mo-spec-card {
  padding: 14px;
  display: grid;
  grid-template-columns: 82px minmax(0, 1fr) auto;
  gap: 12px;
  align-items: center;
}

.mo-spec-index {
  font-size: 11px;
  font-weight: 700;
  color: var(--ink-4);
  text-transform: uppercase;
  letter-spacing: 0.4px;
}

.mo-spec-label {
  min-height: 42px;
  padding: 10px 12px;
  border: 1.5px solid var(--border);
  border-radius: 10px;
  background: var(--surface);
  color: var(--ink);
  font-size: 12.5px;
  font-family: 'Geist Mono', monospace;
  display: flex;
  align-items: center;
}

.mo-remove-btn {
  border: 1.5px solid #fecaca;
  border-radius: 9px;
  background: #fff1f2;
  color: #b91c1c;
  font-size: 12px;
  font-weight: 600;
  padding: 9px 12px;
  cursor: pointer;
}

.mo-state {
  padding: 26px 12px 10px;
}

.mo-vendor-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
  gap: 12px;
}

.mo-vendor-card {
  position: relative;
  text-align: left;
  border: 1.5px solid var(--border);
  border-radius: 12px;
  background: var(--white);
  padding: 14px;
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
  cursor: pointer;
  transition: all 0.14s;
}

.mo-vendor-card:hover {
  transform: translateY(-1px);
  border-color: var(--blue);
  box-shadow: 0 10px 18px rgba(59, 130, 246, 0.08);
}

.mo-vendor-card.selected {
  border-color: var(--blue);
  background: linear-gradient(180deg, #eff6ff 0%, #ffffff 100%);
}

.mo-vendor-name {
  font-size: 12.5px;
  font-weight: 600;
  color: var(--ink);
}

.mo-vendor-meta {
  margin-top: 4px;
  font-size: 10.5px;
  color: var(--ink-4);
}

.mo-vendor-markers {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 8px;
}

.mo-check {
  width: 24px;
  height: 24px;
  border-radius: 999px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--blue);
  color: #fff;
}

.mo-preview {
  align-self: flex-start;
  background: var(--white);
  border: 1.5px solid var(--border);
  border-radius: 14px;
  padding: 14px;
}

.mo-preview-label {
  font-size: 11px;
  font-weight: 700;
  color: var(--ink-4);
  text-transform: uppercase;
  letter-spacing: 0.5px;
  margin-bottom: 10px;
}

.mo-preview-image {
  width: 180px;
  height: 180px;
  object-fit: contain;
  display: block;
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

.mo-stock-grid {
  padding: 16px;
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 14px;
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

.mo-pricing-copy {
  min-width: 0;
}

.mo-pricing-size {
  font-size: 13px;
  font-weight: 600;
  color: var(--ink);
  font-family: 'Geist Mono', monospace;
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

.mo-error {
  padding: 12px 14px;
  border: 1.5px solid #fca5a5;
  background: #fee2e2;
  border-radius: 8px;
  color: #b91c1c;
  font-size: 12px;
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

.btn,
.btn-cancel {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  border-radius: 9px;
  padding: 9px 14px;
  font-size: 12.5px;
  font-weight: 600;
  font-family: 'Geist', sans-serif;
  cursor: pointer;
  transition: all 0.12s;
}

.btn {
  border: none;
}

.btn-primary {
  background: var(--blue);
  color: #fff;
}

.btn-primary:hover:not(:disabled) {
  background: #1d4ed8;
}

.btn-primary-loading,
.btn-primary:disabled {
  background: #93c5fd;
  color: #eff6ff;
}

.btn-cancel {
  border: 1.5px solid var(--border);
  background: transparent;
  color: var(--ink-3);
}

.btn-cancel:hover:not(:disabled) {
  border-color: var(--ink-3);
  color: var(--ink);
}

.btn-primary:disabled,
.btn-cancel:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

@media (max-width: 900px) {
  .mo {
    padding: 10px;
  }

  .mo-grid,
  .mo-stock-grid {
    grid-template-columns: 1fr;
  }

  .mo-span-2 {
    grid-column: auto;
  }

  .mo-spec-card {
    grid-template-columns: 1fr;
  }

  .mo-pricing-row {
    grid-template-columns: 1fr;
  }

  .mo-price-field {
    width: 100%;
  }
}
</style>
