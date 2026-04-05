import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useAIStore = defineStore('aiFeature', () => {
  const matches = ref([])
  const selectedMatches = ref([])
  const jobId = ref(null)
  const isProcessing = ref(false)
  const jobStatusMessage = ref('')
  const errorMsg = ref('')
  
  let pollingInterval = null

  const setMatches = (data) => {
    matches.value = data
  }

  const startJob = async (vendorId, pdfFile) => {
    isProcessing.value = true
    errorMsg.value = ''
    jobStatusMessage.value = 'Uploading file...'
    matches.value = []
    selectedMatches.value = []

    const formData = new FormData()
    formData.append('vendor_id', vendorId)
    formData.append('pdf', pdfFile)

    try {
      const res = await fetch('/api/ai-feature/upload', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token') || ''}`
        },
        body: formData
      })
      
      const data = await res.json()
      if (!res.ok) {
        errorMsg.value = data.error || 'Upload failed'
        isProcessing.value = false
        return false
      }
      
      jobId.value = data.job_id
      startPolling()
      return true
    } catch (e) {
      errorMsg.value = 'Failed to communicate with server.'
      isProcessing.value = false
      return false
    }
  }

  const startPolling = () => {
    if (pollingInterval) clearInterval(pollingInterval)
    
    pollingInterval = setInterval(async () => {
      if (!jobId.value) {
        clearInterval(pollingInterval)
        return
      }

      try {
        const res = await fetch(`/api/ai-feature/status/${jobId.value}`, {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('token') || ''}`
          }
        })
        const data = await res.json()
        
        if (data.state === 'SUCCESS') {
          clearInterval(pollingInterval)
          if (data.matches) {
             matches.value = data.matches
             selectedMatches.value = data.matches.filter(m => m.action === 'AUTO_ACCEPT')
             isProcessing.value = false
             jobStatusMessage.value = 'Complete!'
             jobId.value = null
          }
        } else if (data.state === 'FAILURE' || data.state === 'ERROR') {
          clearInterval(pollingInterval)
          errorMsg.value = data.message || 'Background task failed.'
          isProcessing.value = false
          jobId.value = null
        } else {
          // PROGRESS
          jobStatusMessage.value = data.message || 'Processing...'
        }
      } catch (e) {
        // Keep trying unless it completely crashes
        console.error("Polling error", e)
      }
    }, 2000)
  }

  const resetState = () => {
    matches.value = []
    selectedMatches.value = []
    jobId.value = null
    isProcessing.value = false
    jobStatusMessage.value = ''
    errorMsg.value = ''
    if (pollingInterval) clearInterval(pollingInterval)
  }

  return {
    matches,
    selectedMatches,
    jobId,
    isProcessing,
    jobStatusMessage,
    errorMsg,
    startJob,
    setMatches,
    resetState
  }
})
