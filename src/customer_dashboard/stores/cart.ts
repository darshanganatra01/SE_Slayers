import { defineStore } from 'pinia';
import { ref, computed } from 'vue';
import type { CartItem, Product, SKU } from '@cd/types';

export const useCartStore = defineStore('cart', () => {
  const items = ref<CartItem[]>([]);

  const addItem = (product: Product, sku: SKU, quantity = 1) => {
    const existing = items.value.find(i => i.sku.skuId === sku.skuId);
    if (existing) {
      existing.quantity += quantity;
    } else {
      items.value.push({ product, sku, quantity });
    }
  };

  const removeItem = (skuId: string) => {
    items.value = items.value.filter(i => i.sku.skuId !== skuId);
  };

  const updateQuantity = (skuId: string, quantity: number) => {
    if (quantity <= 0) {
      removeItem(skuId);
    } else {
      const item = items.value.find(i => i.sku.skuId === skuId);
      if (item) {
        item.quantity = quantity;
      }
    }
  };

  const clearCart = () => {
    items.value = [];
  };

  const totalItems = computed(() => items.value.reduce((sum, i) => sum + i.quantity, 0));
  const totalPrice = computed(() => items.value.reduce((sum, i) => sum + i.sku.currentSell * i.quantity, 0));

  return { items, addItem, removeItem, updateQuantity, clearCart, totalItems, totalPrice };
});
