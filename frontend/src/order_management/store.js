import { defineStore } from 'pinia'

export const CC = { VIP: '#16a34a', Regular: '#2563eb', Delayed: '#d97706', New: '#dc2626' }
export const CB = { VIP: '#dcfce7', Regular: '#dbeafe', Delayed: '#fef3c7', New: '#fee2e2' }
export const CL = { VIP: '👑 VIP', Regular: '⭐ Regular', Delayed: '⚠ Delayed', New: '🆕 New' }
export const PC = { High: '#dc2626', Medium: '#d97706', Low: '#16a34a' }
export const PB = { High: '#fee2e2', Medium: '#fef3c7', Low: '#dcfce7' }
export const SC = { inprocess: '#2563eb', packed: '#d97706', shipped: '#16a34a' }
export const SL = { inprocess: 'In Progress', packed: 'Packed', shipped: 'Shipped' }

export const useOrderStore = defineStore('orders', {
  state: () => ({
    inventory: {},
    orders: [],
    loading: false,
    error: null
  }),

  getters: {
    byStatus: (state) => (status) => {
      // Access orders deeply so Pinia tracks nested changes
      state.orders.forEach(o => o.items.forEach(it => it.qty))
      return state.orders.filter(o => o.status === status).sort((a, b) => (a.rank ?? 9999) - (b.rank ?? 9999) || a.order - b.order)
    },

    inprocessCount: (state) =>
      state.orders.filter(o => o.status === 'inprocess').length,

    totalCount: (state) => state.orders.length,

    findById: (state) => (id) => state.orders.find(o => o.id === id)
  },

  actions: {
    async fetchOrders() {
      this.loading = true;
      this.error = null;
      try {
        const res = await fetch('/api/internal-portal/orders');
        if (!res.ok) throw new Error('Failed to fetch orders');
        const data = await res.json();
        let fetchedOrders = data.orders || [];
        fetchedOrders.forEach((o, i) => {
          if (typeof o.order === 'undefined' || isNaN(o.order)) o.order = i
          // rank comes from server (persisted ranking), default 9999 = unranked
          if (typeof o.rank === 'undefined') o.rank = 9999
        })
        this.orders = fetchedOrders;
        this.inventory = data.inventory || {};
      } catch (e) {
        console.error('Failed fetching order data:', e);
        this.error = e.message;
      } finally {
        this.loading = false;
      }
    },
// In store.js — replace your promote action with this:

    async promote(id, newStatus, transport, updatedItems) {
      const o = this.orders.find(x => x.id === id)
      if (!o) return { success: false, error: 'Order not found' }
      const old = o.status

      if (newStatus === 'packed' && old === 'inprocess') {
        const payload = {
          coid: id,
          items: (updatedItems || []).filter(ui => ui.qty > 0).map(ui => ({
            skuid: ui.skuid,
            packed_qty: ui.qty
          }))
        }

        try {
          const res = await fetch('/api/internal-portal/pack', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
          })
          if (!res.ok) {
            const errData = await res.json()
            throw new Error(errData.message || 'Failed to pack order')
          }
          
          const data = await res.json()
          // Refresh data to get new status and updated stock/packing slips
          await this.fetchOrders()
          return { success: true, pslip_id: data.pslip_id, status: data.status }
        } catch (e) {
          console.error('Packing failed:', e)
          this.error = e.message
          return { success: false }
        }

      } else {
        // Fallback or other status transitions (shipped soon)
        o.status = newStatus
        o.order  = this.orders.filter(x => x.status === newStatus).length - 1
        
        if (newStatus === 'shipped') {
          o.transport = transport || 'BlueDart Express'
          o.shippingCost = '₹' + (Math.floor(Math.random() * 400) + 300)
        }
        return { success: true }
      }
    },

    async reorderColumn(status, priority, orderedCards) {
      // Optimistic: update ranks locally
      orderedCards.forEach((card, i) => { card.rank = i })
      const ordered_coids = orderedCards.map(c => c.id)
      try {
        const res = await fetch('/api/internal-portal/reorder-cards', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ status, priority, ordered_coids })
        })
        if (!res.ok) throw new Error('Reorder failed')
        return true
      } catch (e) {
        console.error('Reorder failed:', e)
        this.error = e.message
        await this.fetchOrders()
        return false
      }
    },

    async crossDrag(coid, status, fromPriority, toPriority, toRank) {
      // Optimistic: update the card locally
      const card = this.orders.find(o => o.id === coid)
      if (card) card.priority = toPriority
      try {
        const res = await fetch('/api/internal-portal/cross-drag', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ coid, status, from_priority: fromPriority, to_priority: toPriority, to_rank: toRank })
        })
        if (!res.ok) throw new Error('Cross-drag failed')
        // Refetch to get re-ranked data from server
        await this.fetchOrders()
        return true
      } catch (e) {
        console.error('Cross-drag failed:', e)
        this.error = e.message
        await this.fetchOrders()
        return false
      }
    },

    addOrder(formData) {
      const newId = 'ORD-' + (4900 + this.orders.length)
      const deadline = formData.deadline
        ? new Date(formData.deadline).toLocaleDateString('en-IN', { month: 'short', day: 'numeric' })
        : 'TBD'
      const items = (formData.items
        ? formData.items.split(',').map(s => s.trim()).filter(Boolean)
        : ['Item']
      ).map(name => ({
        name,
        inStock: this.inventory[name] ? this.inventory[name].stock > 0 : Math.random() > 0.4
      }))

      this.orders.unshift({
        id: newId,
        status: 'inprocess',
        order: this.orders.filter(o => o.status === 'inprocess').length,
        customer:  formData.customer || 'New Customer',
        custType:  formData.custType || 'Regular',
        priority:  formData.priority || 'Medium',
        value:     formData.value ? '₹' + Number(formData.value).toLocaleString('en-IN') : '₹0',
        deadline,
        shop:      formData.shop || 'Main Store',
        items
      })
      return newId
    },

    async unpack(pslip_id) {
      try {
        const res = await fetch('/api/internal-portal/unpack', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ pslip_id })
        })
        if (!res.ok) {
          const errData = await res.json()
          throw new Error(errData.message || 'Failed to unpack')
        }
        await this.fetchOrders()
        return true
      } catch (e) {
        console.error('Unpack failed:', e)
        this.error = e.message
        return false
      }
    },

    async ship(pslip_id, transport, invoiceHtml) {
      try {
        const res = await fetch('/api/internal-portal/ship', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ pslip_id, transport, invoice_html: invoiceHtml })
        })
        if (!res.ok) {
          const errData = await res.json()
          throw new Error(errData.message || 'Failed to ship')
        }
        await this.fetchOrders()
        return true
      } catch (e) {
        console.error('Ship failed:', e)
        this.error = e.message
        return false
      }
    }
  }
})