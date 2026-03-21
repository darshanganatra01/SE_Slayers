<template>
  <div v-if="visible" class="mo" @click.self="$emit('close')">
    <div class="mo-box">

      <div class="mo-head">
        <div class="mo-title">Procurement Request</div>
        <div class="mo-x" @click="$emit('close')">✕</div>
      </div>

      <div class="mo-body">
        <!-- Part info (read-only) -->
        <div class="mo-row">
          <div class="fg">
            <label class="fl">Part Name</label>
            <input class="fi fi-readonly" :value="form.partName" readonly />
          </div>
          <div class="fg">
            <label class="fl">Size</label>
            <input class="fi fi-readonly" :value="form.partCode" readonly />
          </div>
        </div>

        <!-- Selected vendor (read-only) -->
        <div class="fg">
          <label class="fl">Selected Vendor</label>
          <input class="fi fi-readonly" :value="vendorDisplayName" readonly />
        </div>

        <!-- Quantity + Required By -->
        <div class="mo-row">
          <div class="fg">
            <label class="fl">Quantity</label>
            <input class="fi" type="number" v-model.number="form.quantity" placeholder="e.g. 50" />
          </div>
          <div class="fg">
            <label class="fl">Required By</label>
            <input class="fi" type="date" v-model="form.requiredBy" />
          </div>
        </div>

        <div class="fg">
          <label class="fl">Notes</label>
          <textarea class="fi mo-textarea" v-model="form.notes" placeholder="Additional notes or instructions…" rows="3"></textarea>
        </div>
      </div>

      <div class="mo-foot">
        <button class="btn-cancel" @click="$emit('close')">Cancel</button>
        <button class="btn btn-primary" @click="submit">Submit Request</button>
      </div>

    </div>
  </div>
</template>

<script>
export default {
  name: 'ProcurementModal',
  props: {
    visible:         { type: Boolean, default: false },
    vendors:         { type: Array,   default: () => [] },
    prefill:         { type: Object,  default: null },
    selectedVendorId:{ type: String,  default: null }
  },
  emits: ['close', 'submit'],
  data() {
    return { form: this.emptyForm() }
  },
  watch: {
    visible(val) {
      if (val) {
        this.form = this.emptyForm()
        if (this.prefill) {
          this.form.partName  = this.prefill.partName  || ''
          this.form.partCode  = this.prefill.partCode  || ''
          this.form.vendorId  = this.prefill.vendorId  || ''
        }
      }
    }
  },
  computed: {
    vendorDisplayName() {
      if (!this.form.vendorId) return '—'
      return this.vendors.find(v => v.id === this.form.vendorId)?.name || this.form.vendorId
    }
  },
  methods: {
    emptyForm() {
      return { partName: '', partCode: '', quantity: null, vendorId: '', requiredBy: '', notes: '' }
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
.mo-textarea { resize: vertical; min-height: 60px; font-family: 'Geist', sans-serif; }

/* Read-only field styling */
.fi-readonly {
  background: var(--surface) !important;
  color: var(--ink-2) !important;
  cursor: default;
  border-color: var(--border-2) !important;
}
</style>
