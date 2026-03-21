import { defineStore } from 'pinia'

export const useVendorStore = defineStore('vendors', {
  state: () => ({
    vendors: [
      {
        id: 'VND-001',
        name: 'ABC Auto Parts',
        leadTime: 3,
        frequency: 'Weekly',
        location: 'Chennai',
        rating: 4.8,
        parts: ['S.S. Step Nipple', 'G.I. Step Nipple'],
        contact: { phone: '+91 98401 12345', email: 'sales@abcauto.com' }
      },
      {
        id: 'VND-002',
        name: 'Delta Spares',
        leadTime: 5,
        frequency: 'Bi-Weekly',
        location: 'Mumbai',
        rating: 4.2,
        parts: ['Hose Clip (Light)', 'G.I. Step Nipple'],
        contact: { phone: '+91 98765 43210', email: 'info@deltaspares.in' }
      },
      {
        id: 'VND-003',
        name: 'Raj Components',
        leadTime: 2,
        frequency: 'Daily',
        location: 'Chennai',
        rating: 4.9,
        parts: ['S.S. Step Nipple', 'Hose Clip (Light)', 'G.I. Step Nipple'],
        contact: { phone: '+91 90000 11122', email: 'orders@rajcomp.com' }
      },
      {
        id: 'VND-004',
        name: 'Global Auto Supply',
        leadTime: 10,
        frequency: 'Monthly',
        location: 'Delhi',
        rating: 3.8,
        parts: ['S.S. Step Nipple', 'Hose Clip (Light)'],
        contact: { phone: '+91 11 2345 6789', email: 'supply@globalauto.in' }
      },
      {
        id: 'VND-005',
        name: 'Southern Motors',
        leadTime: 4,
        frequency: 'Weekly',
        location: 'Bangalore',
        rating: 4.5,
        parts: ['G.I. Step Nipple', 'Hose Clip (Light)'],
        contact: { phone: '+91 80 4567 8901', email: 'parts@southernmotors.com' }
      },
      {
        id: 'VND-006',
        name: 'Precision Parts Co',
        leadTime: 7,
        frequency: 'Bi-Weekly',
        location: 'Hyderabad',
        rating: 4.0,
        parts: ['S.S. Step Nipple', 'G.I. Step Nipple', 'Hose Clip (Light)'],
        contact: { phone: '+91 40 2233 4455', email: 'sales@precisionparts.in' }
      }
    ],

    parts: [
      {
        id: 'PRT-001',
        name: 'S.S. Step Nipple',
        image: '/src/vendor_management/Part Images/S.S. step nipple.jpeg',
        sizes: [
          {
            size: '0.5" x 6"',
            suppliers: [
              { vendorId: 'VND-001', price: 38, leadTime: 3, lastPurchased: 'Mar 12, 2026' },
              { vendorId: 'VND-003', price: 35, leadTime: 2, lastPurchased: 'Mar 18, 2026' },
              { vendorId: 'VND-006', price: 40, leadTime: 7, lastPurchased: 'Mar 01, 2026' }
            ]
          },
          {
            size: '0.75" x 6"',
            suppliers: [
              { vendorId: 'VND-001', price: 45, leadTime: 3, lastPurchased: 'Mar 10, 2026' },
              { vendorId: 'VND-003', price: 42, leadTime: 2, lastPurchased: 'Mar 17, 2026' },
              { vendorId: 'VND-004', price: 48, leadTime: 10, lastPurchased: 'Feb 28, 2026' }
            ]
          },
          {
            size: '1" x 7"',
            suppliers: [
              { vendorId: 'VND-001', price: 46, leadTime: 3, lastPurchased: 'Mar 08, 2026' },
              { vendorId: 'VND-003', price: 43, leadTime: 2, lastPurchased: 'Mar 16, 2026' },
              { vendorId: 'VND-006', price: 50, leadTime: 7, lastPurchased: 'Mar 02, 2026' }
            ]
          },
          {
            size: '1.25" x 7"',
            suppliers: [
              { vendorId: 'VND-001', price: 60, leadTime: 3, lastPurchased: 'Mar 05, 2026' },
              { vendorId: 'VND-004', price: 56, leadTime: 10, lastPurchased: 'Feb 20, 2026' },
              { vendorId: 'VND-006', price: 62, leadTime: 7, lastPurchased: 'Feb 25, 2026' }
            ]
          },
          {
            size: '1.5" x 7"',
            suppliers: [
              { vendorId: 'VND-001', price: 70, leadTime: 3, lastPurchased: 'Mar 03, 2026' },
              { vendorId: 'VND-003', price: 66, leadTime: 2, lastPurchased: 'Mar 14, 2026' },
              { vendorId: 'VND-006', price: 74, leadTime: 7, lastPurchased: 'Feb 28, 2026' }
            ]
          }
        ]
      },
      {
        id: 'PRT-002',
        name: 'G.I. Step Nipple',
        image: '/src/vendor_management/Part Images/G.I. step connector.jpeg',
        sizes: [
          {
            size: '0.5" x 6"',
            suppliers: [
              { vendorId: 'VND-002', price: 25, leadTime: 5, lastPurchased: 'Mar 15, 2026' },
              { vendorId: 'VND-003', price: 23, leadTime: 2, lastPurchased: 'Mar 19, 2026' },
              { vendorId: 'VND-006', price: 27, leadTime: 7, lastPurchased: 'Mar 03, 2026' }
            ]
          },
          {
            size: '0.75" x 6"',
            suppliers: [
              { vendorId: 'VND-002', price: 28, leadTime: 5, lastPurchased: 'Mar 11, 2026' },
              { vendorId: 'VND-003', price: 26, leadTime: 2, lastPurchased: 'Mar 18, 2026' },
              { vendorId: 'VND-005', price: 30, leadTime: 4, lastPurchased: 'Mar 06, 2026' }
            ]
          },
          {
            size: '1" x 7"',
            suppliers: [
              { vendorId: 'VND-001', price: 40, leadTime: 3, lastPurchased: 'Mar 09, 2026' },
              { vendorId: 'VND-003', price: 37, leadTime: 2, lastPurchased: 'Mar 17, 2026' },
              { vendorId: 'VND-005', price: 42, leadTime: 4, lastPurchased: 'Mar 04, 2026' }
            ]
          },
          {
            size: '1.25" x 7"',
            suppliers: [
              { vendorId: 'VND-002', price: 45, leadTime: 5, lastPurchased: 'Mar 07, 2026' },
              { vendorId: 'VND-003', price: 42, leadTime: 2, lastPurchased: 'Mar 16, 2026' },
              { vendorId: 'VND-006', price: 47, leadTime: 7, lastPurchased: 'Feb 26, 2026' }
            ]
          },
          {
            size: '1.5" x 7"',
            suppliers: [
              { vendorId: 'VND-002', price: 51, leadTime: 5, lastPurchased: 'Mar 05, 2026' },
              { vendorId: 'VND-003', price: 48, leadTime: 2, lastPurchased: 'Mar 15, 2026' },
              { vendorId: 'VND-005', price: 54, leadTime: 4, lastPurchased: 'Mar 01, 2026' }
            ]
          }
        ]
      },
      {
        id: 'PRT-003',
        name: 'Hose Clip (Light)',
        image: '/src/vendor_management/Part Images/Hose Clip.jpeg',
        sizes: [
          {
            size: '1.5" (58–62 mm)',
            suppliers: [
              { vendorId: 'VND-002', price: 235, leadTime: 5, lastPurchased: 'Mar 14, 2026' },
              { vendorId: 'VND-003', price: 220, leadTime: 2, lastPurchased: 'Mar 19, 2026' },
              { vendorId: 'VND-005', price: 245, leadTime: 4, lastPurchased: 'Mar 08, 2026' }
            ]
          },
          {
            size: '2" (70–74 mm)',
            suppliers: [
              { vendorId: 'VND-002', price: 242, leadTime: 5, lastPurchased: 'Mar 12, 2026' },
              { vendorId: 'VND-004', price: 230, leadTime: 10, lastPurchased: 'Feb 22, 2026' },
              { vendorId: 'VND-006', price: 250, leadTime: 7, lastPurchased: 'Mar 02, 2026' }
            ]
          },
          {
            size: '2.5" (80–84 mm)',
            suppliers: [
              { vendorId: 'VND-003', price: 255, leadTime: 2, lastPurchased: 'Mar 17, 2026' },
              { vendorId: 'VND-005', price: 265, leadTime: 4, lastPurchased: 'Mar 07, 2026' },
              { vendorId: 'VND-006', price: 270, leadTime: 7, lastPurchased: 'Feb 28, 2026' }
            ]
          },
          {
            size: '3" (90–94 mm)',
            suppliers: [
              { vendorId: 'VND-002', price: 278, leadTime: 5, lastPurchased: 'Mar 10, 2026' },
              { vendorId: 'VND-003', price: 275, leadTime: 2, lastPurchased: 'Mar 18, 2026' },
              { vendorId: 'VND-004', price: 290, leadTime: 10, lastPurchased: 'Feb 18, 2026' }
            ]
          },
          {
            size: '3.25" (95–97 mm)',
            suppliers: [
              { vendorId: 'VND-003', price: 292, leadTime: 2, lastPurchased: 'Mar 16, 2026' },
              { vendorId: 'VND-005', price: 298, leadTime: 4, lastPurchased: 'Mar 05, 2026' },
              { vendorId: 'VND-006', price: 305, leadTime: 7, lastPurchased: 'Feb 25, 2026' }
            ]
          }
        ]
      }
    ],

    procurements: [
      {
        id: 'PRQ-001',
        partName: 'S.S. Step Nipple',
        size: '1" x 7"',
        quantity: 50,
        vendorId: 'VND-003',
        priority: 'High',
        requiredBy: '2026-03-25',
        notes: 'Urgent requirement for upcoming project.',
        date: 'Mar 10, 2026',
        status: 'received'
      },
      {
        id: 'PRQ-002',
        partName: 'Hose Clip (Light)',
        size: '2" (70–74 mm)',
        quantity: 120,
        vendorId: 'VND-002',
        priority: 'Medium',
        requiredBy: '2026-03-30',
        notes: '',
        date: 'Mar 12, 2026',
        status: 'received'
      },
      {
        id: 'PRQ-003',
        partName: 'G.I. Step Nipple',
        size: '0.5" x 6"',
        quantity: 200,
        vendorId: 'VND-003',
        priority: 'Low',
        requiredBy: '2026-04-05',
        notes: 'Standard restock.',
        date: 'Mar 15, 2026',
        status: 'pending'
      },
      {
        id: 'PRQ-004',
        partName: 'S.S. Step Nipple',
        size: '1.5" x 7"',
        quantity: 30,
        vendorId: 'VND-001',
        priority: 'High',
        requiredBy: '2026-03-28',
        notes: 'Required before end of month.',
        date: 'Mar 18, 2026',
        status: 'pending'
      },
      {
        id: 'PRQ-005',
        partName: 'Hose Clip (Light)',
        size: '3" (90–94 mm)',
        quantity: 60,
        vendorId: 'VND-005',
        priority: 'Medium',
        requiredBy: '2026-04-10',
        notes: '',
        date: 'Mar 20, 2026',
        status: 'pending'
      }
    ]
  }),

  getters: {
    activeVendorCount: (state) => state.vendors.length,

    findVendorById: (state) => (id) =>
      state.vendors.find(v => v.id === id),

    vendorsBySize: (state) => (partId, sizeLabel) => {
      const part = state.parts.find(p => p.id === partId)
      if (!part) return []
      const sizeObj = part.sizes.find(s => s.size === sizeLabel)
      if (!sizeObj) return []
      return sizeObj.suppliers.map(s => ({
        ...s,
        vendor: state.vendors.find(v => v.id === s.vendorId)
      }))
    },

    bestPriceVendorForSize: (state) => (partId, sizeLabel) => {
      const part = state.parts.find(p => p.id === partId)
      if (!part) return null
      const sizeObj = part.sizes.find(s => s.size === sizeLabel)
      if (!sizeObj || sizeObj.suppliers.length === 0) return null
      return sizeObj.suppliers.reduce((min, s) => s.price < min.price ? s : min, sizeObj.suppliers[0]).vendorId
    },

    findProcurementById: (state) => (id) =>
      state.procurements.find(p => p.id === id)
  },

  actions: {
    addProcurement(formData, vendorId) {
      const newId = 'PRQ-' + String(this.procurements.length + 1).padStart(3, '0')
      const now = new Date()
      const date = now.toLocaleDateString('en-IN', { month: 'short', day: 'numeric', year: 'numeric' })
      this.procurements.unshift({
        id: newId,
        partName:   formData.partName   || '',
        size:       formData.partCode   || '',
        quantity:   formData.quantity   || null,
        vendorId:   vendorId || formData.vendorId || '',
        priority:   formData.priority   || 'Medium',
        requiredBy: formData.requiredBy || '',
        notes:      formData.notes      || '',
        date,
        status: 'pending'
      })
      return newId
    },

    markReceived(id) {
      const req = this.procurements.find(p => p.id === id)
      if (req) req.status = 'received'
    }
  }
})
