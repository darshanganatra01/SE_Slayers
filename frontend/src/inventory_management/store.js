import { acceptHMRUpdate, defineStore } from 'pinia'
import { useAuthStore } from '../stores/auth'

const normalizePendingOrder = (procurement = {}) => {
  const vendor = procurement.vendor || {}
  const status = String(procurement.status || '').trim().toLowerCase()

  const vendorName = vendor.name || procurement.vendorName || ''
  const specification = procurement.specification || procurement.size || '—'

  return {
    id: String(procurement.id ?? ''),
    procurementId: String(procurement.id ?? ''),
    name: procurement.partName || 'Unknown Part',
    detail: vendorName ? `${specification} · ${vendorName}` : specification,
    qty: Number(procurement.orderedQty ?? 0) || 0,
    status
  }
}

const buildPartPayload = (formData) => ({
  name: formData.name,
  category: formData.category,
  unitMeasurementBuy: formData.unitMeasurementBuy,
  lotSizeBuy: formData.lotSizeBuy,
  vendorIds: [...formData.vendorIds],
  specs: formData.specs.map((spec) => ({
    label: spec.label,
    stockQty: spec.stockQty,
    threshold: spec.threshold,
    sellPrice: spec.sellPrice,
    vendorPrices: Object.entries(spec.vendorPrices || {}).map(([vendorId, unitBuyPrice]) => ({
      vendorId,
      unitBuyPrice
    }))
  }))
})

const partDetailUrl = (productId) => `/api/inventory/parts?productId=${encodeURIComponent(productId)}`

export const useInventoryStore = defineStore('inventory', {
  state: () => ({
    parts: [],
    isLoading: false,
    error: '',
    asOfDate: '',
    profData: {},
    pendingOrders: [],
    stockHistory: [],
    portfolioProducts: [],
    partFormVendors: [],
    partFormVendorsLoading: false,
    partSaving: false,
    partSaveError: ''
  }),

  getters: {
    totalCount: (s) => s.parts.length,
    inStockCount: (s) => s.parts.filter((p) => p.status === 'instock').length,
    lowStockCount: (s) => s.parts.filter((p) => p.status === 'low' || p.status === 'out').length,
    outOfStockCount: (s) => s.parts.filter((p) => p.status === 'out').length,
    lowOnlyCount: (s) => s.parts.filter((p) => p.status === 'low').length,
    inventoryValue: (s) => s.parts.reduce((total, part) => total + (Number(part.sellPrice || 0) * Number(part.stock || 0)), 0),
    categories: (s) => [...new Set(s.parts.map((part) => (part.category || '').trim()).filter(Boolean))].sort((a, b) => a.localeCompare(b)),
  },

  actions: {
    async fetchOverview() {
      this.isLoading = true
      this.error = ''
      this.parts = []
      this.asOfDate = ''
      this.portfolioProducts = []
      this.profData = {}
      this.pendingOrders = []

      try {
        const authStore = useAuthStore()
        const [overviewResult, procurementResult] = await Promise.allSettled([
          authStore.authenticatedRequest('/api/inventory/overview'),
          authStore.authenticatedRequest('/api/vendors/procurements')
        ])

        if (overviewResult.status !== 'fulfilled') {
          throw overviewResult.reason
        }

        const payload = overviewResult.value
        this.parts = payload.parts || []
        this.asOfDate = payload.summary?.asOfDate || ''
        this.portfolioProducts = payload.portfolioProducts || []
        this.profData = payload.portfolioDetails || {}

        if (procurementResult.status === 'fulfilled') {
          this.pendingOrders = (procurementResult.value.procurements || [])
            .map(normalizePendingOrder)
        }
      } catch (error) {
        this.parts = []
        this.asOfDate = ''
        this.portfolioProducts = []
        this.profData = {}
        this.pendingOrders = []
        this.error = error.message || 'Unable to load inventory right now.'
      } finally {
        this.isLoading = false
      }
    },

    async fetchPartFormVendors(force = false) {
      if (this.partFormVendorsLoading) return
      if (!force && this.partFormVendors.length) return

      this.partFormVendorsLoading = true
      try {
        const authStore = useAuthStore()
        const payload = await authStore.authenticatedRequest('/api/vendors')
        this.partFormVendors = (payload.vendors || []).map((vendor) => {
          const leadTime = Number(vendor.leadTime)
          return {
            id: String(vendor.id ?? ''),
            name: vendor.name || 'Unknown Vendor',
            location: vendor.location || '—',
            leadTime: Number.isFinite(leadTime) ? leadTime : null,
            prefix: vendor.prefix || ''
          }
        })
      } catch (error) {
        this.partFormVendors = []
        throw error
      } finally {
        this.partFormVendorsLoading = false
      }
    },

    async createPart(formData) {
      this.partSaving = true
      this.partSaveError = ''

      try {
        const authStore = useAuthStore()
        const payload = buildPartPayload(formData)

        const requestBody = new FormData()
        requestBody.append('payload', JSON.stringify(payload))
        if (typeof File !== 'undefined' && formData.imageFile instanceof File) {
          requestBody.append('image', formData.imageFile)
        }

        const response = await authStore.authenticatedRequest('/api/inventory/parts', {
          method: 'POST',
          body: requestBody
        })
        try {
          await this.fetchOverview()
        } catch {
          // Keep the creation result even if the overview refresh misses once.
        }
        return response.product || null
      } catch (error) {
        this.partSaveError = error.message || 'Unable to create this part right now.'
        throw error
      } finally {
        this.partSaving = false
      }
    },

    async fetchPart(productId) {
      const authStore = useAuthStore()
      const payload = await authStore.authenticatedRequest(partDetailUrl(productId))
      return payload.product || null
    },

    async updatePart(productId, formData) {
      this.partSaving = true
      this.partSaveError = ''

      try {
        const authStore = useAuthStore()
        const payload = buildPartPayload(formData)

        const requestBody = new FormData()
        requestBody.append('payload', JSON.stringify(payload))
        if (typeof File !== 'undefined' && formData.imageFile instanceof File) {
          requestBody.append('image', formData.imageFile)
        }

        const response = await authStore.authenticatedRequest(partDetailUrl(productId), {
          method: 'PATCH',
          body: requestBody
        })
        try {
          await this.fetchOverview()
        } catch {
          // Keep the update result even if the overview refresh misses once.
        }
        return response.product || null
      } catch (error) {
        this.partSaveError = error.message || 'Unable to update this part right now.'
        throw error
      } finally {
        this.partSaving = false
      }
    }
  }
})

if (import.meta.hot) {
  import.meta.hot.accept(acceptHMRUpdate(useInventoryStore, import.meta.hot))
}
