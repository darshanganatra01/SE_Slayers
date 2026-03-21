<template>
  <div class="vcard" :class="{ 'best-price': isBestPrice }">
    <div class="vc-top">
      <div>
        <div class="vc-name">{{ vendor.name }}</div>
        <div class="vc-meta">
          <span>{{ vendor.location }}</span>
          <span class="vc-dot">·</span>
          <span>{{ vendor.frequency }}</span>
        </div>
      </div>
      <span v-if="isBestPrice" class="chip vc-best">Best Price</span>
    </div>

    <div class="vc-details">
      <div class="vc-detail">
        <span class="vc-label">Price</span>
        <span class="vc-value">₹{{ price.toLocaleString('en-IN') }}</span>
      </div>
      <div class="vc-detail">
        <span class="vc-label">Lead Time</span>
        <span class="vc-value vc-lead">
          <span class="vc-lead-dot" :style="{ background: leadColor }"></span>
          {{ leadTime }} day{{ leadTime !== 1 ? 's' : '' }}
        </span>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'VendorCard',
  props: {
    vendor:      { type: Object, required: true },
    price:       { type: Number, required: true },
    leadTime:    { type: Number, required: true },
    isBestPrice: { type: Boolean, default: false }
  },
  computed: {
    leadColor() {
      if (this.leadTime <= 3) return 'var(--green)'
      if (this.leadTime <= 7) return 'var(--amber)'
      return 'var(--red)'
    }
  }
}
</script>

<style scoped>
.vcard {
  background: var(--white);
  border: 1.5px solid var(--border);
  border-radius: 8px;
  padding: 12px 14px;
  transition: border-color 0.12s;
}
.vcard:hover {
  border-color: var(--ink-4);
}
.vcard.best-price {
  border-color: var(--green);
  background: var(--green-dim);
}

.vc-top {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  margin-bottom: 10px;
}
.vc-name {
  font-size: 13px;
  font-weight: 600;
  color: var(--ink);
}
.vc-meta {
  font-size: 11px;
  color: var(--ink-4);
  margin-top: 2px;
  display: flex;
  align-items: center;
  gap: 4px;
}
.vc-dot { color: var(--border); }

.vc-best {
  background: var(--green-dim);
  color: var(--green);
  flex-shrink: 0;
}

.vc-details {
  display: flex;
  gap: 20px;
}
.vc-detail {
  display: flex;
  flex-direction: column;
  gap: 2px;
}
.vc-label {
  font-size: 9.5px;
  font-weight: 600;
  color: var(--ink-4);
  text-transform: uppercase;
  letter-spacing: 0.3px;
}
.vc-value {
  font-size: 13px;
  font-weight: 600;
  color: var(--ink);
  font-family: 'Geist Mono', monospace;
}

.vc-lead {
  display: flex;
  align-items: center;
  gap: 5px;
  font-family: 'Geist', sans-serif;
  font-weight: 500;
  color: var(--ink-2);
}
.vc-lead-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  flex-shrink: 0;
}
</style>
