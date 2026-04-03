<template>
  <div class="stat-cards">
    <div class="stat-card">
      <div class="stat-label">Total parts</div>
      <div class="stat-value">{{ total }}</div>
    </div>
    <div class="stat-card">
      <div class="stat-label">In stock</div>
      <div class="stat-value" style="color: var(--green)">{{ inStock }}</div>
    </div>
    <div class="stat-card">
      <div class="stat-label">Low stock items</div>
      <div class="stat-value" style="color: var(--amber)">{{ lowStock }}</div>
    </div>
    <div class="stat-card">
      <div class="stat-label">Inventory value</div>
      <div class="stat-value stat-value--med">₹{{ formattedInventoryValue }}</div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'StatCards',
  props: {
    total:   { type: Number, default: 0 },
    inStock: { type: Number, default: 0 },
    lowStock:{ type: Number, default: 0 },
    inventoryValue: { type: Number, default: 0 }
  },
  computed: {
    formattedInventoryValue() {
      return Math.round(this.inventoryValue).toLocaleString('en-IN')
    }
  }
}
</script>

<style scoped>
.stat-cards {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  border: 1.5px solid var(--border);
  border-radius: 8px;
  overflow: hidden;
  background: var(--border);
  gap: 1px;
  flex-shrink: 0;
}
.stat-card {
  background: var(--white);
  padding: 16px 18px;
}
.stat-label {
  font-size: 12px;
  color: var(--ink-3);
  margin-bottom: 7px;
}
.stat-value {
  font-size: 26px;
  font-weight: 600;
  letter-spacing: -1px;
  line-height: 1;
  font-family: 'Geist', sans-serif;
}
.stat-value--med {
  font-size: 20px;
}
</style>
