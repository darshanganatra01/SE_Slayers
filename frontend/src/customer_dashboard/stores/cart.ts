import { defineStore } from 'pinia';
import { ref, computed, watch } from 'vue';
import type { CartItem, Product, SKU } from '@cd/types';
import { useAuthStore } from '@/stores/auth';

export const useCartStore = defineStore('cart', () => {
  const items = ref<CartItem[]>([]);
  const authStore = useAuthStore();

  const getStorageKey = () => `se_slayers.cart.${authStore.user?.uid || 'guest'}`;

  const loadFromStorage = () => {
    try {
      const raw = localStorage.getItem(getStorageKey());
      if (raw) {
        items.value = JSON.parse(raw);
      } else {
        items.value = [];
      }
    } catch {
      items.value = [];
    }
  };

  watch(() => authStore.user?.uid, () => {
    loadFromStorage();
  }, { immediate: true });

  watch(items, () => {
    localStorage.setItem(getStorageKey(), JSON.stringify(items.value));
  }, { deep: true });


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
