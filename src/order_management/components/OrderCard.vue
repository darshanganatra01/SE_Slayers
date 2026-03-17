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
        <span class="chip" :style="{ background: CB[order.custType], color: CC[order.custType] }">{{ order.custType }}</span>
      </div>
    </div>

    <div class="oc-body">
      <div class="oc-name">{{ order.customer }}</div>
      <div class="oc-sub">
        <span class="cust-pip" :style="{ background: CC[order.custType] }"></span>
        {{ order.shop }}
      </div>
      <div class="items-wrap">
        <div v-for="(it, i) in order.items" :key="i" class="irow">
          <span class="irow-name">{{ it.name }}</span>
          <span :class="it.inStock ? 'istock-y' : 'istock-n'">{{ it.inStock ? '✓ In stock' : '✕ Out' }}</span>
        </div>
      </div>
    </div>

    <div v-if="order.status === 'packed'" class="oc-extra">
      <span>📦 {{ order.packages || 1 }} pkg</span>
      <span>{{ order.packagingCost || '—' }}</span>
    </div>
    <div v-if="order.status === 'shipped'" class="oc-extra">
      <span>🚚 {{ order.transport || '—' }}</span>
      <span>{{ order.shippingCost || '—' }}</span>
    </div>

    <div class="oc-foot">
      <span class="oc-val">{{ order.value }}</span>
      <span class="oc-dl">Due {{ order.deadline }}</span>
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
.istock-y  { font-size: 10px; font-weight: 600; color: var(--green); }
.istock-n  { font-size: 10px; font-weight: 600; color: var(--red); }

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
</style>