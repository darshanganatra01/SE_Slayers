<template>
  <div class="tbl-wrap">
    <table>
      <colgroup>
        <col style="width:30%">
        <col style="width:70%">
      </colgroup>
      <thead>
        <tr>
          <th>Product name</th>
          <th>Sizes</th>
        </tr>
      </thead>
      <tbody>
        <tr
          v-for="prod in products"
          :key="prod.key"
          class="cr"
          @click="$emit('open-profit', prod.key)"
        >
          <td>
            <div class="pn">{{ prod.name }}</div>
            <div class="pc">{{ prod.category }}</div>
          </td>
          <td>
            <div v-if="prod.sizes.length" class="size-chips">
              <span
                v-for="(sz, idx) in prod.sizes"
                :key="idx"
                class="sc"
                :class="chipClass(sz.status)"
              >{{ sz.label }}</span>
            </div>
            <div v-else class="empty-size">No sizes available yet</div>
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<script>
export default {
  name: 'PortfolioTable',
  props: {
    products: { type: Array, default: () => [] }
  },
  emits: ['open-profit'],
  methods: {
    chipClass(status) {
      if (status === 'ok')  return 'sc-ok'
      if (status === 'low') return 'sc-low'
      if (status === 'out') return 'sc-out'
      return 'sc-ok'
    }
  }
}
</script>

<style scoped>
.tbl-wrap {
  background: var(--white);
  border: 1.5px solid var(--border);
  border-radius: 8px;
  overflow: hidden;
  flex-shrink: 0;
}
table { width: 100%; border-collapse: collapse; table-layout: fixed; }
thead tr { border-bottom: 1.5px solid var(--border); }
th {
  padding: 9px 12px; text-align: left;
  font-size: 11px; font-weight: 500; text-transform: uppercase;
  letter-spacing: .06em; color: var(--ink-4);
  background: var(--surface); white-space: nowrap;
}
th:first-child { padding-left: 16px; }
th.r { text-align: right; }
td {
  padding: 11px 12px; font-size: 12.5px;
  border-bottom: 1px solid var(--border-2);
  vertical-align: middle;
}
td:first-child { padding-left: 16px; }
td.r { text-align: right; }
tr:last-child td { border-bottom: none; }
.cr { cursor: pointer; transition: background .1s; }
.cr:hover { background: var(--surface); }

.pn { font-size: 13px; font-weight: 500; }
.pc { font-size: 11px; color: var(--ink-4); margin-top: 1px; }

/* size chips */
.size-chips { display: flex; gap: 4px; flex-wrap: wrap; }
.empty-size {
  font-size: 12px;
  color: var(--ink-4);
}
.sc {
  font-size: 11px; border-radius: 4px;
  padding: 2px 7px; font-weight: 500; border: 1px solid;
}
.sc-ok  { background: var(--green-dim); color: var(--green); border-color: #bbf7d0; }
.sc-low { background: var(--amber-dim); color: #92400e; border-color: #fde68a; }
.sc-out { background: var(--red-dim);   color: var(--red);   border-color: #fecaca; }


</style>
