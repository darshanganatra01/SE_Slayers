<template>
  <main class="main">

    <AppTopbar title="Orders" :meta="headMeta">
      <template #actions>
        <AppSearchbar v-model="searchQ" placeholder="Search orders…" />
        <select class="tb-select" v-model="priFilter">
          <option value="all">All priorities</option>
          <option value="High">High</option>
          <option value="Medium">Medium</option>
          <option value="Low">Low</option>
        </select>
        <button class="btn btn-primary" @click="showModal = true">+ New order</button>
      </template>
    </AppTopbar>

    <!-- Page head with tabs -->
    <div class="page-head">
      <div class="head-top">
        <div>
          <div class="head-title">All Orders</div>
          <div class="head-sub">{{ headSub }}</div>
        </div>
      </div>
      <div class="tabs">
        <button
          v-for="tab in tabs"
          :key="tab.status"
          class="tab"
          :class="{ active: activeStatus === tab.status }"
          @click="switchTab(tab.status)"
        >
          <span class="tab-dot" :style="{ background: tab.color }"></span>
          {{ tab.label }}
          <span class="tab-count" :class="{ active: activeStatus === tab.status }">
            {{ store.byStatus(tab.status).length }}
          </span>
        </button>
      </div>
    </div>

    <!-- Board -->
    <div class="board">
      <div class="cards-panel">

        <!-- Column header -->
        <div class="col-header">
          <div class="col-header-dot" :style="{ background: SC[activeStatus] }"></div>
          <div class="col-header-label">{{ SL[activeStatus] }}</div>
          <div class="col-header-count">{{ visibleOrders.length }} order{{ visibleOrders.length !== 1 ? 's' : '' }}</div>
          <div class="col-header-hint">Drag to reprioritise</div>
        </div>

        <!-- Empty state -->
        <div v-if="visibleOrders.length === 0" class="empty-state">
          <div class="es-icon">📭</div>
          <div class="es-text">No orders</div>
          <div class="es-sub">Try adjusting your filters</div>
        </div>

        <!-- Cards grid -->
        <div v-else class="cards-grid">
          <OrderCard
            v-for="(order, i) in visibleOrders"
            :key="order.id"
            :order="order"
            :selected="selectedId === order.id"
            :style="{ animationDelay: i * 0.04 + 's' }"
            @select="selectedId = $event"
            @drag-start="dragId = $event"
            @drag-end="dragId = null"
            @reorder="handleReorder($event)"
          />
        </div>
      </div>

      <!-- Detail panel -->
      <OrderDetailPanel
        :order="selectedOrder"
        @close="selectedId = null"
        @promote="handlePromote"
      />
    </div>

    <!-- Stock bar -->
    <StockBar :inventory="store.inventory" />

    <!-- New order modal -->
    <NewOrderModal
      :visible="showModal"
      @close="showModal = false"
      @submit="handleNewOrder"
    />

    <!-- Toast -->
    <AppToast ref="toast" />

  </main>
</template>

<script>
import { useOrderStore, SC, SL } from './store.js'
import AppTopbar        from '../components/AppTopbar.vue'
import AppSearchbar     from '../components/AppSearchbar.vue'
import AppToast         from '../components/AppToast.vue'
import OrderCard        from './components/OrderCard.vue'
import OrderDetailPanel from './components/OrderDetailPanel.vue'
import NewOrderModal    from './components/NewOrderModal.vue'
import StockBar         from './components/StockBar.vue'

export default {
  name: 'OrderManagement',
  components: { AppTopbar, AppSearchbar, AppToast, OrderCard, OrderDetailPanel, NewOrderModal, StockBar },

  setup() {
    const store = useOrderStore()
    return { store }
  },

  data() {
    return {
      SC, SL,
      activeStatus: 'inprocess',
      selectedId:   null,
      dragId:       null,
      searchQ:      '',
      priFilter:    'all',
      showModal:    false,
      tabs: [
        { status: 'inprocess', label: 'In Progress', color: '#2563eb' },
        { status: 'packed',    label: 'Packed',      color: '#d97706' },
        { status: 'shipped',   label: 'Shipped',     color: '#16a34a' },
      ]
    }
  },

  computed: {
    headMeta() {
      return `Mar 2026 · ${this.store.totalCount} total`
    },
    headSub() {
      return `${this.store.byStatus(this.activeStatus).length} orders in ${SL[this.activeStatus].toLowerCase()}`
    },
    selectedOrder() {
      return this.selectedId ? this.store.findById(this.selectedId) : null
    },
    visibleOrders() {
      // Touch items deeply so qty changes trigger re-render
      this.store.orders.forEach(o => o.items.forEach(it => it.qty))
      
      let list = this.store.byStatus(this.activeStatus)
      if (this.searchQ) {
        const q = this.searchQ.toLowerCase()
        list = list.filter(o =>
          o.customer.toLowerCase().includes(q) ||
          o.id.toLowerCase().includes(q)
        )
      }
      if (this.priFilter !== 'all') {
        list = list.filter(o => o.priority === this.priFilter)
      }
      return list
    }
  },

  methods: {
    switchTab(status) {
      this.activeStatus = status
      this.selectedId = null
    },

    handleReorder({ toId, pos }) {
      if (!this.dragId || this.dragId === toId) return
      this.store.reorder(this.dragId, toId, pos)
      this.$refs.toast.show('↕', 'Reordered', 'Priority updated')
    },

// In management.vue — replace handlePromote with this:

    handlePromote({ id, newStatus, transport, updatedItems }) {
      this.store.promote(id, newStatus, transport, updatedItems)
      if (newStatus === 'packed') {
        this.$refs.toast.show('📦', `${id} → Packed`, 'Quantities confirmed')
      } else if (newStatus === 'shipped') {
        this.$refs.toast.show('🚚', `${id} → Shipped`, transport || 'BlueDart Express')
      } else {
        this.$refs.toast.show('↩', `${id} moved back`, SL[newStatus])
      }
      this.activeStatus = newStatus
    },

    handleNewOrder(formData) {
      const newId = this.store.addOrder(formData)
      this.showModal = false
      this.switchTab('inprocess')
      this.$refs.toast.show('✓', `${newId} created`, formData.customer || 'New Customer')
    }
  }
}
</script>

<style scoped>
.main { flex: 1; display: flex; flex-direction: column; overflow: hidden; background: var(--bg); }

.tb-select {
  padding: 5px 9px;
  background: var(--white); border: 1.5px solid var(--border);
  border-radius: 6px; color: var(--ink-2); font-size: 12px;
  outline: none; font-family: 'Geist', sans-serif; cursor: pointer;
}
.tb-select option { background: #fff; }

/* Page head */
.page-head  { background: var(--white); border-bottom: 1.5px solid var(--border); flex-shrink: 0; padding: 14px 22px 0; }
.head-top   { display: flex; align-items: center; justify-content: space-between; margin-bottom: 14px; }
.head-title { font-size: 18px; font-weight: 600; color: var(--ink); letter-spacing: -0.4px; }
.head-sub   { font-size: 11.5px; color: var(--ink-4); font-family: 'Geist Mono', monospace; margin-top: 2px; }

/* Tabs */
.tabs { display: flex; align-items: stretch; }
.tab {
  display: flex; align-items: center; gap: 6px;
  padding: 8px 16px; border: none; background: transparent; cursor: pointer;
  color: var(--ink-4); font-family: 'Geist', sans-serif;
  font-size: 12.5px; font-weight: 500;
  border-bottom: 2px solid transparent;
  transition: all 0.12s; position: relative; top: 1.5px;
}
.tab:hover:not(.active) { color: var(--ink-2); }
.tab.active { color: var(--ink); border-bottom-color: var(--blue); font-weight: 600; }
.tab-dot    { width: 6px; height: 6px; border-radius: 50%; flex-shrink: 0; }
.tab-count  {
  font-family: 'Geist Mono', monospace; font-size: 10px;
  background: var(--surface); border: 1px solid var(--border-2);
  border-radius: 10px; padding: 0 6px; color: var(--ink-4); line-height: 1.8;
}
.tab-count.active { background: var(--blue); color: #fff; border-color: var(--blue); }

/* Board */
.board       { flex: 1; display: flex; overflow: hidden; }
.cards-panel { flex: 1; overflow-y: auto; padding: 18px 20px; }
.cards-panel::-webkit-scrollbar { width: 3px; }
.cards-panel::-webkit-scrollbar-thumb { background: var(--border-2); border-radius: 2px; }

/* Column header */
.col-header        { display: flex; align-items: center; gap: 8px; margin-bottom: 14px; padding-bottom: 12px; border-bottom: 1.5px solid var(--border-2); }
.col-header-dot    { width: 8px; height: 8px; border-radius: 50%; flex-shrink: 0; }
.col-header-label  { font-size: 11px; font-weight: 600; color: var(--ink-3); text-transform: uppercase; letter-spacing: 0.6px; }
.col-header-count  { font-family: 'Geist Mono', monospace; font-size: 11px; color: var(--ink-4); }
.col-header-hint   { margin-left: auto; font-size: 11px; color: var(--ink-4); }

/* Cards grid */
.cards-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(260px, 1fr)); gap: 10px; align-items: start; }
</style>