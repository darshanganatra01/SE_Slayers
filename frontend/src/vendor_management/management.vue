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
        <button class="btn btn-primary" @click="notifyAddVendorComingSoon">+ Add Vendor</button>
      </template>
    </AppTopbar>

    <!-- Page head with tabs -->
    <div class="page-head">
      <div class="head-top">
        <div>
          <div class="head-title">Vendors</div>
          <div class="head-sub">{{ pageSubtitle }}</div>
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
      <div v-if="store.directoryError" class="vendor-error">{{ store.directoryError }}</div>
      <VendorTable :vendors="filteredVendors" :loading="store.directoryLoading" @select="selectVendor" />
    </div>

    <!-- Vendor Details tab -->
    <div v-else-if="activeTab === 'details'" class="tab-body">
      <VendorDetails
        :vendor="selectedVendor"
        :loading="store.vendorDetailLoading"
        :error="store.vendorDetailError"
        @back="goBackToList"
      />
    </div>

    <!-- Part Search & Compare tab -->
    <div v-else-if="activeTab === 'compare'" class="tab-body tab-compare">
      <PartList
        :parts="store.compareParts"
        :loading="store.compareLoading"
        :error="store.compareError"
        :selected-part-id="selectedPartId"
        @select="selectedPartId = $event"
      />
      <PartDetailPanel
        :part="selectedPart"
        @select-vendor="handleVendorSelected"
      />
    </div>

    <!-- Procurement History tab -->
    <div v-else-if="activeTab === 'procurement'" class="tab-body tab-compare">
      <ProcurementHistory
        :procurements="store.procurements"
        :vendors="procurementVendors"
        :selected-id="selectedProcurementId"
        @select="selectedProcurementId = $event"
        @mark-received="handleMarkReceived"
      />
    </div>

    <!-- Procurement Request Modal -->
    <ProcurementModal
      :visible="showProcurement"
      :vendors="procurementVendors"
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
import ProcurementModal    from './components/ProcurementModal.vue'
import ProcurementHistory  from './components/ProcurementHistory.vue'

export default {
  name: 'VendorManagement',
  components: {
    AppTopbar, AppSearchbar, AppToast, FilterBar,
    VendorTable, VendorDetails, PartList, PartDetailPanel,
    ProcurementModal, ProcurementHistory
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

  mounted() {
    this.store.fetchVendorDirectory()
    this.store.fetchCompareCatalog()
  },

  computed: {
    headMeta() {
      if (this.store.directoryLoading) return 'Loading vendor directory...'
      return `${this.store.activeVendorCount} Active Vendors`
    },
    pageSubtitle() {
      if (this.store.directoryLoading) return 'Loading vendors...'
      return `${this.store.activeVendorCount} Active Vendors`
    },
    uniqueLocations() {
      return [...new Set(this.store.directoryVendors.map(v => v.location).filter(Boolean))].sort()
    },
    procurementPendingCount() {
      return this.store.procurements.filter(r => r.status === 'pending').length
    },
    procurementVendors() {
      const combined = [...this.store.directoryVendors]
      for (const vendor of this.store.vendors) {
        if (!combined.some(item => item.id === vendor.id)) {
          combined.push(vendor)
        }
      }
      return combined
    },
    filteredVendors() {
      let list = this.store.directoryVendors
      if (this.searchQ) {
        const q = this.searchQ.toLowerCase()
        list = list.filter(v =>
          v.name.toLowerCase().includes(q) || v.id.toLowerCase().includes(q)
        )
      }
      if (this.filterLeadTime !== 'all') {
        if (this.filterLeadTime === 'fast') list = list.filter(v => v.leadTime != null && v.leadTime <= 3)
        else if (this.filterLeadTime === 'medium') list = list.filter(v => v.leadTime != null && v.leadTime >= 4 && v.leadTime <= 7)
        else if (this.filterLeadTime === 'slow') list = list.filter(v => v.leadTime != null && v.leadTime > 7)
      }
      if (this.filterLocation !== 'all') {
        list = list.filter(v => v.location === this.filterLocation)
      }
      return list
    },
    selectedVendor() {
      return this.store.selectedDirectoryVendor
    },
    selectedPart() {
      if (!this.selectedPartId) return null
      return this.store.compareParts.find(p => p.id === this.selectedPartId) || null
    }
  },

  watch: {
    '$route.params.vendorId': {
      immediate: true,
      handler(vendorId) {
        this.syncVendorRoute(typeof vendorId === 'string' ? vendorId : '')
      }
    }
  },

  methods: {
    switchTab(key) {
      this.activeTab = key
      if (key !== 'details') {
        this.selectedVendorId = null
        this.store.clearVendorDetails()
        if (this.$route.params.vendorId) {
          this.$router.push({ name: 'vendors' })
        }
      }
      if (key !== 'procurement') this.selectedProcurementId = null
    },

    selectVendor(vendorId) {
      if (!vendorId) return
      this.$router.push({ name: 'vendor-details', params: { vendorId } })
    },

    async syncVendorRoute(vendorId) {
      this.selectedVendorId = vendorId || null

      if (this.selectedVendorId) {
        this.activeTab = 'details'
        await this.store.fetchVendorDetails(this.selectedVendorId)
        return
      }

      this.store.clearVendorDetails()
      if (this.activeTab === 'details') {
        this.activeTab = 'list'
      }
    },

    goBackToList() {
      this.$router.push({ name: 'vendors' })
    },

    notifyAddVendorComingSoon() {
      this.$refs.toast.show('+', 'Vendor creation will be added later', 'This screen now uses live vendor data')
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

    handleProcurement(formData) {
      const newId = this.store.addProcurement(formData, formData.vendorId)
      this.showProcurement = false
      const vendorName = formData.vendorId
        ? (this.store.findDirectoryVendorById(formData.vendorId)?.name || this.store.findVendorById(formData.vendorId)?.name || formData.vendorId)
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
.vendor-error {
  margin-bottom: 14px;
  padding: 12px 14px;
  border: 1.5px solid #fca5a5;
  background: #fee2e2;
  color: #b91c1c;
  border-radius: 8px;
  font-size: 13px;
}
</style>
