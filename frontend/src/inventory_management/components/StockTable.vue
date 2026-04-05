<template>
  <div class="tbl-wrap">
    <table>
      <colgroup>
        <col style="width:26%">
        <col style="width:28%">
        <col style="width:20%">
        <col style="width:14%">
        <col style="width:12%">
      </colgroup>
      <thead>
        <tr>
          <th>Part name</th>
          <th>Size &amp; specifications</th>
          <th>Stock level</th>
          <th>Status</th>
          <th class="r">Sell price</th>
        </tr>
      </thead>
      <tbody v-if="filteredParts.length">
        <tr
          v-for="p in filteredParts"
          :key="p.id"
          class="cr"
          @click="$emit('go-vendor', vendorTarget(p))"
        >
          <td>
            <div class="pn">{{ p.name }}</div>
            <div class="pc">{{ p.category }}</div>
          </td>
          <td>
            <div class="pd">{{ sizeDisplay(p) }}</div>
            <div class="pd2">{{ p.spec }}</div>
          </td>
          <td class="sbw">
            <div class="sbn">{{ p.stock }} <span>/ {{ p.maxStock }}</span></div>
            <div class="sbb">
              <div class="sbf" :class="barColor(p)" :style="{ width: barWidth(p) }"></div>
            </div>
          </td>
          <td>
            <span class="badge" :class="badgeClass(p.status)">{{ badgeLabel(p.status) }}</span>
          </td>
          <td class="r sp">₹{{ formatPrice(p.sellPrice) }}</td>
        </tr>
      </tbody>
      <tbody v-else>
        <tr class="empty-row"><td colspan="5">No parts match your filter</td></tr>
      </tbody>
    </table>
  </div>
</template>

<script>
export default {
  name: 'StockTable',
  props: {
    parts:  { type: Array,  default: () => [] },
    tab:    { type: String,  default: 'all' },
    search: { type: String,  default: '' }
  },
  emits: ['go-vendor'],
  computed: {
    filteredParts() {
      let list = this.parts
      // tab filter
      if (this.tab === 'instock') list = list.filter(p => p.status === 'instock')
      else if (this.tab === 'low') list = list.filter(p => p.status === 'low')
      else if (this.tab === 'out') list = list.filter(p => p.status === 'out')
      // search filter
      if (this.search) {
        const q = this.search.toLowerCase()
        list = list.filter(p => {
          const hay = `${p.name} ${p.sku} ${p.category} ${p.size} ${p.dims} ${p.spec}`.toLowerCase()
          return hay.includes(q)
        })
      }
      return list
    }
  },
  methods: {
    vendorTarget(p) {
      return {
        source: 'inventory-stock',
        partId: p.pid || '',
        specKey: this.specKey(p),
        specLabel: this.sizeDisplay(p)
      }
    },
    specKey(p) {
      if (p.spec) return `${p.size}\n${p.spec}`
      return p.size
    },
    sizeDisplay(p) {
      if (p.dims) return `${p.size} · ${p.dims}`
      return p.size
    },
    barWidth(p) {
      if (p.maxStock === 0) return '0%'
      return Math.min(100, Math.round((p.stock / p.maxStock) * 100)) + '%'
    },
    barColor(p) {
      if (p.stock === 0) return 'bar-red'
      const pct = p.stock / p.maxStock
      if (pct <= 0.25) return 'bar-red'
      if (pct <= 0.5) return 'bar-amber'
      return 'bar-green'
    },
    badgeClass(s) {
      if (s === 'instock') return 'badge-green'
      if (s === 'low') {
        // check if critical (stock <= 20% of max)
        return 'badge-amber'
      }
      if (s === 'out') return 'badge-red'
      return 'badge-amber'
    },
    badgeLabel(s) {
      if (s === 'instock') return 'In stock'
      if (s === 'low') return 'Low stock'
      if (s === 'out') return 'Out of stock'
      return s
    },
    formatPrice(value) {
      return Number(value || 0).toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
    }
  }
}
</script>

<style scoped>
.tbl-wrap {
  --table-head-height: 42px;
  --table-row-height: 58px;
  --table-visible-rows: 10;
  background: var(--white);
  border: 1.5px solid var(--border);
  border-radius: 8px;
  overflow-x: hidden;
  overflow-y: auto;
  flex-shrink: 0;
  max-height: calc(var(--table-head-height) + (var(--table-row-height) * var(--table-visible-rows)));
}
table { width: 100%; border-collapse: collapse; table-layout: fixed; }
thead tr { border-bottom: 1.5px solid var(--border); }
th {
  position: sticky;
  top: 0;
  z-index: 2;
  padding: 9px 12px; text-align: left;
  font-size: 11px; font-weight: 500; text-transform: uppercase;
  letter-spacing: .06em; color: var(--ink-4);
  background: var(--surface); white-space: nowrap; overflow: hidden;
}
th:first-child { padding-left: 16px; }
th.r { text-align: right; }
td {
  padding: 11px 12px; font-size: 12.5px;
  border-bottom: 1px solid var(--border-2);
  vertical-align: middle; overflow: hidden;
}
td:first-child { padding-left: 16px; }
td.r { text-align: right; }
tr:last-child td { border-bottom: none; }
.cr { cursor: pointer; transition: background .1s; }
.cr:hover { background: var(--surface); }

.pn { font-size: 13px; font-weight: 500; }
.pc { font-size: 11px; color: var(--ink-4); margin-top: 1px; }
.pd { font-size: 12px; color: var(--ink-3); }
.pd2 { font-size: 11px; color: var(--ink-4); margin-top: 1px; }

/* stock bar */
.sbw { min-width: 100px; }
.sbn { font-size: 12.5px; font-weight: 500; margin-bottom: 4px; }
.sbn span { font-weight: 400; color: var(--ink-4); font-size: 11px; }
.sbb { height: 3px; background: var(--border-2); border-radius: 2px; overflow: hidden; }
.sbf { height: 100%; border-radius: 2px; }
.bar-green { background: var(--green); }
.bar-amber { background: var(--amber); }
.bar-red   { background: var(--red); }

/* badge */
.badge {
  display: inline-block; padding: 2px 8px;
  border-radius: 4px; font-size: 12px; font-weight: 500;
}
.badge-green { background: var(--green-dim); color: var(--green); }
.badge-amber { background: var(--amber-dim); color: #92400e; }
.badge-red   { background: var(--red-dim);   color: var(--red); }
.sp {
  font-weight: 600;
  font-variant-numeric: tabular-nums;
}

.empty-row td {
  padding: 32px; text-align: center;
  color: var(--ink-4); font-size: 13px;
}

.tbl-wrap::-webkit-scrollbar {
  width: 8px;
}

.tbl-wrap::-webkit-scrollbar-thumb {
  background: var(--border-2);
  border-radius: 999px;
}
</style>
