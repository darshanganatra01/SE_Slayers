<template>
  <main class="main">

    <AppTopbar title="Vendors" :meta="headMeta">
      <template #actions>
        <AppSearchbar v-model="searchQ" placeholder="Search vendors…" />
        <FilterBar
          v-if="activeTab === 'list'"
          v-model:lead-time="filterLeadTime"
          v-model:location="filterLocation"
          :locations="uniqueLocations"
        />
        <button class="btn btn-primary" @click="showAddVendor = true">+ Add Vendor</button>
      </template>
    </AppTopbar>

    <!-- Page head with tabs -->
    <div class="page-head">
      <div class="head-top">
        <div>
          <div class="head-title">Vendors</div>
          <div class="head-sub">{{ store.activeVendorCount }} Active Vendors</div>
        </div>
      </div>
      <div class="tabs">
        <button
          v-for="tab in tabs"
          :key="tab.key"
          class="tab"
          :class="{ active: activeTab === tab.key }"
          @click="switchTab(tab.key)"
        >
          {{ tab.label }}
          <span
            class="tab-count"
            :class="{ active: activeTab === tab.key, 'tab-count-alert': tab.key === 'procurement' && procurementPendingCount > 0 }"
          >
            {{ tab.key === 'procurement' ? procurementPendingCount : tab.count }}
          </span>
        </button>
      </div>
    </div>

    <!-- Vendor List tab -->
    <div v-if="activeTab === 'list'" class="tab-body tab-list">
      <VendorTable :vendors="filteredVendors" @select="selectVendor" />
    </div>

    <!-- Vendor Details tab -->
    <div v-else-if="activeTab === 'details'" class="tab-body">
      <VendorDetails
        :vendor="selectedVendor"
        @back="switchTab('list')"
      />
    </div>

    <!-- Part Search & Compare tab -->
    <div v-else-if="activeTab === 'compare'" class="tab-body tab-compare">
      <PartList
        :parts="store.parts"
        :selected-part-id="selectedPartId"
        @select="selectedPartId = $event"
      />
      <PartDetailPanel
        :part="selectedPart"
        :vendors="store.vendors"
        @select-vendor="handleVendorSelected"
      />
    </div>

    <!-- Procurement History tab -->
    <div v-else-if="activeTab === 'procurement'" class="tab-body tab-compare">
      <ProcurementHistory
        :procurements="store.procurements"
        :vendors="store.vendors"
        :selected-id="selectedProcurementId"
        @select="selectedProcurementId = $event"
        @mark-received="handleMarkReceived"
      />
    </div>

    <!-- Add Vendor Modal -->
    <AddVendorModal
      :visible="showAddVendor"
      @close="showAddVendor = false"
      @submit="handleAddVendor"
    />

    <!-- Procurement Request Modal -->
    <ProcurementModal
      :visible="showProcurement"
      :vendors="store.vendors"
      :prefill="procurementPrefill"
      @close="showProcurement = false"
      @submit="handleProcurement"
    />

    <!-- Toast -->
    <AppToast ref="toast" />

  </main>
</template>

<script>
import { useVendorStore }  from './store.js'
import AppTopbar           from '../components/AppTopbar.vue'
import AppSearchbar        from '../components/AppSearchbar.vue'
import AppToast            from '../components/AppToast.vue'
import FilterBar           from './components/FilterBar.vue'
import VendorTable         from './components/VendorTable.vue'
import VendorDetails       from './components/VendorDetails.vue'
import PartList            from './components/PartList.vue'
import PartDetailPanel     from './components/PartDetailPanel.vue'
import AddVendorModal      from './components/AddVendorModal.vue'
import ProcurementModal    from './components/ProcurementModal.vue'
import ProcurementHistory  from './components/ProcurementHistory.vue'

export default {
  name: 'VendorManagement',
  components: {
    AppTopbar, AppSearchbar, AppToast, FilterBar,
    VendorTable, VendorDetails, PartList, PartDetailPanel,
    AddVendorModal, ProcurementModal, ProcurementHistory
  },

  setup() {
    const store = useVendorStore()
    return { store }
  },

  data() {
    return {
      activeTab: 'list',
      searchQ: '',
      filterLeadTime: 'all',
      filterLocation: 'all',
      selectedPartId: null,
      selectedVendorId: null,
      selectedProcurementId: null,

      showAddVendor:      false,
      showProcurement:    false,
      procurementPrefill: null,

      tabs: [
        { key: 'list',        label: 'Vendor List',           count: '—' },
        { key: 'details',     label: 'Vendor Details',        count: '—' },
        { key: 'compare',     label: 'Part Search & Compare', count: '—' },
        { key: 'procurement', label: 'Procurement History',   count: '—' }
      ]
    }
  },

  computed: {
    headMeta() {
      return `${this.store.activeVendorCount} Active Vendors`
    },
    uniqueLocations() {
      return [...new Set(this.store.vendors.map(v => v.location))].sort()
    },
    procurementPendingCount() {
      return this.store.procurements.filter(r => r.status === 'pending').length
    },
    filteredVendors() {
      let list = this.store.vendors
      if (this.searchQ) {
        const q = this.searchQ.toLowerCase()
        list = list.filter(v =>
          v.name.toLowerCase().includes(q) || v.id.toLowerCase().includes(q)
        )
      }
      if (this.filterLeadTime !== 'all') {
        if (this.filterLeadTime === 'fast')        list = list.filter(v => v.leadTime <= 3)
        else if (this.filterLeadTime === 'medium') list = list.filter(v => v.leadTime >= 4 && v.leadTime <= 7)
        else if (this.filterLeadTime === 'slow')   list = list.filter(v => v.leadTime > 7)
      }
      if (this.filterLocation !== 'all') {
        list = list.filter(v => v.location === this.filterLocation)
      }
      return list
    },
    selectedVendor() {
      if (!this.selectedVendorId) return null
      return this.store.findVendorById(this.selectedVendorId) || null
    },
    selectedPart() {
      if (!this.selectedPartId) return null
      return this.store.parts.find(p => p.id === this.selectedPartId) || null
    }
  },

  methods: {
    switchTab(key) {
      this.activeTab = key
      if (key !== 'details') this.selectedVendorId = null
      if (key !== 'procurement') this.selectedProcurementId = null
    },

    selectVendor(vendorId) {
      this.selectedVendorId = vendorId
      this.activeTab = 'details'
    },

    // Called when user picks a vendor in PartDetailPanel → open procurement form
    handleVendorSelected({ part, size, vendorId }) {
      this.procurementPrefill = {
        partName: part.name,
        partCode: size,
        vendorId: vendorId
      }
      this.showProcurement = true
    },

    handleAddVendor(formData) {
      const newVendor = {
        id:        formData.id || 'VND-' + String(this.store.vendors.length + 1).padStart(3, '0'),
        name:      formData.name || 'New Vendor',
        leadTime:  formData.leadTime || 3,
        frequency: 'Weekly',
        location:  formData.location || 'Unknown',
        rating:    4.0,
        parts:     formData.parts ? formData.parts.split(',').map(s => s.trim()).filter(Boolean) : [],
        contact:   { phone: formData.phone || '', email: formData.email || '' }
      }
      this.store.vendors.push(newVendor)
      this.showAddVendor = false
      this.$refs.toast.show('✓', `${newVendor.name} added`, newVendor.id)
    },

    handleProcurement(formData) {
      const newId = this.store.addProcurement(formData, formData.vendorId)
      this.showProcurement = false
      const vendorName = formData.vendorId
        ? (this.store.findVendorById(formData.vendorId)?.name || formData.vendorId)
        : '—'
      this.$refs.toast.show('📋', `${newId} submitted`, `${formData.partName} → ${vendorName}`)
    },

    handleMarkReceived(id) {
      this.store.markReceived(id)
      this.$refs.toast.show('✓', 'Order received', id)
    }
  }
}
</script>

<style scoped>
.main { flex: 1; display: flex; flex-direction: column; overflow: hidden; background: var(--bg); }

.page-head  { background: var(--white); border-bottom: 1.5px solid var(--border); flex-shrink: 0; padding: 14px 22px 0; }
.head-top   { display: flex; align-items: center; justify-content: space-between; margin-bottom: 14px; }
.head-title { font-size: 18px; font-weight: 600; color: var(--ink); letter-spacing: -0.4px; }
.head-sub   { font-size: 11.5px; color: var(--ink-4); font-family: 'Geist Mono', monospace; margin-top: 2px; }

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
.tab-count {
  font-family: 'Geist Mono', monospace; font-size: 10px;
  background: var(--surface); border: 1px solid var(--border-2);
  border-radius: 10px; padding: 0 6px; color: var(--ink-4); line-height: 1.8;
}
.tab-count.active { background: var(--blue); color: #fff; border-color: var(--blue); }
.tab-count-alert  { background: var(--amber-dim) !important; color: var(--amber) !important; border-color: var(--amber) !important; }

.tab-body    { flex: 1; overflow-y: auto; }
.tab-list    { padding: 18px 22px; }
.tab-compare { display: flex; overflow: hidden; }
</style>
