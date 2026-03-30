<template>
  <div v-if="visible" class="ovl" @click.self="$emit('close')">
    <div class="pop">
      <div class="pop-h">
        <div>
          <div class="pop-title">{{ data.title }}</div>
          <div class="pop-sub">Stock levels by size · tap to view vendor procurement</div>
        </div>
        <button class="pop-x" @click="$emit('close')">×</button>
      </div>
      <div class="pop-b">
        <div
          v-for="(r, i) in data.rows"
          :key="i"
          class="pop-row"
          @click="$emit('go-vendor', data.sku, r.size)"
        >
          <div class="pop-size-col">
            <div class="pop-size">{{ r.size }}</div>
            <div class="pop-dim">{{ r.dim }}</div>
          </div>
          <div class="pop-mid">
            <span class="badge" :class="badgeClass(r.status)">{{ badgeLabel(r.status) }}</span>
          </div>
          <div class="pop-stock-col">
            <div class="sbn">{{ r.stock }} <span>/ {{ r.maxStock }}</span></div>
            <div class="sbb">
              <div class="sbf" :class="barColor(r)" :style="{ width: barWidth(r) }"></div>
            </div>
          </div>
          <div class="pop-arrow">
            <svg fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><polyline points="9,18 15,12 9,6"/></svg>
          </div>
        </div>
      </div>
      <div class="pop-footer">
        <div>
          <div class="pop-total-lbl">Total stock</div>
          <div class="pop-total-val">{{ totalStock }} units</div>
        </div>
        <button class="btn-vendor" @click="$emit('go-vendor', data.sku, 'all'); $emit('close')">
          <svg fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path d="M3 9l9-7 9 7v11a2 2 0 01-2 2H5a2 2 0 01-2-2z"/><polyline points="9,22 9,12 15,12 15,22"/></svg>
          View all vendors for this product
        </button>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'ProfitPopup',
  props: {
    visible: { type: Boolean, default: false },
    data: {
      type: Object,
      default: () => ({ title: '', sku: '', rows: [] })
    }
  },
  emits: ['close', 'go-vendor'],
  computed: {
    totalStock() {
      return this.data.rows.reduce((sum, r) => sum + (r.stock || 0), 0)
    }
  },
  methods: {
    badgeClass(s) {
      if (s === 'ok')  return 'badge-green'
      if (s === 'low') return 'badge-amber'
      if (s === 'out') return 'badge-red'
      return 'badge-green'
    },
    badgeLabel(s) {
      if (s === 'ok')  return 'In stock'
      if (s === 'low') return 'Low stock'
      if (s === 'out') return 'Out of stock'
      return s
    },
    barWidth(r) {
      if (!r.maxStock) return '0%'
      return Math.round((r.stock / r.maxStock) * 100) + '%'
    },
    barColor(r) {
      if (r.stock === 0) return 'bar-red'
      const pct = r.stock / r.maxStock
      if (pct <= 0.25) return 'bar-red'
      if (pct <= 0.5) return 'bar-amber'
      return 'bar-green'
    }
  }
}
</script>

<style scoped>
.ovl {
  position: fixed; inset: 0;
  background: rgba(0,0,0,0.18);
  display: grid; place-items: center;
  z-index: 300;
}
.pop {
  background: var(--white);
  border-radius: 10px;
  width: 480px; max-width: 94vw;
  box-shadow: 0 8px 32px rgba(0,0,0,0.12);
  overflow: hidden;
}
.pop-h {
  padding: 16px 18px 14px;
  border-bottom: 1px solid var(--border);
  display: flex; align-items: flex-start;
  justify-content: space-between; gap: 12px;
}
.pop-title { font-size: 14px; font-weight: 600; }
.pop-sub   { font-size: 12px; color: var(--ink-4); margin-top: 2px; }
.pop-x {
  width: 26px; height: 26px;
  border-radius: 50%;
  border: 1px solid var(--border);
  background: var(--surface);
  cursor: pointer; display: grid; place-items: center;
  font-size: 16px; color: var(--ink-4); flex-shrink: 0;
}
.pop-x:hover { background: var(--border); }

.pop-b { padding: 0; }
.pop-row {
  display: grid;
  grid-template-columns: 120px 90px 1fr 20px;
  align-items: center;
  padding: 12px 18px;
  border-bottom: 1px solid var(--border-2);
  gap: 14px; cursor: pointer;
  transition: background .1s;
}
.pop-row:last-child { border-bottom: none; }
.pop-row:hover { background: var(--surface); }

.pop-size-col { min-width: 0; }
.pop-size { font-size: 13px; font-weight: 500; }
.pop-dim  { font-size: 11.5px; color: var(--ink-4); margin-top: 1px; }
.pop-mid  { display: flex; align-items: center; gap: 8px; min-width: 0; }

.badge {
  display: inline-block; padding: 1px 7px;
  border-radius: 4px; font-size: 11px; font-weight: 500;
  white-space: nowrap; flex-shrink: 0;
}
.badge-green { background: var(--green-dim); color: var(--green); }
.badge-amber { background: var(--amber-dim); color: #92400e; }
.badge-red   { background: var(--red-dim);   color: var(--red); }

/* stock bar — matching All Parts table */
.pop-stock-col { min-width: 80px; }
.sbn { font-size: 12.5px; font-weight: 500; margin-bottom: 4px; }
.sbn span { font-weight: 400; color: var(--ink-4); font-size: 11px; }
.sbb { height: 3px; background: var(--border-2); border-radius: 2px; overflow: hidden; }
.sbf { height: 100%; border-radius: 2px; }
.bar-green { background: var(--green); }
.bar-amber { background: var(--amber); }
.bar-red   { background: var(--red); }

.pop-arrow { color: var(--ink-4); display: flex; align-items: center; justify-content: flex-end; }
.pop-arrow svg { width: 14px; height: 14px; }
.pop-row:hover .pop-arrow { color: var(--blue); }

.pop-footer {
  display: flex; align-items: center;
  justify-content: space-between;
  padding: 12px 18px;
  background: var(--surface);
  border-top: 1px solid var(--border);
}
.pop-total-lbl { font-size: 12px; color: var(--ink-3); font-weight: 500; }
.pop-total-val { font-size: 14px; font-weight: 600; }

.btn-vendor {
  background: var(--blue-dim); color: var(--blue);
  border: 1px solid #bfdbfe; border-radius: 6px;
  padding: 5px 12px;
  font-family: 'Geist', sans-serif; font-size: 12.5px; font-weight: 500;
  cursor: pointer; display: flex; align-items: center; gap: 5px;
}
.btn-vendor:hover { background: #dbeafe; }
.btn-vendor svg { width: 12px; height: 12px; }
</style>
