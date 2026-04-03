import { defineStore } from 'pinia'
import { useAuthStore } from '../stores/auth'

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
  },

  actions: {
    async fetchOverview() {
      this.isLoading = true
      this.error = ''
      this.parts = []
      this.asOfDate = ''
      this.portfolioProducts = []
      this.profData = {}

      try {
        const authStore = useAuthStore()
        const payload = await authStore.authenticatedRequest('/api/inventory/overview')
        this.parts = payload.parts || []
        this.asOfDate = payload.summary?.asOfDate || ''
        this.portfolioProducts = payload.portfolioProducts || []
        this.profData = payload.portfolioDetails || {}
      } catch (error) {
        this.parts = []
        this.asOfDate = ''
        this.portfolioProducts = []
        this.profData = {}
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
