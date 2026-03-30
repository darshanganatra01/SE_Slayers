import { Product, SKU, CustomerOrder, CustomerInvoice, CustomerInvDetail, Address, OrderWithDetails } from '@cd/types';

export const products: Product[] = [
  { pid: 'P101', pName: 'G. I. Step Connector', category: 'Plumbing', unitMeasurement: 'piece', image: '@/customer_dashboard/customer_assets/GI Step connector.png' },
  { pid: 'P102', pName: 'S. S. Step Nipple', category: 'Plumbing', unitMeasurement: 'piece', image: '@/customer_dashboard/customer_assets/SS Step Nipple.png' },
  { pid: 'P103', pName: 'Hose Clip (Light)', category: 'Hardware', unitMeasurement: 'pack (12 pcs)', image: '@/customer_dashboard/customer_assets/Hose clip (Light).png' },
];

export const skus: SKU[] = [
  // P101 (G.I. Step Connector - Medium)
  { skuId: 'SKU101-1', vpId: 'VP101-1', pid: 'P101', currentBuy: 18, currentSell: 23, specs: '{"size": "0.5\\" x 6\\""}', stockQty: 100 },
  { skuId: 'SKU101-2', vpId: 'VP101-2', pid: 'P101', currentBuy: 20, currentSell: 26, specs: '{"size": "0.75\\" x 6\\""}', stockQty: 80 },
  { skuId: 'SKU101-3', vpId: 'VP101-3', pid: 'P101', currentBuy: 30, currentSell: 37, specs: '{"size": "1\\" x 7\\""}', stockQty: 60 },
  { skuId: 'SKU101-4', vpId: 'VP101-4', pid: 'P101', currentBuy: 35, currentSell: 42, specs: '{"size": "1.25\\" x 7\\""}', stockQty: 50 },
  { skuId: 'SKU101-5', vpId: 'VP101-5', pid: 'P101', currentBuy: 40, currentSell: 48, specs: '{"size": "1.5\\" x 7\\""}', stockQty: 40 },

  // P102 (S.S. Step Nipple - Regular)
  { skuId: 'SKU102-1', vpId: 'VP102-1', pid: 'P102', currentBuy: 28, currentSell: 35, specs: '{"size": "0.5\\" x 6\\""}', stockQty: 90 },
  { skuId: 'SKU102-2', vpId: 'VP102-2', pid: 'P102', currentBuy: 34, currentSell: 42, specs: '{"size": "0.75\\" x 6\\""}', stockQty: 75 },
  { skuId: 'SKU102-3', vpId: 'VP102-3', pid: 'P102', currentBuy: 35, currentSell: 43, specs: '{"size": "1\\" x 7\\""}', stockQty: 55 },

  // P103 (Hose Clip Light - Rate per 12 pieces)
  { skuId: 'SKU103-1', vpId: 'VP103-1', pid: 'P103', currentBuy: 180, currentSell: 220, specs: '{"size": "1.5\\"", "bolt": "12mm x 45mm", "range": "58 to 62 mm"}', stockQty: 30 },
  { skuId: 'SKU103-2', vpId: 'VP103-2', pid: 'P103', currentBuy: 190, currentSell: 230, specs: '{"size": "2\\"", "bolt": "12mm x 45mm", "range": "70 to 74 mm"}', stockQty: 25 },
  { skuId: 'SKU103-3', vpId: 'VP103-3', pid: 'P103', currentBuy: 210, currentSell: 255, specs: '{"size": "2.5\\"", "bolt": "12mm x 45mm", "range": "80 to 84 mm"}', stockQty: 20 },
];

export const categories = ['All', 'Plumbing', 'Hardware'];

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
  // CINV001 for CO001
  { cDetailId: 'CD001', cInvId: 'CINV001', skuId: 'SKU101-1', orderedQty: 5, deliveredQty: 5, salePrice: 23 },
  { cDetailId: 'CD002', cInvId: 'CINV001', skuId: 'SKU101-3', orderedQty: 1, deliveredQty: 1, salePrice: 37 },
  
  // CINV002 for CO002
  { cDetailId: 'CD003', cInvId: 'CINV002', skuId: 'SKU102-1', orderedQty: 10, deliveredQty: 0, salePrice: 35 },
  { cDetailId: 'CD004', cInvId: 'CINV002', skuId: 'SKU102-2', orderedQty: 5, deliveredQty: 0, salePrice: 42 },

  // CINV003 for CO003
  { cDetailId: 'CD005', cInvId: 'CINV003', skuId: 'SKU103-1', orderedQty: 2, deliveredQty: 0, salePrice: 220 },
  { cDetailId: 'CD006', cInvId: 'CINV003', skuId: 'SKU101-5', orderedQty: 12, deliveredQty: 0, salePrice: 48 },
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
  const matchingSkus = skus.filter(s => s.pid === pid);
  return product && matchingSkus.length > 0 ? { product, skus: matchingSkus } : null;
}

