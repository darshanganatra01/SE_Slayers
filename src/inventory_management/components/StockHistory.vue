<template>
  <div class="panel">
    <div class="panel-head">
      <div>
        <div class="panel-title">Stock updates</div>
        <div class="panel-sub">Dispatches &amp; receipts</div>
      </div>
    </div>
    <div v-for="(h, i) in history" :key="i" class="hr">
      <div
        class="hdot"
        :style="{ background: h.type === 'in' ? 'var(--green)' : 'var(--red)' }"
      ></div>
      <div class="hb">
        <div class="ht" v-html="h.text"></div>
        <div class="htm">{{ h.time }}</div>
      </div>
      <div
        class="hd"
        :style="{ color: h.delta > 0 ? 'var(--green)' : 'var(--red)' }"
      >{{ h.delta > 0 ? '+' + h.delta : h.delta }}</div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'StockHistory',
  props: {
    history: { type: Array, default: () => [] }
  }
}
</script>

<style scoped>
.panel {
  background: var(--white);
  border: 1.5px solid var(--border);
  border-radius: 8px;
  overflow: hidden;
}
.panel-head {
  display: flex; align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  border-bottom: 1px solid var(--border);
}
.panel-title { font-size: 13px; font-weight: 600; }
.panel-sub   { font-size: 11.5px; color: var(--ink-4); margin-top: 2px; }

.hr {
  display: flex; align-items: flex-start;
  padding: 11px 16px;
  border-bottom: 1px solid var(--border-2);
  gap: 10px;
}
.hr:last-child { border-bottom: none; }
.hr:hover { background: var(--surface); }

.hdot {
  width: 7px; height: 7px;
  border-radius: 50%;
  margin-top: 4px; flex-shrink: 0;
}
.hb { flex: 1; min-width: 0; }
.ht { font-size: 12.5px; line-height: 1.4; }
.ht :deep(strong) { font-weight: 500; }
.htm { font-size: 11px; color: var(--ink-4); margin-top: 2px; }
.hd {
  font-size: 12.5px; font-weight: 600;
  margin-left: auto; padding-top: 1px;
  font-variant-numeric: tabular-nums;
  white-space: nowrap;
}
</style>
