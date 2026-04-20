<template>
  <main class="main">

    <AppTopbar title="Vendors" :meta="headMeta">
      <template #actions>
        <div class="vendor-actions">
          <AppSearchbar v-model="searchQ" class="vendor-search" :placeholder="searchPlaceholder" />
          <FilterBar
            v-if="activeTab === 'list'"
            class="vendor-filterbar"
            v-model:lead-time="filterLeadTime"
            v-model:location="filterLocation"
            :locations="uniqueLocations"
          />
          <button class="btn btn-primary vendor-add-btn" @click="openAddVendor">+ Add Vendor</button>
        </div>
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
            v-if="tab.key === 'procurement'"
            class="tab-count"
            :class="{ active: activeTab === tab.key, 'tab-count-alert': procurementPendingCount > 0 }"
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
        :deleting="deletingVendorId === selectedVendor?.id"
        @back="goBackToList"
        @edit="openEditVendor"
        @delete="handleDeleteVendor"
      />
    </div>

    <!-- Part Search & Compare tab -->
    <div v-else-if="activeTab === 'compare'" class="tab-body tab-compare">
      <PartList
        :parts="filteredCompareParts"
        :loading="store.compareLoading"
        :error="store.compareError"
        :selected-part-id="selectedComparePartId"
        @select="handleComparePartSelect"
      />
      <PartDetailPanel
        :part="selectedComparePart"
        :selected-spec-key="selectedCompareSpecKey"
        :selection="store.compareSelection"
        :loading="store.compareSelectionLoading"
        :error="store.compareSelectionError"
        @select-spec="handleCompareSpecSelect"
        @select-vendor="handleVendorSelected"
      />
    </div>

    <!-- Procurement History tab -->
    <div v-else-if="activeTab === 'procurement'" class="tab-body tab-compare">
      <ProcurementHistory
        :procurements="store.procurements"
        :vendors="procurementVendors"
        :loading="store.procurementLoading"
        :error="store.procurementError"
        :selected-id="selectedProcurementId"
        :marking-received-id="markingReceivedId"
        @select="selectedProcurementId = $event"
        @mark-received="handleMarkReceived"
      />
    </div>

    <!-- Procurement Request Modal -->
    <ProcurementModal
      :visible="showProcurement"
      :vendors="procurementVendors"
      :prefill="procurementPrefill"
      :submitting="store.procurementSubmitting"
      @close="showProcurement = false"
      @submit="handleProcurement"
    />

    <AddVendorModal
      :visible="showVendorModal"
      :mode="vendorModalMode"
      :parts-catalog="store.compareParts"
      :parts-loading="store.compareLoading"
      :initial-vendor="vendorModalVendor"
      :saving="store.vendorSaving"
      :save-error="store.vendorSaveError"
      @close="closeVendorModal"
      @save="handleVendorSave"
    />

    <!-- Toast -->
    <AppToast ref="toast" />

  </main>
</template>

<script>
import { useVendorStore }  from './store.js'
import { useAuthStore }    from '../stores/auth'
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
import AddVendorModal      from './components/AddVendorModal.vue'

export default {
  name: 'VendorManagement',
  components: {
    AppTopbar, AppSearchbar, AppToast, FilterBar,
    VendorTable, VendorDetails, PartList, PartDetailPanel,
    ProcurementModal, ProcurementHistory, AddVendorModal
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
      selectedComparePartId: null,
      selectedCompareSpecKey: null,
      selectedVendorId: null,
      selectedProcurementId: null,
      markingReceivedId: null,
      deletingVendorId: null,
      showVendorModal: false,
      vendorModalMode: 'add',
      vendorModalVendor: null,

      showProcurement:    false,
      procurementPrefill: null,

      tabs: [
        { key: 'list',        label: 'Vendor List' },
        { key: 'details',     label: 'Vendor Details' },
        { key: 'compare',     label: 'Part Search & Compare' },
        { key: 'procurement', label: 'Procurement History' }
      ]
    }
  },

  mounted() {
    this.store.fetchVendorDirectory()
    this.store.fetchCompareCatalog()
    this.store.fetchCompareSearchCatalog()
    this.store.fetchProcurements()
  },

  computed: {
    headMeta() {
      if (this.activeTab === 'compare') {
        if (this.store.compareLoading) return 'Loading parts catalog...'
        return `${this.filteredCompareParts.length} Part${this.filteredCompareParts.length !== 1 ? 's' : ''}`
      }
      if (this.store.directoryLoading) return 'Loading vendor directory...'
      return `${this.store.activeVendorCount} Active Vendors`
    },
    pageSubtitle() {
      if (this.activeTab === 'compare') {
        if (this.store.compareLoading) return 'Loading parts...'
        return `${this.filteredCompareParts.length} parts in the catalog`
      }
      if (this.store.directoryLoading) return 'Loading vendors...'
      return `${this.store.activeVendorCount} Active Vendors`
    },
    searchPlaceholder() {
      if (this.activeTab === 'compare') return 'Search parts or specifications...'
      return 'Search vendors...'
    },
    uniqueLocations() {
      return [...new Set(this.store.directoryVendors.map(v => v.location).filter(Boolean))].sort()
    },
    procurementPendingCount() {
      return this.store.procurements.filter(r => r.status === 'pending').length
    },
    procurementVendors() {
      const combined = [...this.store.directoryVendors]
      for (const procurement of this.store.procurements) {
        if (!procurement.vendorId || combined.some((item) => item.id === procurement.vendorId)) {
          continue
        }
        combined.push({
          id: procurement.vendorId,
          name: procurement.vendorName || procurement.vendorId,
          prefix: '',
          leadTime: procurement.vendorLeadTime,
          location: procurement.vendorLocation || '—',
          contact: { phone: '—', email: '—' },
          parts: [],
          products: [],
          partCount: 0
        })
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
    filteredCompareParts() {
      let list = this.store.compareParts
      if (!this.searchQ) return list

      const q = this.searchQ.toLowerCase()
      return list.filter((part) => {
        const haystack = [
          part.name,
          ...(Array.isArray(part.sizes)
            ? part.sizes.flatMap((size) => [
              size.size,
              size.spec,
              size.specification,
              ...(Array.isArray(size.suppliers)
                ? size.suppliers.flatMap((supplier) => [supplier.vendor?.name, supplier.vendor?.location, supplier.skuId])
                : [])
            ])
            : [])
        ].filter(Boolean).join(' ').toLowerCase()
        return haystack.includes(q)
      })
    },
    selectedVendor() {
      return this.store.selectedDirectoryVendor
    },
    selectedComparePart() {
      if (!this.selectedComparePartId) return null
      return this.store.compareParts.find((part) => part.id === this.selectedComparePartId) || null
    }
  },

  watch: {
    '$route.params.vendorId': {
      immediate: true,
      handler(vendorId) {
        this.syncVendorRoute(typeof vendorId === 'string' ? vendorId : '')
      }
    },
    '$route.fullPath': {
      immediate: true,
      handler() {
        this.syncCompareRoute()
      }
    },
    'store.compareParts.length'() {
      this.syncCompareRoute()
    },
    'store.compareSkuEntries.length'() {
      this.syncCompareRoute()
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

    syncCompareRoute() {
      if (this.$route.params.vendorId) return

      const routeTab = typeof this.$route.query.tab === 'string' ? this.$route.query.tab : ''
      if (routeTab === 'procurement') {
        this.activeTab = 'procurement'
        this.selectedProcurementId = typeof this.$route.query.procurementId === 'string'
          ? this.$route.query.procurementId
          : null
        return
      }
      if (routeTab !== 'compare') return

      this.activeTab = 'compare'
      const routeSkuId = typeof this.$route.query.skuId === 'string' ? this.$route.query.skuId : ''
      if (routeSkuId) {
        const routeEntry = this.store.compareSkuEntries.find((entry) => entry.skuId === routeSkuId)
        if (routeEntry) {
          this.selectComparePart(routeEntry.pid, routeEntry.specKey)
        }
        return
      }

      const routePartId = typeof this.$route.query.partId === 'string' ? this.$route.query.partId : ''
      const routeSpecKey = typeof this.$route.query.specKey === 'string' ? this.$route.query.specKey : ''
      if (!routePartId || !routeSpecKey) {
        return
      }
      this.selectComparePart(routePartId, routeSpecKey)
    },

    goBackToList() {
      this.$router.push({ name: 'vendors' })
    },

    representativeSkuId(part, specKey) {
      const spec = Array.isArray(part?.sizes)
        ? part.sizes.find((size) => size.key === specKey)
        : null
      if (!spec) return ''

      const suppliers = Array.isArray(spec.suppliers) ? [...spec.suppliers] : []
      const pricedSuppliers = suppliers.filter((supplier) => typeof supplier.price === 'number')
      if (pricedSuppliers.length) {
        pricedSuppliers.sort((left, right) => left.price - right.price)
        return pricedSuppliers[0]?.skuId || ''
      }
      if (suppliers.length) {
        return suppliers[0]?.skuId || ''
      }

      const fallbackEntry = this.store.compareSkuEntries.find(
        (entry) => entry.pid === part.id && entry.specKey === specKey
      )
      return fallbackEntry?.skuId || ''
    },

    async selectCompareSpec(partId, specKey) {
      const normalizedPartId = String(partId || '').trim()
      const normalizedSpecKey = String(specKey || '').trim()
      if (!normalizedPartId || !normalizedSpecKey) return

      const part = this.store.compareParts.find((candidate) => candidate.id === normalizedPartId)
      if (!part) return

      this.selectedComparePartId = normalizedPartId
      this.selectedCompareSpecKey = normalizedSpecKey

      const skuId = this.representativeSkuId(part, normalizedSpecKey)
      if (!skuId) {
        this.store.clearCompareSelection()
        return
      }

      if (
        this.store.compareSelection?.sourceSku?.skuId === skuId
        && !this.store.compareSelectionError
      ) {
        return
      }

      try {
        await this.store.fetchCompareSelection(skuId)
      } catch {
        // The store already captures the error state for the panel.
      }
    },

    async selectComparePart(partId, preferredSpecKey = '') {
      const normalizedPartId = String(partId || '').trim()
      if (!normalizedPartId) return

      const part = this.store.compareParts.find((candidate) => candidate.id === normalizedPartId)
      if (!part) return

      this.selectedComparePartId = normalizedPartId
      const availableSizes = Array.isArray(part.sizes) ? part.sizes : []
      const nextSpecKey = preferredSpecKey && availableSizes.some((size) => size.key === preferredSpecKey)
        ? preferredSpecKey
        : availableSizes[0]?.key || ''

      if (!nextSpecKey) {
        this.selectedCompareSpecKey = null
        this.store.clearCompareSelection()
        return
      }

      await this.selectCompareSpec(normalizedPartId, nextSpecKey)
    },

    handleComparePartSelect(partId) {
      this.selectComparePart(partId, this.selectedComparePartId === partId ? this.selectedCompareSpecKey : '')
    },

    handleCompareSpecSelect(specKey) {
      if (!this.selectedComparePartId) return
      this.selectCompareSpec(this.selectedComparePartId, specKey)
    },

    openAddVendor() {
      this.store.vendorSaveError = ''
      this.vendorModalMode = 'add'
      this.vendorModalVendor = null
      this.showVendorModal = true
    },

    openEditVendor() {
      if (!this.selectedVendor) return
      this.store.vendorSaveError = ''
      this.vendorModalMode = 'edit'
      this.vendorModalVendor = this.selectedVendor
      this.showVendorModal = true
    },

    closeVendorModal() {
      this.store.vendorSaveError = ''
      this.showVendorModal = false
      this.vendorModalVendor = null
    },

    async handleVendorSave(formData) {
      try {
        const vendor = this.vendorModalMode === 'edit' && this.vendorModalVendor?.id
          ? await this.store.updateVendor(this.vendorModalVendor.id, formData)
          : await this.store.createVendor(formData)

        this.closeVendorModal()
        this.$router.push({ name: 'vendor-details', params: { vendorId: vendor.id } })
        this.$refs.toast.show(
          this.vendorModalMode === 'edit' ? '✓' : '+',
          this.vendorModalMode === 'edit' ? 'Vendor updated' : 'Vendor added',
          vendor.name
        )
      } catch (error) {
        this.$refs.toast.show(
          '!',
          this.vendorModalMode === 'edit' ? 'Unable to update vendor' : 'Unable to add vendor',
          error.message || 'Please try again'
        )
      }
    },

    async handleDeleteVendor() {
      const vendor = this.selectedVendor
      if (!vendor || this.deletingVendorId === vendor.id) return

      const shouldDelete = window.confirm(
        `Delete ${vendor.name}? This will remove the vendor and its mapped catalog entries.`
      )
      if (!shouldDelete) return

      this.deletingVendorId = vendor.id
      try {
        await this.deleteVendor(vendor.id)
        this.$router.push({ name: 'vendors' })
        this.$refs.toast.show('✓', 'Vendor deleted', vendor.name)
      } catch (error) {
        this.$refs.toast.show('!', 'Unable to delete vendor', error.message || 'Please try again')
      } finally {
        if (this.deletingVendorId === vendor.id) {
          this.deletingVendorId = null
        }
      }
    },

    async deleteVendor(vendorId) {
      if (typeof this.store.deleteVendor === 'function') {
        await this.store.deleteVendor(vendorId)
        return
      }

      const authStore = useAuthStore()
      await authStore.authenticatedRequest(`/api/vendors/${encodeURIComponent(vendorId)}`, {
        method: 'DELETE'
      })

      this.store.directoryVendors = this.store.directoryVendors.filter((vendor) => vendor.id !== String(vendorId))
      if (this.store.selectedDirectoryVendor?.id === String(vendorId)) {
        this.store.clearVendorDetails()
      }
      await Promise.all([
        this.store.fetchCompareCatalog(),
        this.store.fetchCompareSearchCatalog()
      ])
    },

    handleVendorSelected(selection) {
      this.procurementPrefill = {
        skuId: selection.skuId,
        partName: selection.partName,
        specification: selection.specification,
        vendorId: selection.vendorId,
        vendorName: selection.vendorName,
        currentBuy: selection.currentBuy,
        unitMeasurementBuy: selection.unitMeasurementBuy,
        lotSize: selection.lotSize
      }
      this.showProcurement = true
    },

    async handleProcurement(formData) {
      try {
        const procurement = await this.store.createProcurement({
          skuId: formData.skuId,
          vendorId: formData.vendorId,
          lotCount: formData.lotCount
        })
        this.showProcurement = false
        this.activeTab = 'procurement'
        this.selectedProcurementId = procurement.id
        this.$refs.toast.show('📋', `${procurement.id} submitted`, `${procurement.partName} → ${procurement.vendorName}`)
      } catch (error) {
        this.$refs.toast.show('!', 'Unable to submit request', error.message || 'Please try again')
      }
    },

    async handleMarkReceived(id) {
      if (!id || this.markingReceivedId === id) return

      this.markingReceivedId = id
      try {
        const procurement = await this.store.markReceived(id)
        this.selectedProcurementId = procurement.id
        this.$refs.toast.show('✓', 'Order received', procurement.id)
      } catch (error) {
        this.$refs.toast.show('!', 'Unable to update request', error.message || 'Please try again')
      } finally {
        if (this.markingReceivedId === id) {
          this.markingReceivedId = null
        }
      }
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
.vendor-actions {
  width: 100%;
  min-width: 0;
  display: flex;
  align-items: center;
  justify-content: flex-end;
  flex-wrap: wrap;
  gap: 6px;
}
.vendor-search {
  flex: 0 1 200px;
  min-width: 160px;
}
.vendor-filterbar {
  flex: 0 1 auto;
  min-width: 0;
}
.vendor-add-btn {
  flex-shrink: 0;
  white-space: nowrap;
}
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
