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
        <button class="btn btn-primary" @click="showAddModal = true">+ Add part</button>
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
      @close="showAddModal = false"
      @submit="handleAddPart"
    />

    <AppToast ref="toast" />

  </main>
</template>

<script>
import { onMounted } from 'vue'
import { useInventoryStore } from './store.js'
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
    onMounted(() => {
      store.fetchOverview()
    })
    return { store }
  },

  data() {
    return {
      curTab: 'all',
      searchQ: '',
      showProfitPopup: false,
      profitPopupKey: '',
      showAddModal: false
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
      if (!this.profitPopupKey) return { title: '', sku: '', total: '', rows: [] }
      return this.store.profData[this.profitPopupKey] || { title: '', sku: '', total: '', rows: [] }
    }
  },

  methods: {
    goVendor(sku, size) {
      alert(`→ Vendor procurement: ${sku} · ${size}`)
    },
    openProfit(key) {
      this.profitPopupKey = key
      this.showProfitPopup = true
    },
    handleAddPart(formData) {
      this.store.addPart(formData)
      this.$refs.toast.show('✓', 'Part added', formData.name || 'New Part')
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
