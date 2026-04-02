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
      return state.orders.filter(o => o.status === status).sort((a, b) => a.order - b.order)
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
        this.orders = data.orders || [];
        this.inventory = data.inventory || {};
      } catch (e) {
        console.error('Failed fetching order data:', e);
        this.error = e.message;
      } finally {
        this.loading = false;
      }
    },
// In store.js — replace your promote action with this:

    promote(id, newStatus, transport, updatedItems) {
      const o = this.orders.find(x => x.id === id)
      if (!o) return
      const old = o.status
      o.status = newStatus
      o.order  = this.orders.filter(x => x.status === newStatus).length - 1

      if (newStatus === 'packed' && old === 'inprocess') {
        // Apply updated quantities from the packing modal
        if (updatedItems && updatedItems.length) {
          const newItems = o.items.map(it => {
            const updated = updatedItems.find(u => u.name === it.name)
            if (updated) {
              return { ...it, originalQty: it.qty || 1, qty: updated.qty }
            }
            return it
          })
          o.items.splice(0, o.items.length, ...newItems)
        }
        // Update inventory
        o.items.forEach(it => {
          if (it.inStock && this.inventory[it.name]) {
            this.inventory[it.name].stock = Math.max(0, this.inventory[it.name].stock - (it.qty || 1))
            it.inStock = this.inventory[it.name].stock > 0
          }
        })
        if (!o.packages)      o.packages      = Math.ceil(o.items.length / 2)
        if (!o.packagingCost) o.packagingCost = '₹' + (o.packages * 150)

      } else if (newStatus === 'shipped') {
        o.transport   = transport || 'BlueDart Express'
        o.shippingCost = '₹' + (Math.floor(Math.random() * 400) + 300)
      }
    },

    reorder(fromId, toId, pos) {
      const from = this.orders.find(o => o.id === fromId)
      const to   = this.orders.find(o => o.id === toId)
      if (!from || !to || from.status !== to.status) return
      let col = this.orders
        .filter(o => o.status === from.status)
        .sort((a, b) => a.order - b.order)
        .filter(o => o.id !== fromId)
      const ti = col.findIndex(o => o.id === toId)
      col.splice(pos === 'before' ? ti : ti + 1, 0, from)
      col.forEach((o, i) => { o.order = i })
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
    }
  }
})