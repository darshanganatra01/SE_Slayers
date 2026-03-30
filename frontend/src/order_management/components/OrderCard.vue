<template>
  <div
    class="ocard"
    :class="{ selected, dragging, 'drag-over-top': dragOverTop, 'drag-over-bottom': dragOverBottom }"
    :style="{ borderTopColor: CC[order.custType] }"
    draggable="true"
    @click="$emit('select', order.id)"
    @dragstart="onDragStart"
    @dragend="onDragEnd"
    @dragover.prevent="onDragOver"
    @dragleave="onDragLeave"
    @drop.prevent="onDrop"
  >
    <div class="oc-head">
      <span class="oc-id">{{ order.id }}</span>
      <div class="oc-chips">
        <span class="chip" :style="{ background: PB[order.priority], color: PC[order.priority] }">{{ order.priority }}</span>
      </div>
    </div>

    <div class="oc-body">
      <div class="oc-name">{{ order.shop }}</div>
      <div class="items-wrap">
        <div v-for="(it, i) in order.items" :key="i" class="irow">
          <span class="irow-name">{{ it.name }}</span>
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
      <span>🚚 {{ order.transport || '—' }}</span>
      <button class="dl-invoice-btn" @click.stop="downloadInvoice(order)">Download Invoice</button>
    </div>

    <div class="oc-foot">
      <span class="oc-val">{{ order.value }}</span>
      <span class="oc-dl">Placed {{ order.placedOn  }}</span>
    </div>

    <div class="drag-handle">⠿</div>
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
  emits: ['select', 'drag-start', 'drag-end', 'reorder'],
  data() {
    return { CC, CB, PC, PB, dragging: false, dragOverTop: false, dragOverBottom: false }
  },
  methods: {
    onDragStart(e) {
      this.dragging = true
      e.dataTransfer.effectAllowed = 'move'
      this.$emit('drag-start', this.order.id)
    },
    onDragEnd() {
      this.dragging = false
      this.dragOverTop = false
      this.dragOverBottom = false
      this.$emit('drag-end')
    },
    onDragOver(e) {
      const rect = this.$el.getBoundingClientRect()
      const mid  = rect.top + rect.height / 2
      this.dragOverTop    = e.clientY < mid
      this.dragOverBottom = e.clientY >= mid
    },
    onDragLeave() {
      this.dragOverTop = false
      this.dragOverBottom = false
    },
    onDrop(e) {
      const rect = this.$el.getBoundingClientRect()
      const mid  = rect.top + rect.height / 2
      this.$emit('reorder', { toId: this.order.id, pos: e.clientY < mid ? 'before' : 'after' })
      this.dragOverTop = false
      this.dragOverBottom = false
    },
// ADD inside methods: {}
    downloadInvoice(order) {
      const lines = order.items.map(it =>
        `<tr>
          <td style="padding:8px 12px;border-bottom:1px solid #e4e4e7">${it.name}</td>
          <td style="padding:8px 12px;border-bottom:1px solid #e4e4e7;text-align:center">${it.qty || 1}</td>
        </tr>`
      ).join('')

      const html = `<!DOCTYPE html>
    <html><head><meta charset="UTF-8"/>
    <style>
      body{font-family:sans-serif;color:#09090b;padding:40px;max-width:600px;margin:auto}
      h1{font-size:22px;font-weight:700;margin-bottom:4px}
      .meta{font-size:12px;color:#71717a;margin-bottom:24px}
      .label{font-size:10px;font-weight:600;letter-spacing:1px;text-transform:uppercase;color:#a1a1aa;margin-bottom:6px}
      .val{font-size:14px;font-weight:500}
      .row{display:flex;justify-content:space-between;padding:8px 0;border-bottom:1px solid #e4e4e7;font-size:13px}
      table{width:100%;border-collapse:collapse;margin-top:8px}
      th{padding:8px 12px;background:#f7f7f8;font-size:10px;font-weight:600;letter-spacing:1px;text-transform:uppercase;color:#a1a1aa;text-align:left;border-bottom:1.5px solid #e4e4e7}
      .total{text-align:right;margin-top:16px;font-size:16px;font-weight:700}
    </style>
    </head><body>
      <h1>Invoice</h1>
      <div class="meta">${order.id} · Generated ${new Date().toLocaleDateString('en-IN',{day:'numeric',month:'short',year:'numeric'})}</div>
      <div class="row"><span style="color:#71717a">Customer</span><span>${order.customer}</span></div>
      <div class="row"><span style="color:#71717a">Shop</span><span>${order.shop}</span></div>
      <div class="row"><span style="color:#71717a">Placed On</span><span>${order.placedOn}</span></div>
      <div class="row"><span style="color:#71717a">Carrier</span><span>${order.transport || '—'}</span></div>
      <table>
        <thead><tr><th>Item</th><th style="text-align:center">Qty</th></tr></thead>
        <tbody>${lines}</tbody>
      </table>
      <div class="total">Total: ${order.value}</div>
    </body></html>`

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
  cursor: grab; user-select: none;
  transition: border-color 0.12s, box-shadow 0.12s, transform 0.12s;
  position: relative; overflow: hidden;
  border-top: 2.5px solid transparent;
  animation: fadeUp 0.18s ease both;
}
.ocard:hover {
  border-color: var(--border);
  box-shadow: 0 2px 12px rgba(0,0,0,.07);
  transform: translateY(-1px);
}
.ocard.dragging         { opacity: 0.3; cursor: grabbing; transform: scale(0.97); }
.ocard.drag-over-top    { box-shadow: 0 -3px 0 0 var(--blue); }
.ocard.drag-over-bottom { box-shadow: 0 3px 0 0 var(--blue); }
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
.irow-name { color: var(--ink-3); }
.irow-qty  { font-family: 'Geist Mono', monospace; font-size: 10px; font-weight: 500; color: var(--ink-3); }

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

.drag-handle {
  position: absolute; right: 9px; top: 50%; transform: translateY(-50%);
  color: var(--ink-4); font-size: 12px; opacity: 0;
  transition: opacity 0.12s; cursor: grab; padding: 3px;
}
.ocard:hover .drag-handle { opacity: 0.5; }

/* ADD at bottom of <style scoped> */
.dl-invoice-btn {
  background: none; border: 1.5px solid var(--border); border-radius: 4px;
  padding: 2px 8px; font-size: 10.5px; font-weight: 600; color: var(--blue);
  cursor: pointer; font-family: 'Geist', sans-serif; transition: all 0.12s;
}
.dl-invoice-btn:hover { background: var(--blue-dim); border-color: var(--blue); }
</style>