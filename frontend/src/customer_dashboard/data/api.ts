import type { Product, SKU } from '../types'

const API_BASE = '/api/customer'

export async function fetchProducts(): Promise<Product[]> {
  const response = await fetch(`${API_BASE}/products`)
  if (!response.ok) {
    throw new Error('Failed to fetch products')
  }
  return response.json()
}

export async function fetchCategories(): Promise<string[]> {
  const response = await fetch(`${API_BASE}/categories`)
  if (!response.ok) {
    throw new Error('Failed to fetch categories')
  }
  return response.json()
}


export async function fetchProductDetail(pid: string): Promise<{ product: Product, skus: SKU[] } | null> {
  const response = await fetch(`${API_BASE}/products/${pid}`)
  if (!response.ok) {
    if (response.status === 404) return null
    throw new Error('Failed to fetch product details')
  }
  return response.json()
}

export async function placeOrder(cid: string, items: { skuId: string, quantity: number }[]): Promise<any> {
  const response = await fetch(`${API_BASE}/orders`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({ cid, items })
  })
  if (!response.ok) {
    throw new Error('Failed to place order')
  }
  return response.json()
}

export async function getOrders(cid: string) {
  const response = await fetch(`${API_BASE}/orders?cid=${encodeURIComponent(cid)}`)
  if (!response.ok) {
    throw new Error('Failed to fetch orders')
  }
  return response.json()
}

export async function getOrderDetails(coId: string) {
  const response = await fetch(`${API_BASE}/orders/${encodeURIComponent(coId)}`)
  if (!response.ok) {
    throw new Error('Failed to fetch order details')
  }
  return response.json()
}

export async function getInvoices(cid: string) {
  const response = await fetch(`${API_BASE}/invoices?cid=${encodeURIComponent(cid)}`)
  if (!response.ok) {
    throw new Error('Failed to fetch invoices')
  }
  return response.json()
}

export async function getInvoiceDetails(invId: string) {
  const response = await fetch(`${API_BASE}/invoices/${encodeURIComponent(invId)}`)
  if (!response.ok) {
    throw new Error('Failed to fetch invoice details')
  }
  return response.json()
}

export async function getItems(cid: string) {
  const response = await fetch(`${API_BASE}/items?cid=${encodeURIComponent(cid)}`)
  if (!response.ok) {
    throw new Error('Failed to fetch items')
  }
  return response.json()
}

export async function getItemDetails(codId: string) {
  const response = await fetch(`${API_BASE}/items/${encodeURIComponent(codId)}`)
  if (!response.ok) {
    throw new Error('Failed to fetch item details')
  }
  return response.json()
}

export async function confirmReceipt(cinvId: string, uid: string) {
  const response = await fetch(`${API_BASE}/receive`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({ cinv_id: cinvId, uid })
  })
  if (!response.ok) {
    const error = await response.json()
    throw new Error(error.message || 'Failed to confirm receipt')
  }
  return response.json()
}
