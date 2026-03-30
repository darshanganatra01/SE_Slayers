import { defineStore } from 'pinia'

export const useInventoryStore = defineStore('inventory', {
  state: () => ({
    parts: [
      { id: 1,  name: 'Hose Clip (Light)', sku: 'HC-27', category: 'Hose Fittings', size: '1.5"',  dims: '58–62 mm',  spec: 'Bolt: 12 × 45 mm',    stock: 7,  maxStock: 30, status: 'low',     sellPrice: 220,  buyPrice: null, unit: 'per 12 pcs' },
      { id: 2,  name: 'Hose Clip (Light)', sku: 'HC-27', category: 'Hose Fittings', size: '2"',    dims: '70–74 mm',  spec: 'Bolt: 12 × 45 mm',    stock: 25, maxStock: 25, status: 'instock', sellPrice: 230,  buyPrice: null, unit: 'per 12 pcs' },
      { id: 3,  name: 'Hose Clip (Light)', sku: 'HC-27', category: 'Hose Fittings', size: '2.5"',  dims: '80–84 mm',  spec: 'Bolt: 12 × 45 mm',    stock: 20, maxStock: 20, status: 'instock', sellPrice: 255,  buyPrice: null, unit: 'per 12 pcs' },
      { id: 4,  name: 'Hose Clip (Light)', sku: 'HC-27', category: 'Hose Fittings', size: '4"',    dims: '110–115 mm', spec: 'Bolt: 12 × 45 mm',    stock: 0,  maxStock: 12, status: 'out',     sellPrice: 305,  buyPrice: null, unit: 'per 12 pcs' },
      { id: 5,  name: 'G.I. Step Connector', sku: 'SC-14', category: 'Pipe Fittings', size: '0.5" × 6"', dims: 'Medium', spec: 'G.I. galvanised', stock: 18, maxStock: 20, status: 'instock', sellPrice: 23,   buyPrice: null, unit: 'per piece' },
      { id: 6,  name: 'G.I. Step Connector', sku: 'SC-14', category: 'Pipe Fittings', size: '1" × 7"',   dims: 'Medium', spec: 'G.I. galvanised', stock: 10, maxStock: 20, status: 'instock', sellPrice: 37,   buyPrice: null, unit: 'per piece' },
      { id: 7,  name: 'G.I. Step Connector', sku: 'SC-14', category: 'Pipe Fittings', size: '2" × 8"',   dims: 'Medium', spec: 'G.I. galvanised', stock: 3,  maxStock: 15, status: 'low',     sellPrice: 79,   buyPrice: null, unit: 'per piece' },
      { id: 8,  name: 'G.I. Step Connector', sku: 'SC-14', category: 'Pipe Fittings', size: '4" × 8"',   dims: 'Medium', spec: 'G.I. galvanised', stock: 8,  maxStock: 10, status: 'instock', sellPrice: 220,  buyPrice: null, unit: 'per piece' },
      { id: 9,  name: 'Air Filter AF-3',    sku: 'AF-3',  category: 'Filtration',    size: 'Panel', dims: '300 × 200 × 40 mm', spec: 'Flow: 350 m³/h', stock: 2,  maxStock: 30, status: 'low', sellPrice: 650, buyPrice: 420, unit: '' },
      { id: 10, name: 'Oil Filter OF-7',    sku: 'OF-7',  category: 'Filtration',    size: 'Ø 66 mm', dims: 'Height 90 mm', spec: 'Thread: M20 × 1.5', stock: 0,  maxStock: 40, status: 'out', sellPrice: 480, buyPrice: 310, unit: '' },
      { id: 11, name: 'Fuel Pump FP-11',    sku: 'FP-11', category: 'Engine',        size: 'In-line', dims: 'Flow 120 L/h', spec: 'Pressure: 3.5 bar', stock: 19, maxStock: 20, status: 'instock', sellPrice: 2100, buyPrice: 1550, unit: '' },
      { id: 12, name: 'Spark Plug SP-9',    sku: 'SP-9',  category: 'Engine',        size: 'Thread: M14 × 1.25', dims: '', spec: 'Reach: 19 mm · Hex: 16 mm', stock: 22, maxStock: 50, status: 'instock', sellPrice: 320, buyPrice: 210, unit: '' },
    ],

    profData: {
      hose: {
        title: 'Hose Clip (Light)', sku: 'HC-27',
        rows: [
          { size: '1.5"', dim: '58–62 mm',   stock: 7,  maxStock: 30, status: 'low' },
          { size: '2"',   dim: '70–74 mm',   stock: 25, maxStock: 25, status: 'ok' },
          { size: '2.5"', dim: '80–84 mm',   stock: 20, maxStock: 20, status: 'ok' },
          { size: '3"',   dim: '90–94 mm',   stock: 5,  maxStock: 20, status: 'low' },
          { size: '4"',   dim: '110–115 mm', stock: 0,  maxStock: 12, status: 'out' },
        ]
      },
      gi: {
        title: 'G.I. Step Connector', sku: 'SC-14',
        rows: [
          { size: '0.5" × 6"',  dim: 'Medium · G.I.', stock: 18, maxStock: 20, status: 'ok' },
          { size: '0.75" × 6"', dim: 'Medium · G.I.', stock: 15, maxStock: 20, status: 'ok' },
          { size: '1" × 7"',    dim: 'Medium · G.I.', stock: 10, maxStock: 20, status: 'ok' },
          { size: '1.5" × 7"',  dim: 'Medium · G.I.', stock: 12, maxStock: 20, status: 'ok' },
          { size: '2" × 8"',    dim: 'Medium · G.I.', stock: 3,  maxStock: 15, status: 'low' },
          { size: '4" × 8"',    dim: 'Medium · G.I.', stock: 8,  maxStock: 10, status: 'ok' },
        ]
      },
      air: {
        title: 'Air Filter', sku: 'AF',
        rows: [
          { size: 'AF-3', dim: '300×200×40 mm', stock: 2,  maxStock: 30, status: 'low' },
          { size: 'AF-5', dim: '400×250×45 mm', stock: 15, maxStock: 20, status: 'ok' },
          { size: 'AF-7', dim: '500×300×50 mm', stock: 10, maxStock: 15, status: 'ok' },
        ]
      },
      oil: {
        title: 'Oil Filter', sku: 'OF',
        rows: [
          { size: 'OF-5', dim: 'Ø 55 mm · H 80 mm',  stock: 12, maxStock: 20, status: 'ok' },
          { size: 'OF-7', dim: 'Ø 66 mm · H 90 mm',  stock: 0,  maxStock: 40, status: 'out' },
          { size: 'OF-9', dim: 'Ø 76 mm · H 100 mm', stock: 8,  maxStock: 15, status: 'ok' },
        ]
      },
      fuel: {
        title: 'Fuel Pump', sku: 'FP',
        rows: [
          { size: 'FP-9',  dim: 'In-line · 90 L/h',  stock: 14, maxStock: 20, status: 'ok' },
          { size: 'FP-11', dim: 'In-line · 120 L/h', stock: 19, maxStock: 20, status: 'ok' },
          { size: 'FP-14', dim: 'In-line · 160 L/h', stock: 10, maxStock: 15, status: 'ok' },
        ]
      }
    },

    pendingOrders: [
      { name: 'Hose Clip HC-27 · 4"', detail: 'ORD-V-091 · Amul Engineering',    qty: 24, sku: 'HC-27', size: '4"' },
      { name: 'G.I. Step Connector · 2"', detail: 'ORD-V-088 · Rajkot Pipes Co.', qty: 30, sku: 'SC-14', size: '2"×8"' },
      { name: 'Air Filter AF-3',       detail: 'ORD-V-085 · Mehta Auto Parts',     qty: 30, sku: 'AF-3',  size: 'AF-3' },
      { name: 'Oil Filter OF-7',       detail: 'ORD-V-082 · Srivastava Filters',   qty: 40, sku: 'OF-7',  size: 'OF-7' },
    ],

    stockHistory: [
      { type: 'out', text: 'Dispatched — <strong>Hose Clip HC-27 (1.5")</strong> × 4 · ORD-4816', time: 'Today 9:14 am',     delta: -4 },
      { type: 'out', text: 'Dispatched — <strong>G.I. Step Connector (2")</strong> × 12 · ORD-4819', time: 'Today 8:50 am',  delta: -12 },
      { type: 'in',  text: 'Received — <strong>Oil Filter OF-7</strong> × 25 units',               time: 'Yesterday 6:30 pm', delta: 25 },
      { type: 'out', text: 'Dispatched — <strong>Spark Plug SP-9</strong> × 8 · ORD-4815',         time: 'Mar 20 4:10 pm',    delta: -8 },
      { type: 'in',  text: 'Received — <strong>Fuel Pump FP-11</strong> × 19 units',               time: 'Mar 13 3:20 pm',    delta: 19 },
      { type: 'out', text: 'Dispatched — <strong>Hose Clip HC-27 (4")</strong> × 12 · ORD-4812',   time: 'Mar 12 11:00 am',   delta: -12 },
    ],

    portfolioProducts: [
      {
        name: 'Hose Clip (Light)', code: 'HC-27 · Hose Fittings', key: 'hose',
        sizes: [
          { label: '1.5"', status: 'ok' }, { label: '2"', status: 'ok' }, { label: '2.5"', status: 'ok' },
          { label: '3"', status: 'low' }, { label: '4"', status: 'out' }
        ]
      },
      {
        name: 'G.I. Step Connector', code: 'SC-14 · Pipe Fittings', key: 'gi',
        sizes: [
          { label: '0.5"', status: 'ok' }, { label: '0.75"', status: 'ok' }, { label: '1"', status: 'ok' },
          { label: '1.25"', status: 'ok' }, { label: '1.5"', status: 'ok' }, { label: '2"', status: 'low' },
          { label: '4"', status: 'ok' }
        ]
      },
      {
        name: 'Air Filter', code: 'AF series · Filtration', key: 'air',
        sizes: [
          { label: 'AF-3', status: 'low' }, { label: 'AF-5', status: 'ok' }, { label: 'AF-7', status: 'ok' }
        ]
      },
      {
        name: 'Oil Filter', code: 'OF series · Filtration', key: 'oil',
        sizes: [
          { label: 'OF-5', status: 'ok' }, { label: 'OF-7', status: 'out' }, { label: 'OF-9', status: 'ok' }
        ]
      },
      {
        name: 'Fuel Pump', code: 'FP series · Engine', key: 'fuel',
        sizes: [
          { label: 'FP-9', status: 'ok' }, { label: 'FP-11', status: 'ok' }, { label: 'FP-14', status: 'ok' }
        ]
      }
    ]
  }),

  getters: {
    totalCount:    (s) => s.parts.length,
    inStockCount:  (s) => s.parts.filter(p => p.status === 'instock').length,
    lowStockCount: (s) => s.parts.filter(p => p.status === 'low' || p.status === 'out').length,
    outOfStockCount: (s) => s.parts.filter(p => p.status === 'out').length,
    lowOnlyCount:  (s) => s.parts.filter(p => p.status === 'low').length,
  },

  actions: {
    addPart(data) {
      const id = this.parts.length ? Math.max(...this.parts.map(p => p.id)) + 1 : 1
      const stock = parseInt(data.openingStock) || 0
      const threshold = parseInt(data.threshold) || 5
      let status = 'instock'
      if (stock === 0) status = 'out'
      else if (stock <= threshold) status = 'low'

      this.parts.push({
        id,
        name: data.name,
        sku: data.sku,
        category: data.category,
        size: data.size,
        dims: data.dims,
        spec: data.spec,
        stock,
        maxStock: Math.max(stock, threshold * 2),
        status,
        sellPrice: parseInt(data.sellPrice) || 0,
        buyPrice: parseInt(data.buyPrice) || null,
        unit: data.unit
      })
    }
  }
})
