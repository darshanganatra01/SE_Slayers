<template>
  <div v-if="visible" class="mo" @click.self="$emit('close')">
    <div class="mo-box">

      <div class="mo-head">
        <div class="mo-title">New Order</div>
        <div class="mo-x" @click="$emit('close')">✕</div>
      </div>

      <div class="mo-body">
        <div class="mo-row">
          <div class="fg">
            <label class="fl">Customer Name</label>
            <input class="fi" v-model="form.customer" placeholder="Full name" />
          </div>
          <div class="fg">
            <label class="fl">Customer Type</label>
            <select class="fi" v-model="form.custType">
              <option value="VIP">👑 VIP</option>
              <option value="Regular">⭐ Regular</option>
              <option value="Delayed">⚠ Delayed</option>
              <option value="New">🆕 New</option>
            </select>
          </div>
        </div>

        <div class="mo-row">
          <div class="fg">
            <label class="fl">Priority</label>
            <select class="fi" v-model="form.priority">
              <option value="High">High</option>
              <option value="Medium">Medium</option>
              <option value="Low">Low</option>
            </select>
          </div>
          <div class="fg">
            <label class="fl">Order Value (₹)</label>
            <input class="fi" v-model="form.value" placeholder="e.g. 12000" />
          </div>
        </div>

        <div class="mo-row">
          <div class="fg">
            <label class="fl">Deadline</label>
            <input class="fi" type="date" v-model="form.deadline" />
          </div>
          <div class="fg">
            <label class="fl">Shop / Location</label>
            <input class="fi" v-model="form.shop" placeholder="e.g. Chennai Central" />
          </div>
        </div>

        <div class="fg">
          <label class="fl">Items (comma separated)</label>
          <input class="fi" v-model="form.items" placeholder="e.g. Brake Pads B200, Oil Filter OF-7" />
        </div>
      </div>

      <div class="mo-foot">
        <button class="btn-cancel" @click="$emit('close')">Cancel</button>
        <button class="btn btn-primary" @click="submit">Create order</button>
      </div>

    </div>
  </div>
</template>

<script>
export default {
  name: 'NewOrderModal',
  props: {
    visible: { type: Boolean, default: false }
  },
  emits: ['close', 'submit'],
  data() {
    return {
      form: { customer: '', custType: 'Regular', priority: 'Medium', value: '', deadline: '', shop: '', items: '' }
    }
  },
  methods: {
    submit() {
      this.$emit('submit', { ...this.form })
      this.form = { customer: '', custType: 'Regular', priority: 'Medium', value: '', deadline: '', shop: '', items: '' }
    }
  }
}
</script>

<style scoped>
.mo {
  position: fixed; inset: 0; background: rgba(0,0,0,.45); z-index: 200;
  display: flex; align-items: center; justify-content: center;
  backdrop-filter: blur(2px);
}
.mo-box {
  background: var(--white); border: 1.5px solid var(--border);
  border-radius: 10px; width: 480px;
  max-height: 86vh; overflow-y: auto;
  box-shadow: 0 8px 30px rgba(0,0,0,.12);
}
.mo-head {
  padding: 18px 20px 14px; border-bottom: 1.5px solid var(--border);
  display: flex; justify-content: space-between; align-items: center;
}
.mo-title { font-size: 16px; font-weight: 600; color: var(--ink); letter-spacing: -0.2px; }
.mo-x {
  background: none; border: 1.5px solid var(--border); border-radius: 6px;
  width: 26px; height: 26px; display: flex; align-items: center; justify-content: center;
  color: var(--ink-3); font-size: 12px; cursor: pointer; transition: all 0.12s;
}
.mo-x:hover { background: var(--ink); color: #fff; border-color: var(--ink); }
.mo-body { padding: 18px 20px; display: flex; flex-direction: column; gap: 12px; }
.mo-row  { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }
.mo-foot {
  padding: 12px 20px; border-top: 1.5px solid var(--border);
  display: flex; justify-content: flex-end; gap: 7px;
}
</style>