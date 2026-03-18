import { Product, SKU, CustomerOrder, CustomerInvoice, CustomerInvDetail, Address, OrderWithDetails } from '@cd/types';

export const products: Product[] = [
  { pid: 'P001', pName: 'Claw Hammer', category: 'Hand Tools', unitMeasurement: 'piece', image: '🔨' },
  { pid: 'P002', pName: 'Phillips Screwdriver Set', category: 'Hand Tools', unitMeasurement: 'set', image: '🪛' },
  { pid: 'P003', pName: 'Adjustable Wrench 12"', category: 'Hand Tools', unitMeasurement: 'piece', image: '🔧' },
  { pid: 'P004', pName: 'Cordless Drill 20V', category: 'Power Tools', unitMeasurement: 'piece', image: '🔩' },
  { pid: 'P005', pName: 'Circular Saw 7.25"', category: 'Power Tools', unitMeasurement: 'piece', image: '⚙️' },
  { pid: 'P006', pName: 'Angle Grinder 4.5"', category: 'Power Tools', unitMeasurement: 'piece', image: '💿' },
  { pid: 'P007', pName: 'PVC Pipe 1" (10ft)', category: 'Plumbing', unitMeasurement: 'piece', image: '🔲' },
  { pid: 'P008', pName: 'Ball Valve 1/2"', category: 'Plumbing', unitMeasurement: 'piece', image: '🚰' },
  { pid: 'P009', pName: 'Copper Elbow 3/4"', category: 'Plumbing', unitMeasurement: 'piece', image: '📐' },
  { pid: 'P010', pName: 'LED Bulb 9W (Pack of 4)', category: 'Electrical', unitMeasurement: 'pack', image: '💡' },
  { pid: 'P011', pName: 'MCB 32A Single Pole', category: 'Electrical', unitMeasurement: 'piece', image: '⚡' },
  { pid: 'P012', pName: 'Wire 2.5mm (90m Roll)', category: 'Electrical', unitMeasurement: 'roll', image: '🔌' },
];

export const skus: SKU[] = [
  { skuId: 'SKU001', vpId: 'VP001', pid: 'P001', currentBuy: 180, currentSell: 299, specs: 'Steel head, fiberglass handle, 16oz', stockQty: 45 },
  { skuId: 'SKU002', vpId: 'VP002', pid: 'P002', currentBuy: 220, currentSell: 449, specs: '6-piece set, magnetic tips, ergonomic grip', stockQty: 30 },
  { skuId: 'SKU003', vpId: 'VP003', pid: 'P003', currentBuy: 350, currentSell: 599, specs: 'Chrome vanadium steel, 12 inch, wide jaw', stockQty: 25 },
  { skuId: 'SKU004', vpId: 'VP004', pid: 'P004', currentBuy: 2800, currentSell: 4999, specs: '20V Li-Ion, 2 batteries, 13mm chuck, LED light', stockQty: 12 },
  { skuId: 'SKU005', vpId: 'VP005', pid: 'P005', currentBuy: 3500, currentSell: 5999, specs: '1400W motor, 7.25" blade, laser guide', stockQty: 8 },
  { skuId: 'SKU006', vpId: 'VP006', pid: 'P006', currentBuy: 1800, currentSell: 2999, specs: '850W, 4.5" disc, anti-vibration handle', stockQty: 15 },
  { skuId: 'SKU007', vpId: 'VP007', pid: 'P007', currentBuy: 85, currentSell: 149, specs: 'Schedule 40, ASTM D1785, white', stockQty: 200 },
  { skuId: 'SKU008', vpId: 'VP008', pid: 'P008', currentBuy: 120, currentSell: 219, specs: 'Brass, full port, chrome plated', stockQty: 60 },
  { skuId: 'SKU009', vpId: 'VP009', pid: 'P009', currentBuy: 45, currentSell: 89, specs: 'Type L copper, 90° elbow, sweat fitting', stockQty: 100 },
  { skuId: 'SKU010', vpId: 'VP010', pid: 'P010', currentBuy: 180, currentSell: 349, specs: '9W = 60W equivalent, 6500K daylight, B22 base', stockQty: 80 },
  { skuId: 'SKU011', vpId: 'VP011', pid: 'P011', currentBuy: 140, currentSell: 249, specs: 'C-curve, 10kA breaking capacity, DIN rail', stockQty: 50 },
  { skuId: 'SKU012', vpId: 'VP012', pid: 'P012', currentBuy: 2200, currentSell: 3799, specs: 'FR PVC insulated, copper conductor, ISI marked', stockQty: 20 },
];

export const categories = ['All', 'Hand Tools', 'Power Tools', 'Plumbing', 'Electrical'];

export const mockAddresses: Address[] = [
  { id: 'A1', label: 'Workshop', line1: '42 Industrial Area, Phase 2', line2: 'Sector 18', city: 'Gurugram', state: 'Haryana', pincode: '122015' },
  { id: 'A2', label: 'Store', line1: '15 Main Market Road', line2: 'Near City Center', city: 'Delhi', state: 'Delhi', pincode: '110001' },
];

export const mockOrders: CustomerOrder[] = [
  { coId: 'CO001', cId: 'C001', orderDate: '2026-03-10', status: 'Delivered' },
  { coId: 'CO002', cId: 'C001', orderDate: '2026-03-14', status: 'Shipped' },
  { coId: 'CO003', cId: 'C001', orderDate: '2026-03-17', status: 'Confirmed' },
];

export const mockInvoices: CustomerInvoice[] = [
  { cInvId: 'CINV001', coId: 'CO001', invoiceDate: '2026-03-10', status: 'Paid' },
  { cInvId: 'CINV002', coId: 'CO002', invoiceDate: '2026-03-14', status: 'Pending' },
  { cInvId: 'CINV003', coId: 'CO003', invoiceDate: '2026-03-17', status: 'Pending' },
];

export const mockInvDetails: CustomerInvDetail[] = [
  { cDetailId: 'CD001', cInvId: 'CINV001', skuId: 'SKU001', orderedQty: 5, deliveredQty: 5, salePrice: 299 },
  { cDetailId: 'CD002', cInvId: 'CINV001', skuId: 'SKU004', orderedQty: 1, deliveredQty: 1, salePrice: 4999 },
  { cDetailId: 'CD003', cInvId: 'CINV002', skuId: 'SKU010', orderedQty: 3, deliveredQty: 0, salePrice: 349 },
  { cDetailId: 'CD004', cInvId: 'CINV003', skuId: 'SKU007', orderedQty: 20, deliveredQty: 0, salePrice: 149 },
  { cDetailId: 'CD005', cInvId: 'CINV003', skuId: 'SKU008', orderedQty: 10, deliveredQty: 0, salePrice: 219 },
];

export function getOrdersWithDetails(): OrderWithDetails[] {
  return mockOrders.map(order => {
    const invoice = mockInvoices.find(inv => inv.coId === order.coId)!;
    const details = mockInvDetails
      .filter(d => d.cInvId === invoice.cInvId)
      .map(d => {
        const sku = skus.find(s => s.skuId === d.skuId)!;
        const product = products.find(p => p.pid === sku.pid)!;
        return { ...d, product, sku };
      });
    const totalAmount = details.reduce((sum, d) => sum + d.salePrice * d.orderedQty, 0);
    return { order, invoice, items: details, totalAmount };
  });
}

export function getProductWithSku(pid: string) {
  const product = products.find(p => p.pid === pid);
  const sku = skus.find(s => s.pid === pid);
  return product && sku ? { product, sku } : null;
}
