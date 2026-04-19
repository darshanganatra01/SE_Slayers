<template>
  <main class="main">
    <AppTopbar title="Rate Updater" meta="Map & update vendor price lists" />

    <div class="page-body">
      <!-- Upload Section -->
      <div v-if="!showReview" class="card upload-card">
        <h2 class="card-title">Start a New Update</h2>
        
        <form @submit.prevent="processUpload" class="upload-form">
          <div class="form-group">
            <label>Select Vendor</label>
            <select v-model="selectedVendor" required class="input-el">
              <option value="" disabled>-- Select a Vendor --</option>
              <option v-for="v in vendors" :key="v.vid" :value="v.vid">
                {{ v.vendor_name }} ({{ v.vid }})
              </option>
            </select>
          </div>

          <div class="form-group">
            <label>Vendor PDF Price List</label>
            <input type="file" @change="handleFileChange" accept="application/pdf" required class="file-input" />
          </div>
          
          <div class="form-actions">
            <button type="submit" class="btn btn-primary" :disabled="aiStore.isProcessing">
              {{ aiStore.isProcessing ? 'Processing...' : 'Process Vendor PDF' }}
            </button>
          </div>
        </form>
        
        <div v-if="aiStore.errorMsg" class="error-msg">{{ aiStore.errorMsg }}</div>
        <div v-if="aiStore.isProcessing && aiStore.jobStatusMessage" class="status-msg">
          <div class="status-text">{{ aiStore.jobStatusMessage }}</div>
          <div class="progress-bar-container">
            <div class="progress-bar"></div>
          </div>
        </div>
      </div>

      <!-- Review Section -->
      <div v-else class="review-section">
        <div class="page-head">
          <div class="head-top">
            <div>
              <div class="head-title">Review Price Updates</div>
              <div class="head-sub">Confirm the extracted prices before applying</div>
            </div>
            <div class="head-actions">
              <button @click="cancelReview" class="btn btn-outline" style="margin-right:8px;">← Back</button>
              <button @click="submitApprovals" :disabled="aiStore.selectedMatches.length === 0 || isUpdating" class="btn btn-primary">
                {{ isUpdating ? 'Saving...' : `Confirm before adding (${aiStore.selectedMatches.length})` }}
              </button>
            </div>
          </div>
          <div class="tabs">
            <button 
              v-for="tab in tabs" 
              :key="tab.status" 
              class="tab"
              :class="{ active: activeStatus === tab.status }"
              @click="activeStatus = tab.status"
            >
              <span class="tab-dot" :style="{ background: tab.color }"></span>
              {{ tab.label }}
              <span class="tab-count" :class="{ active: activeStatus === tab.status }">
                {{ groupCount(tab.status) }}
              </span>
            </button>
          </div>
        </div>

        <div class="table-wrap">
          <table class="data-table">
            <thead>
              <tr>
                <th v-if="activeStatus !== 'REJECT'" style="width:40px; text-align:center;">
                  <input type="checkbox" @change="toggleAll($event.target.checked)" :checked="isAllSelected" class="custom-chk" />
                </th>
                <th>SKU</th>
                <th>Product</th>
                <th>Specs</th>
                <th class="num-col">Old Price</th>
                <th class="num-col">New Price</th>
                <th class="num-col">Diff</th>
                <th v-if="activeStatus === 'FLAG_FOR_REVIEW'">Issues</th>
                <th v-if="activeStatus === 'REJECT'">Reason</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="m in visibleMatches" :key="m.sku_id">
                <td v-if="activeStatus !== 'REJECT'" style="text-align:center;">
                  <input type="checkbox" :value="m" v-model="aiStore.selectedMatches" class="custom-chk" />
                </td>
                <td class="fw-500">{{ m.sku_id }}</td>
                <td>{{ m.product_name }}</td>
                <td class="specs-cell">{{ formatSpecs(m.specs) }}</td>
                <td class="num-col">{{ formatPrice(m.current_price) }}</td>
                <td class="num-col fw-600" :class="m.price ? 'text-blue' : ''">{{ formatPrice(m.price) }}</td>
                <td class="num-col" :class="getDiffClass(m.change_pct)">
                  {{ formatChange(m.change_pct) }}
                </td>
                <td v-if="activeStatus === 'FLAG_FOR_REVIEW'" class="issues">
                  {{ m.issues.join(', ') || 'Low Confidence' }} (Conf: {{ m.confidence }}/10)
                </td>
                <td v-if="activeStatus === 'REJECT'" class="issues">{{ m.reason || 'No match found' }}</td>
              </tr>
              <tr v-if="visibleMatches.length === 0">
                <td colspan="8" class="empty-text">No records in this category.</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>

    <!-- Toast Notification -->
    <AppToast ref="toast" />
  </main>
</template>

<script setup>
import { ref, onMounted, computed, watch } from 'vue'
import AppTopbar from '../components/AppTopbar.vue'
import AppToast from '../components/AppToast.vue'
import { useAIStore } from '../stores/aiStore'

const aiStore = useAIStore()
const toast = ref(null)

const vendors = ref([])
const selectedVendor = ref('')
const pdfFile = ref(null)

const showReview = ref(aiStore.matches.length > 0)
const isUpdating = ref(false)
const activeStatus = ref('AUTO_ACCEPT')

const tabs = [
  { status: 'AUTO_ACCEPT', label: 'Auto Accept', color: '#10b981' },
  { status: 'FLAG_FOR_REVIEW', label: 'Needs Review', color: '#f59e0b' },
  { status: 'REJECT', label: 'Rejected', color: '#ef4444' }
]

onMounted(async () => {
  try {
    const token = localStorage.getItem('se_slayers.auth.token')
    const headers = token ? { Authorization: `Bearer ${token}` } : {}
    const res = await fetch('/api/ai-feature/vendors', { headers })
    const data = await res.json()
    if (res.ok) {
      vendors.value = data
    }
  } catch (e) {
    console.error("Error loading vendors", e)
  }

  // Ensure active status resets back properly if reviewing
  if (aiStore.matches.length > 0) {
    activeStatus.value = 'AUTO_ACCEPT'
  }
  
  if (aiStore.isProcessing && toast.value) {
    toast.value.show('⏳', 'Resuming', 'Job is still running in background...')
  }
})

// Watch for processing to finish
watch(() => aiStore.isProcessing, (newVal, oldVal) => {
  if (oldVal === true && newVal === false && !aiStore.errorMsg && aiStore.matches.length > 0) {
    showReview.value = true
    activeStatus.value = 'AUTO_ACCEPT'
    if (toast.value) {
      toast.value.show('✅', 'Extraction Complete', 'Matches are ready for review')
    }
  } else if (oldVal === true && newVal === false && aiStore.errorMsg) {
    if (toast.value) {
      toast.value.show('❌', 'Upload Failed', aiStore.errorMsg)
    }
  }
})

const handleFileChange = (e) => {
  if (e.target.files.length) {
    pdfFile.value = e.target.files[0]
  }
}

const processUpload = async () => {
  if (!selectedVendor.value || !pdfFile.value) {
    if(toast.value) toast.value.show('⚠️', 'Missing Data', 'Please select a vendor and PDF.')
    return
  }
  
  const started = await aiStore.startJob(selectedVendor.value, pdfFile.value)
  if (started && toast.value) {
    toast.value.show('⏳', 'Background Task Started', 'You can navigate away. Processing (~30s)...')
  }
}

const submitApprovals = async () => {
  if (!aiStore.selectedMatches.length) return
  
  isUpdating.value = true
  try {
    const token = localStorage.getItem('se_slayers.auth.token')
    const headers = {
      'Content-Type': 'application/json',
      ...(token ? { 'Authorization': `Bearer ${token}` } : {})
    }
    const res = await fetch('/api/ai-feature/confirm', {
      method: 'POST',
      headers,
      body: JSON.stringify({
        approved_matches: aiStore.selectedMatches
      })
    })
    
    if (res.ok) {
      if (toast.value) toast.value.show('✓', 'Success', 'Successfully updated prices!')
      showReview.value = false
      pdfFile.value = null
      aiStore.resetState()
    } else {
      if (toast.value) toast.value.show('❌', 'Error', 'Failed to confirm updates.')
    }
  } catch (e) {
    if (toast.value) toast.value.show('❌', 'Error', 'Communicating with server.')
    console.error(e)
  } finally {
    isUpdating.value = false
  }
}

const cancelReview = () => {
  showReview.value = false
  pdfFile.value = null
  aiStore.resetState()
}

// Groupings
const groupCount = (status) => aiStore.matches.filter(m => m.action === status).length

const visibleMatches = computed(() => {
  return aiStore.matches.filter(m => m.action === activeStatus.value)
})

const isAllSelected = computed(() => {
  const currentTabMatches = visibleMatches.value
  if (!currentTabMatches.length) return false
  return currentTabMatches.every(m => aiStore.selectedMatches.some(s => s.sku_id === m.sku_id))
})

const toggleAll = (isChecked) => {
  const currentTabMatches = visibleMatches.value
  if (isChecked) {
    const newAdditions = currentTabMatches.filter(m => !aiStore.selectedMatches.some(s => s.sku_id === m.sku_id))
    aiStore.selectedMatches = [...aiStore.selectedMatches, ...newAdditions]
  } else {
    aiStore.selectedMatches = aiStore.selectedMatches.filter(s => s.action !== activeStatus.value)
  }
}

const formatPrice = (val) => {
  if (val === null || val === undefined || val === '') return '—'
  return `₹${parseFloat(val).toFixed(2)}`
}

const formatChange = (val) => {
  if (val === null || val === undefined) return '—'
  const num = parseFloat(val)
  return `${num > 0 ? '+' : ''}${num.toFixed(1)}%`
}

const getDiffClass = (val) => {
  if (!val) return ''
  const num = parseFloat(val)
  if (Math.abs(num) > 30) return 'text-red fw-600'
  if (num > 0) return 'text-red'
  if (num < 0) return 'text-green'
  return ''
}

const formatSpecs = (rawSpecs) => {
  if (!rawSpecs) return '—'
  try {
    const parsed = typeof rawSpecs === 'string' ? JSON.parse(rawSpecs) : rawSpecs
    if (!parsed || Object.keys(parsed).length === 0) return '—'
    return Object.values(parsed).join('\n')
  } catch(e) {
    return rawSpecs
  }
}
</script>

<style scoped>
.main { flex: 1; display: flex; flex-direction: column; overflow: hidden; background: var(--bg); }
.page-body { flex: 1; overflow-y: auto; padding: 20px; display: flex; flex-direction: column; }

/* Custom Inputs & Forms */
.card { background: var(--white); border: 1.5px solid var(--border); border-radius: 8px; padding: 24px; max-width: 600px; margin: 0 auto; margin-top: 40px; box-shadow: 0 1px 3px rgba(0,0,0,0.02); }
.upload-card { width: 100%; }
.card-title { font-size: 16px; font-weight: 600; color: var(--ink); margin-bottom: 20px; letter-spacing: -0.2px; }

.form-group { margin-bottom: 20px; }
.form-group label { display: block; font-size: 12px; font-weight: 500; color: var(--ink-3); margin-bottom: 8px; text-transform: uppercase; letter-spacing: 0.5px;}
.input-el { width: 100%; padding: 10px 12px; border: 1.5px solid var(--border-2); border-radius: 6px; font-family: 'Geist', sans-serif; font-size: 14px; color: var(--ink); outline: none; transition: border-color 0.2s; background: var(--white); }
.input-el:focus { border-color: var(--blue); }

.file-input { display: block; width: 100%; font-size: 13px; color: var(--ink-3); }
.file-input::file-selector-button { margin-right: 12px; padding: 8px 16px; border-radius: 6px; border: 1.5px solid var(--border-2); background: var(--surface); color: var(--ink-2); font-weight: 500; font-family: 'Geist', sans-serif; cursor: pointer; transition: background 0.15s; }
.file-input::file-selector-button:hover { background: var(--border); }

.form-actions { margin-top: 30px; display: flex; justify-content: flex-end; padding-top: 20px; border-top: 1px dashed var(--border-2); }
.error-msg { margin-top: 16px; padding: 12px; background: #fee2e2; border: 1.5px solid #fca5a5; border-radius: 6px; color: #b91c1c; font-size: 13px; font-weight: 500; }

/* Page head (matches order_management) */
.review-section { display: flex; flex-direction: column; flex: 1; }
.page-head { background: var(--white); border: 1.5px solid var(--border); border-bottom: none; border-radius: 8px 8px 0 0; padding: 16px 22px 0; }
.head-top { display: flex; align-items: center; justify-content: space-between; margin-bottom: 14px; }
.head-title { font-size: 18px; font-weight: 600; color: var(--ink); letter-spacing: -0.4px; }
.head-sub { font-size: 12.5px; color: var(--ink-4); margin-top: 2px; }

/* Tabs */
.tabs { display: flex; align-items: stretch; border-bottom: 1.5px solid var(--border); margin: 0 -22px; padding: 0 22px; }
.tab { display: flex; align-items: center; gap: 6px; padding: 10px 16px; border: none; background: transparent; cursor: pointer; color: var(--ink-4); font-family: 'Geist', sans-serif; font-size: 13px; font-weight: 500; border-bottom: 2px solid transparent; transition: all 0.12s; position: relative; top: 1.5px; }
.tab:hover:not(.active) { color: var(--ink-2); }
.tab.active { color: var(--ink); border-bottom-color: var(--blue); font-weight: 600; }
.tab-dot { width: 8px; height: 8px; border-radius: 50%; flex-shrink: 0; }
.tab-count { font-family: 'Geist Mono', monospace; font-size: 11px; background: var(--surface); border: 1px solid var(--border-2); border-radius: 10px; padding: 0 6px; color: var(--ink-4); line-height: 1.8; }
.tab-count.active { background: var(--blue); color: #fff; border-color: var(--blue); }

/* Table */
.table-wrap { background: var(--white); border: 1.5px solid var(--border); border-top: none; border-radius: 0 0 8px 8px; overflow-x: auto; flex: 1; }
.data-table { width: 100%; border-collapse: collapse; text-align: left; }
.data-table th { background: var(--surface); padding: 12px 16px; font-size: 11px; font-weight: 600; color: var(--ink-3); text-transform: uppercase; letter-spacing: 0.6px; border-bottom: 1.5px solid var(--border-2); white-space: nowrap; }
.data-table td { padding: 14px 16px; font-size: 13.5px; color: var(--ink-2); border-bottom: 1px solid var(--border); vertical-align: middle; }
.data-table tr:last-child td { border-bottom: none; }
.data-table tr:-webkit-any(:hover) td { background: var(--bg); }
.data-table tr:hover td { background: var(--bg); }

.num-col { text-align: right; }
.fw-500 { font-weight: 500; color: var(--ink); }
.fw-600 { font-weight: 600; }
.text-blue { color: var(--blue); }
.text-red { color: #dc2626; }
.text-green { color: #16a34a; }

.specs-cell { font-family: 'Geist Mono', monospace; font-size: 12px; color: var(--ink-3); white-space: pre-line; padding-top: 8px; padding-bottom: 8px; line-height: 1.5; }
.issues { font-size: 12px; color: #d97706; font-weight: 500; }
.empty-text { text-align: center; color: var(--ink-4); font-size: 14px; padding: 40px !important; }

/* Checkbox */
.custom-chk { width: 16px; height: 16px; border: 1.5px solid var(--border-2); border-radius: 4px; cursor: pointer; accent-color: var(--blue); }

/* Buttons */
.btn { padding: 8px 16px; border-radius: 6px; font-size: 13px; font-weight: 500; cursor: pointer; font-family: 'Geist', sans-serif; transition: all 0.15s; border: none; }
.btn:disabled { opacity: 0.5; cursor: not-allowed; }
.btn-primary { background: var(--blue); color: #fff; }
.btn-primary:hover:not(:disabled) { background: #1d4ed8; }
.btn-outline { background: var(--white); color: var(--ink-2); border: 1.5px solid var(--border); }
.btn-outline:hover:not(:disabled) { background: var(--surface); color: var(--ink); }

/* Progress bar */
.status-msg { margin-top: 16px; padding: 14px; background: var(--blue-dim, #eff6ff); border: 1.5px solid var(--border-2); border-radius: 6px; }
.status-text { color: var(--blue); font-size: 13px; font-weight: 600; font-family: 'Geist', sans-serif; margin-bottom: 10px; }
.progress-bar-container { width: 100%; height: 4px; background-color: var(--surface); border-radius: 2px; overflow: hidden; }
.progress-bar { width: 100%; height: 100%; background-color: var(--blue); animation: indeterminate 1.5s infinite linear; transform-origin: 0% 50%; }

@keyframes indeterminate {
  0% { transform: translateX(-100%) scaleX(0.2); }
  50% { transform: translateX(0%) scaleX(0.5); }
  100% { transform: translateX(200%) scaleX(0.2); }
}
</style>
