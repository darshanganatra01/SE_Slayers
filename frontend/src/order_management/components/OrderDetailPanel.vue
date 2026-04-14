<template>
  <div class="dp" :class="{ open: !!order }">
    <template v-if="order">

      <div class="dp-head">
        <div class="dp-close-row">
          <div class="dp-oid">{{ order.id }}</div>
          <button class="dp-close-btn" @click="$emit('close')">Close ✕</button>
        </div>
        <div class="dp-name">{{ order.shop }}</div>
        <div class="dp-chips-row">
          <span class="chip" :style="{ background: PB[order.priority], color: PC[order.priority] }">{{ order.priority }} Priority</span>
        </div>
      </div>

      <div class="dp-scroll">

        <div>
          <div class="dp-sec-label">Details</div>
          <div class="dp-kv"><span class="k">Value</span>          <span class="v" style="color:var(--green)">{{ order.value }}</span></div>
          <div class="dp-kv"><span class="k">Order Placed on</span> <span class="v">{{ order.placedOn }}</span></div>
          <div class="dp-kv"><span class="k">Customer</span>       <span class="v">{{ order.customer }}</span></div>
          <div class="dp-kv"><span class="k">Status</span>         <span class="v" :style="{ color: SC[order.status] }">{{ SL[order.status] }}</span></div>
        </div>

        <div>
          <div class="dp-sec-label">Items ({{ order.items.length }})</div>
          <div v-for="(it, i) in order.items" :key="i" class="dp-item-row">
            <div class="dp-item-info">
              <div class="dp-item-name">{{ it.name }}</div>
              <div v-if="it.specs" class="dp-item-specs">{{ it.specs }}</div>
            </div>
            <span class="item-qty">
              Qty: {{ it.qty || 1 }}
              <span v-if="it.originalQty && it.qty !== it.originalQty" class="qty-changed">
                (was {{ it.originalQty }})
              </span>
            </span>
          </div>
        </div>


        <div v-if="order.status === 'shipped' && (!order.packing_slips || !order.packing_slips.length)">
          <div class="dp-sec-label">Shipping</div>
          <div class="dp-kv"><span class="k">Carrier</span> <span class="v">{{ order.transport || '—' }}</span></div>
        </div>

      </div>

      <div class="dp-footer">
        <div class="dp-flow-label">Status flow</div>
        <div class="dp-flow">
          <template v-for="(s, i) in steps" :key="s">
            <div class="df-step" :class="{ done: i < currentStep, current: i === currentStep }">{{ SL[s] }}</div>
            <div v-if="i < steps.length - 1" class="df-arrow">›</div>
          </template>
        </div>
        <button
          v-if="order.status === 'inprocess'"
          class="dp-action-btn dp-btn-fwd"
          @click="onForwardClick"
        >
          → Mark as {{ SL[nextStatus] }}
        </button>
        <template v-if="order.status === 'packed'">
          <button
            class="dp-action-btn dp-btn-fwd"
            :disabled="isShipping"
            @click="confirmShipAndInvoice"
          >
            {{ isShipping ? 'Shipping…' : '→ Move to Shipped & Send Invoice' }}
          </button>
          <button
            class="dp-action-btn dp-btn-back"
            @click="onBackClick"
          >
            ← Back to {{ SL[prevStatus] }}
          </button>
        </template>
        <button
          v-if="order.status === 'shipped'"
          class="dp-action-btn"
          :class="order.is_received ? 'dp-btn-back' : 'dp-btn-fwd'"
          :disabled="order.is_received || isMarkingReceived"
          @click="handleMarkReceived"
        >
          <span v-if="order.is_received">✓ Order Received</span>
          <span v-else>{{ isMarkingReceived ? 'Processing...' : '→ Mark as Received' }}</span>
        </button>
      </div>

    </template>
  </div>

  <!-- Packing modal -->
  <PackingModal
    :visible="showPackingModal"
    :order-id="order?.id"
    :items="order?.items || []"
    @cancel="showPackingModal = false"
    @confirm="confirmPack"
  />

  <!-- Transport modal -->
  <teleport to="body">
    <div v-if="showTransportModal" class="tr-overlay" @click.self="showTransportModal = false">
      <div class="tr-box">
        <div class="tr-head">
          <div class="tr-title">Select Transport</div>
          <button class="dp-close-btn" @click="showTransportModal = false">✕</button>
        </div>
        <div class="tr-body">
          <div class="fg">
            <label class="fl">Carrier</label>
            <select class="fi" v-model="selectedTransport">
              <option value="">Select carrier…</option>
              <option>BlueDart Express</option>
              <option>DTDC Courier</option>
              <option>Delhivery</option>
              <option>Ekart Logistics</option>
              <option>India Post</option>
              <option>Shadowfax</option>
              <option>Xpressbees</option>
            </select>
          </div>
        </div>
        <div class="tr-foot">
          <button class="btn-cancel" @click="showTransportModal = false">Cancel</button>
          <button class="btn btn-primary" :disabled="!selectedTransport" @click="confirmShipAndInvoice">Move to Shipped & Send Invoice</button>
        </div>
      </div>
    </div>
  </teleport>
</template>

<script>
import { CC, CB, CL, PC, PB, SC, SL, useOrderStore } from '../store.js'
import { useAuthStore } from '@/stores/auth'
import PackingModal from './Packingmodal.vue'

export default {
  name: 'OrderDetailPanel',
  components: { PackingModal },
  props: {
    order: { type: Object, default: null }
  },
  emits: ['close', 'promote'],
  data() {
    return {
      CC, CB, CL, PC, PB, SC, SL,
      steps: ['inprocess', 'packed', 'shipped'],
      showPackingModal:   false,
      selectedTransport:  '',
      isMarkingReceived: false,
      isShipping: false
    }
  },
  setup() {
    const store = useOrderStore();
    return { store };
  },
  computed: {
    currentStep() { return this.steps.indexOf(this.order?.status) },
    nextStatus()  { return this.steps[this.currentStep + 1] },
    prevStatus()  { return this.steps[this.currentStep - 1] }
  },
  methods: {
    async onBackClick() {
      if (this.order.status === 'packed' && this.order.pslip_ids) {
        if (!confirm('Are you sure you want to unpack this order?')) return
        for (const pslip_id of this.order.pslip_ids) {
          await this.store.unpack(pslip_id)
        }
      } else {
        this.$emit('promote', { id: this.order.id, newStatus: this.prevStatus })
      }
    },
    onForwardClick() {
      if (this.nextStatus === 'packed') {
        this.showPackingModal = true
      } else {
        this.$emit('promote', { id: this.order.id, newStatus: this.nextStatus })
      }
    },
    confirmPack(updatedItems) {
      this.$emit('promote', {
        id: this.order.id,
        newStatus: 'packed',
        updatedItems
      })
      this.showPackingModal = false
    },
    async confirmShipAndInvoice() {
      const pslip_ids = this.order.pslip_ids || []
      if (pslip_ids.length === 0) {
        alert('No packed items to ship.')
        return
      }

      this.isShipping = true
      // Save a snapshot before async refresh replaces the order
      const orderSnapshot = JSON.parse(JSON.stringify(this.order))

      try {
        for (const pslip_id of pslip_ids) {
          await this.store.ship(pslip_id, '')
        }
        this.downloadInvoice(orderSnapshot)
      } finally {
        this.isShipping = false
      }
    },
    async handleMarkReceived() {
      if (!this.order.cinv_ids || this.order.cinv_ids.length === 0) {
        alert('No invoices found for this order.')
        return
      }
      if (!confirm('Mark this entire shipment as received by the customer?')) return

      this.isMarkingReceived = true
      try {
        const authStore = useAuthStore()
        for (const cinv_id of this.order.cinv_ids) {
          const res = await fetch('/api/internal-portal/receive', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ cinv_id, uid: authStore.user.uid })
          })
          if (!res.ok) throw new Error('Failed to mark one or more invoices as received')
        }
        alert('Items marked as received.')
        await this.store.fetchOrders()
      } catch (e) {
        alert(e.message)
      } finally {
        this.isMarkingReceived = false
      }
    },
    downloadInvoice(order) {
      const lines = order.items.map(it =>
        `<tr>
          <td>
            <div style="display:flex; align-items:center; gap:12px;">
              <div style="width:40px;height:40px;background:#eff6ff;color:#2563eb;border-radius:8px;display:flex;align-items:center;justify-content:center;font-size:18px;">📦</div>
              <div>
                <div style="font-weight:600;color:#0f172a;">${it.name}</div>
                <div style="font-size:12px;color:#64748b;margin-top:2px;">${it.specs || 'Standard Packaging'}</div>
              </div>
            </div>
          </td>
          <td>
            <div style="text-align:center; padding:6px; background:#f8fafc; border:1px solid #e2e8f0; border-radius:6px; font-weight:600; color:#0f172a;">
              ${it.qty || 1}
            </div>
          </td>
        </tr>`
      ).join('')

      const html = `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
  <style>
    body { font-family: 'Inter', sans-serif; background-color: #e2e8f0; padding: 40px 20px; margin: 0; -webkit-font-smoothing: antialiased; }
    .card { max-width: 800px; margin: 0 auto; background: #fff; border-radius: 16px; box-shadow: 0 20px 40px -15px rgba(0,0,0,0.05); overflow: hidden; }
    .head { background: #0f172a; color: #fff; padding: 40px; display: flex; justify-content: space-between; align-items: center; }
    .head h1 { font-size: 28px; margin: 0; font-weight: 700; letter-spacing: -0.5px; }
    .head p { margin: 4px 0 0; color: #94a3b8; font-size: 14px; }
    .badge { display: inline-block; background: rgba(255,255,255,0.1); padding: 6px 12px; border-radius: 99px; font-size: 12px; font-weight: 600; text-transform: uppercase; letter-spacing: 1px; border: 1px solid rgba(255,255,255,0.2); }
    .body { padding: 40px; }
    .grid { display: grid; grid-template-columns: 1fr 1fr; gap: 32px; margin-bottom: 40px; }
    .block h3 { font-size: 11px; text-transform: uppercase; letter-spacing: 1.5px; color: #64748b; margin: 0 0 12px 0; }
    .block p { margin: 0 0 6px 0; font-size: 14px; line-height: 1.5; color:#0f172a;}
    .block .prim { font-weight: 600; font-size: 16px; }
    table { width: 100%; border-collapse: separate; border-spacing: 0; margin-bottom: 32px; }
    th { background: #f8fafc; color: #64748b; font-size: 12px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px; padding: 16px 20px; text-align: left; border-top: 1px solid #e2e8f0; border-bottom: 1px solid #e2e8f0; }
    th:first-child { border-radius: 8px 0 0 8px; border-left: 1px solid #e2e8f0; }
    th:last-child { border-radius: 0 8px 8px 0; text-align: center; border-right: 1px solid #e2e8f0; width: 100px; }
    td { padding: 20px; border-bottom: 1px solid #e2e8f0; }
    .tot-box { background: #eff6ff; border: 1px solid #dbeafe; border-radius: 12px; padding: 24px; display: flex; justify-content: space-between; align-items: center; margin-left: auto; max-width: 320px; }
    .tot-box span { font-size: 14px; color: #2563eb; font-weight: 600; text-transform: uppercase; letter-spacing: 1px; }
    .tot-box strong { font-size: 28px; color: #2563eb; font-weight: 700; }
    .foot { text-align: center; padding-top: 32px; border-top: 1px dashed #e2e8f0; color: #64748b; font-size: 13px; }
  </style>
</head>
<body>
  <div class="card">
    <div class="head">
      <div>
        <h1>Invoice</h1>
        <p>${order.id} • Generated ${new Date().toLocaleDateString('en-IN', {day:'numeric', month:'short', year:'numeric'})}</p>
      </div>
      <div><div class="badge">${order.status}</div></div>
    </div>
    <div class="body">
      <div class="grid">
        <div class="block">
          <h3>Billed To</h3>
          <p class="prim">${order.customer}</p>
          <p style="color:#64748b">${order.shop}</p>
        </div>
        <div class="block">
          <h3>Order Details</h3>
          <p><span style="color:#64748b;display:inline-block;width:80px;">Date:</span> ${order.placedOn}</p>
          <p><span style="color:#64748b;display:inline-block;width:80px;">Priority:</span> ${order.priority || 'Standard'}</p>
          <p><span style="color:#64748b;display:inline-block;width:80px;">Carrier:</span> ${order.transport || '—'}</p>
        </div>
      </div>
      <table>
        <thead><tr><th>Description</th><th>Quantity</th></tr></thead>
        <tbody>${lines}</tbody>
      </table>
      <div class="tot-box">
        <span>Total Amount</span>
        <strong>${order.value}</strong>
      </div>
      <div class="foot">Thank you for your business!</div>
    </div>
  </div>
</body>
</html>`

      const blob = new Blob([html], { type: 'text/html' })
      const url  = URL.createObjectURL(blob)
      const a    = document.createElement('a')
      a.href     = url
      a.download = `Invoice-${order.id}.html`
      a.click()
      URL.revokeObjectURL(url)
    }
  }
}
</script>

<style scoped>
.dp {
  width: 0; flex-shrink: 0; overflow: hidden;
  background: var(--white);
  border-left: 1.5px solid var(--border);
  display: flex; flex-direction: column;
  transition: width 0.24s cubic-bezier(0.4,0,0.2,1);
}
.dp.open { width: 420px; }

.dp-head { padding: 14px 18px 12px; border-bottom: 1.5px solid var(--border); flex-shrink: 0; }
.dp-close-row { display: flex; align-items: center; justify-content: space-between; margin-bottom: 10px; }
.dp-oid       { font-family: 'Geist Mono', monospace; font-size: 10.5px; color: var(--blue); }
.dp-close-btn {
  background: none; border: 1.5px solid var(--border); border-radius: 5px;
  padding: 3px 10px; font-size: 10.5px; color: var(--ink-3); cursor: pointer;
  font-family: 'Geist', sans-serif; font-weight: 600; transition: all 0.12s;
}
.dp-close-btn:hover { background: var(--ink); color: #fff; border-color: var(--ink); }
.dp-name      { font-size: 17px; font-weight: 600; color: var(--ink); letter-spacing: -0.3px; margin-bottom: 7px; line-height: 1.2; }
.dp-chips-row { display: flex; gap: 5px; flex-wrap: wrap; }

.dp-scroll {
  flex: 1; overflow-y: auto; padding: 14px 18px;
  display: flex; flex-direction: column; gap: 14px;
}
.dp-scroll::-webkit-scrollbar       { width: 3px; }
.dp-scroll::-webkit-scrollbar-thumb { background: var(--border-2); }

.dp-sec-label {
  font-size: 9.5px; font-weight: 600; color: var(--ink-4);
  letter-spacing: 1.5px; text-transform: uppercase; margin-bottom: 8px;
  display: flex; align-items: center; gap: 8px;
}
.dp-sec-label::after { content: ''; flex: 1; height: 1px; background: var(--border-2); }
.dp-kv      { display: flex; justify-content: space-between; align-items: center; padding: 4px 0; font-size: 12.5px; }
.dp-kv .k   { color: var(--ink-4); }
.dp-kv .v   { color: var(--ink); font-weight: 500; }

.dp-item-row {
  display: flex; justify-content: space-between; align-items: flex-start;
  padding: 8px 12px; border-radius: 6px; font-size: 12px;
  background: var(--surface); border: 1px solid var(--border-2); margin-bottom: 6px;
}
.dp-item-row:last-child { margin-bottom: 0; }
.dp-item-info  { display: flex; flex-direction: column; gap: 2px; }
.dp-item-name  { font-weight: 600; color: var(--ink); }
.dp-item-specs { font-size: 10.5px; color: var(--ink-4); line-height: 1.4; }
.item-qty      { font-family: 'Geist Mono', monospace; font-size: 10.5px; color: var(--ink-3); display: flex; align-items: center; gap: 5px; margin-top: 2px; }
.qty-changed  { color: var(--amber); font-size: 10px; font-weight: 600; }

.dp-footer { padding: 12px 18px; border-top: 1.5px solid var(--border); flex-shrink: 0; }
.dp-flow-label { font-size: 9.5px; font-weight: 600; color: var(--ink-4); letter-spacing: 1.5px; text-transform: uppercase; margin-bottom: 8px; }
.dp-flow       { display: flex; align-items: center; gap: 4px; margin-bottom: 10px; }
.df-step {
  flex: 1; padding: 5px 4px; border-radius: 5px;
  border: 1px solid var(--border-2); background: var(--surface);
  text-align: center; font-size: 9px; font-weight: 600;
  font-family: 'Geist', sans-serif; letter-spacing: 0.3px; text-transform: uppercase;
  color: var(--ink-4); transition: all 0.15s;
}
.df-step.done    { background: var(--green-dim); border-color: #86efac; color: var(--green); }
.df-step.current { background: var(--ink); border-color: var(--ink); color: #fff; }
.df-arrow { color: var(--ink-4); font-size: 10px; flex-shrink: 0; }

.dp-action-btn {
  width: 100%; padding: 9px; border-radius: 6px;
  font-family: 'Geist', sans-serif; font-weight: 600; font-size: 12px;
  cursor: pointer; transition: all 0.12s; border: none;
  margin-bottom: 6px; display: flex; align-items: center; justify-content: center; gap: 5px;
}
.dp-action-btn:last-child { margin-bottom: 0; }
.dp-btn-fwd        { background: var(--blue); color: #fff; }
.dp-btn-fwd:hover  { background: #1d4ed8; }
.dp-btn-back       { background: transparent; border: 1.5px solid var(--border) !important; color: var(--ink-2); }
.dp-btn-back:hover { border-color: var(--ink) !important; color: var(--ink); }

/* Slip Box */
.slip-box {
  background: var(--stone-50); border: 1.5px solid var(--border-2);
  border-radius: 8px; padding: 12px; margin-bottom: 12px;
}
.slip-head { display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px; }
.slip-id   { font-family: 'Geist Mono', monospace; font-size: 11px; font-weight: 600; color: var(--blue); }
.slip-status {
  font-size: 9px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.5px;
  padding: 2px 6px; border-radius: 4px;
}
.slip-status.packed  { background: #fef3c7; color: #d97706; }
.slip-status.shipped { background: #dcfce7; color: #16a34a; }
.slip-date  { font-size: 10.5px; color: var(--ink-4); margin-bottom: 8px; }
.slip-items { border-top: 1px solid var(--border-2); padding-top: 8px; margin-bottom: 10px; }
.slip-item  { font-size: 11.5px; color: var(--ink-2); padding: 2px 0; }
.slip-actions { display: flex; gap: 8px; align-items: center; }
.slip-btn {
  padding: 5px 10px; border-radius: 5px; font-size: 11px; font-weight: 600;
  cursor: pointer; transition: all 0.12s; border: 1.5px solid var(--border); background: #fff;
  display: flex; align-items: center; gap: 4px;
}
.slip-btn.ship:hover { background: var(--blue); color: #fff; border-color: var(--blue); }
.slip-btn.unpack:hover { background: var(--ink); color: #fff; border-color: var(--ink); }
.shipped-note { font-size: 11px; font-weight: 600; color: var(--green); display: flex; align-items: center; gap: 4px; }

/* Inline ship section */
.dp-ship-inline {
  background: var(--surface); border: 1.5px solid var(--border-2);
  border-radius: 8px; padding: 12px; margin-bottom: 8px;
}
.dp-ship-inline .fi {
  width: 100%; padding: 7px 10px; background: var(--white); border: 1.5px solid var(--border);
  border-radius: 6px; color: var(--ink); font-size: 12px; outline: none;
  font-family: 'Geist', sans-serif; cursor: pointer;
}
.btn-primary:disabled { opacity: 0.45; cursor: not-allowed; }
</style>