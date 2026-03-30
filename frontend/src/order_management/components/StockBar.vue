<template>
  <div class="stock-bar">
    <div class="sb-label">Stock</div>
    <div class="sb-items">
      <div v-for="(d, name) in inventory" :key="name" class="sb-item">
        <span class="sb-name">{{ name }}</span>
        <span class="sb-qty" :style="{ color: stockColor(d) }">{{ d.stock }}</span>
        <div class="sb-track">
          <div class="sb-fill" :style="{ width: pct(d) + '%', background: stockColor(d) }"></div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'StockBar',
  props: {
    inventory: { type: Object, required: true }
  },
  methods: {
    pct(d)        { return Math.round((d.stock / d.max) * 100) },
    stockColor(d) {
      const p = this.pct(d)
      return p < 25 ? '#dc2626' : p < 55 ? '#d97706' : '#16a34a'
    }
  }
}
</script>

<style scoped>
.stock-bar {
  padding: 7px 22px; background: var(--white);
  border-top: 1.5px solid var(--border);
  display: flex; align-items: center; gap: 16px;
  flex-shrink: 0; overflow-x: auto;
}
.stock-bar::-webkit-scrollbar { display: none; }
.sb-label {
  font-size: 9.5px; font-weight: 600; color: var(--ink-4);
  text-transform: uppercase; letter-spacing: 1px; flex-shrink: 0;
}
.sb-items { display: flex; gap: 14px; }
.sb-item  { display: flex; align-items: center; gap: 6px; flex-shrink: 0; }
.sb-name  { font-size: 11px; color: var(--ink-3); }
.sb-qty   { font-family: 'Geist Mono', monospace; font-size: 11px; font-weight: 500; }
.sb-track { width: 36px; height: 3px; background: var(--border-2); border-radius: 2px; overflow: hidden; }
.sb-fill  { height: 100%; border-radius: 2px; transition: width 0.5s; }
</style>