<template>
  <div v-if="visible" class="movl" @click.self="$emit('close')">
    <div class="modal">
      <div class="modal-head">
        <span class="modal-title">Add new part</span>
        <button class="modal-x" @click="$emit('close')">×</button>
      </div>
      <div class="modal-body">
        <div class="form-row">
          <div class="ff full">
            <label class="fl2">Part name</label>
            <input class="fi2" type="text" v-model="form.name" placeholder="Enter part name">
          </div>
        </div>
        <div class="form-row">
          <div class="ff">
            <label class="fl2">SKU / Part code</label>
            <input class="fi2" type="text" v-model="form.sku" placeholder="Enter SKU">
          </div>
          <div class="ff">
            <label class="fl2">Category</label>
            <input class="fi2" type="text" v-model="form.category" list="inventory-categories" placeholder="Enter category">
            <datalist id="inventory-categories">
              <option v-for="category in categories" :key="category" :value="category"></option>
            </datalist>
          </div>
        </div>
        <div class="form-divider">Size &amp; Dimensions</div>
        <div class="form-row">
          <div class="ff">
            <label class="fl2">Size (inches)</label>
            <input class="fi2" type="text" v-model="form.size" placeholder="Enter size">
          </div>
          <div class="ff">
            <label class="fl2">Diameter / Range</label>
            <input class="fi2" type="text" v-model="form.dims" placeholder="Enter dimensions">
          </div>
        </div>
        <div class="form-row">
          <div class="ff full">
            <label class="fl2">Additional spec</label>
            <input class="fi2" type="text" v-model="form.spec" placeholder="Enter specification details">
            <span class="form-hint">Bolt size, thread pitch, pressure rating etc.</span>
          </div>
        </div>
        <div class="form-divider">Stock &amp; Pricing</div>
        <div class="form-row form-row-3">
          <div class="ff">
            <label class="fl2">Opening stock</label>
            <input class="fi2" type="number" v-model="form.openingStock" placeholder="0">
          </div>
          <div class="ff">
            <label class="fl2">Threshold</label>
            <input class="fi2" type="number" v-model="form.threshold" placeholder="5">
          </div>
          <div class="ff">
            <label class="fl2">Unit</label>
            <select class="fi2" v-model="form.unit">
              <option>per piece</option>
              <option>per 12 pcs</option>
              <option>per bag</option>
              <option>per dozen</option>
            </select>
          </div>
        </div>
        <div class="form-row">
          <div class="ff">
            <label class="fl2">Buy price (₹)</label>
            <input class="fi2" type="number" v-model="form.buyPrice" placeholder="0">
          </div>
          <div class="ff">
            <label class="fl2">Sell price (₹)</label>
            <input class="fi2" type="number" v-model="form.sellPrice" placeholder="0">
          </div>
        </div>
      </div>
      <div class="modal-foot">
        <button class="btn btn-outline" @click="$emit('close')">Cancel</button>
        <button class="btn btn-primary" @click="submit">Add part</button>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'AddPartModal',
  props: {
    visible: { type: Boolean, default: false },
    categories: { type: Array, default: () => [] }
  },
  emits: ['close', 'submit'],
  data() {
    return {
      form: this.emptyForm()
    }
  },
  watch: {
    visible(v) {
      if (v) this.form = this.emptyForm()
    }
  },
  methods: {
    emptyForm() {
      return {
        name: '', sku: '', category: '',
        size: '', dims: '', spec: '',
        openingStock: '', threshold: '', unit: 'per piece',
        buyPrice: '', sellPrice: ''
      }
    },
    submit() {
      this.$emit('submit', { ...this.form })
      this.$emit('close')
    }
  }
}
</script>

<style scoped>
.movl {
  position: fixed; inset: 0;
  background: rgba(0,0,0,0.18);
  display: grid; place-items: center;
  z-index: 200;
}
.modal {
  background: var(--white);
  border-radius: 10px;
  width: 460px; max-width: 94vw;
  box-shadow: 0 8px 32px rgba(0,0,0,0.12);
}
.modal-head {
  display: flex; align-items: center;
  justify-content: space-between;
  padding: 15px 18px 13px;
  border-bottom: 1px solid var(--border);
}
.modal-title { font-size: 14px; font-weight: 600; }
.modal-x {
  width: 26px; height: 26px;
  border-radius: 50%;
  border: 1px solid var(--border);
  background: var(--surface);
  cursor: pointer; display: grid; place-items: center;
  font-size: 16px; color: var(--ink-4);
}
.modal-x:hover { background: var(--border); }

.modal-body {
  padding: 16px 18px;
  display: flex; flex-direction: column; gap: 11px;
}
.form-row {
  display: grid; grid-template-columns: 1fr 1fr; gap: 10px;
}
.form-row-3 {
  grid-template-columns: 1fr 1fr 1fr;
}
.ff {
  display: flex; flex-direction: column; gap: 4px;
}
.ff.full { grid-column: 1 / -1; }
.fl2 {
  font-size: 11.5px; font-weight: 500; color: var(--ink-3);
}
.fi2 {
  padding: 7px 10px;
  border: 1.5px solid var(--border);
  border-radius: 6px;
  font-family: 'Geist', sans-serif;
  font-size: 12.5px; color: var(--ink);
  background: var(--white); outline: none;
}
.fi2:focus {
  border-color: var(--blue);
  box-shadow: 0 0 0 2px rgba(37,99,235,.08);
}
.form-hint {
  font-size: 11px; color: var(--ink-4);
}
.form-divider {
  font-size: 11px; font-weight: 600;
  text-transform: uppercase; letter-spacing: .06em;
  color: var(--ink-4);
  border-top: 1px solid var(--border);
  padding-top: 10px;
}

.modal-foot {
  display: flex; gap: 8px; justify-content: flex-end;
  padding: 11px 18px;
  border-top: 1px solid var(--border);
  background: var(--surface);
  border-radius: 0 0 10px 10px;
}
.btn {
  display: inline-flex; align-items: center; gap: 5px;
  padding: 5px 12px; border-radius: 5px;
  font-size: 12.5px; font-weight: 500;
  cursor: pointer; font-family: 'Geist', sans-serif;
  border: none; transition: all 0.1s; white-space: nowrap;
}
.btn-primary       { background: var(--blue); color: #fff; }
.btn-primary:hover { background: #1d4ed8; }
.btn-outline       { background: transparent; color: var(--ink-3); border: 1.5px solid var(--border); }
.btn-outline:hover { border-color: var(--ink-3); color: var(--ink); }
</style>
