<template>
  <div
    class="ocard"
    :class="{ selected }"
    :style="{ borderTopColor: CC[order.custType] }"
    @click="$emit('select', order.id)"
  >
    <div class="oc-head">
      <div class="oc-head-left">
        <span v-if="order.status !== 'shipped'" class="drag-handle" title="Drag to reorder">⠿</span>
        <span class="oc-id">{{ order.id }}</span>
      </div>
      <div class="oc-chips">
        <span class="chip" :style="{ background: PB[order.priority], color: PC[order.priority] }">{{ order.priority }}</span>
      </div>
    </div>

    <div class="oc-body">
      <div class="oc-name">{{ order.shop }}</div>
      <div class="items-wrap">
        <div v-for="(it, i) in order.items" :key="i" class="irow">
          <div class="irow-name-col">
            <span class="irow-name">{{ it.name }}</span>
            <span v-if="it.specs" class="irow-specs">{{ it.specs }}</span>
          </div>
          <span class="irow-qty">
            <span v-if="it.originalQty && it.qty !== it.originalQty">
              {{ it.qty }}/{{ it.originalQty }}
            </span>
            <span v-else>{{ it.qty || 1 }}</span>
          </span>
        </div>
      </div>
    </div>

    <div v-if="order.status === 'shipped'" class="oc-extra">
      <button class="dl-invoice-btn" @click.stop="downloadInvoice(order)">Download Invoice</button>
    </div>

    <div class="oc-foot">
      <span class="oc-val">{{ order.value }}</span>
      <span class="oc-dl">Placed {{ order.placedOn  }}</span>
    </div>
  </div>
</template>

<script>
import { CC, CB, PC, PB } from '../store.js'

export default {
  name: 'OrderCard',
  props: {
    order:    { type: Object,  required: true },
    selected: { type: Boolean, default: false }
  },
  emits: ['select'],
  data() {
    return { CC, CB, PC, PB }
  },
  methods: {
// ADD inside methods: {}
    downloadInvoice(order) {
      const lines = order.items.map(it =>
        `<tr>
          <td>
            <div style="display:flex; align-items:center; gap:12px;">
              <div style="width:40px;height:40px;background:#eff6ff;color:#2563eb;border-radius:8px;display:flex;align-items:center;justify-content:center;font-size:18px;">📦</div>
              <div>
                <div style="font-weight:600;color:#0f172a;">${it.name}</div>
                <div style="font-size:12px;color:#64748b;margin-top:2px;">${it.specs || 'Standard Packaging'}</div>
              </div>
            </div>
          </td>
          <td>
            <div style="text-align:center; padding:6px; background:#f8fafc; border:1px solid #e2e8f0; border-radius:6px; font-weight:600; color:#0f172a;">
              ${it.qty || 1}
            </div>
          </td>
        </tr>`
      ).join('')

      const html = `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
  <style>
    body { font-family: 'Inter', sans-serif; background-color: #e2e8f0; padding: 40px 20px; margin: 0; -webkit-font-smoothing: antialiased; }
    .card { max-width: 800px; margin: 0 auto; background: #fff; border-radius: 16px; box-shadow: 0 20px 40px -15px rgba(0,0,0,0.05); overflow: hidden; }
    .head { background: #0f172a; color: #fff; padding: 40px; display: flex; justify-content: space-between; align-items: center; }
    .head h1 { font-size: 28px; margin: 0; font-weight: 700; letter-spacing: -0.5px; }
    .head p { margin: 4px 0 0; color: #94a3b8; font-size: 14px; }
    .badge { display: inline-block; background: rgba(255,255,255,0.1); padding: 6px 12px; border-radius: 99px; font-size: 12px; font-weight: 600; text-transform: uppercase; letter-spacing: 1px; border: 1px solid rgba(255,255,255,0.2); }
    .body { padding: 40px; }
    .grid { display: grid; grid-template-columns: 1fr 1fr; gap: 32px; margin-bottom: 40px; }
    .block h3 { font-size: 11px; text-transform: uppercase; letter-spacing: 1.5px; color: #64748b; margin: 0 0 12px 0; }
    .block p { margin: 0 0 6px 0; font-size: 14px; line-height: 1.5; color:#0f172a;}
    .block .prim { font-weight: 600; font-size: 16px; }
    table { width: 100%; border-collapse: separate; border-spacing: 0; margin-bottom: 32px; }
    th { background: #f8fafc; color: #64748b; font-size: 12px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px; padding: 16px 20px; text-align: left; border-top: 1px solid #e2e8f0; border-bottom: 1px solid #e2e8f0; }
    th:first-child { border-radius: 8px 0 0 8px; border-left: 1px solid #e2e8f0; }
    th:last-child { border-radius: 0 8px 8px 0; text-align: center; border-right: 1px solid #e2e8f0; width: 100px; }
    td { padding: 20px; border-bottom: 1px solid #e2e8f0; }
    .tot-box { background: #eff6ff; border: 1px solid #dbeafe; border-radius: 12px; padding: 24px; display: flex; justify-content: space-between; align-items: center; margin-left: auto; max-width: 320px; }
    .tot-box span { font-size: 14px; color: #2563eb; font-weight: 600; text-transform: uppercase; letter-spacing: 1px; }
    .tot-box strong { font-size: 28px; color: #2563eb; font-weight: 700; }
    .foot { text-align: center; padding-top: 32px; border-top: 1px dashed #e2e8f0; color: #64748b; font-size: 13px; }
  </style>
</head>
<body>
  <div class="card">
    <div class="head">
      <div>
        <h1>Invoice</h1>
        <p>${order.id} • Generated ${new Date().toLocaleDateString('en-IN', {day:'numeric', month:'short', year:'numeric'})}</p>
      </div>
      <div><div class="badge">${order.status}</div></div>
    </div>
    <div class="body">
      <div class="grid">
        <div class="block">
          <h3>Billed To</h3>
          <p class="prim">${order.customer}</p>
          <p style="color:#64748b">${order.shop}</p>
        </div>
        <div class="block">
          <h3>Order Details</h3>
          <p><span style="color:#64748b;display:inline-block;width:80px;">Date:</span> ${order.placedOn}</p>
          <p><span style="color:#64748b;display:inline-block;width:80px;">Priority:</span> ${order.priority || 'Standard'}</p>
          <p><span style="color:#64748b;display:inline-block;width:80px;">Carrier:</span> ${order.transport || '—'}</p>
        </div>
      </div>
      <table>
        <thead><tr><th>Description</th><th>Quantity</th></tr></thead>
        <tbody>${lines}</tbody>
      </table>
      <div class="tot-box">
        <span>Total Amount</span>
        <strong>${order.value}</strong>
      </div>
      <div class="foot">Thank you for your business!</div>
    </div>
  </div>
</body>
</html>`

      const blob = new Blob([html], { type: 'text/html' })
      const url  = URL.createObjectURL(blob)
      const a    = document.createElement('a')
      a.href     = url
      a.download = `Invoice-${order.id}.html`
      a.click()
      URL.revokeObjectURL(url)
    }
  }
}
</script>

<style scoped>
.ocard {
  background: var(--white);
  border: 1.5px solid var(--border-2);
  border-radius: 8px;
  flex-shrink: 0;
  cursor: grab; user-select: none;
  transition: border-color 0.12s, box-shadow 0.12s, transform 0.12s;
  position: relative; overflow: hidden;
  border-top: 2.5px solid transparent;
  animation: fadeUp 0.18s ease both;
}
.ocard:active { cursor: grabbing; }
.ocard:hover {
  border-color: var(--border);
  box-shadow: 0 2px 12px rgba(0,0,0,.07);
  transform: translateY(-1px);
}
.ocard.selected         { border-color: var(--blue) !important; box-shadow: 0 0 0 2px rgba(37,99,235,.15); }

@keyframes fadeUp {
  from { opacity: 0; transform: translateY(5px); }
  to   { opacity: 1; transform: translateY(0); }
}

.oc-head {
  display: flex; align-items: center; justify-content: space-between;
  padding: 9px 12px 8px;
  border-bottom: 1px solid var(--border-2);
}
.oc-head-left { display: flex; align-items: center; gap: 6px; }
.drag-handle {
  font-size: 13px; color: var(--ink-4); cursor: grab;
  opacity: 0.4; transition: opacity 0.15s;
  line-height: 1;
}
.ocard:hover .drag-handle { opacity: 0.9; }
.oc-id    { font-family: 'Geist Mono', monospace; font-size: 10.5px; color: var(--blue); }
.oc-chips { display: flex; gap: 4px; }

.oc-body  { padding: 10px 12px 2px; }
.oc-name  { font-size: 14px; font-weight: 600; color: var(--ink); margin-bottom: 3px; letter-spacing: -0.2px; }
.oc-sub   { font-size: 11px; color: var(--ink-4); display: flex; align-items: center; gap: 5px; margin-bottom: 9px; }
.cust-pip { width: 5px; height: 5px; border-radius: 50%; flex-shrink: 0; display: inline-block; }

.items-wrap { display: flex; flex-direction: column; gap: 1px; margin-bottom: 10px; }
.irow {
  display: flex; justify-content: space-between; align-items: center;
  font-size: 11px; padding: 3px 0;
  border-bottom: 1px solid var(--border-2);
}
.irow:last-child { border-bottom: none; }
.irow-name-col { display: flex; flex-direction: column; gap: 1px; min-width: 0; }
.irow-name { color: var(--ink-3); }
.irow-specs { font-size: 9.5px; color: var(--ink-4); opacity: 0.75; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.irow-qty  { font-family: 'Geist Mono', monospace; font-size: 10px; font-weight: 500; color: var(--ink-3); flex-shrink: 0; }

.oc-extra { padding: 0 12px 8px; display: flex; gap: 10px; flex-wrap: wrap; font-size: 11px; color: var(--ink-4); }
.oc-extra span { display: flex; align-items: center; gap: 3px; }

.oc-foot {
  display: flex; justify-content: space-between; align-items: center;
  padding: 8px 12px;
  border-top: 1px solid var(--border-2);
  background: var(--surface);
}
.oc-val { font-family: 'Geist Mono', monospace; font-size: 12.5px; font-weight: 500; color: var(--ink); }
.oc-dl  { font-size: 10.5px; color: var(--ink-4); }

/* ADD at bottom of <style scoped> */
.dl-invoice-btn {
  background: none; border: 1.5px solid var(--border); border-radius: 4px;
  padding: 2px 8px; font-size: 10.5px; font-weight: 600; color: var(--blue);
  cursor: pointer; font-family: 'Geist', sans-serif; transition: all 0.12s;
}
.dl-invoice-btn:hover { background: var(--blue-dim); border-color: var(--blue); }
</style>