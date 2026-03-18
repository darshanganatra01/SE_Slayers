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
    inventory: {
      'Brake Pads B200':    { stock: 8,  max: 20 },
      'Engine Filter EF-X': { stock: 3,  max: 15 },
      'Spark Plug SP-9':    { stock: 11, max: 20 },
      'Clutch Cable CC-4':  { stock: 6,  max: 12 },
      'Oil Filter OF-7':    { stock: 14, max: 20 },
      'Air Filter AF-3':    { stock: 2,  max: 10 },
    },
    orders: [
      { id: 'ORD-4821', status: 'inprocess', order: 0, customer: 'Arjun Mehta',   custType: 'VIP',     priority: 'High',   value: '₹12,400', placedOn: 'March 10 2026', shop: 'Mehta Garage', items: [{ name: 'Brake Pads B200', inStock: true }, { name: 'Engine Filter EF-X', inStock: false }, { name: 'Oil Filter OF-7', inStock: true }] },
      { id: 'ORD-4819', status: 'inprocess', order: 1, customer: 'Priya Sharma',  custType: 'Regular', priority: 'High',   value: '₹8,750',  placedOn: 'March 11 2026', shop: 'Raj Plumbing service',        items: [{ name: 'Spark Plug SP-9', inStock: true }, { name: 'Clutch Cable CC-4', inStock: true }] },
      { id: 'ORD-4816', status: 'inprocess', order: 2, customer: 'Kiran Nair',    custType: 'Delayed', priority: 'Medium', value: '₹5,100',  placedOn: 'March 15 2026', shop: 'Adyar Mechanics',        items: [{ name: 'Air Filter AF-3', inStock: false }, { name: 'Oil Filter OF-7', inStock: true }] },
      { id: 'ORD-4812', status: 'inprocess', order: 3, customer: 'Deepak Rao',    custType: 'New',     priority: 'Low',    value: '₹3,200',  placedOn: 'March 10 2026', shop: 'Poonam Mart',            items: [{ name: 'Brake Pads B200', inStock: true }] },
      { id: 'ORD-4815', status: 'packed',    order: 0, customer: 'Ravi Kumar',    custType: 'VIP',     priority: 'Low',    value: '₹22,100', placedOn: 'March 20 2026', shop: 'Anna Garage',       packages: 3, packagingCost: '₹450', items: [{ name: 'Engine Filter EF-X', inStock: true }, { name: 'Clutch Cable CC-4', inStock: true }] },
      { id: 'ORD-4808', status: 'packed',    order: 1, customer: 'Neha Patel',    custType: 'Regular', priority: 'Medium', value: '₹9,600',  placedOn: 'March 20 2026', shop: 'Mylapore Spare point',          packages: 2, packagingCost: '₹300', items: [{ name: 'Spark Plug SP-9', inStock: true }, { name: 'Air Filter AF-3', inStock: false }] },
      { id: 'ORD-4803', status: 'shipped',   order: 0, customer: 'Suresh Babu',   custType: 'VIP',     priority: 'Medium', value: '₹18,900', placedOn: 'March 10 2026',  shop: 'Porur Mart',             transport: 'BlueDart Express', shippingCost: '₹650', items: [{ name: 'Brake Pads B200', inStock: true }, { name: 'Oil Filter OF-7', inStock: true }] },
      { id: 'ORD-4798', status: 'shipped',   order: 1, customer: 'Meena Das',     custType: 'Delayed', priority: 'Low',    value: '₹6,400',  placedOn: 'March 11 2026',  shop: 'Anna Plumbing',            transport: 'DTDC Courier', shippingCost: '₹420', items: [{ name: 'Clutch Cable CC-4', inStock: true }] },
    ]
  }),

  getters: {
    byStatus: (state) => (status) =>
      state.orders.filter(o => o.status === status).sort((a, b) => a.order - b.order),

    inprocessCount: (state) =>
      state.orders.filter(o => o.status === 'inprocess').length,

    totalCount: (state) => state.orders.length,

    findById: (state) => (id) => state.orders.find(o => o.id === id)
  },

  actions: {
    promote(id, newStatus, transport) {
      const o = this.orders.find(x => x.id === id)
      if (!o) return
      const old = o.status
      o.status = newStatus
      o.order = this.orders.filter(x => x.status === newStatus).length - 1

      if (newStatus === 'packed' && old === 'inprocess') {
        o.items.forEach(it => {
          if (it.inStock && this.inventory[it.name]) {
            this.inventory[it.name].stock = Math.max(0, this.inventory[it.name].stock - 1)
            it.inStock = this.inventory[it.name].stock > 0
          }
        })
        if (!o.packages) o.packages = Math.ceil(o.items.length / 2)
        if (!o.packagingCost) o.packagingCost = '₹' + (o.packages * 150)
      } else if (newStatus === 'shipped') {
        o.transport = transport || 'BlueDart Express'
        if (!o.shippingCost) o.shippingCost = '₹' + (Math.floor(Math.random() * 400) + 300)
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