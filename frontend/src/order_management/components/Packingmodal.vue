<template>
  <teleport to="body">
    <div v-if="visible" class="pk-overlay" @click.self="$emit('cancel')">
      <div class="pk-box">

        <div class="pk-head">
          <div>
            <div class="pk-title">Confirm Packing</div>
            <div class="pk-sub">{{ orderId }} · Set quantities before packing</div>
          </div>
          <button class="pk-close" @click="$emit('cancel')">✕</button>
        </div>

        <div class="pk-body">
          <div class="pk-item" v-for="(item, i) in localItems" :key="i">
            <div class="pk-item-info">
              <div class="pk-item-name">{{ item.name }}</div>
              <div v-if="item.specs" class="pk-item-specs">{{ item.specs }}</div>
              <div class="pk-item-hint">
                {{ item.packed_qty }} of {{ item.ordered_qty }} already packed
                <span v-if="item.ordered_qty - item.packed_qty > 0">
                  · {{ item.ordered_qty - item.packed_qty }} remaining
                </span>
              </div>
            </div>
            <div class="pk-qty-row">
              <button class="qty-btn" @click="decrement(i)" :disabled="item.qty <= 0">−</button>
              <div class="qty-val">{{ item.qty }}</div>
              <button class="qty-btn" @click="increment(i)" :disabled="item.packed_qty + item.qty >= item.ordered_qty">+</button>
            </div>
          </div>
        </div>

        <div class="pk-foot">
          <div class="pk-total">
            Total items: <strong>{{ totalQty }}</strong>
          </div>
          <div class="pk-actions">
            <button class="btn-cancel" @click="$emit('cancel')">Cancel</button>
            <button class="btn btn-primary" @click="confirm">📦 Confirm Packed</button>
          </div>
        </div>

      </div>
    </div>
  </teleport>
</template>

<script>
export default {
  name: 'PackingModal',
  props: {
    visible:  { type: Boolean, default: false },
    orderId:  { type: String,  default: '' },
    items:    { type: Array,   default: () => [] }
  },
  emits: ['cancel', 'confirm'],
  data() {
    return { localItems: [] }
  },
  computed: {
    totalQty() { return this.localItems.reduce((s, i) => s + i.qty, 0) }
  },
  watch: {
    // Re-initialise local copy whenever modal opens with new items
    visible(val) {
      if (val) {
        this.localItems = this.items.map(it => {
          const remaining = (it.qty || 0) - (it.packed_qty || 0)
          return {
            name: it.name,
            skuid: it.skuid,
            specs: it.specs || '',
            ordered_qty: it.qty || 0,
            packed_qty: it.packed_qty || 0,
            qty: Math.max(0, remaining)
          }
        })
      }
    }
  },
  methods: {
    increment(i) { this.localItems[i].qty++ },
    decrement(i) { if (this.localItems[i].qty > 0) this.localItems[i].qty-- },
    confirm() {
      this.$emit('confirm', this.localItems.map(it => ({ ...it })))
    }
  }
}
</script>

<style scoped>
.pk-overlay {
  position: fixed; inset: 0; background: rgba(0,0,0,.45); z-index: 400;
  display: flex; align-items: center; justify-content: center;
  backdrop-filter: blur(2px);
}
.pk-box {
  background: var(--white); border: 1.5px solid var(--border);
  border-radius: 10px; width: 400px; max-height: 80vh;
  display: flex; flex-direction: column;
  box-shadow: 0 8px 30px rgba(0,0,0,.14);
  animation: popIn .18s cubic-bezier(0.34,1.56,0.64,1) both;
}
@keyframes popIn {
  from { opacity: 0; transform: scale(0.94); }
  to   { opacity: 1; transform: scale(1); }
}

.pk-head {
  padding: 16px 18px 14px; border-bottom: 1.5px solid var(--border);
  display: flex; justify-content: space-between; align-items: flex-start;
  flex-shrink: 0;
}
.pk-title { font-size: 15px; font-weight: 600; color: var(--ink); letter-spacing: -0.2px; }
.pk-sub   { font-size: 11px; color: var(--ink-4); font-family: 'Geist Mono', monospace; margin-top: 3px; }
.pk-close {
  background: none; border: 1.5px solid var(--border); border-radius: 5px;
  width: 26px; height: 26px; display: flex; align-items: center; justify-content: center;
  color: var(--ink-3); font-size: 11px; cursor: pointer; transition: all 0.12s; flex-shrink: 0;
}
.pk-close:hover { background: var(--ink); color: #fff; border-color: var(--ink); }

.pk-body {
  flex: 1; overflow-y: auto; padding: 12px 18px;
  display: flex; flex-direction: column; gap: 8px;
}
.pk-body::-webkit-scrollbar { width: 3px; }
.pk-body::-webkit-scrollbar-thumb { background: var(--border-2); }

.pk-item {
  display: flex; align-items: center; justify-content: space-between;
  padding: 10px 14px; background: var(--surface);
  border: 1.5px solid var(--border-2); border-radius: 8px;
  transition: border-color 0.12s;
}
.pk-item:hover { border-color: var(--border); }
.pk-item-info { display: flex; flex-direction: column; gap: 2px; flex: 1; min-width: 0; }
.pk-item-name { font-size: 13.5px; font-weight: 500; color: var(--ink); }
.pk-item-specs { font-size: 10.5px; color: var(--ink-4); line-height: 1.4; padding-right: 10px; }
.pk-item-hint { font-size: 10px; color: var(--blue); font-weight: 500; margin-top: 2px; }

.pk-qty-row { display: flex; align-items: center; gap: 0; flex-shrink: 0; }
.qty-btn {
  width: 30px; height: 30px; border-radius: 6px;
  border: 1.5px solid var(--border); background: var(--white);
  color: var(--ink); font-size: 16px; font-weight: 500;
  cursor: pointer; display: flex; align-items: center; justify-content: center;
  transition: all 0.12s; line-height: 1;
}
.qty-btn:hover:not(:disabled) { background: var(--blue); color: #fff; border-color: var(--blue); }
.qty-btn:disabled { opacity: 0.3; cursor: not-allowed; }
.qty-val {
  min-width: 40px; text-align: center;
  font-family: 'Geist Mono', monospace; font-size: 15px; font-weight: 600;
  color: var(--ink);
}

.pk-foot {
  padding: 12px 18px; border-top: 1.5px solid var(--border);
  display: flex; align-items: center; justify-content: space-between;
  flex-shrink: 0;
}
.pk-total   { font-size: 12px; color: var(--ink-3); }
.pk-total strong { color: var(--ink); font-size: 13px; }
.pk-actions { display: flex; gap: 7px; }
</style>