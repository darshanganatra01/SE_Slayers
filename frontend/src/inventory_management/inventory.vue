<template>
  <main class="inv-main">

    <AppTopbar title="Inventory" :meta="headMeta">
      <template #actions>
        <AppSearchbar
          v-if="curTab !== 'portfolio'"
          v-model="searchQ"
          placeholder="Search parts…"
        />
        <button class="btn btn-outline" @click="exportData">
          <svg fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24" width="12" height="12"><path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4"/><polyline points="17,8 12,3 7,8"/><line x1="12" y1="3" x2="12" y2="15"/></svg>
          Export
        </button>
        <button class="btn btn-primary" @click="openAddPart">+ Add part</button>
      </template>
    </AppTopbar>

    <div class="inv-body">

      <!-- Stat cards -->
      <StatCards
        :total="store.totalCount"
        :in-stock="store.inStockCount"
        :low-stock="store.lowStockCount"
        :inventory-value="store.inventoryValue"
      />

      <!-- Tabs -->
      <div class="inv-tabs">
        <div
          v-for="tab in tabs"
          :key="tab.key"
          class="inv-tab"
          :class="{ active: curTab === tab.key }"
          @click="curTab = tab.key"
        >
          {{ tab.label }}
          <span class="inv-tab-count" :class="{ active: curTab === tab.key }">{{ tab.count }}</span>
        </div>
      </div>

      <StockTable
        v-if="curTab !== 'portfolio'"
        :parts="store.parts"
        :tab="curTab"
        :search="searchQ"
        @go-vendor="goVendor"
      />

      <div v-if="store.error" class="inv-error">{{ store.error }}</div>

      <PortfolioTable
        v-if="curTab === 'portfolio'"
        :products="store.portfolioProducts"
        @open-profit="openProfit"
        @edit-product="openEditPart"
      />

      <div v-if="curTab !== 'portfolio'" class="inv-bottom-grid">
        <PendingArrivals
          :orders="store.pendingOrders"
          @go-vendor="goVendor"
        />
        <StockHistory
          :history="store.stockHistory"
        />
      </div>

    </div>

    <ProfitPopup
      :visible="showProfitPopup"
      :data="profitData"
      @close="showProfitPopup = false"
      @go-vendor="goVendor"
    />

    <AddPartModal
      :visible="showAddModal"
      :mode="partModalMode"
      :initial-data="partModalData"
      :categories="store.categories"
      :vendors="store.partFormVendors"
      :vendors-loading="store.partFormVendorsLoading"
      :saving="store.partSaving"
      :save-error="store.partSaveError"
      @close="closeAddPart"
      @save="handleAddPart"
    />

    <AppToast ref="toast" />

  </main>
</template>

<script>
import { onMounted } from 'vue'
import { useInventoryStore } from './store.js'
import { useAuthStore } from '../stores/auth'
import AppTopbar       from '../components/AppTopbar.vue'
import AppSearchbar    from '../components/AppSearchbar.vue'
import AppToast        from '../components/AppToast.vue'
import StatCards       from './components/StatCards.vue'
import StockTable      from './components/StockTable.vue'
import PortfolioTable  from './components/PortfolioTable.vue'
import PendingArrivals from './components/PendingArrivals.vue'
import StockHistory    from './components/StockHistory.vue'
import ProfitPopup     from './components/ProfitPopup.vue'
import AddPartModal    from './components/AddPartModal.vue'

const partDetailUrl = (productId) => `/api/inventory/parts?productId=${encodeURIComponent(productId)}`

export default {
  name: 'InventoryManagement',
  components: {
    AppTopbar, AppSearchbar, AppToast,
    StatCards, StockTable, PortfolioTable,
    PendingArrivals, StockHistory,
    ProfitPopup, AddPartModal
  },

  setup() {
    const store = useInventoryStore()
    const authStore = useAuthStore()
    onMounted(() => {
      store.fetchOverview()
    })
    return { store, authStore }
  },

  data() {
    return {
      curTab: 'all',
      searchQ: '',
      showProfitPopup: false,
      profitPopupKey: '',
      showAddModal: false,
      partModalMode: 'add',
      partModalData: null
    }
  },

  computed: {
    headMeta() {
      const label = this.store.asOfDate
        ? new Date(this.store.asOfDate).toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' })
        : new Date().toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' })
      return `${label} · ${this.store.totalCount} parts`
    },
    tabs() {
      return [
        { key: 'all',       label: 'All parts',         count: this.store.totalCount },
        { key: 'instock',   label: 'In stock',          count: this.store.inStockCount },
        { key: 'low',       label: 'Low stock',         count: this.store.lowOnlyCount },
        { key: 'out',       label: 'Out of stock',      count: this.store.outOfStockCount },
        { key: 'portfolio', label: 'Product portfolio',  count: this.store.portfolioProducts.length }
      ]
    },
    profitData() {
      if (!this.profitPopupKey) return { key: '', title: '', category: '', rows: [] }
      return {
        key: this.profitPopupKey,
        ...(this.store.profData[this.profitPopupKey] || { title: '', category: '', rows: [] })
      }
    }
  },

  methods: {
    buildPartRequestBody(formData) {
      const payload = {
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
      }

      const requestBody = new FormData()
      requestBody.append('payload', JSON.stringify(payload))
      if (typeof File !== 'undefined' && formData.imageFile instanceof File) {
        requestBody.append('image', formData.imageFile)
      }
      return requestBody
    },
    async fetchPartForEdit(productId) {
      if (typeof this.store.fetchPart === 'function') {
        return this.store.fetchPart(productId)
      }
      const payload = await this.authStore.authenticatedRequest(partDetailUrl(productId))
      return payload.product || null
    },
    async savePartChanges(productId, formData) {
      if (typeof this.store.updatePart === 'function') {
        return this.store.updatePart(productId, formData)
      }

      this.store.partSaving = true
      this.store.partSaveError = ''
      try {
        const response = await this.authStore.authenticatedRequest(partDetailUrl(productId), {
          method: 'PATCH',
          body: this.buildPartRequestBody(formData)
        })
        await this.store.fetchOverview()
        return response.product || null
      } catch (error) {
        this.store.partSaveError = error.message || 'Unable to update this part right now.'
        throw error
      } finally {
        this.store.partSaving = false
      }
    },
    goVendor(target, size) {
      if (target && typeof target === 'object' && target.source === 'procurement-history') {
        this.$router.push({
          name: 'vendors',
          query: {
            tab: 'procurement',
            ...(target.procurementId ? { procurementId: target.procurementId } : {})
          }
        })
        return
      }
      if (
        target
        && typeof target === 'object'
      ) {
        if (target.skuId) {
          this.$router.push({
            name: 'vendors',
            query: {
              tab: 'compare',
              skuId: target.skuId
            }
          })
          return
        }
        if (!target.partId || !target.specKey) {
          return
        }
        this.$router.push({
          name: 'vendors',
          query: {
            tab: 'compare',
            partId: target.partId,
            specKey: target.specKey,
          }
        })
        return
      }
      alert(`→ Vendor procurement: ${target} · ${size}`)
    },
    openProfit(key) {
      this.profitPopupKey = key
      this.showProfitPopup = true
    },
    async openAddPart() {
      this.store.partSaveError = ''
      this.partModalMode = 'add'
      this.partModalData = null
      this.showAddModal = true
      try {
        await this.store.fetchPartFormVendors()
      } catch (error) {
        this.$refs.toast.show('!', 'Unable to load vendors', error.message || 'Please try again')
      }
    },
    async openEditPart(productId) {
      this.store.partSaveError = ''
      this.partModalMode = 'edit'
      this.partModalData = null

      try {
        await this.store.fetchPartFormVendors()
        this.partModalData = await this.fetchPartForEdit(productId)
        this.showAddModal = true
      } catch (error) {
        this.$refs.toast.show('!', 'Unable to load part', error.message || 'Please try again')
      }
    },
    closeAddPart() {
      if (this.store.partSaving) return
      this.store.partSaveError = ''
      this.showAddModal = false
      this.partModalData = null
      this.partModalMode = 'add'
    },
    async handleAddPart(formData) {
      const isEditMode = this.partModalMode === 'edit'
      try {
        const product = isEditMode && formData.id
          ? await this.savePartChanges(formData.id, formData)
          : await this.store.createPart(formData)
        this.closeAddPart()
        this.$refs.toast.show(
          '✓',
          isEditMode ? 'Part updated' : 'Part added',
          product?.name || formData.name || 'New Part'
        )
      } catch (error) {
        this.$refs.toast.show(
          '!',
          isEditMode ? 'Unable to update part' : 'Unable to add part',
          error.message || 'Please try again'
        )
      }
    },
    exportData() {
      alert('Export functionality — coming soon')
    }
  }
}
</script>

<style scoped>
.inv-main {
  flex: 1; display: flex;
  flex-direction: column;
  overflow: hidden;
  background: var(--bg);
}
.inv-body {
  flex: 1; overflow-y: auto;
  padding: 18px 20px 28px;
  display: flex; flex-direction: column;
  gap: 14px;
}

.inv-tabs {
  display: flex;
  border-bottom: 1.5px solid var(--border);
  flex-shrink: 0;
}
.inv-tab {
  padding: 7px 0 8px;
  font-size: 13px; font-weight: 400;
  color: var(--ink-3); cursor: pointer;
  border-bottom: 2px solid transparent;
  margin-bottom: -1.5px;
  display: flex; align-items: center; gap: 5px;
  white-space: nowrap;
  transition: color .1s;
  margin-right: 20px;
}
.inv-tab:last-child { margin-right: 0; }
.inv-tab:hover { color: var(--ink); }
.inv-tab.active {
  color: var(--blue); font-weight: 500;
  border-bottom-color: var(--blue);
}
.inv-tab-count {
  font-size: 12.5px; color: var(--ink-4);
}
.inv-tab.active .inv-tab-count {
  color: var(--blue);
}

.inv-bottom-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 14px;
  flex-shrink: 0;
}
.inv-error {
  padding: 12px 14px;
  border: 1.5px solid #fca5a5;
  background: #fee2e2;
  color: #b91c1c;
  border-radius: 8px;
  font-size: 13px;
}
</style>
