// Catalog & Inventory
export interface Product {
  pid: string;
  pName: string;
  category: string;
  unitMeasurement: string;
  image: string;
}

export interface SKU {
  skuId: string;
  vpId: string;
  pid: string;
  currentBuy: number;
  currentSell: number;
  specs: string;
  stockQty: number;
}

// Customer Operations
export interface CustomerOrder {
  coId: string;
  cId: string;
  orderDate: string;
  status: 'Pending' | 'Confirmed' | 'Shipped' | 'Delivered' | 'Cancelled';
}

export interface CustomerInvoice {
  cInvId: string;
  coId: string;
  invoiceDate: string;
  status: 'Pending' | 'Paid';
}

export interface CustomerInvDetail {
  cDetailId: string;
  cInvId: string;
  skuId: string;
  orderedQty: number;
  deliveredQty: number;
  salePrice: number;
}

// App-specific types
export interface CartItem {
  product: Product;
  sku: SKU;
  quantity: number;
}

export interface User {
  id: string;
  name: string;
  email: string;
}

export interface Address {
  id: string;
  label: string;
  line1: string;
  line2: string;
  city: string;
  state: string;
  pincode: string;
}

export interface OrderWithDetails {
  order: CustomerOrder;
  invoice: CustomerInvoice;
  items: (CustomerInvDetail & { product: Product; sku: SKU })[];
  totalAmount: number;
}
