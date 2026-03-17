<template>
  <div class="dp" :class="{ open: !!order }">
    <template v-if="order">

      <div class="dp-head">
        <div class="dp-close-row">
          <div class="dp-oid">{{ order.id }}</div>
          <button class="dp-close-btn" @click="$emit('close')">Close ✕</button>
        </div>
        <div class="dp-name">{{ order.customer }}</div>
        <div class="dp-chips-row">
          <span class="chip" :style="{ background: PB[order.priority], color: PC[order.priority] }">{{ order.priority }} Priority</span>
          <span class="chip" :style="{ background: CB[order.custType],  color: CC[order.custType]  }">{{ CL[order.custType] }}</span>
        </div>
      </div>

      <div class="dp-scroll">

        <div>
          <div class="dp-sec-label">Details</div>
          <div class="dp-kv"><span class="k">Value</span>    <span class="v" style="color:var(--green)">{{ order.value }}</span></div>
          <div class="dp-kv"><span class="k">Deadline</span> <span class="v">{{ order.deadline }}</span></div>
          <div class="dp-kv"><span class="k">Shop</span>     <span class="v">{{ order.shop }}</span></div>
          <div class="dp-kv"><span class="k">Status</span>   <span class="v" :style="{ color: SC[order.status] }">{{ SL[order.status] }}</span></div>
        </div>

        <div>
          <div class="dp-sec-label">Items ({{ order.items.length }})</div>
          <div v-for="(it, i) in order.items" :key="i" class="dp-item-row">
            <span>{{ it.name }}</span>
            <span :class="it.inStock ? 'istock-y' : 'istock-n'">{{ it.inStock ? '✓ In stock' : '✕ Out' }}</span>
          </div>
        </div>

        <div v-if="order.status === 'packed'">
          <div class="dp-sec-label">Packing</div>
          <div class="dp-kv"><span class="k">Packages</span> <span class="v">{{ order.packages || 1 }}</span></div>
          <div class="dp-kv"><span class="k">Cost</span>     <span class="v">{{ order.packagingCost || '—' }}</span></div>
        </div>

        <div v-if="order.status === 'shipped'">
          <div class="dp-sec-label">Shipping</div>
          <div class="dp-kv"><span class="k">Carrier</span> <span class="v">{{ order.transport || '—' }}</span></div>
          <div class="dp-kv"><span class="k">Cost</span>    <span class="v">{{ order.shippingCost || '—' }}</span></div>
        </div>

      </div>

      <div class="dp-footer">
        <div class="dp-flow-label">Status flow</div>
        <div class="dp-flow">
          <template v-for="(s, i) in steps" :key="s">
            <div class="df-step" :class="{ done: i < currentStep, current: i === currentStep }">{{ SL[s] }}</div>
            <div v-if="i < steps.length - 1" class="df-arrow">›</div>
          </template>
        </div>
        <button
          v-if="order.status !== 'shipped'"
          class="dp-action-btn dp-btn-fwd"
          @click="$emit('promote', { id: order.id, newStatus: nextStatus })"
        >
          → Mark as {{ SL[nextStatus] }}
        </button>
        <button
          v-if="order.status !== 'inprocess'"
          class="dp-action-btn dp-btn-back"
          @click="$emit('promote', { id: order.id, newStatus: prevStatus })"
        >
          ← Back to {{ SL[prevStatus] }}
        </button>
      </div>

    </template>
  </div>
</template>

<script>
import { CC, CB, CL, PC, PB, SC, SL } from '../store.js'

export default {
  name: 'OrderDetailPanel',
  props: {
    order: { type: Object, default: null }
  },
  emits: ['close', 'promote'],
  data() {
    return { CC, CB, CL, PC, PB, SC, SL, steps: ['inprocess', 'packed', 'shipped'] }
  },
  computed: {
    currentStep() { return this.steps.indexOf(this.order?.status) },
    nextStatus()  { return this.steps[this.currentStep + 1] },
    prevStatus()  { return this.steps[this.currentStep - 1] }
  }
}
</script>

<style scoped>
.dp {
  width: 0; flex-shrink: 0; overflow: hidden;
  background: var(--white);
  border-left: 1.5px solid var(--border);
  display: flex; flex-direction: column;
  transition: width 0.24s cubic-bezier(0.4,0,0.2,1);
}
.dp.open { width: 300px; }

.dp-head {
  padding: 14px 18px 12px;
  border-bottom: 1.5px solid var(--border);
  flex-shrink: 0;
}
.dp-close-row { display: flex; align-items: center; justify-content: space-between; margin-bottom: 10px; }
.dp-oid       { font-family: 'Geist Mono', monospace; font-size: 10.5px; color: var(--blue); }
.dp-close-btn {
  background: none; border: 1.5px solid var(--border); border-radius: 5px;
  padding: 3px 10px; font-size: 10.5px; color: var(--ink-3); cursor: pointer;
  font-family: 'Geist', sans-serif; font-weight: 600; transition: all 0.12s;
}
.dp-close-btn:hover { background: var(--ink); color: #fff; border-color: var(--ink); }
.dp-name      { font-size: 17px; font-weight: 600; color: var(--ink); letter-spacing: -0.3px; margin-bottom: 7px; line-height: 1.2; }
.dp-chips-row { display: flex; gap: 5px; flex-wrap: wrap; }

.dp-scroll {
  flex: 1; overflow-y: auto; padding: 14px 18px;
  display: flex; flex-direction: column; gap: 14px;
}
.dp-scroll::-webkit-scrollbar { width: 3px; }
.dp-scroll::-webkit-scrollbar-thumb { background: var(--border-2); }

.dp-sec-label {
  font-size: 9.5px; font-weight: 600; color: var(--ink-4);
  letter-spacing: 1.5px; text-transform: uppercase; margin-bottom: 8px;
  display: flex; align-items: center; gap: 8px;
}
.dp-sec-label::after { content: ''; flex: 1; height: 1px; background: var(--border-2); }
.dp-kv   { display: flex; justify-content: space-between; align-items: center; padding: 4px 0; font-size: 12.5px; }
.dp-kv .k { color: var(--ink-4); }
.dp-kv .v { color: var(--ink); font-weight: 500; }

.dp-item-row {
  display: flex; justify-content: space-between; align-items: center;
  padding: 6px 10px; border-radius: 6px; font-size: 12px;
  background: var(--surface); border: 1px solid var(--border-2); margin-bottom: 4px;
}
.dp-item-row:last-child { margin-bottom: 0; }
.istock-y { font-size: 10px; font-weight: 600; color: var(--green); }
.istock-n { font-size: 10px; font-weight: 600; color: var(--red); }

.dp-footer {
  padding: 12px 18px;
  border-top: 1.5px solid var(--border);
  flex-shrink: 0;
}
.dp-flow-label { font-size: 9.5px; font-weight: 600; color: var(--ink-4); letter-spacing: 1.5px; text-transform: uppercase; margin-bottom: 8px; }
.dp-flow       { display: flex; align-items: center; gap: 4px; margin-bottom: 10px; }
.df-step {
  flex: 1; padding: 5px 4px; border-radius: 5px;
  border: 1px solid var(--border-2); background: var(--surface);
  text-align: center; font-size: 9px; font-weight: 600;
  font-family: 'Geist', sans-serif; letter-spacing: 0.3px; text-transform: uppercase;
  color: var(--ink-4); transition: all 0.15s;
}
.df-step.done    { background: var(--green-dim); border-color: #86efac; color: var(--green); }
.df-step.current { background: var(--ink); border-color: var(--ink); color: #fff; }
.df-arrow { color: var(--ink-4); font-size: 10px; flex-shrink: 0; }

.dp-action-btn {
  width: 100%; padding: 9px; border-radius: 6px;
  font-family: 'Geist', sans-serif; font-weight: 600; font-size: 12px;
  cursor: pointer; transition: all 0.12s; border: none;
  margin-bottom: 6px; display: flex; align-items: center; justify-content: center; gap: 5px;
}
.dp-action-btn:last-child { margin-bottom: 0; }
.dp-btn-fwd { background: var(--blue); color: #fff; }
.dp-btn-fwd:hover { background: #1d4ed8; }
.dp-btn-back { background: transparent; border: 1.5px solid var(--border) !important; color: var(--ink-2); }
.dp-btn-back:hover { border-color: var(--ink) !important; color: var(--ink); }
</style>