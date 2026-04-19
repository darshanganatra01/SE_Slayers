import { defineStore } from 'pinia'
import { useAuthStore } from '../stores/auth'

const partImageModules = import.meta.glob('../customer_dashboard/customer_assets/*.{png,jpg,jpeg,webp,avif,svg}', {
  eager: true,
  import: 'default'
})

const normalizePartAssetName = (value = '') => String(value)
  .toLowerCase()
  .replace(/\.[^.]+$/, '')
  .replace(/[^a-z0-9]+/g, ' ')
  .trim()
  .replace(/\s+/g, ' ')

const partImagesByName = Object.fromEntries(
  Object.entries(partImageModules).map(([path, src]) => {
    const filename = path.split('/').pop() || ''
    return [normalizePartAssetName(filename), src]
  })
)

const resolvePartImage = (partName) => partImagesByName[normalizePartAssetName(partName)] || null

const numberOrNull = (value) => {
  const parsed = Number(value)
  return Number.isFinite(parsed) ? parsed : null
}

const integerOrNull = (value) => {
  const parsed = Number(value)
  return Number.isInteger(parsed) ? parsed : null
}

const parseDateValue = (value) => {
  if (!value || typeof value !== 'string') return null

  const isoMatch = value.match(/^(\d{4})-(\d{2})-(\d{2})$/)
  if (isoMatch) {
    const [, year, month, day] = isoMatch
    const parsed = new Date(Number(year), Number(month) - 1, Number(day))
    return Number.isNaN(parsed.getTime()) ? null : parsed
  }

  const parsed = new Date(value)
  return Number.isNaN(parsed.getTime()) ? null : parsed
}

const formatOrderDate = (value) => {
  const parsed = parseDateValue(value)
  if (!parsed) return '—'

  return parsed.toLocaleDateString('en-IN', {
    month: 'short',
    day: 'numeric',
    year: 'numeric'
  })
}

const normalizeVendor = (vendor = {}) => {
  const products = Array.isArray(vendor.products) ? vendor.products : []
  const parts = Array.isArray(vendor.parts)
    ? vendor.parts
    : products.map((product) => product.name).filter(Boolean)

  return {
    id: String(vendor.id ?? ''),
    name: vendor.name || 'Unknown Vendor',
    prefix: vendor.prefix || '',
    leadTime: integerOrNull(vendor.leadTime),
    location: vendor.location || '—',
    contact: {
      phone: vendor.contact?.phone || '—',
      email: vendor.contact?.email || '—'
    },
    parts,
    products,
    partCount: Number(vendor.partCount ?? parts.length ?? 0),
    priceEntries: Array.isArray(vendor.priceEntries) ? vendor.priceEntries.map(normalizePriceEntry) : []
  }
}

const normalizeSupplier = (supplier = {}) => ({
  vendorId: String(supplier.vendorId ?? supplier.vendor?.id ?? ''),
  skuId: String(supplier.skuId ?? ''),
  price: numberOrNull(supplier.price),
  currentBuy: numberOrNull(supplier.currentBuy ?? supplier.price),
  unitMeasurementBuy: integerOrNull(supplier.unitMeasurementBuy),
  lotSize: integerOrNull(supplier.lotSize),
  leadTime: integerOrNull(supplier.leadTime ?? supplier.vendor?.leadTime),
  vendor: {
    id: String(supplier.vendor?.id ?? supplier.vendorId ?? ''),
    name: supplier.vendor?.name || 'Unknown Vendor',
    location: supplier.vendor?.location || '—',
    leadTime: integerOrNull(supplier.vendor?.leadTime ?? supplier.leadTime)
  }
})

const normalizeCompareSize = (size = {}) => ({
  key: size.key || size.size || '',
  size: size.size || '—',
  spec: size.spec || '',
  specs: size.specs && typeof size.specs === 'object' ? { ...size.specs } : {},
  suppliers: Array.isArray(size.suppliers) ? size.suppliers.map(normalizeSupplier) : []
})

const normalizePriceEntry = (entry = {}) => {
  const size = entry.size || '—'
  const spec = entry.spec || ''

  return {
    productId: String(entry.productId ?? ''),
    skuId: String(entry.skuId ?? ''),
    key: entry.key || '',
    size,
    spec,
    specification: entry.specification || [size, spec].filter(Boolean).join(' · '),
    specs: entry.specs && typeof entry.specs === 'object' ? { ...entry.specs } : {},
    price: numberOrNull(entry.price)
  }
}

const normalizeComparePart = (part = {}) => ({
  id: String(part.id ?? ''),
  name: part.name || 'Unknown Part',
  image: part.image || resolvePartImage(part.name),
  sizes: Array.isArray(part.sizes) ? part.sizes.map(normalizeCompareSize) : []
})

const normalizeProcurement = (procurement = {}) => {
  const vendor = procurement.vendor || {}
  const rawStatus = String(procurement.status || '').trim().toLowerCase()
  const status = rawStatus === 'received' || rawStatus === 'completed'
    ? 'received'
    : rawStatus === 'cancelled'
      ? 'cancelled'
      : 'pending'

  return {
    id: String(procurement.id ?? ''),
    skuId: String(procurement.skuId ?? ''),
    partName: procurement.partName || 'Unknown Part',
    specification: procurement.specification || procurement.size || '—',
    vendorId: String(procurement.vendorId ?? vendor.id ?? ''),
    vendorName: vendor.name || procurement.vendorName || '—',
    vendorLocation: vendor.location || '—',
    vendorLeadTime: integerOrNull(vendor.leadTime),
    orderDate: procurement.orderDate || '',
    date: formatOrderDate(procurement.orderDate || procurement.date || ''),
    currentBuy: numberOrNull(procurement.currentBuy),
    unitMeasurementBuy: integerOrNull(procurement.unitMeasurementBuy),
    lotSize: integerOrNull(procurement.lotSize),
    lotCount: integerOrNull(procurement.lotCount),
    orderedQty: integerOrNull(procurement.orderedQty),
    totalCost: numberOrNull(procurement.totalCost),
    status,
    statusRaw: procurement.statusRaw || procurement.status || null
  }
}

const upsertById = (items, nextItem) => {
  const nextId = String(nextItem.id)
  const existingIndex = items.findIndex((item) => String(item.id) === nextId)

  if (existingIndex === -1) {
    return [nextItem, ...items]
  }

  const nextItems = [...items]
  nextItems.splice(existingIndex, 1, {
    ...items[existingIndex],
    ...nextItem
  })
  return nextItems
}

export const useVendorStore = defineStore('vendors', {
  state: () => ({
    directoryVendors: [],
    directoryLoading: false,
    directoryError: '',
    compareParts: [],
    compareLoading: false,
    compareError: '',
    selectedDirectoryVendor: null,
    vendorDetailLoading: false,
    vendorDetailError: '',
    vendorSaving: false,
    vendorSaveError: '',
    procurements: [],
    procurementLoading: false,
    procurementError: '',
    procurementSubmitting: false
  }),

  getters: {
    activeVendorCount: (state) => state.directoryVendors.length,

    findDirectoryVendorById: (state) => (id) =>
      state.directoryVendors.find((vendor) => vendor.id === String(id)),

    findProcurementById: (state) => (id) =>
      state.procurements.find((procurement) => procurement.id === id)
  },

  actions: {
    async fetchVendorDirectory() {
      this.directoryLoading = true
      this.directoryError = ''

      try {
        const authStore = useAuthStore()
        const payload = await authStore.authenticatedRequest('/api/vendors')
        this.directoryVendors = (payload.vendors || []).map(normalizeVendor)
      } catch (error) {
        this.directoryVendors = []
        this.directoryError = error.message || 'Unable to load vendors right now.'
      } finally {
        this.directoryLoading = false
      }
    },

    async fetchCompareCatalog() {
      this.compareLoading = true
      this.compareError = ''

      try {
        const authStore = useAuthStore()
        const payload = await authStore.authenticatedRequest('/api/vendors/catalog/compare')
        this.compareParts = (payload.parts || []).map(normalizeComparePart)
      } catch (error) {
        this.compareParts = []
        this.compareError = error.message || 'Unable to load the parts catalog right now.'
      } finally {
        this.compareLoading = false
      }
    },

    async fetchVendorDetails(vendorId) {
      if (!vendorId) {
        this.clearVendorDetails()
        return null
      }

      const existingVendor = this.findDirectoryVendorById(vendorId)
      if (existingVendor) {
        this.selectedDirectoryVendor = existingVendor
      }

      this.vendorDetailLoading = true
      this.vendorDetailError = ''

      try {
        const authStore = useAuthStore()
        const payload = await authStore.authenticatedRequest(`/api/vendors/${encodeURIComponent(vendorId)}`)
        const vendor = normalizeVendor(payload.vendor || {})
        this.selectedDirectoryVendor = vendor
        this.directoryVendors = upsertById(this.directoryVendors, vendor)
        return vendor
      } catch (error) {
        this.selectedDirectoryVendor = null
        this.vendorDetailError = error.message || 'Unable to load vendor details right now.'
        return null
      } finally {
        this.vendorDetailLoading = false
      }
    },

    async fetchProcurements() {
      this.procurementLoading = true
      this.procurementError = ''

      try {
        const authStore = useAuthStore()
        const payload = await authStore.authenticatedRequest('/api/vendors/procurements')
        this.procurements = (payload.procurements || []).map(normalizeProcurement)
      } catch (error) {
        this.procurements = []
        this.procurementError = error.message || 'Unable to load procurement requests right now.'
      } finally {
        this.procurementLoading = false
      }
    },

    clearVendorDetails() {
      this.selectedDirectoryVendor = null
      this.vendorDetailLoading = false
      this.vendorDetailError = ''
    },

    async createVendor(formData) {
      this.vendorSaving = true
      this.vendorSaveError = ''

      try {
        const authStore = useAuthStore()
        const payload = await authStore.authenticatedRequest('/api/vendors', {
          method: 'POST',
          body: JSON.stringify(formData)
        })
        const vendor = normalizeVendor(payload.vendor || {})
        await Promise.all([
          this.fetchVendorDirectory(),
          this.fetchCompareCatalog()
        ])
        this.selectedDirectoryVendor = vendor
        return vendor
      } catch (error) {
        this.vendorSaveError = error.message || 'Unable to save this vendor right now.'
        throw error
      } finally {
        this.vendorSaving = false
      }
    },

    async updateVendor(vendorId, formData) {
      this.vendorSaving = true
      this.vendorSaveError = ''

      try {
        const authStore = useAuthStore()
        const payload = await authStore.authenticatedRequest(`/api/vendors/${encodeURIComponent(vendorId)}`, {
          method: 'PATCH',
          body: JSON.stringify(formData)
        })
        const vendor = normalizeVendor(payload.vendor || {})
        await Promise.all([
          this.fetchVendorDirectory(),
          this.fetchCompareCatalog()
        ])
        this.selectedDirectoryVendor = vendor
        return vendor
      } catch (error) {
        this.vendorSaveError = error.message || 'Unable to update this vendor right now.'
        throw error
      } finally {
        this.vendorSaving = false
      }
    },

    async createProcurement({ skuId, vendorId, lotCount }) {
      this.procurementSubmitting = true
      this.procurementError = ''

      try {
        const authStore = useAuthStore()
        const payload = await authStore.authenticatedRequest('/api/vendors/procurements', {
          method: 'POST',
          body: JSON.stringify({ skuId, vendorId, lotCount })
        })
        const procurement = normalizeProcurement(payload.procurement || {})
        this.procurements = upsertById(this.procurements, procurement)
        return procurement
      } catch (error) {
        this.procurementError = error.message || 'Unable to submit the procurement request right now.'
        throw error
      } finally {
        this.procurementSubmitting = false
      }
    },

    async markReceived(id) {
      this.procurementError = ''

      try {
        const authStore = useAuthStore()
        const payload = await authStore.authenticatedRequest(`/api/vendors/procurements/${encodeURIComponent(id)}/receive`, {
          method: 'PATCH'
        })
        const procurement = normalizeProcurement(payload.procurement || {})
        this.procurements = upsertById(this.procurements, procurement)
        return procurement
      } catch (error) {
        this.procurementError = error.message || 'Unable to update the procurement request right now.'
        throw error
      }
    }
  }
})
