<template>
  <div class="comparison">
    <!-- No part selected -->
    <div v-if="!part" class="empty-state">
      <div class="es-icon">🔍</div>
      <div class="es-text">Select a part</div>
      <div class="es-sub">Choose a part from the left to compare vendors</div>
    </div>

    <!-- Part selected -->
    <template v-else>
      <div class="cmp-header">
        <div>
          <div class="cmp-title">{{ part.name }}</div>
          <div class="cmp-code">{{ part.code }} · {{ vendors.length }} vendor{{ vendors.length !== 1 ? 's' : '' }}</div>
        </div>
      </div>

      <div class="cmp-cards">
        <VendorCard
          v-for="v in vendors"
          :key="v.vendorId"
          :vendor="v.vendor"
          :price="v.price"
          :lead-time="v.leadTime"
          :is-best-price="v.vendorId === bestPriceId"
        />
      </div>

      <!-- Last purchased + action -->
      <div v-if="lastPurchased" class="cmp-footer">
        <div class="cmp-last">
          <span class="cmp-last-label">Last purchased from</span>
          <span class="cmp-last-vendor">{{ lastPurchased.vendorName }}</span>
          <span class="cmp-last-date">on {{ lastPurchased.date }} · ₹{{ lastPurchased.price.toLocaleString('en-IN') }}</span>
        </div>
        <button class="btn btn-primary" @click="$emit('procure', part)">Make Procurement Request</button>
      </div>
    </template>
  </div>
</template>

<script>
import VendorCard from './VendorCard.vue'

export default {
  name: 'VendorComparison',
  components: { VendorCard },
  props: {
    part:          { type: Object, default: null },
    vendors:       { type: Array, default: () => [] },
    bestPriceId:   { type: String, default: null },
    lastPurchased: { type: Object, default: null }
  },
  emits: ['procure']
}
</script>

<style scoped>
.comparison {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.cmp-header {
  padding: 14px 18px;
  border-bottom: 1.5px solid var(--border-2);
  flex-shrink: 0;
}
.cmp-title {
  font-size: 15px;
  font-weight: 600;
  color: var(--ink);
}
.cmp-code {
  font-size: 11px;
  color: var(--ink-4);
  font-family: 'Geist Mono', monospace;
  margin-top: 2px;
}

.cmp-cards {
  flex: 1;
  overflow-y: auto;
  padding: 14px 18px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.cmp-footer {
  border-top: 1.5px solid var(--border);
  padding: 12px 18px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-shrink: 0;
  background: var(--surface);
}
.cmp-last {
  display: flex;
  align-items: center;
  gap: 5px;
  flex-wrap: wrap;
}
.cmp-last-label {
  font-size: 11px;
  color: var(--ink-4);
}
.cmp-last-vendor {
  font-size: 11.5px;
  font-weight: 600;
  color: var(--ink);
}
.cmp-last-date {
  font-size: 11px;
  color: var(--ink-4);
  font-family: 'Geist Mono', monospace;
}
</style>
