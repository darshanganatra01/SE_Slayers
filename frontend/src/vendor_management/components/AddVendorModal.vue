<template>
  <div v-if="visible" class="mo" @click.self="$emit('close')">
    <div class="mo-box">

      <div class="mo-head">
        <div class="mo-title">Add Vendor</div>
        <div class="mo-x" @click="$emit('close')">✕</div>
      </div>

      <div class="mo-body">
        <div class="mo-row">
          <div class="fg">
            <label class="fl">Vendor Name</label>
            <input class="fi" v-model="form.name" placeholder="e.g. ABC Auto Parts" />
          </div>
          <div class="fg">
            <label class="fl">Vendor ID</label>
            <input class="fi" v-model="form.id" placeholder="e.g. VND-007" />
          </div>
        </div>

        <div class="mo-row">
          <div class="fg">
            <label class="fl">Location</label>
            <input class="fi" v-model="form.location" placeholder="e.g. Chennai" />
          </div>
          <div class="fg">
            <label class="fl">Lead Time (days)</label>
            <input class="fi" type="number" v-model.number="form.leadTime" placeholder="e.g. 3" />
          </div>
        </div>

        <div class="mo-row">
          <div class="fg">
            <label class="fl">Phone</label>
            <input class="fi" v-model="form.phone" placeholder="+91 98401 12345" />
          </div>
          <div class="fg">
            <label class="fl">Email</label>
            <input class="fi" type="email" v-model="form.email" placeholder="sales@example.com" />
          </div>
        </div>

        <div class="fg">
          <label class="fl">Parts Supplied (comma separated)</label>
          <input class="fi" v-model="form.parts" placeholder="e.g. S.S. Step Nipple, Hose Clip (Light)" />
        </div>
      </div>

      <div class="mo-foot">
        <button class="btn-cancel" @click="$emit('close')">Cancel</button>
        <button class="btn btn-primary" @click="submit">Add Vendor</button>
      </div>

    </div>
  </div>
</template>

<script>
export default {
  name: 'AddVendorModal',
  props: {
    visible: { type: Boolean, default: false }
  },
  emits: ['close', 'submit'],
  data() {
    return { form: this.emptyForm() }
  },
  methods: {
    emptyForm() {
      return { name: '', id: '', location: '', leadTime: 3, phone: '', email: '', parts: '' }
    },
    submit() {
      this.$emit('submit', { ...this.form })
      this.form = this.emptyForm()
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
  border-radius: 10px; width: 460px;
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
