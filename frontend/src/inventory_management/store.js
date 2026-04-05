import { defineStore } from 'pinia'
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

export const useInventoryStore = defineStore('inventory', {
  state: () => ({
    parts: [],
    isLoading: false,
    error: '',
    asOfDate: '',
    profData: {},
    pendingOrders: [],
    stockHistory: [],
    portfolioProducts: []
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

    addPart(data) {
      const id = this.parts.length ? Math.max(...this.parts.map((p) => Number(p.id))) + 1 : 1
      const stock = parseInt(data.openingStock) || 0
      const threshold = parseInt(data.threshold) || 5
      let status = 'instock'
      if (stock === 0) status = 'out'
      else if (stock < threshold) status = 'low'

      this.parts.push({
        id,
        skuId: data.sku || String(id),
        sku: data.sku || String(id),
        name: data.name,
        category: data.category,
        size: data.size,
        dims: data.dims,
        spec: data.spec,
        stock,
        threshold,
        maxStock: Math.max(stock, threshold, 1),
        status,
        sellPrice: parseFloat(data.sellPrice) || 0,
      })
    }
  }
})
